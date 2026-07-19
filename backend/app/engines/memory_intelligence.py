import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.database_models import MemoryItem, KnowledgeNode

def sm2_update(q: int, interval: int, ease_factor: float, repetitions: int) -> Tuple[int, float, int]:
    """Applies the SM-2 spaced repetition algorithm adjustments.
    
    Returns (new_interval, new_ease_factor, new_repetitions)
    q: Grade/rating from 0 (forgot) to 5 (perfect recall)
    """
    if q >= 3:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = int(round(interval * ease_factor))
        new_repetitions = repetitions + 1
    else:
        new_repetitions = 0
        new_interval = 1
        
    # Adjust ease factor
    new_ease_factor = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3
        
    return new_interval, round(new_ease_factor, 3), new_repetitions

def calculate_retention(last_reviewed: datetime, interval: int, ease_factor: float, repetitions: int) -> float:
    """Calculates retention percentage using exponential forgetting curve: R = exp(-t / S)
    where t is days since last review and S is memory strength.
    """
    now = datetime.utcnow()
    delta_days = (now - last_reviewed).total_seconds() / (24 * 3600.0)
    
    # Memory strength S increases with repetitions and ease factor
    memory_strength = ease_factor * (repetitions + 0.5)
    if memory_strength <= 0:
        memory_strength = 0.5
        
    # Calculate retention
    retention = math.exp(-delta_days / memory_strength)
    return max(0.01, min(1.0, retention))

def update_memory_state(db: Session, user_id: int, concept_id: str, score: int) -> MemoryItem:
    """Updates or inserts a memory tracking item for a user and a specific concept."""
    item = db.query(MemoryItem).filter(
        MemoryItem.user_id == user_id, 
        MemoryItem.concept_id == concept_id
    ).first()
    
    now = datetime.utcnow()
    
    if not item:
        interval, ease_factor, reps = sm2_update(score, 0, 2.5, 0)
        item = MemoryItem(
            user_id=user_id,
            concept_id=concept_id,
            interval=interval,
            ease_factor=ease_factor,
            repetitions=reps,
            last_reviewed=now,
            next_review=now + timedelta(days=interval)
        )
        db.add(item)
    else:
        interval, ease_factor, reps = sm2_update(
            score, item.interval, item.ease_factor, item.repetitions
        )
        item.interval = interval
        item.ease_factor = ease_factor
        item.repetitions = reps
        item.last_reviewed = now
        item.next_review = now + timedelta(days=interval)
        db.add(item)
        
    db.commit()
    db.refresh(item)
    
    # Mirror the memory update to node mastery and confidence
    node = db.query(KnowledgeNode).filter(
        KnowledgeNode.user_id == user_id,
        KnowledgeNode.concept_id == concept_id
    ).first()
    if node:
        # Scale mastery based on repetitions and performance score
        new_mastery = min(1.0, 0.2 + (item.repetitions * 0.15) + (score * 0.05))
        node.mastery = round(new_mastery, 3)
        node.confidence = round(0.4 + (score * 0.1), 3)
        node.status = "mastered" if new_mastery > 0.8 else "in_progress"
        db.add(node)
        db.commit()
        
    return item

def get_revision_recommendations(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Analyzes memory items, lists items due for revision sorted by urgency (low retention)."""
    items = db.query(MemoryItem).filter(MemoryItem.user_id == user_id).all()
    recommendations = []
    
    for item in items:
        node = db.query(KnowledgeNode).filter(
            KnowledgeNode.user_id == user_id,
            KnowledgeNode.concept_id == item.concept_id
        ).first()
        
        if not node:
            continue
            
        retention = calculate_retention(
            item.last_reviewed, item.interval, item.ease_factor, item.repetitions
        )
        
        # Urgency is higher if retention is lower
        urgency = 1.0 - retention
        
        # Highlight item if it's past its next review date or retention drops below 75%
        now = datetime.utcnow()
        if now >= item.next_review or retention < 0.75:
            recommendations.append({
                "concept_id": item.concept_id,
                "title": node.title,
                "retention": round(retention, 3),
                "urgency": round(urgency, 3),
                "next_review": item.next_review,
                "repetitions": item.repetitions,
                "reason": (
                    f"Retention has decayed to {int(retention*100)}%. "
                    f"Next scheduled review was {item.next_review.strftime('%Y-%m-%d')}."
                )
            })
            
    # Sort by urgency descending
    return sorted(recommendations, key=lambda x: x["urgency"], reverse=True)

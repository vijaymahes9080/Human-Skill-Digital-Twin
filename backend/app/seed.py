from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.models.database_models import User, DigitalTwin, KnowledgeNode, KnowledgeEdge, LearningSession, MemoryItem, DecisionLog, ReflectionLog
from backend.app.engines.core_twin import get_default_twin_state

def seed_db():
    db = SessionLocal()
    try:
        # 1. Reset tables (clean start for developer convenience)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # 2. Create Demo User
        demo_email = "demo@digitaltwin.ai"
        hashed_pwd = get_password_hash("password123")
        user = User(
            email=demo_email,
            hashed_password=hashed_pwd,
            full_name="Alex Mercer",
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # 3. Create Digital Twin State
        twin_state = get_default_twin_state()
        # Mock some active habits and skills matching the initial stats
        twin_state["habits"].update({
            "study_streak": 5,
            "practice_to_theory_ratio": 1.25,
            "total_focus_hours": 14.5
        })
        twin_state["skills"].update({
            "programming": {"level": 0.85, "confidence": 0.90},
            "technical": {"level": 0.70, "confidence": 0.80},
            "research": {"level": 0.50, "confidence": 0.60},
            "problem_solving": {"level": 0.68, "confidence": 0.75},
            "critical_thinking": {"level": 0.72, "confidence": 0.78}
        })
        twin_state["learning_dna"].update({
            "project": {"score": 0.40, "confidence": 0.85},
            "visual": {"score": 0.25, "confidence": 0.65},
            "reading": {"score": 0.20, "confidence": 0.70},
            "audio": {"score": 0.15, "confidence": 0.40}
        })
        
        twin = DigitalTwin(
            user_id=user.id,
            state=twin_state
        )
        db.add(twin)
        
        # 4. Seed Knowledge Graph Nodes (AI/ML Path)
        concepts = [
            {"id": "python_basics", "title": "Advanced Python Programming", "difficulty": 1.5, "mastery": 0.90, "confidence": 0.88, "status": "mastered"},
            {"id": "calculus", "title": "Vector Calculus", "difficulty": 3.0, "mastery": 0.40, "confidence": 0.55, "status": "in_progress"},
            {"id": "linear_algebra", "title": "Linear Algebra for ML", "difficulty": 2.5, "mastery": 0.82, "confidence": 0.78, "status": "mastered"},
            {"id": "statistics", "title": "Probability & Statistics", "difficulty": 2.8, "mastery": 0.76, "confidence": 0.80, "status": "mastered"},
            {"id": "machine_learning", "title": "Supervised & Unsupervised ML", "difficulty": 3.5, "mastery": 0.58, "confidence": 0.64, "status": "in_progress"},
            {"id": "neural_networks", "title": "Neural Networks & Deep Learning", "difficulty": 4.2, "mastery": 0.15, "confidence": 0.20, "status": "in_progress"},
            {"id": "pytorch_framework", "title": "PyTorch Implementations", "difficulty": 4.0, "mastery": 0.0, "confidence": 0.0, "status": "not_started"},
            {"id": "large_language_models", "title": "LLMs & RAG Architectures", "difficulty": 5.0, "mastery": 0.0, "confidence": 0.0, "status": "not_started"}
        ]
        
        node_objs = {}
        for c in concepts:
            node = KnowledgeNode(
                user_id=user.id,
                concept_id=c["id"],
                title=c["title"],
                difficulty=c["difficulty"],
                mastery=c["mastery"],
                confidence=c["confidence"],
                status=c["status"],
                examples=[{"title": f"Introductory Examples for {c['title']}"}],
                projects=[{"title": f"Hands-on project for {c['title']}"}],
                practice_history=[{"date": (datetime.utcnow() - timedelta(days=2)).isoformat(), "score": c["mastery"]}] if c["mastery"] > 0 else []
            )
            db.add(node)
            node_objs[c["id"]] = node
            
        # 5. Seed Knowledge Graph Edges (Prerequisites)
        edges = [
            ("python_basics", "pytorch_framework"),
            ("calculus", "neural_networks"),
            ("linear_algebra", "machine_learning"),
            ("statistics", "machine_learning"),
            ("machine_learning", "neural_networks"),
            ("neural_networks", "pytorch_framework"),
            ("pytorch_framework", "large_language_models")
        ]
        
        for src, dest in edges:
            edge = KnowledgeEdge(
                user_id=user.id,
                source_id=src,
                target_id=dest,
                relation_type="prerequisite"
            )
            db.add(edge)
            
        # 6. Seed Spaced Repetition Memory Items
        now = datetime.utcnow()
        # Seed memory parameters for mastered items
        memories = [
            {"concept_id": "python_basics", "interval": 14, "ease_factor": 2.6, "reps": 4, "last": now - timedelta(days=2)},
            {"concept_id": "linear_algebra", "interval": 8, "ease_factor": 2.4, "reps": 3, "last": now - timedelta(days=3)},
            {"concept_id": "statistics", "interval": 6, "ease_factor": 2.5, "reps": 2, "last": now - timedelta(days=5)}
        ]
        
        for m in memories:
            item = MemoryItem(
                user_id=user.id,
                concept_id=m["concept_id"],
                interval=m["interval"],
                ease_factor=m["ease_factor"],
                repetitions=m["reps"],
                last_reviewed=m["last"],
                next_review=m["last"] + timedelta(days=m["interval"])
            )
            db.add(item)
            
        # 7. Seed Learning Sessions History
        sessions = [
            {"type": "coding", "concept": "python_basics", "duration": 45, "score": 0.95, "offset": 5},
            {"type": "coding", "concept": "python_basics", "duration": 60, "score": 0.90, "offset": 4},
            {"type": "reading", "concept": "linear_algebra", "duration": 30, "score": 0.85, "offset": 3},
            {"type": "reading", "concept": "statistics", "duration": 40, "score": 0.80, "offset": 2},
            {"type": "quiz", "concept": "machine_learning", "duration": 20, "score": 0.65, "offset": 1}
        ]
        
        for s in sessions:
            sess = LearningSession(
                user_id=user.id,
                session_type=s["type"],
                start_time=now - timedelta(days=s["offset"]),
                end_time=now - timedelta(days=s["offset"]) + timedelta(minutes=s["duration"]),
                data={
                    "concept_id": s["concept"],
                    "score": s["score"],
                    "tags": [s["concept"], s["type"]]
                }
            )
            db.add(sess)
            
        # 8. Seed Decision Logs
        decision = DecisionLog(
            user_id=user.id,
            title="Selecting Neural Net Optimization Strategy",
            description="Choosing between SGD with momentum vs Adam optimizer for model learning speed.",
            choice_made="Adam Optimizer",
            risk_level="medium",
            evidence_collected=["Adam provides adaptive learning rates per parameter.", "SGD requires extensive manual tuning of schedules."],
            bias_detected={"confirmation_bias": {"severity": 0.2}},
            decision_speed_seconds=42.0,
            confidence=0.8,
            status="resolved",
            outcome="Successful training rate stabilization, no severe plateaus detected.",
            created_at=now - timedelta(days=1)
        )
        db.add(decision)
        
        db.commit()
        print("Database seeded with mock user 'demo@digitaltwin.ai' (Password: password123) successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()

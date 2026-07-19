from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")

    twin = relationship("DigitalTwin", back_populates="user", uselist=False, cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    knowledge_nodes = relationship("KnowledgeNode", back_populates="user", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")
    decision_logs = relationship("DecisionLog", back_populates="user", cascade="all, delete-orphan")
    reflection_logs = relationship("ReflectionLog", back_populates="user", cascade="all, delete-orphan")

class DigitalTwin(Base):
    __tablename__ = "digital_twins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Stores DNA parameters, general skill levels, habits summary, interests
    state = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="twin")

class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(Float, default=1.0)  # 1 (Beginner) to 5 (Advanced)
    mastery = Column(Float, default=0.0)     # 0.0 to 1.0
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    status = Column(String, default="not_started") # 'not_started', 'in_progress', 'mastered'
    
    # Metadata lists/objects
    examples = Column(JSON, nullable=True, default=list)
    projects = Column(JSON, nullable=True, default=list)
    practice_history = Column(JSON, nullable=True, default=list)
    revision_history = Column(JSON, nullable=True, default=list)

    user = relationship("User", back_populates="knowledge_nodes")

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String, index=True, nullable=False) # source concept_id
    target_id = Column(String, index=True, nullable=False) # target concept_id
    relation_type = Column(String, default="prerequisite") # 'prerequisite', 'related'

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_type = Column(String, nullable=False) # 'reading', 'practice', 'quiz', 'reflection'
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Event metadata, scores, text inputs, quiz options, etc.
    data = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="learning_sessions")

class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(String, index=True, nullable=False)
    
    # SuperMemo parameters
    interval = Column(Integer, default=0)       # Days until next review
    ease_factor = Column(Float, default=2.5)     # Difficulty modifier
    repetitions = Column(Integer, default=0)    # Number of correct iterations
    
    last_reviewed = Column(DateTime, default=datetime.utcnow)
    next_review = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memory_items")

class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    choice_made = Column(String, nullable=False)
    risk_level = Column(String, default="medium") # 'low', 'medium', 'high'
    evidence_collected = Column(JSON, nullable=True, default=list)
    bias_detected = Column(JSON, nullable=True, default=dict)
    decision_speed_seconds = Column(Float, nullable=True)
    confidence = Column(Float, default=0.5)      # 0.0 to 1.0
    status = Column(String, default="pending")   # 'pending', 'resolved'
    outcome = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="decision_logs")

class ReflectionLog(Base):
    __tablename__ = "reflection_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reflection_type = Column(String, nullable=False) # 'daily', 'weekly', 'monthly'
    reflection_date = Column(DateTime, default=datetime.utcnow)
    content = Column(Text, nullable=False)
    
    # Capture state of twin at time of reflection
    digital_twin_snapshot = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="reflection_logs")

from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- AUTH & USER ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[str] = "user"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# --- DIGITAL TWIN ---
class DigitalTwinUpdate(BaseModel):
    state: Dict[str, Any]

class DigitalTwinResponse(BaseModel):
    id: int
    user_id: int
    state: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True

# --- KNOWLEDGE GRAPH ---
class KnowledgeNodeBase(BaseModel):
    concept_id: str
    title: str
    difficulty: float
    mastery: float
    confidence: float
    status: str
    examples: Optional[List[Any]] = []
    projects: Optional[List[Any]] = []
    practice_history: Optional[List[Any]] = []
    revision_history: Optional[List[Any]] = []

class KnowledgeNodeCreate(KnowledgeNodeBase):
    pass

class KnowledgeNodeResponse(KnowledgeNodeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class KnowledgeEdgeBase(BaseModel):
    source_id: str
    target_id: str
    relation_type: Optional[str] = "prerequisite"

class KnowledgeEdgeCreate(KnowledgeEdgeBase):
    pass

class KnowledgeEdgeResponse(KnowledgeEdgeBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class KnowledgeGraphResponse(BaseModel):
    nodes: List[KnowledgeNodeResponse]
    edges: List[KnowledgeEdgeResponse]

# --- SESSIONS ---
class LearningSessionCreate(BaseModel):
    session_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    data: Dict[str, Any]

class LearningSessionResponse(BaseModel):
    id: int
    user_id: int
    session_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    data: Dict[str, Any]

    class Config:
        from_attributes = True

# --- DECISION LOGS ---
class DecisionLogCreate(BaseModel):
    title: str
    description: Optional[str] = None
    choice_made: str
    risk_level: Optional[str] = "medium"
    evidence_collected: Optional[List[str]] = []
    bias_detected: Optional[Dict[str, Any]] = {}
    decision_speed_seconds: Optional[float] = None
    confidence: Optional[float] = 0.5
    status: Optional[str] = "pending"
    outcome: Optional[str] = None

class DecisionLogUpdate(BaseModel):
    status: str
    outcome: Optional[str] = None

class DecisionLogResponse(DecisionLogCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- MEMORY & REVISION ---
class MemoryItemBase(BaseModel):
    concept_id: str
    interval: int
    ease_factor: float
    repetitions: int
    last_reviewed: datetime
    next_review: datetime

class MemoryItemResponse(MemoryItemBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class RevisionRecommendation(BaseModel):
    concept_id: str
    title: str
    due_date: datetime
    urgency: float
    reason: str

# --- REFLECTION ---
class ReflectionLogCreate(BaseModel):
    reflection_type: str
    content: str

class ReflectionLogResponse(ReflectionLogCreate):
    id: int
    user_id: int
    reflection_date: datetime
    digital_twin_snapshot: Dict[str, Any]

    class Config:
        from_attributes = True

# --- SIMULATOR & PREDICTOR ---
class SimulationRequest(BaseModel):
    study_minutes_daily: float
    practice_frequency: str  # 'never', 'weekly', 'daily'
    skip_revision: bool
    strategy: str  # 'visual', 'project', 'mixed'
    months: Optional[int] = 12

class SimulationResult(BaseModel):
    time_series: List[Dict[str, Any]]
    final_mastery: float
    final_retention: float
    predicted_weaknesses: List[str]
    explaination: Dict[str, Any]

class PredictionResponse(BaseModel):
    burnout_risk: float  # 0.0 to 1.0
    velocity_score: float
    forgetting_rate_monthly: float
    predicted_concepts_to_forget: List[str]
    readiness_career: Dict[str, float]
    explanations: Dict[str, Any]

# --- AI MENTOR ---
class MentorMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class MentorChatRequest(BaseModel):
    messages: List[MentorMessage]
    current_topic: Optional[str] = None

class MentorChatResponse(BaseModel):
    message: str
    twin_parameters_injected: Dict[str, Any]
    explanation: Dict[str, Any]

# --- COGNITIVE ARENA ---
class ArenaStepSubmit(BaseModel):
    step_id: int
    option_selected: str
    confidence: float
    time_spent_seconds: float
    evidence_collected: List[str]

class ArenaScenarioSubmit(BaseModel):
    scenario_id: str
    steps: List[ArenaStepSubmit]

class ArenaScenarioResult(BaseModel):
    score: float
    feedback: str
    metrics: Dict[str, float]
    biases_detected: Dict[str, Any]
    explanation: Dict[str, Any]


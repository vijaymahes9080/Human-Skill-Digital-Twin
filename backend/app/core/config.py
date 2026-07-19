import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Human Skill Digital Twin"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "SUPER_SECRET_SECURITY_KEY_FOR_JWT_SIGNING_OFFLINE_FIRST"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Databases
    DATABASE_URL: str = "sqlite:///./digital_twin.db"
    
    # AI models & APIs
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"
    
    class Config:
        case_sensitive = True

settings = Settings()

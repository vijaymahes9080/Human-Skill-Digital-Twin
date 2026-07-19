from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.models.database_models import User
from backend.app.schemas import schemas
from backend.app.engines.core_twin import get_or_create_twin

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user profile and initializes their default digital twin blueprint."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email address already exists."
        )
        
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role or "user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Initialize the default digital twin immediately
    get_or_create_twin(db, user.id)
    
    return user

@router.post("/login", response_model=schemas.Token)
def login_user(login_in: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Checks credentials and returns a signed bearer access token."""
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

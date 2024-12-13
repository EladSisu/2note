from datetime import timedelta

from db_models import User, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from requests_models import RegisterUserRequest
from sqlalchemy.orm import Session
from utils.auth_helps import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()

# User registration
@router.post("/register")
async def register_user(request: RegisterUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.strip()).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(request.password)
    new_user = User(email=request.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"status": "User created successfully"}

# User login
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


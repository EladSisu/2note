
from datetime import datetime, timedelta
from typing import Optional

from db_models import Document, User, UserDocumentAssociation, get_db
from fastapi import (
    Depends,
    HTTPException,
    WebSocket,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Database setup

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
# Dependency to get the current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
async def get_current_user_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db)
) -> User:
    try:
        # Get token from query parameter
        token = websocket.query_params.get('token')
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
        
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="Invalid token")

def authorized_view(user: User, document_id: int, db: Session):
    """
    Check if the user is the owner of the document or has the permission to view the document
    """
    all_authorized_documents = db.query(Document).outerjoin(
            UserDocumentAssociation, Document.id == UserDocumentAssociation.document_id
        ).filter(
            (UserDocumentAssociation.user_id == user.id) | (Document.owner_id == user.id)
        ).all()
    return document_id in [document.id for document in all_authorized_documents]

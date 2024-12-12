import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./documents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# sharing permission
SHARING_PERMISSIONS = ["read", "write", "owner"]

class DocumentCreate(BaseModel):
    title: str = 'Untitled Document'

# Document model
class Document(Base):
    __tablename__ = "documents"    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    title: Mapped[str] = mapped_column(String, default="Untitled Document")
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

# User model
class User(Base):
    __tablename__: str = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)

# user - document many-to-many relationship
user_document_association = Table(
    "user_document_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("document_id", Integer, ForeignKey("documents.id")),
    Column("permission", String, CheckConstraint(f"permission IN {tuple(SHARING_PERMISSIONS)}"))
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = set()
        self.active_connections[document_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections:
            self.active_connections[document_id].discard(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]

    async def broadcast(self, message: dict, document_id: str, exclude: Optional[WebSocket] = None):
        if document_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[document_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except RuntimeError:
                        disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                await self.disconnect(conn, document_id)

manager = ConnectionManager()

# Secret key for JWT
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

class RegisterUserRequest(BaseModel):
    email: str
    password: str

# User registration
@app.post("/register")
async def register_user(request: RegisterUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(request.password)
    new_user = User(email=request.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    breakpoint()
    return {"status": "User created successfully"}

# User login
@app.post("/token")
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

# REST endpoints

@app.get("/documents")
async def get_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    documents = db.query(Document).join(
        user_document_association, Document.id == user_document_association.c.document_id
    ).filter(
        user_document_association.c.user_id == current_user.id
    ).all()
    return documents

@app.get("/documents/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "documentId": document.id,
        "content": document.content,
        "title": document.title,
        "lastModified": document.last_modified.isoformat()
    }

@app.post("/documents")
async def create_document(document: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_document = Document(owner_id=current_user.id, title=document.title)
    db.add(new_document)
    db.commit()
    return new_document

@app.put("/documents/{document_id}")
async def update_document(document_id: str, content: str, title: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.content = content
    if title:
        document.title = title
    document.last_modified = datetime.utcnow()
    db.commit()
    
    return {"status": "success"}

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(document)
    db.commit()
    return {"status": "success"}

# WebSocket endpoint
@app.websocket("/ws/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    await manager.connect(websocket, document_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "update":
                # Update document in database
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    document = Document(id=document_id)
                    db.add(document)
                
                document.content = message["content"]
                if "title" in message:
                    document.title = message["title"]
                document.last_modified = datetime.utcnow()
                db.commit()
                
                # Broadcast to all other clients
                await manager.broadcast(
                    {
                        "type": "update",
                        "documentId": document_id,
                        "content": document.content,
                        "title": document.title,
                        "lastModified": document.last_modified.isoformat()
                    },
                    document_id,
                    exclude=websocket
                )
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, document_id)
    except RuntimeError:
        await manager.disconnect(websocket, document_id)
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
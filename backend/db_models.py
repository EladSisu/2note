from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./documents.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# sharing permission
SHARING_PERMISSIONS = ["read", "write", "owner"]

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

class UserDocumentAssociation(Base):
    __tablename__ = "user_document_association"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id"))
    permission: Mapped[str] = mapped_column(String, CheckConstraint(f"permission IN {tuple(SHARING_PERMISSIONS)}"))


# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
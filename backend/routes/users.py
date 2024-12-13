
from db_models import User, get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.auth_helps import get_current_user

router = APIRouter(prefix='/users')

@router.get("")
async def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    return users
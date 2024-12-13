from datetime import datetime
from typing import Optional

from db_models import Document, User, UserDocumentAssociation, get_db
from fastapi import APIRouter, Depends, HTTPException
from requests_models import DocumentCreate, ShareRequest
from sqlalchemy.orm import Session
from utils.auth_helps import get_current_user

router = APIRouter(prefix='/documents')

@router.get("/{document_id}")
async def get_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).outerjoin(
        UserDocumentAssociation, Document.id == UserDocumentAssociation.document_id
    ).filter(
        (UserDocumentAssociation.user_id == current_user.id) | (Document.owner_id == current_user.id),
        Document.id == document_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "content": document.content,
        "title": document.title,
        "lastModified": document.last_modified.isoformat()
    }

@router.get("")
async def get_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        documents = db.query(Document).outerjoin(
            UserDocumentAssociation, Document.id == UserDocumentAssociation.document_id
        ).filter(
            (UserDocumentAssociation.user_id == current_user.id) | (Document.owner_id == current_user.id)
        ).order_by(Document.last_modified.desc()).all()
        response = []
        for document in documents:
            response.append({
                "id": document.id,
                "title": document.title,
                "lastModified": document.last_modified.isoformat(),
                "owned_by_current_user": document.owner_id == current_user.id
            })
        return response
    finally:
        db.close()



@router.post("")
async def create_document(document: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_document = Document(owner_id=current_user.id, title=document.title)
    db.add(new_document)
    db.commit()
    return {"title": new_document.title, "id": new_document.id, "owner_id": new_document.owner_id, "last_modified": new_document.last_modified}

@router.put("/{document_id}")
async def update_document(document_id: str, content: str, title: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).join(User).filter(Document.id == document_id, User.id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.content = content
    if title:
        document.title = title
    document.last_modified = datetime.utcnow()
    db.commit()
    
    return {"status": "success"}

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).join(User).filter(Document.id == document_id, User.id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(document)
    db.commit()
    return {"status": "success"}

@router.post("/share")
async def share_document( share_request: ShareRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.email == share_request.email:
        raise HTTPException(status_code=400, detail="Cannot share document with yourself")
    document = db.query(Document).join(User).filter(Document.id == share_request.document_id, User.id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    user = db.query(User).filter(User.email == share_request.email.strip()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.add(UserDocumentAssociation(user_id=user.id, document_id=document.id, permission=share_request.permission))
    db.commit()
    return {"status": "success"}
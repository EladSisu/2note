from pydantic import BaseModel


class RegisterUserRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class DocumentCreate(BaseModel):
    title: str = 'Untitled Document'

class ShareRequest(BaseModel):
    email: str
    permission: str = "write"
    document_id: int
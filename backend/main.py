import json
from datetime import datetime

from db_models import Document, SessionLocal
from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.documents import router as documents_router
from routes.users import router as users_router
from starlette.middleware.base import BaseHTTPMiddleware
from utils.auth_helps import authorized_view, get_current_user_ws
from utils.connection_manager import ConnectionManager

app = FastAPI()

app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(users_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

class DBConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if hasattr(request.state, 'db'):
            request.state.db.close()
        return response

app.add_middleware(DBConnectionMiddleware)

manager = ConnectionManager()

@app.websocket("/ws/{document_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    document_id: int
):
    # Get a fresh DB session for authentication
    db = SessionLocal()
    try:
        # Authenticate user before accepting connection
        current_user = await get_current_user_ws(websocket, db)
        if not authorized_view(current_user, document_id, db):
            print("User", current_user.email, "is not authorized to view document", document_id)
            await websocket.close(code=1008)
            return
    finally:
        db.close()
        
    await manager.connect(websocket, str(document_id))
    print("Connected to WebSocket for document", document_id, "with user", current_user.email)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print("Received message", message)
            if message["type"] == "update":
                # Get a fresh DB session for each update
                db = SessionLocal()
                try:
                    # Update document in database
                    document = db.query(Document).filter(Document.id == document_id).first()
                    document.content = message["content"]
                    if "title" in message:
                        document.title = message["title"]
                    document.last_modified = datetime.utcnow()
                    db.commit()
                    
                    # Broadcast to all other clients
                    await manager.broadcast(
                        message,
                        str(document_id),
                        exclude=websocket
                    )
                finally:
                    db.close()
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, str(document_id))
    except RuntimeError:
        await manager.disconnect(websocket, str(document_id))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
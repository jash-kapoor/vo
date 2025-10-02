from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import socketio
import json
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize SocketIO
sio = socketio.AsyncServer(cors_allowed_origins="*")

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# AI Models and Configuration
AI_MOODS = {
    'happy': {
        'system_message': 'You are a cheerful and optimistic AI. Respond with enthusiasm and positivity. Keep responses concise but warm.',
        'color': '#FFD700',
        'emoji': '😊'
    },
    'calm': {
        'system_message': 'You are a peaceful and measured AI. Speak slowly and thoughtfully. Provide calming and reassuring responses.',
        'color': '#87CEEB',
        'emoji': '😌'
    },
    'energetic': {
        'system_message': 'You are a dynamic and enthusiastic AI. Use exciting language and be motivational. Keep the energy high!',
        'color': '#FF6347',
        'emoji': '⚡'
    },
    'wise': {
        'system_message': 'You are a thoughtful and insightful AI. Provide deep, philosophical responses with wisdom and understanding.',
        'color': '#9370DB',
        'emoji': '🦉'
    },
    'playful': {
        'system_message': 'You are a creative and fun AI. Use humor, wordplay, and imaginative responses. Be lighthearted and entertaining.',
        'color': '#FF69B4',
        'emoji': '🎭'
    },
    'professional': {
        'system_message': 'You are a formal and business-focused AI. Use professional language and provide structured, informative responses.',
        'color': '#708090',
        'emoji': '💼'
    }
}

# Define Models
class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mood: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    connected_devices: int = 0

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    type: str  # 'user', 'ai', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    mood: Optional[str] = None

class CreateSessionRequest(BaseModel):
    mood: str

class SendMessageRequest(BaseModel):
    content: str
    type: str = 'user'

# Store active connections
active_connections = {}

# OpenAI client for AI responses
openai_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def generate_ai_response(session_id: str, mood: str, user_text: str) -> str:
    """Generate an AI response using OpenAI with the session mood as system prompt."""
    mood_config = AI_MOODS.get(mood, AI_MOODS['happy'])
    system_message = mood_config['system_message']
    try:
        completion = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_text},
            ],
            temperature=0.6,
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        return f"AI error: {str(exc)}"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Vocrypt AI Communication API"}

@api_router.post("/sessions", response_model=ChatSession)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session with specified mood"""
    session = ChatSession(mood=request.mood)
    await db.chat_sessions.insert_one(session.dict())
    
    # Create initial system message
    system_message = ChatMessage(
        session_id=session.id,
        type='system',
        content=f'Vocrypt session started in {request.mood} mode. Waiting for devices to connect...',
        mood=request.mood
    )
    await db.chat_messages.insert_one(system_message.dict())
    
    return session

@api_router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str):
    """Get session details"""
    session_data = await db.chat_sessions.find_one({"id": session_id})
    if session_data:
        return ChatSession(**session_data)
    return {"error": "Session not found"}

@api_router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_messages(session_id: str):
    """Get all messages for a session"""
    messages = await db.chat_messages.find({"session_id": session_id}).to_list(100)
    return [ChatMessage(**msg) for msg in messages]

@api_router.post("/sessions/{session_id}/messages", response_model=ChatMessage)
async def send_message(session_id: str, request: SendMessageRequest):
    """Send a message in a session"""
    # Get session details
    session_data = await db.chat_sessions.find_one({"id": session_id})
    if not session_data:
        return {"error": "Session not found"}
    
    session = ChatSession(**session_data)
    
    # Create user message
    user_message = ChatMessage(
        session_id=session_id,
        type=request.type,
        content=request.content,
        mood=session.mood
    )
    await db.chat_messages.insert_one(user_message.dict())
    
    # Generate AI response if it's a user message
    if request.type == 'user':
        try:
            ai_response = await generate_ai_response(session_id, session.mood, request.content)
            
            # Create AI message
            ai_message = ChatMessage(
                session_id=session_id,
                type='ai',
                content=ai_response,
                mood=session.mood
            )
            await db.chat_messages.insert_one(ai_message.dict())
            
            # Broadcast to connected clients
            await sio.emit('new_message', {
                'session_id': session_id,
                'message': ai_message.dict()
            }, room=session_id)
            
            return ai_message
            
        except Exception as e:
            error_message = ChatMessage(
                session_id=session_id,
                type='system',
                content=f'Error generating AI response: {str(e)}',
                mood=session.mood
            )
            await db.chat_messages.insert_one(error_message.dict())
            return error_message
    
    return user_message

@api_router.get("/moods")
async def get_moods():
    """Get available AI moods"""
    return [
        {
            'name': mood,
            'color': config['color'],
            'emoji': config['emoji'],
            'description': config['system_message']
        }
        for mood, config in AI_MOODS.items()
    ]

# WebSocket for real-time communication
@api_router.websocket("/sessions/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Add to active connections
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)
    
    # Update session connection count
    await db.chat_sessions.update_one(
        {"id": session_id},
        {"$inc": {"connected_devices": 1}}
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Broadcast to other connected devices in the same session
            for connection in active_connections[session_id]:
                if connection != websocket:
                    try:
                        await connection.send_text(data)
                    except:
                        # Remove dead connections
                        active_connections[session_id].remove(connection)
                        
    except WebSocketDisconnect:
        # Remove from active connections
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]
            
        # Update session connection count
        await db.chat_sessions.update_one(
            {"id": session_id},
            {"$inc": {"connected_devices": -1}}
        )

# SocketIO Events
@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")

@sio.event
async def join_session(sid, data):
    session_id = data.get('session_id')
    if session_id:
        await sio.enter_room(sid, session_id)
        await sio.emit('status', {'message': 'Joined session'}, room=sid)

@sio.event
async def leave_session(sid, data):
    session_id = data.get('session_id')
    if session_id:
        await sio.leave_room(sid, session_id)

@sio.event
async def send_audio_signal(sid, data):
    """Handle audio transmission between devices"""
    session_id = data.get('session_id')
    if session_id:
        # Broadcast audio signal to other devices in the session
        await sio.emit('audio_signal', data, room=session_id, skip_sid=sid)

# Include the router in the main app
app.include_router(api_router)

# Add SocketIO to the app
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
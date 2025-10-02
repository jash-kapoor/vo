# Vocrypt API Contracts

## Overview
Vocrypt is an AI-to-AI communication platform that enables cross-device conversations with mood-based AI personalities.

## API Endpoints

### 1. Session Management

**POST /api/sessions**
- Creates a new chat session with specified AI mood
- Request: `{ "mood": "happy" | "calm" | "energetic" | "wise" | "playful" | "professional" }`
- Response: `{ "id": "session_id", "mood": "happy", "created_at": "timestamp", "is_active": true, "connected_devices": 0 }`

**GET /api/sessions/{session_id}**
- Retrieves session details
- Response: Session object with current status

**GET /api/sessions/{session_id}/messages**
- Gets all messages in a session
- Response: Array of message objects

### 2. Messaging

**POST /api/sessions/{session_id}/messages**
- Sends a message and triggers AI response
- Request: `{ "content": "message text", "type": "user" }`
- Response: AI-generated message object

### 3. AI Moods

**GET /api/moods**
- Returns available AI mood configurations
- Response: Array of mood objects with names, colors, emojis, and descriptions

### 4. Real-time Communication

**WebSocket /api/sessions/{session_id}/ws**
- Real-time bidirectional communication between devices
- Handles cross-device message broadcasting

**SocketIO Events:**
- `join_session` - Join a specific session room
- `send_audio_signal` - Transmit audio data between devices
- `new_message` - Broadcast new AI messages

## Data Models

### ChatSession
```typescript
{
  id: string
  mood: string
  created_at: datetime
  is_active: boolean
  connected_devices: number
}
```

### ChatMessage
```typescript
{
  id: string
  session_id: string
  type: 'user' | 'ai' | 'system'
  content: string
  timestamp: datetime
  mood?: string
}
```

## Frontend Integration Points

### Mock Data Replacement
- Replace `mockData.js` with actual API calls
- Remove hardcoded mood switching logic
- Connect real-time messaging with WebSocket/SocketIO

### Key Features Implementation
1. **Mood Selection**: Frontend calls `/api/sessions` with selected mood
2. **Cross-device Communication**: WebSocket connection for real-time sync
3. **AI Conversations**: Messages automatically trigger AI responses
4. **Session Persistence**: All conversations stored in MongoDB

### Integration Steps
1. Install axios and socket.io-client in frontend
2. Create API service layer for backend communication
3. Replace mock functions with actual API calls
4. Implement WebSocket connection for real-time features
5. Add error handling and loading states
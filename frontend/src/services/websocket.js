import { io } from 'socket.io-client';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.sessionId = null;
  }

  connect() {
    if (!this.socket) {
      this.socket = io(BACKEND_URL, {
        transports: ['websocket', 'polling']
      });

      this.socket.on('connect', () => {
        this.isConnected = true;
        console.log('Connected to WebSocket');
      });

      this.socket.on('disconnect', () => {
        this.isConnected = false;
        console.log('Disconnected from WebSocket');
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.sessionId = null;
    }
  }

  joinSession(sessionId) {
    if (this.socket && this.isConnected) {
      this.sessionId = sessionId;
      this.socket.emit('join_session', { session_id: sessionId });
    }
  }

  leaveSession() {
    if (this.socket && this.isConnected && this.sessionId) {
      this.socket.emit('leave_session', { session_id: this.sessionId });
      this.sessionId = null;
    }
  }

  sendAudioSignal(audioData) {
    if (this.socket && this.isConnected && this.sessionId) {
      this.socket.emit('send_audio_signal', {
        session_id: this.sessionId,
        audio_data: audioData
      });
    }
  }

  onNewMessage(callback) {
    if (this.socket) {
      this.socket.on('new_message', callback);
    }
  }

  onAudioSignal(callback) {
    if (this.socket) {
      this.socket.on('audio_signal', callback);
    }
  }

  onStatus(callback) {
    if (this.socket) {
      this.socket.on('status', callback);
    }
  }

  removeAllListeners() {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }
}

// Create singleton instance
const webSocketService = new WebSocketService();
export default webSocketService;
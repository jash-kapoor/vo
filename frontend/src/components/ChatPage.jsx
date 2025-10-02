import React, { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Send, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { sessionAPI } from '../services/api';
import webSocketService from '../services/websocket';

const ChatPage = () => {
  const { sessionId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const mood = searchParams.get('mood') || 'happy';
  
  const [messages, setMessages] = useState([]);
  const [session, setSession] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load session and messages
    const initializeSession = async () => {
      try {
        setConnectionStatus('Loading session...');
        
        // Load session details
        const sessionData = await sessionAPI.get(sessionId);
        if (!sessionData || sessionData.error) {
          throw new Error('Session not found');
        }
        
        setSession(sessionData);
        
        // Load existing messages
        const messagesData = await sessionAPI.getMessages(sessionId);
        setMessages(Array.isArray(messagesData) ? messagesData : []);
        
        setIsConnected(true);
        setConnectionStatus('Connected');

        // Connect to WebSocket
        webSocketService.connect();
        webSocketService.joinSession(sessionId);
        
        // Listen for new messages
        webSocketService.onNewMessage((data) => {
          if (data.session_id === sessionId) {
            setMessages(prev => [...prev, data.message]);
          }
        });

        webSocketService.onStatus((data) => {
          console.log('WebSocket status:', data);
        });

        // Add initial system message if no messages exist
        if (!messagesData || messagesData.length === 0) {
          const systemMessage = {
            id: `system_${Date.now()}`,
            type: 'system',
            content: `Vocrypt session started in ${mood} mode. Waiting for AI communication...`,
            timestamp: new Date().toISOString()
          };
          setMessages([systemMessage]);
        }

      } catch (error) {
        console.error('Failed to initialize session:', error);
        setConnectionStatus('Connection failed');
        setIsConnected(false);
        
        // Add error message
        const errorMessage = {
          id: `error_${Date.now()}`,
          type: 'system',
          content: `Failed to load session: ${error.message}. Please go back and try again.`,
          timestamp: new Date().toISOString()
        };
        setMessages([errorMessage]);
      }
    };

    if (sessionId) {
      initializeSession();
    }

    return () => {
      webSocketService.leaveSession();
      webSocketService.removeAllListeners();
    };
  }, [sessionId, mood]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleBack = () => {
    navigate('/');
  };

  const toggleListening = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Start audio recording/listening
      console.log('Starting to listen for audio...');
    } else {
      // Stop audio recording/listening
      console.log('Stopped listening for audio...');
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId || !isConnected) return;

    const userMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
      session_id: sessionId
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    const messageToSend = inputMessage.trim();
    setInputMessage('');

    try {
      // Send message to backend and get AI response
      const response = await sessionAPI.sendMessage(sessionId, messageToSend);
      
      if (response && response.content) {
        // Only add AI response if we got one (user message was already added)
        if (response.type === 'ai') {
          setMessages(prev => [...prev, response]);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      if (isNaN(date.getTime())) return '';
      return date.toLocaleTimeString();
    } catch (error) {
      return '';
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center p-4 border-b border-gray-800">
        <div className="flex items-center space-x-4">
          <button 
            onClick={handleBack}
            className="text-white hover:text-gray-300 transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-lg font-medium">Vocrypt Session</h1>
            <p className="text-sm text-gray-400">Mode: {mood} | ID: {sessionId}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
          <span className="text-sm text-gray-400">{connectionStatus}</span>
          {session && (
            <span className="text-sm text-gray-400">
              ({session.connected_devices || 0} devices)
            </span>
          )}
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex justify-center">
            <div className="bg-gray-800 text-gray-300 text-sm px-4 py-2 rounded-lg">
              Loading messages...
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'system' ? 'justify-center' : 'justify-start'}`}
            >
              <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.type === 'system' 
                  ? 'bg-gray-800 text-gray-300 text-sm'
                  : message.type === 'ai'
                  ? 'bg-blue-900 text-blue-100'
                  : 'bg-green-900 text-green-100'
              }`}>
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
                {message.timestamp && (
                  <p className="text-xs opacity-60 mt-1">
                    {formatTimestamp(message.timestamp)}
                  </p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center space-x-2 mb-4">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 bg-gray-800 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            disabled={!isConnected}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || !isConnected}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          >
            <Send size={16} />
          </button>
        </div>

        {/* Audio Controls */}
        <div className="flex items-center justify-center space-x-6">
          <button
            onClick={toggleMute}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
              isMuted ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
          </button>
          
          <button
            onClick={toggleListening}
            className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
              isListening 
                ? 'bg-red-600 hover:bg-red-700 pulse-animation' 
                : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {isListening ? <MicOff size={24} /> : <Mic size={24} />}
          </button>
          
          <button 
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
            className="w-12 h-12 rounded-full bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 flex items-center justify-center transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
        
        <div className="text-center mt-4">
          <p className="text-sm text-gray-400">
            {!isConnected 
              ? 'Connecting to session...' 
              : isListening 
                ? 'Listening for audio...' 
                : 'AI conversations active. Cross-device communication enabled.'
            }
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
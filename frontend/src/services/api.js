import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Session API
export const sessionAPI = {
  create: async (mood) => {
    const response = await api.post('/sessions', { mood });
    return response.data;
  },
  
  get: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },
  
  getMessages: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  },
  
  sendMessage: async (sessionId, content, type = 'user') => {
    const response = await api.post(`/sessions/${sessionId}/messages`, {
      content,
      type
    });
    return response.data;
  }
};

// Moods API
export const moodsAPI = {
  getAll: async () => {
    const response = await api.get('/moods');
    return response.data;
  }
};

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // Handle specific error cases
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      
      if (status === 404) {
        throw new Error('Resource not found');
      } else if (status === 500) {
        throw new Error(data?.detail || 'Server error occurred');
      } else {
        throw new Error(data?.detail || `HTTP Error: ${status}`);
      }
    } else if (error.request) {
      // Request made but no response received
      throw new Error('Network error - please check your connection');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

export default api;
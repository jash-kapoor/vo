// Mock data for AI moods and communication
export const aiMoods = [
  {
    id: 1,
    name: 'Happy',
    color: '#FFD700',
    emoji: '😊',
    description: 'Cheerful and optimistic responses'
  },
  {
    id: 2,
    name: 'Calm',
    color: '#87CEEB',
    emoji: '😌',
    description: 'Peaceful and measured communication'
  },
  {
    id: 3,
    name: 'Energetic',
    color: '#FF6347',
    emoji: '⚡',
    description: 'Dynamic and enthusiastic interactions'
  },
  {
    id: 4,
    name: 'Wise',
    color: '#9370DB',
    emoji: '🦉',
    description: 'Thoughtful and insightful responses'
  },
  {
    id: 5,
    name: 'Playful',
    color: '#FF69B4',
    emoji: '🎭',
    description: 'Creative and fun communication style'
  },
  {
    id: 6,
    name: 'Professional',
    color: '#708090',
    emoji: '💼',
    description: 'Formal and business-focused tone'
  }
];

export const mockMessages = [
  {
    id: 1,
    type: 'system',
    content: 'Session initialized. Connecting to peer device...',
    timestamp: new Date()
  },
  {
    id: 2,
    type: 'ai',
    content: 'Audio transmission established. Beginning AI-to-AI communication.',
    timestamp: new Date()
  }
];

export const mockSessions = [
  {
    id: 'sess_001',
    mood: 'happy',
    status: 'active',
    connectedDevices: 2,
    startTime: new Date()
  }
];
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, HelpCircle } from 'lucide-react';
import { sessionAPI, moodsAPI } from '../services/api';

const HomePage = () => {
  const [moods, setMoods] = useState([]);
  const [currentMoodIndex, setCurrentMoodIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  // Load available moods from API
  useEffect(() => {
    const loadMoods = async () => {
      try {
        const availableMoods = await moodsAPI.getAll();
        if (availableMoods && availableMoods.length > 0) {
          setMoods(availableMoods);
        } else {
          throw new Error('No moods received from API');
        }
      } catch (error) {
        console.error('Failed to load moods:', error);
        // Fallback to default moods that match the backend structure
        setMoods([
          { name: 'happy', color: '#FFD700', emoji: '😊', description: 'Cheerful and optimistic responses' },
          { name: 'calm', color: '#87CEEB', emoji: '😌', description: 'Peaceful and measured communication' },
          { name: 'energetic', color: '#FF6347', emoji: '⚡', description: 'Dynamic and enthusiastic interactions' },
          { name: 'wise', color: '#9370DB', emoji: '🦉', description: 'Thoughtful and insightful responses' },
          { name: 'playful', color: '#FF69B4', emoji: '🎭', description: 'Creative and fun communication style' },
          { name: 'professional', color: '#708090', emoji: '💼', description: 'Formal and business-focused tone' }
        ]);
      }
    };

    loadMoods();
  }, []);

  const currentMood = moods[currentMoodIndex] || moods[0];

  const handleMoodChange = () => {
    if (moods.length > 0) {
      const nextIndex = (currentMoodIndex + 1) % moods.length;
      setCurrentMoodIndex(nextIndex);
    }
  };

  const handleStart = async () => {
    if (!currentMood) return;
    
    setIsLoading(true);
    try {
      // Use lowercase mood name as expected by backend
      const session = await sessionAPI.create(currentMood.name.toLowerCase());
      if (session && session.id) {
        navigate(`/chat/${session.id}?mood=${currentMood.name.toLowerCase()}`);
      } else {
        throw new Error('Invalid session response');
      }
    } catch (error) {
      console.error('Error starting session:', error);
      alert('Failed to start session. Please try again.');
      setIsLoading(false);
    }
  };

  if (moods.length === 0) {
    return (
      <div className="min-h-screen bg-black grid-background flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black grid-background flex flex-col">
      {/* Header */}
      <header className="flex justify-between items-center p-6">
        <div className="flex items-center space-x-2 text-white">
          <span className="text-xl">🖇️</span>
          <span className="text-lg font-medium">Vocrypt</span>
        </div>
        
        <div className="flex items-center space-x-4">
          <button className="text-white hover:text-gray-300 transition-colors">
            <Plus size={20} />
          </button>
          <button className="text-white hover:text-gray-300 transition-colors">
            <HelpCircle size={20} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center space-y-8">
        {/* AI Mood Circle */}
        <div className="relative">
          <button
            onClick={handleMoodChange}
            className="w-48 h-48 rounded-full border-none outline-none cursor-pointer transition-all duration-500 hover-scale hover-glow"
            style={{ 
              backgroundColor: currentMood.color,
              boxShadow: `0 0 50px ${currentMood.color}40`
            }}
            disabled={isLoading}
          >
            <div className="text-4xl">
              {currentMood.emoji}
            </div>
          </button>
          
          {/* Mood indicator */}
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
            <div className="text-gray-400 text-sm capitalize">
              {currentMood.name} Mode
            </div>
          </div>
        </div>

        {/* Tap to change text */}
        <p className="text-gray-400 text-sm">
          Tap to change
        </p>

        {/* Start Button */}
        <button
          onClick={handleStart}
          disabled={isLoading}
          className="px-16 py-3 bg-transparent border border-white text-white rounded-full hover:bg-white hover:text-black transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed min-w-[200px]"
        >
          {isLoading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Starting...</span>
            </div>
          ) : (
            'Start'
          )}
        </button>

        {/* Info Text */}
        <div className="text-center text-gray-500 text-xs max-w-md">
          <p>Create AI-to-AI conversations across devices.</p>
          <p className="mt-1">Select a mood and start communicating.</p>
        </div>
      </div>

      {/* Footer */}
      <footer className="p-6 text-center text-gray-600 text-xs">
        <p>Vocrypt - More Efficient Communication</p>
      </footer>
    </div>
  );
};

export default HomePage;
// File: src/hooks/useChat.jscd 

'use client';
import { useState } from 'react';

export const useChat = () => {
  const [messages, setMessages] = useState([
    { sender: 'ai', text: 'Welcome to the Ocean AI Analytics Interface. How can I assist you?' }
  ]);
  const [isThinking, setIsThinking] = useState(false);

  const sendMessage = async (text) => {
    // Add user's message to the history
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setIsThinking(true);

    // --- FAKE AI RESPONSE (Replace with actual API call) ---
    await new Promise(res => setTimeout(res, 2000)); // Simulate network delay
    const aiResponse = `This is a simulated response to your query: "${text}". The ocean data indicates a significant thermal anomaly in the specified region.`;
    // --- END FAKE AI RESPONSE ---

    setMessages(prev => [...prev, { sender: 'ai', text: aiResponse }]);
    setIsThinking(false);
  };

  return { messages, isThinking, sendMessage };
};
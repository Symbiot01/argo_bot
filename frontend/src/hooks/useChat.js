// File: src/hooks/useChat.js
'use client';
import { useState } from 'react';

export const useChat = (session) => {
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [chatId, setChatId] = useState(null);

  // This is your defined fallback object.
  const apiErrorFallback = {
    sender: 'ai',
    text: "The API is currently unavailable. Please try again later. This is a fallback message.",
    imageUrl: null,
  };

  const processQueryWithPipeline = async (currentChatId, text) => {
    try {
      const response = await fetch('/api/chat/pipeline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.accessToken}`,
        },
        body: JSON.stringify({
          user_input: text,
          chat_id: currentChatId,
          user_id: session.user.name,
          include_visualization: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Pipeline API Error: ${response.statusText}`);
      }

      const data = await response.json();
      setMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: data.response,
          imageUrl: data.visualization_created ? data.visualization_url : null,
        },
      ]);
    } catch (error) {
      console.error("Failed to process pipeline query:", error);
      // CORRECTED: Use the structured fallback object on failure.
      setMessages(prev => [...prev, apiErrorFallback]);
    }
  };

  const sendMessage = async (text) => {
    setMessages(prev => [...prev, { sender: 'user', text }]);
    setIsThinking(true);

    try {
      if (!chatId) {
        const newChatRes = await fetch('/api/chat/new', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.accessToken}`,
          },
          body: JSON.stringify({
            userid: session.user.name,
            description: text,
          }),
        });

        if (!newChatRes.ok) throw new Error('Failed to create new chat.');

        const newChatData = await newChatRes.json();
        const newChatToken = newChatData.chat_token;
        setChatId(newChatToken);
        await processQueryWithPipeline(newChatToken, text);
      } else {
        await processQueryWithPipeline(chatId, text);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // CORRECTED: Use the structured fallback object on failure.
      setMessages(prev => [...prev, apiErrorFallback]);
    } finally {
      setIsThinking(false);
    }
  };

  return { messages, isThinking, sendMessage };
};
// File: src/components/chat/ChatInterface.js
// Description: The main component that assembles the chat view.


'use client';
import { useEffect, useRef } from 'react';
import { useChat } from '../../hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import ThinkingIndicator from './ThinkingIndicator';
import WelcomeScreen from './WelcomeScreen';
import styles from './ChatInterface.module.scss';

export default function ChatInterface({ session, sidebarOpen }) {
  const { messages, isThinking, sendMessage } = useChat(session);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const marginLeft = sidebarOpen ? 300 : 48;

  const handleSuggestionClick = (query) => {
    sendMessage(query);
  };

  return (
    <div className={styles.chatWrapper} style={{ marginLeft }}>
      <div className={styles.messageList}>
        {/* Using messages.length === 0 is slightly cleaner for showing the WelcomeScreen */}
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestionClick={handleSuggestionClick} />
        ) : (
          <>
            {messages.map((msg, index) => (
              <MessageBubble
                key={index}
                sender={msg.sender}
                text={msg.text}
                // CORRECTED: Pass the imageUrl prop to the MessageBubble component.
                imageUrl={msg.imageUrl} 
              />
            ))}
            {isThinking && <ThinkingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      <ChatInput onSend={sendMessage} disabled={isThinking} />
    </div>
  );
}
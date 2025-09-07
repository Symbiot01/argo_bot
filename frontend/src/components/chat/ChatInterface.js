// File: src/components/chat/ChatInterface.js
// Description: The main component that assembles the chat view.

'use client';
import { useEffect, useRef } from 'react';
import { useChat } from '../../hooks/useChat';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import ThinkingIndicator from './ThinkingIndicator';
import styles from './ChatInterface.module.scss';

export default function ChatInterface({ sidebarOpen }) {
  const { messages, isThinking, sendMessage } = useChat();
  const messagesEndRef = useRef(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Dynamic margin style
  const marginLeft = sidebarOpen ? 300 : 48;

  return (
    <div className={styles.chatWrapper} style={{ marginLeft }}>
      <div className={styles.messageList}>
        {messages.map((msg, index) => (
          <MessageBubble key={index} sender={msg.sender} text={msg.text} />
        ))}
        {isThinking && <ThinkingIndicator />}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSend={sendMessage} disabled={isThinking} />
    </div>
  );
}
// File: src/components/chat/ChatInput.js
// Description: The input form for sending messages.


'use client';
import { useState } from 'react';
import styles from './ChatInput.module.scss';

export default function ChatInput({ onSend, disabled }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSend(text);
      setText('');
    }
  };

  return (
    <div className={styles.inputContainer}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <textarea
          className={styles.textarea}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter your command..."
          rows="1"
          disabled={disabled}
        />
        <button type="submit" className={styles.sendButton} disabled={disabled}>
          &gt;
        </button>
      </form>
    </div>
  );
}
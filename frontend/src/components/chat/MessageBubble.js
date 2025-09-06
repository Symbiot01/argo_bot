// File: src/components/chat/MessageBubble.js
// Description: Renders a single chat bubble.


import styles from './MessageBubble.module.scss';

export default function MessageBubble({ sender, text }) {
  const bubbleClasses = `${styles.bubble} ${sender === 'user' ? styles.user : styles.ai}`;
  return <div className={bubbleClasses}>{text}</div>;
}
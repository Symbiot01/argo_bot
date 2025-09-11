// File: src/components/chat/MessageBubble.js
// Description: Renders a single chat bubble.

import styles from './MessageBubble.module.scss';
import ReactMarkdown from 'react-markdown'; // Recommended for rendering text from the AI

export default function MessageBubble({ sender, text, imageUrl }) {
  const bubbleClasses = `${styles.bubble} ${sender === 'user' ? styles.user : styles.ai}`;
  
  return (
    <div className={bubbleClasses}>
      {/* Using ReactMarkdown allows for better formatting like lists, code blocks, etc. */}
      <ReactMarkdown>{text}</ReactMarkdown>
      
      {/* Conditionally render the image container if an imageUrl is provided */}
      {imageUrl && (
        <div className={styles.visualizationContainer}>
          <img 
            src={imageUrl} 
            alt="Generated Visualization" 
            className={styles.visualizationImage} 
          />
        </div>
      )}
    </div>
  );
}
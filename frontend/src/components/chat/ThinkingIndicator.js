// File: src/components/chat/ThinkingIndicator.js
// Description: Renders the thinking animation.

import styles from './ThinkingIndicator.module.scss';

export default function ThinkingIndicator() {
  return (
    <div className={styles.thinking}>
      <div className={styles.dot}></div>
      <div className={styles.dot}></div>
      <div className={styles.dot}></div>
    </div>
  );
}
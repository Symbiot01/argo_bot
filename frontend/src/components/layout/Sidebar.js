'use client';
import styles from './Sidebar.module.scss';
import { useSidebar } from '../../hooks/useSidebar';

export default function Sidebar() {
  const { isOpen, toggle } = useSidebar();

  const sidebarClasses = `${styles.sidebar} ${!isOpen ? styles.collapsed : ''}`;

  return (
    <aside className={sidebarClasses}>
      <h2>Chat History</h2>
      {/* Chat history list would go here */}
      <button className={styles.toggleButton} onClick={toggle}>
        {isOpen ? '<' : '>'}
      </button>
    </aside>
  );
}
'use client';
import styles from './Sidebar.module.scss';
import { useSidebar } from '../../hooks/useSidebar';

export default function Sidebar() {
  const { isOpen, toggle } = useSidebar();

  const sidebarClasses = `${styles.sidebar} ${!isOpen ? styles.collapsed : ''}`;

  // Dummy chat history data
  const chatHistory = [
    { id: 1, title: "Ocean Temperature Analysis", date: "2024-01-15", preview: "Can you analyze the temperature patterns..." },
    { id: 2, title: "Argo Float Data Query", date: "2024-01-14", preview: "Show me data from floats in the Indian Ocean..." },
    { id: 3, title: "Salinity Trends Discussion", date: "2024-01-13", preview: "What are the current salinity trends..." },
    { id: 4, title: "Deep Water Analysis", date: "2024-01-12", preview: "Looking at deep water formations..." },
    { id: 5, title: "Climate Change Impact", date: "2024-01-11", preview: "How is climate change affecting..." },
    { id: 6, title: "Current Patterns Study", date: "2024-01-10", preview: "Analyze the current patterns in..." },
    { id: 7, title: "Marine Ecosystem Query", date: "2024-01-09", preview: "Impact on marine ecosystems..." },
  ];

  return (
    <aside className={sidebarClasses}>
      <h2>Chat History</h2>
      <div className={styles.chatList}>
        {chatHistory.map((chat) => (
          <div key={chat.id} className={styles.chatItem}>
            <div className={styles.chatTitle}>{chat.title}</div>
            <div className={styles.chatDate}>{chat.date}</div>
            {isOpen && <div className={styles.chatPreview}>{chat.preview}</div>}
          </div>
        ))}
      </div>
      <button className={styles.toggleButton} onClick={toggle}>
        {isOpen ? '<' : '>'}
      </button>
    </aside>
  );
}
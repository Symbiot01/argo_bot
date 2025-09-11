// File: src/components/layout/Sidebar.js

'use client';

import { useState, useEffect } from 'react'; // Import useEffect
import Link from 'next/link';
import styles from './Sidebar.module.scss';
import { useSidebar } from '../../context/SidebarContext';
import { useSession, signOut } from 'next-auth/react';

// Define dummy data to be used when the API fails
const DUMMY_FALLBACK_HISTORY = [
  {
    id: 'fallback-1',
    title: "API is Offline",
    preview: "Chat history could not be loaded at this time.",
  },
  {
    id: 'fallback-2',
    title: "Please Try Again Later",
    preview: "The server appears to be unresponsive.",
  }
];

export default function Sidebar() {
  const { isOpen, toggle } = useSidebar();
  const { data: session, status } = useSession();
  const [activeChatId, setActiveChatId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]); // State for real chat history

  // Fetch chat history when the component mounts and the session is ready
  useEffect(() => {
    if (status === 'authenticated') {
      const fetchChatHistory = async () => {
        try {
          const res = await fetch('/api/chat/activechats', {
            headers: {
              'Authorization': `Bearer ${session.accessToken}`,
            },
          });
          if (!res.ok) {
            // This will trigger the catch block for server errors (e.g., 500)
            throw new Error('Failed to fetch chat history');
          }
          const data = await res.json();
          // IMPORTANT: Adjust the properties below based on your actual API response
          setChatHistory(data); 
        } catch (error) {
          console.error("Sidebar API Error:", error);
          // --- FALLBACK LOGIC ---
          // If the fetch fails, populate the sidebar with dummy data
          setChatHistory(DUMMY_FALLBACK_HISTORY);
        }
      };
      fetchChatHistory();
    }
  }, [status, session]); // Rerun if the session status changes

  const sidebarClasses = `${styles.sidebar} ${!isOpen ? styles.collapsed : ''}`;

  const handleNewChat = () => {
    // A simple page reload is the easiest way to start a fresh chat
    window.location.href = '/'; 
  };

  const handleLogout = () => {
    signOut({ callbackUrl: '/authenticate' });
  };

  return (
    <aside className={sidebarClasses}>
      <div> {/* Main content wrapper */}
        <div className={styles.sidebarHeader}>
          <h2>Chat History</h2>
          {isOpen && (
            <button onClick={handleNewChat} className={styles.newChatButton}>
              + New Chat
            </button>
          )}
        </div>
        <div className={styles.chatList}>
          {chatHistory.map((chat) => (
            <div
              key={chat.id} // Adjust to your chat object's unique key
              className={`${styles.chatItem} ${chat.id === activeChatId ? styles.active : ''}`}
              onClick={() => setActiveChatId(chat.id)}
            >
              {/* Adjust properties to match your chat object's structure */}
              <div className={styles.chatTitle}>{chat.title || "Chat Session"}</div>
              {isOpen && <div className={styles.chatPreview}>{chat.preview || ""}</div>}
            </div>
          ))}
        </div>
      </div>

      <div className={styles.profileContainer}>
        {status === 'authenticated' && session.user && (
          <div className={styles.profileSection}>
            {/* Avatar + Name goes to profile */}
            <Link href="/profile" className={styles.profileInfoLink}>
              <div className={styles.profileAvatar}>
                {session.user.name?.charAt(0).toUpperCase()}
              </div>
              {isOpen && (
                <div className={styles.profileInfo}>
                  <span className={styles.profileName}>{session.user.name}</span>
                </div>
              )}
            </Link>

            {/* Logout button (separate action) */}
            {isOpen && (
              <button
                onClick={handleLogout}
                className={styles.logoutButton}
              >
                Logout
              </button>
            )}
          </div>
        )}
        {status === 'loading' && isOpen && (
          <div className={styles.profileInfo}>
            <span className={styles.profileName}>Loading...</span>
          </div>
        )}
      </div>

      <button className={styles.toggleButton} onClick={toggle}>
        {isOpen ? '<' : '>'}
      </button>
    </aside>
  );
}
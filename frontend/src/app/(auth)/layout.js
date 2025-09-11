// File: src/app/(main)/layout.js

'use client';
import Sidebar from '../../components/layout/Sidebar';
import { useSidebar } from '../../context/SidebarContext';
import styles from './layout.module.scss';
// REMOVED: No longer need the custom AuthProvider

export default function MainAppLayout({ children }) {
  const { isOpen } = useSidebar();
  const contentClasses = `${styles.contentWrapper} ${isOpen ? styles.sidebarOpen : styles.sidebarClosed}`;

  return (
    // REMOVED: The AuthProvider wrapper is gone
    <div>
      <Sidebar />
      <main className={contentClasses}>
        {children}
      </main>
    </div>
  );
}
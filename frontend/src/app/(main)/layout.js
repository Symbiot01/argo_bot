// File: src/app/(main)/layout.js

'use client';
import Sidebar from '../../components/layout/Sidebar';
import { useSidebar } from '../../context/SidebarContext'; // This hook is needed to get the sidebar's state
import styles from './layout.module.scss';

export default function MainAppLayout({ children }) {
  // We use the hook here to know if the sidebar is open or not
  const { isOpen } = useSidebar();

  const contentClasses = `${styles.contentWrapper} ${isOpen ? styles.sidebarOpen : styles.sidebarClosed}`;

  return (
    <div>
      <Sidebar />
      <main className={contentClasses}>
        {children}
      </main>
    </div>
  );
}
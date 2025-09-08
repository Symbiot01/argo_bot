// File: src/app/(main)/layout.js

'use client';
import Sidebar from '../../components/layout/Sidebar';
import { useSidebar } from '../../context/SidebarContext';
import { AuthProvider } from '../../context/AuthContext'; // Import AuthProvider
import styles from './layout.module.scss';

export default function MainAppLayout({ children }) {
  const { isOpen } = useSidebar();
  const contentClasses = `${styles.contentWrapper} ${isOpen ? styles.sidebarOpen : styles.sidebarClosed}`;

  return (
    <AuthProvider> {/* Wrap with AuthProvider */}
      <div>
        <Sidebar />
        <main className={contentClasses}>
          {children}
        </main>
      </div>
    </AuthProvider>
  );
}
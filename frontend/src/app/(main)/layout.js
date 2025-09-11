// File: src/app/(main)/layout.js

'use client';
// import { useEffect } from 'react'; // 1. Import useEffect
// import { useSession } from 'next-auth/react'; // 2. Import useSession

import Sidebar from '../../components/layout/Sidebar';
import { useSidebar } from '../../context/SidebarContext';
import styles from './layout.module.scss';
// REMOVED: No longer need the custom AuthProvider

export default function MainAppLayout({ children }) {
  const { isOpen } = useSidebar();
  // const { data: session, status } = useSession(); // 3. Get session data
  // // 4. Store session in sessionStorage for access in non-React parts of the app
  // useEffect(() => {
  //   if (status === 'authenticated' && session) {
  //     // Store the entire session object as a JSON string
  //     sessionStorage.setItem('user-session', JSON.stringify(session));
  //   } else {
  //     // Clear storage on logout
  //     sessionStorage.removeItem('user-session');
  //   }
  // }, [session, status]); // This effect runs whenever the session changes

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
// File: src/app/(auth)/layout.js
'use client';
import styles from './layout.module.scss';

// This layout's only job is to center the auth form on the page.
// It should NOT include the Sidebar.
export default function AuthLayout({ children }) {
  return (
    <main className={styles.container}>
      {children}
    </main>
  );
}
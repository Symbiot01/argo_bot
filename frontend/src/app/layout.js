// File: src/app/layout.js
// This remains a Server Component, but it wraps children in a Client Component Provider

import './globals.scss';
import DynamicBackground from '../components/layout/DynamicBackground';
import { SidebarProvider } from '../context/SidebarContext';
import AuthSessionProvider from '../context/AuthSessionProvider'; // 1. Import the AuthSessionProvider

export const metadata = {
  title: 'Ocean AI Analytics',
  description: 'An immersive interface for interacting with a powerful AI.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        {/* 2. Wrap existing providers and children with the Auth provider */}
        <AuthSessionProvider>
          <SidebarProvider>
            <DynamicBackground />
            {children}
          </SidebarProvider>
        </AuthSessionProvider>
      </body>
    </html>
  );
}
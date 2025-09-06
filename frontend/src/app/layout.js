'use client'

import './globals.scss';
import DynamicBackground from '../components/layout/DynamicBackground';
import Sidebar from '../components/layout/Sidebar';
import { useSidebar } from '../hooks/useSidebar';

// export const metadata = {
//   title: 'Ocean AI Analytics',
//   description: 'An immersive interface for interacting with a powerful AI.',
// };

export default function RootLayout({ children }) {

  const { isOpen } = useSidebar();

  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        <Sidebar />
        <DynamicBackground />
        {children}
      </body>
    </html>
  );
}
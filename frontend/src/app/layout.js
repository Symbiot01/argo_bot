// File: src/app/layout.js
// This remains a Server Component, but it wraps children in a Client Component Provider
import './globals.scss';
import DynamicBackground from '../components/layout/DynamicBackground';
import { SidebarProvider } from '../context/SidebarContext'; // Import the provider

export const metadata = {
  title: 'Ocean AI Analytics',
  description: 'An immersive interface for interacting with a powerful AI.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning={true}>
        <SidebarProvider> {/* Wrap everything in the provider */}
          <DynamicBackground />
          {children}
        </SidebarProvider>
      </body>
    </html>
  );
}
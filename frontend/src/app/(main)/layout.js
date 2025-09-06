'use client';
import Sidebar from '../../components/layout/Sidebar';
import { useSidebar } from '../../hooks/useSidebar';

export default function MainAppLayout({ children }) {
  const { isOpen } = useSidebar();

  return (
    <div>
      <Sidebar />
      <main style={{ 
        marginLeft: isOpen ? '300px' : '60px', 
        transition: 'margin-left 0.3s ease-in-out' 
      }}>
        {children}
      </main>
    </div>
  );
}
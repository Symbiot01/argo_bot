// File: src/context/SidebarContext.js
// Description: A React Context and Provider to manage and share the sidebar's open/closed state across the entire application.


'use client';
import { createContext, useState, useContext, useCallback } from 'react';

// 1. Create the context
const SidebarContext = createContext();

// 2. Create the Provider component
export function SidebarProvider({ children }) {
  const [isOpen, setIsOpen] = useState(true); // Default state is open

  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  const value = { isOpen, toggle };

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
}

// 3. Create a custom hook for easy access to the context
export function useSidebar() {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
}
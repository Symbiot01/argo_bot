// File: src/hooks/useSidebar.js
// Description: A simple hook to manage the sidebar's collapsed/expanded state.


'use client';
import { useState, useCallback } from 'react';

export const useSidebar = (initialState = true) => {
  const [isOpen, setIsOpen] = useState(initialState);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);
  return { isOpen, toggle };
};
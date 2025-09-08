// File: src/context/AuthContext.js
// Description: Manages and provides authentication state (e.g., current user) to the application.

'use client';

import { createContext, useContext, useState } from 'react';
import { useRouter } from 'next/navigation';

const AuthContext = createContext();

// Mock user data - replace with API call in a real app
const MOCK_USER = {
  name: 'Alex Ray',
  email: 'alex.ray@oceandata.io',
  imageUrl: 'https://i.pravatar.cc/150?u=alexray', // A random avatar service
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(MOCK_USER); // Assume user is logged in
  const router = useRouter();

  const login = (userData) => {
    // In a real app, you'd get this from your API
    setUser(userData);
  };

  const logout = () => {
    // Clear user state and redirect to login page
    setUser(null);
    router.push('/authenticate');
  };

  const updateUser = (newDetails) => {
    // Update user state
    setUser(prev => ({ ...prev, ...newDetails }));
  };

  const value = { user, login, logout, updateUser };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
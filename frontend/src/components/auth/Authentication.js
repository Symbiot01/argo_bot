// File: src/components/auth/Authentication.js
// Description: A client component that provides a tabbed interface for users to switch between login and registration forms.


'use client';
import { useState } from 'react';
import styles from './Authentication.module.scss';

export default function Authentication() {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  
  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (mode === 'register' && password !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    // Handle form submission logic here (e.g., call your API)
    console.log({ mode, email, password });
  };
  
  const isLogin = mode === 'login';

  return (
    <div className={styles.container}>
      {/* Tab Switcher */}
      <div className={styles.tabContainer}>
        <button 
          className={`${styles.tab} ${isLogin ? styles.active : ''}`}
          onClick={() => setMode('login')}
        >
          Login
        </button>
        <button 
          className={`${styles.tab} ${!isLogin ? styles.active : ''}`}
          onClick={() => setMode('register')}
        >
          Register
        </button>
      </div>

      {/* Form Area */}
      <div className={styles.formContainer}>
        <h1 className={styles.title}>
          {isLogin ? 'Welcome Back' : 'Create Account'}
        </h1>
        <form onSubmit={handleSubmit}>
          <div className={styles.inputGroup}>
            <label htmlFor="email" className={styles.label}>Email</label>
            <input
              type="email"
              id="email"
              className={styles.input}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="password" className={styles.label}>Password</label>
            <input
              type="password"
              id="password"
              className={styles.input}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          {/* Conditional field for registration */}
          {!isLogin && (
            <div className={styles.inputGroup}>
              <label htmlFor="confirmPassword" className={styles.label}>Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                className={styles.input}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          <button type="submit" className={styles.submitButton}>
            {isLogin ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}
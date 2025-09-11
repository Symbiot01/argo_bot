// Path: src/components/auth/Authentication.js
'use client';
import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import styles from './Authentication.module.scss'; // Assuming styles are in the same folder

export default function Authentication() {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState(''); // ADDED username state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false); // ADDED for better UX
  const router = useRouter();

  const isLogin = mode === 'login';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match!");
      setIsLoading(false);
      return;
    }

    if (isLogin) {
      // Use NextAuth's signIn function to handle the redirect automatically
      const result = await signIn('credentials', {
        // REMOVED: redirect: false
        username,
        password,
        callbackUrl: '/', // ADDED: Tell NextAuth where to redirect on success
      });

      // This part now only runs if there was an error
      if (result.error) {
        setError('Invalid username or password');
        setIsLoading(false); // Stop loading on error
      }
    } else { // Registration Logic
      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password }),
        });

        if (res.ok) {
          alert('Registration successful! Please log in.');
          setMode('login');
        } else {
          const data = await res.json();
          setError(data.message || 'Registration failed.');
        }
      } catch (err) {
        setError('An error occurred during registration.');
      }
    }
    setIsLoading(false);
  };

  return (
    <div className={styles.container}>
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
      
      <div className={styles.formContainer}>
        <h1 className={styles.title}>{isLogin ? 'Welcome Back' : 'Create Account'}</h1>
        {error && <p className={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          {/* ADDED USERNAME FIELD */}
          <div className={styles.inputGroup}>
            <label htmlFor="username" className={styles.label}>Username</label>
            <input
              type="text"
              id="username"
              className={styles.input}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          {/* Email field is now only for registration */}
          {!isLogin && (
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
          )}

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
          
          <button type="submit" className={styles.submitButton} disabled={isLoading}>
            {isLoading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account')}
          </button>
        </form>
      </div>
    </div>
  );
}
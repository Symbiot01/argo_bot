'use client';
import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import styles from './Authentication.module.scss';

export default function Authentication() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const router = useRouter();

  const isLogin = mode === 'login';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!isLogin && password !== confirmPassword) {
      setError("Passwords do not match!");
      return;
    }

    if (isLogin) {
      const result = await signIn('credentials', {
        redirect: false,
        email,
        password,
      });

      if (result.error) {
        setError('Invalid email or password');
      } else {
        router.push('/'); // Redirect to home/dashboard on successful login
      }
    } else {
      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
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
  };

  return (
    <div className={styles.container}>
      {/* START: Added Missing JSX for Tabs */}
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
      {/* END: Added Missing JSX for Tabs */}

      <div className={styles.formContainer}>
        <h1 className={styles.title}>{isLogin ? 'Welcome Back' : 'Create Account'}</h1>
        {error && <p className={styles.error}>{error}</p>} {/* Make sure you have a .error class in your SCSS */}
        <form onSubmit={handleSubmit}>
          {/* START: Added Missing JSX for Inputs */}
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
          {/* END: Added Missing JSX for Inputs */}
          <button type="submit" className={styles.submitButton}>
            {isLogin ? 'Login' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}
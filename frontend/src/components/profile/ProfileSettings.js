// File: src/components/profile/ProfileSettings.js
'use client';
import { useState } from 'react';
import { signOut } from 'next-auth/react'; // Import signOut from NextAuth
import styles from './ProfileSettings.module.scss';

// The 'user' object is now passed as a prop from the server component page
export default function ProfileSettings({ user }) {
  const [name, setName] = useState(user?.name || '');
  // const [email, setEmail] = useState(user?.email || ''); // Assuming email isn't editable for now

  const handleSaveChanges = async (e) => {
    e.preventDefault();
    // TODO: Add an API call here to your backend to actually update the user's name
    // For example:
    // await fetch('/api/user/update', { method: 'POST', body: JSON.stringify({ name }) });
    alert('Profile updated! (Frontend only for now)');
  };

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div className={styles.settingsWrapper}>
      <div className={styles.card}>
        <h2>Edit Profile</h2>
        <form onSubmit={handleSaveChanges}>
          <div className={styles.inputGroup}>
            <label htmlFor="name">Username</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          {/* If email is part of your user model from the backend */}
          {user.email && (
            <div className={styles.inputGroup}>
              <label htmlFor="email">Email</label>
              <input id="email" type="email" value={user.email} disabled />
            </div>
          )}
          <button type="submit" className={styles.saveButton}>Save Changes</button>
        </form>
      </div>

      <div className={styles.card}>
        <h2>Account Actions</h2>
        {/* Use NextAuth's signOut function */}
        <button onClick={() => signOut({ callbackUrl: '/authenticate' })} className={styles.logoutButton}>
          Logout
        </button>
      </div>
    </div>
  );
}
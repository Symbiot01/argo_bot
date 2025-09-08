// File: src/components/profile/ProfileSettings.js
// Description: UI component for editing user details and logging out.

'use client';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import styles from './ProfileSettings.module.scss';

export default function ProfileSettings() {
  const { user, logout, updateUser } = useAuth();
  const [name, setName] = useState(user?.name || '');

  const handleSaveChanges = (e) => {
    e.preventDefault();
    updateUser({ name });
    alert('Profile updated!');
  };

  if (!user) {
    return <p>Loading...</p>;
  }

  return (
    <div className={styles.settingsWrapper}>
      {/* Edit Profile Section */}
      <div className={styles.card}>
        <h2>Edit Profile</h2>
        <div className={styles.profilePictureSection}>
          <img src={user.imageUrl} alt="Profile Avatar" className={styles.avatar} />
          <button className={styles.uploadButton}>Upload New Photo</button>
        </div>
        <form onSubmit={handleSaveChanges}>
          <div className={styles.inputGroup}>
            <label htmlFor="name">Full Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className={styles.inputGroup}>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={user.email} disabled />
          </div>
          <button type="submit" className={styles.saveButton}>Save Changes</button>
        </form>
      </div>

      {/* Logout & Account Actions */}
      <div className={styles.card}>
        <h2>Account Actions</h2>
        <button onClick={logout} className={styles.logoutButton}>
          Logout
        </button>
      </div>
      
      {/* Danger Zone - My addition as something that fits well */}
      <div className={`${styles.card} ${styles.dangerZone}`}>
        <h2>Danger Zone</h2>
        <p>Permanently delete your account and all associated data. This action cannot be undone.</p>
        <button className={styles.deleteButton}>Delete My Account</button>
      </div>
    </div>
  );
}
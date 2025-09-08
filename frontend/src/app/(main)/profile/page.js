// File: src/app/(main)/profile/page.js
// Description: The page route for the user's profile and settings.

import ProfileSettings from '../../../components/profile/ProfileSettings';
import styles from './page.module.scss';

export default function ProfilePage() {
  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Profile & Settings</h1>
      <ProfileSettings />
    </div>
  );
}
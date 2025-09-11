// File: src/app/(main)/profile/page.js
// Description: The page route for the user's profile and settings.

import { getServerSession } from 'next-auth/next';
import { authOptions } from '../../api/auth/[...nextauth]/route'; // Correct import path
import ProfileSettings from '../../../components/profile/ProfileSettings';
import styles from './page.module.scss';
import { redirect } from 'next/navigation';

// This is now an async Server Component
export default async function ProfilePage() {
  // Fetch the session on the server. Middleware protects this page,
  // but it's good practice to fetch the data here to pass down.
  const session = await getServerSession(authOptions);

  // Although middleware should prevent access, this is a safeguard.
  // If there's no session for any reason, redirect to the login page.
  if (!session) {
    redirect('/authenticate');
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Profile & Settings</h1>
      {/* Pass the user object from the session directly as a prop.
        The ProfileSettings component can now be a client component that uses this initial data
        without needing to fetch it again.
      */}
      <ProfileSettings user={session.user} />
    </div>
  );
}

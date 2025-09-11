// File: src/app/page.js
// Description: The main page of the application, which simply renders the complete chat interface.

import { getServerSession } from 'next-auth/next';
import { authOptions } from '../api/auth/[...nextauth]/route';
import ChatInterface from '../../components/chat/ChatInterface';

// This is now an async Server Component to fetch session data
export default async function HomePage() {
  // Fetch the session details on the server side.
  // This is the recommended and most performant way to get session data in the App Router.
  const session = await getServerSession(authOptions);

  // The ChatInterface component will need the session to know who the user is
  // and to use the accessToken for any API calls it makes.
  return <ChatInterface session={session} />;
}

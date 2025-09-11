
// File: src/app/api/auth/[...nextauth]/route.js

import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

// Ensure this is set in your .env.local file
const NEXTAUTH_SECRET = process.env.NEXTAUTH_SECRET;
// The base URL of your FastAPI backend
const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

if (!NEXTAUTH_SECRET) {
  throw new Error("NEXTAUTH_SECRET is not set in environment variables!");
}
if (!BACKEND_API_URL) {
  throw new Error("NEXT_PUBLIC_BACKEND_API_URL is not set in environment variables!");
}


export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null;
        }

        // The backend expects 'x-www-form-urlencoded' data for login
        const params = new URLSearchParams();
        params.append('username', credentials.username);
        params.append('password', credentials.password);

        try {
          // CORRECTED: Added /api/v1 to the fetch URL
          const res = await fetch(`${BACKEND_API_URL}api/v1/login`, {
            method: 'POST',
            body: params,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          });

          if (!res.ok) {
            console.error("Failed to login with backend:", res.status, await res.text());
            return null; // Authentication failed
          }

          const tokenData = await res.json();
          
          const user = {
            id: credentials.username,
            name: credentials.username,
            accessToken: tokenData.access_token,
          };

          return user;

        } catch (error) {
          console.error("Error during authorization:", error);
          return null;
        }
      },
    }),
  ],
  
  secret: NEXTAUTH_SECRET,

  session: {
    strategy: "jwt", // Use JWTs for session management
  },

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },

  pages: {
    signIn: '/authenticate', // Redirect users to this page for login
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
// In a real application, you would use a library like bcryptjs to securely hash and compare passwords.
// import bcrypt from 'bcryptjs';

// --- MOCK DATABASE ---
// In a real application, this would be a connection to your database (e.g., PostgreSQL, MongoDB, Supabase).
// NOTE: This array is only for this file. The register route has its own, demonstrating the need for a shared database.
const users = [
  { id: '1', name: 'Alex Ray', email: 'alex.ray@oceandata.io', password: 'password123' }
];
// --------------------

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // This is where you retrieve a user from your database and check their password.
        if (!credentials) {
          return null;
        }

        const user = users.find(u => u.email === credentials.email);

        // IMPORTANT: In a real app, you MUST compare hashed passwords.
        // const isPasswordCorrect = await bcrypt.compare(credentials.password, user.passwordHash);
        if (user && user.password === credentials.password) {
          // If the credentials are valid, return the user object (without the password).
          return { id: user.id, name: user.name, email: user.email };
        }
        
        // If credentials are not valid, return null.
        return null;
      }
    })
  ],
  session: {
    // Use JSON Web Tokens for session management.
    strategy: 'jwt',
  },
  // A secret is required to sign the JWTs. This must be in your .env.local file.
  secret: process.env.NEXTAUTH_SECRET,
  pages: {
    // Tell NextAuth.js where your custom sign-in page is located.
    // The middleware will use this to redirect unauthenticated users.
    signIn: '/authenticate',
  },
};

// This exports the handler that Next.js will use for all requests to /api/auth/*
const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };

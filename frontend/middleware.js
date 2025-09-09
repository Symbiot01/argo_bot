// // File: middleware.js (in the project root)

// import { withAuth } from "next-auth/middleware";
// import { NextResponse } from "next/server";

// export default function middleware(req) {
//   // Log the path for every request to see if the middleware is running
//   console.log("MIDDLEWARE IS RUNNING FOR PATH: ", req.nextUrl.pathname);

//   // This is the default protection logic from NextAuth
//   return withAuth(req);
// }

// // This config specifies which routes should be protected.
// export const config = { 
//   matcher: [
//     /*
//      * Match all request paths except for the ones starting with:
//      * - api (API routes)
//      * - _next/static (static files)
//      * - _next/image (image optimization files)
//      * - favicon.ico (favicon file)
//      * - authenticate (the login/register page itself)
//      */
//     '/((?!api|_next/static|_next/image|favicon.ico|authenticate).*)',
//   ],
// };


// File: middleware.js (in the project root)

// import { getToken } from 'next-auth/jwt';
// import { NextResponse } from 'next/server';

// export async function middleware(req) {
//   // Use getToken to see if a session exists.
//   // It needs the secret from your .env.local file to decrypt the JWT.
//   const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

//   // Log the token to the terminal. This is our key diagnostic step.
//   // It will be `null` if the user is not logged in.
//   console.log("SESSION TOKEN FOUND IN MIDDLEWARE: ", token);

//   const { pathname } = req.nextUrl;

//   // If there's NO token (user is not logged in)
//   // AND they are trying to access a protected page (any page that isn't /authenticate)
//   if (!token && pathname !== '/authenticate') {
//     console.log("NO TOKEN, REDIRECTING TO /authenticate");
    
//     // Create a new URL for the login page
//     const url = req.nextUrl.clone();
//     url.pathname = '/authenticate';
    
//     // Redirect them
//     return NextResponse.redirect(url);
//   }

//   // If a token exists or the page is public, allow the request to continue.
//   return NextResponse.next();
// }

// // The config remains the same, telling the middleware which paths to run on.
// export const config = {
//   matcher: [
//     '/((?!api|_next/static|_next/image|favicon.ico|authenticate).*)',
//   ],
// };

import { getToken } from 'next-auth/jwt';
import { NextResponse } from 'next/server';

export async function middleware(req) {
  // Get the session token from the request
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

  const { pathname } = req.nextUrl;

  // If the user is NOT logged in (no token) and is trying to access a protected page
  if (!token && pathname !== '/authenticate') {
    const url = req.nextUrl.clone();
    url.pathname = '/authenticate';
    // Redirect them to the login page
    return NextResponse.redirect(url);
  }

  // If the user IS logged in and tries to visit the authenticate page
  if (token && pathname === '/authenticate') {
    const url = req.nextUrl.clone();
    url.pathname = '/'; // or '/profile' or any other default page
    // Redirect them away from the login page
    return NextResponse.redirect(url);
  }

  // Allow the request to proceed
  return NextResponse.next();
}

// Config to specify which routes the middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};

// File: src/app/api/register/route.js

import { NextResponse } from 'next/server';
// In a real app, use a library like bcryptjs to hash passwords
// import bcrypt from 'bcryptjs';

// This is the same mock DB from the NextAuth config.
// In a real app, this would be a connection to your actual database.
const users = [
  { id: '1', name: 'Alex Ray', email: 'alex.ray@oceandata.io', password: 'password123' }
];

export async function POST(request) {
  try {
    const { email, password } = await request.json();

    // Check if user already exists
    const existingUser = users.find(u => u.email === email);
    if (existingUser) {
      return NextResponse.json({ message: 'User already exists' }, { status: 409 });
    }

    // Hash the password before saving
    // const hashedPassword = await bcrypt.hash(password, 10);

    // Create and save the new user (we'll just log it here)
    const newUser = {
      id: String(users.length + 1),
      email,
      password, // In a real app, you would save hashedPassword
    };
    users.push(newUser);
    console.log('New user created:', newUser);

    return NextResponse.json({ message: 'User created successfully' }, { status: 201 });
  } catch (error) {
    return NextResponse.json({ message: 'An error occurred' }, { status: 500 });
  }
}
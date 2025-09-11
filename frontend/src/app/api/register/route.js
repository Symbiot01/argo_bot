// File: src/app/api/register/route.js

import { NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

export async function POST(req) {
  try {
    const body = await req.json();
    const { username, email, password } = body;

    // CORRECTED: Changed the fetch URL from /v1/register to /api/v1/register
    const apiRes = await fetch(`${BACKEND_API_URL}api/v1/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password }),
    });

    console.log("Registration API response", apiRes);

    if (!apiRes.ok) {
      const errorData = await apiRes.json();
      return NextResponse.json(
        { message: errorData.detail || 'Registration failed.' },
        { status: apiRes.status }
      );
    }

    const data = await apiRes.json();
    return NextResponse.json(data, { status: 201 });

  } catch (error) {
    console.error("Registration API error:", error);
    return NextResponse.json(
      { message: 'An internal server error occurred.' },
      { status: 500 }
    );
  }
}
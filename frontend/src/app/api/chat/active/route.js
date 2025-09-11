// src/app/api/chat/active/route.js

import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

export async function GET() {
  try {
    const headersList = headers();
    const authorization = headersList.get('authorization');

    if (!authorization) {
      return NextResponse.json({ message: 'Authorization header missing' }, { status: 401 });
    }

    const apiRes = await fetch(`${BACKEND_API_URL}api/v1/chat/getactivechats`, {
      method: 'GET',
      headers: {
        'Authorization': authorization, // Forward the token
      },
    });

    const data = await apiRes.json();

    if (!apiRes.ok) {
      return NextResponse.json(data, { status: apiRes.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error("API Route Error (getactivechats):", error);
    return NextResponse.json({ message: 'An internal server error occurred.' }, { status: 500 });
  }
}
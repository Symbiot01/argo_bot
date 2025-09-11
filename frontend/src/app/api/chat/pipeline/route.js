// File: src/app/api/chat/pipeline/route.js
// This is the main route for processing user queries.

import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;

export async function POST(req) {
  try {
    const headersList = headers();
    // const authorization = headersList.get('authorization');
    const body = await req.json();

    // if (!authorization) {
    //   return NextResponse.json({ message: 'Authorization header missing' }, { status: 401 });
    // }

    const apiRes = await fetch(`${BACKEND_API_URL}api/v1/pipeline/combined-pipeline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await apiRes.json();

    if (!apiRes.ok) {
        return NextResponse.json(data, { status: apiRes.status });
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error("API Route Error (pipeline):", error);
    return NextResponse.json({ message: 'An internal server error occurred.' }, { status: 500 });
  }
}
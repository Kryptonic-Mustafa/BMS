import { NextResponse } from 'next/server';
import { getSession } from '@/lib/session'; // FIXED: Use DB Session, not Auth

export async function GET() {
  // This now fetches the User + Role + FRESH Permissions from DB
  const session = await getSession();
  
  if (!session) return NextResponse.json({});
  
  // Return session with the latest permissions array
  return NextResponse.json(session);
}
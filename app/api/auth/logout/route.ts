import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
  cookieStore.delete('client_policy');
  return NextResponse.json({ success: true });
}
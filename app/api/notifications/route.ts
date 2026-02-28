import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json([], { status: 200 });

    const notifications: any = await query(
      'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
      [session.id]
    );

    return NextResponse.json(notifications || []);
  } catch (error) {
    console.error("Notifications API Error:", error);
    // Return empty array instead of 500 to keep UI stable
    return NextResponse.json([]);
  }
}
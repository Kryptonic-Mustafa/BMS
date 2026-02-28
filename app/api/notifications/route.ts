import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

// CRITICAL: This line stops Next.js from caching the response!
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  // Fetch notifications (limit 50)
  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
    [session.id]
  );
  
  // Fetch unread count
  const count: any = await query(
    'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE',
    [session.id]
  );

  return NextResponse.json({ 
    notifications, 
    unreadCount: count[0].count 
  });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id, markAll, status } = await request.json();
  const isRead = status !== undefined ? status : true;

  if (markAll) {
    await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  } else if (id) {
    await query('UPDATE notifications SET is_read = ? WHERE id = ? AND user_id = ?', [isRead, id, session.id]);
  }

  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  const { id } = await request.json();
  if (id) {
      await query('DELETE FROM notifications WHERE id = ? AND user_id = ?', [id, session.id]);
  }
  return NextResponse.json({ success: true });
}
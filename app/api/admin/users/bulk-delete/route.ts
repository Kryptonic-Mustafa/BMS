import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) {
    return NextResponse.json({ error: 'Super Admin access required' }, { status: 403 });
  }

  const { ids } = await request.json();

  if (!Array.isArray(ids) || ids.length === 0) {
    return NextResponse.json({ error: 'No IDs provided' }, { status: 400 });
  }

  // Delete multiple users in one go
  // Note: We use a placeholder string like (?,?,?) based on array length
  const placeholders = ids.map(() => '?').join(',');
  const sql = `DELETE FROM users WHERE id IN (${placeholders})`;

  await query(sql, ids);

  return NextResponse.json({ success: true });
}
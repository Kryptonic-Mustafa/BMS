import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);
  
  // Fetch saved contacts
  const list = await query('SELECT * FROM beneficiaries WHERE user_id = ? ORDER BY saved_name ASC', [session.id]);
  return NextResponse.json(list);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { name, accountNumber } = await request.json();

  // 1. Validate Account Exists
  const target: any = await query('SELECT id FROM accounts WHERE account_number = ?', [accountNumber]);
  if (target.length === 0) return NextResponse.json({ error: 'Invalid Account Number' }, { status: 404 });

  // 2. Prevent Duplicate
  const check: any = await query('SELECT id FROM beneficiaries WHERE user_id = ? AND account_number = ?', [session.id, accountNumber]);
  if (check.length > 0) return NextResponse.json({ error: 'Contact already saved' }, { status: 400 });

  // 3. Save
  await query('INSERT INTO beneficiaries (user_id, saved_name, account_number) VALUES (?, ?, ?)', [session.id, name, accountNumber]);
  
  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const session = await getSession();
  const { id } = await request.json();
  await query('DELETE FROM beneficiaries WHERE id = ? AND user_id = ?', [id, session.id]);
  return NextResponse.json({ success: true });
}
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { type, number, file } = await request.json();

  if (!file) return NextResponse.json({ error: 'Document image required' }, { status: 400 });

  // 1. Save Document
  await query(
    'INSERT INTO kyc_documents (user_id, document_type, document_number, file_data) VALUES (?, ?, ?, ?)',
    [session.id, type, number, file]
  );

  // 2. Update User Status
  await query("UPDATE users SET kyc_status = 'pending' WHERE id = ?", [session.id]);

  return NextResponse.json({ success: true });
}

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({});

  const res: any = await query('SELECT kyc_status FROM users WHERE id = ?', [session.id]);
  return NextResponse.json({ status: res[0]?.kyc_status || 'unverified' });
}
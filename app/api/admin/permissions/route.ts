import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get only Manager permissions for now (Admins have full access by default)
  const perms = await query("SELECT * FROM permissions WHERE role = 'manager'");
  return NextResponse.json(perms);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { resource, action, is_allowed } = await request.json();

  // Upsert Permission
  await query(
    `INSERT INTO permissions (role, resource, action, is_allowed) 
     VALUES ('manager', ?, ?, ?) 
     ON DUPLICATE KEY UPDATE is_allowed = ?`,
    [resource, action, is_allowed, is_allowed]
  );

  return NextResponse.json({ success: true });
}
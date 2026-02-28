import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

// Helper to check permission
async function checkPermission(role: string, resource: string, action: string) {
  if (role === 'admin') return true; // Admins can do everything
  
  const rows: any = await query(
    "SELECT is_allowed FROM permissions WHERE role = ? AND resource = ? AND action = ?", 
    [role, resource, action]
  );
  
  return rows.length > 0 && rows[0].is_allowed === 1;
}

// DELETE USER
export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // SECURITY CHECK
  const canDelete = await checkPermission(session.role, 'customers', 'delete');
  if (!canDelete) {
      return NextResponse.json({ error: 'Permission Denied: You cannot delete customers.' }, { status: 403 });
  }

  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

  await query('DELETE FROM users WHERE id = ?', [id]);
  return NextResponse.json({ success: true });
}

// EDIT USER
export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // SECURITY CHECK
  const canEdit = await checkPermission(session.role, 'customers', 'edit');
  if (!canEdit) {
      return NextResponse.json({ error: 'Permission Denied: You cannot edit customers.' }, { status: 403 });
  }

  const body = await request.json();
  const { id, name, email } = body;

  await query('UPDATE users SET name = ?, email = ? WHERE id = ?', [name, email, id]);
  return NextResponse.json({ success: true });
}
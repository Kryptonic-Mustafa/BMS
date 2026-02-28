import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get Roles
  const roles = await query('SELECT * FROM roles ORDER BY id ASC');
  
  // Get Permissions for each role
  for (const role of roles) {
      const perms = await query(`
        SELECT p.name 
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id = ?
      `, [role.id]);
      role.permissions = perms.map((p: any) => p.name);
  }

  return NextResponse.json(roles);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { name, description, permissions } = await request.json();

  // Create Role
  const res: any = await query('INSERT INTO roles (name, description) VALUES (?, ?)', [name, description]);
  const roleId = res.insertId;

  // Assign Permissions
  if (permissions && permissions.length > 0) {
      // Find IDs for permission names
      const permRecords: any = await query(`SELECT id FROM permissions WHERE name IN (?)`, [permissions]);
      
      for (const p of permRecords) {
          await query('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', [roleId, p.id]);
      }
  }

  return NextResponse.json({ success: true });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { id, name, description, permissions } = await request.json();

  await query('UPDATE roles SET name = ?, description = ? WHERE id = ?', [name, description, id]);
  
  // Reset Permissions
  await query('DELETE FROM role_permissions WHERE role_id = ?', [id]);

  if (permissions && permissions.length > 0) {
      const permRecords: any = await query(`SELECT id FROM permissions WHERE name IN (?)`, [permissions]);
      for (const p of permRecords) {
          await query('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', [id, p.id]);
      }
  }

  return NextResponse.json({ success: true });
}
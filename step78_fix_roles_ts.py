import os

files = {
    "app/api/admin/roles/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session || (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('RolesManage'))) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // THE FIX: Added ': any' so TypeScript knows this is an iterable array
  const roles: any = await query('SELECT * FROM roles');
  
  for (const role of roles) {
      const perms: any = await query(`
        SELECT p.name 
        FROM permissions p 
        JOIN role_permissions rp ON p.id = rp.permission_id 
        WHERE rp.role_id = ?
      `, [role.id]);
      
      role.permissions = perms.map((p: any) => p.name);
  }

  const allPerms = await query('SELECT * FROM permissions');
  return NextResponse.json({ roles, allPermissions: allPerms });
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('RolesManage'))) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { roleId, permissions } = await request.json();

  if (roleId === 1) {
      return NextResponse.json({ error: 'SuperAdmin cannot be modified' }, { status: 403 });
  }

  await query('DELETE FROM role_permissions WHERE role_id = ?', [roleId]);

  if (permissions && permissions.length > 0) {
      // THE FIX: Added ': any' to prevent loop conflicts
      const permsList: any = permissions;
      for (const permName of permsList) {
          const perm: any = await query('SELECT id FROM permissions WHERE name = ?', [permName]);
          if (perm.length > 0) {
              await query('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', [roleId, perm[0].id]);
          }
      }
  }

  return NextResponse.json({ success: true });
}
"""
}

def fix_roles_ts():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed Roles TypeScript Error!")

if __name__ == "__main__":
    fix_roles_ts()
import { cookies } from 'next/headers';
import { decrypt } from '@/lib/auth';
import { query } from '@/lib/db';

export async function getSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get('session')?.value;
  if (!session) return null;
  
  const payload: any = await decrypt(session);
  if(!payload) return null;

  try {
    // Fetch fresh permissions from DB
    // We check if role_id exists to handle migration, otherwise fallback
    if (payload.role_id) {
        const perms: any = await query(`
            SELECT p.name 
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        `, [payload.role_id]);

        const permissionList = perms.map((p: any) => p.name);
        return { ...payload, permissions: permissionList };
    }
    return payload; 
  } catch (e) {
    // Fallback if DB fails or during strict edge cases
    return payload;
  }
}
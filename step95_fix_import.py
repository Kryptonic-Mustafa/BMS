import os

files = {
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth'; // THE FIX: Reverted to the correct path
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();
    console.log(`[LOGIN DEBUG] Attempting login for: ${email}`);

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) {
        console.log("[LOGIN DEBUG] User not found in DB.");
        return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }
    
    const user = users[0];
    console.log(`[LOGIN DEBUG] Found user -> ID: ${user.id}, Role: ${user.role}, Role_ID: ${user.role_id}, SuperAdmin: ${user.is_super_admin}`);
    
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
        console.log("[LOGIN DEBUG] Password mismatch.");
        return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';
    
    console.log(`[LOGIN DEBUG] Routing decision -> isStaff: ${isStaff}, Target: ${targetRoute}`);

    let permissionNames: string[] = [];
    if (isStaff) {
        try {
            const perms: any = await query(`
                SELECT p.name FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ?
            `, [user.role_id]);
            permissionNames = perms.map((p: any) => p.name);
            console.log(`[LOGIN DEBUG] Fetched ${permissionNames.length} permissions.`);
        } catch (e) {
            console.warn("[LOGIN DEBUG] Permissions fetch failed.");
        }
    }

    const sessionData = { 
        id: user.id, 
        name: user.name, 
        email: user.email, 
        role: roleName,
        permissions: permissionNames 
    };
    
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    
    cookieStore.set('session', token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
    cookieStore.set('client_policy', JSON.stringify({ role: roleName, permissions: permissionNames }), { httpOnly: false, secure: false, maxAge: 86400, path: '/' });

    console.log(`[LOGIN DEBUG] Success! Sending redirect to: ${targetRoute}`);
    return NextResponse.json({ message: 'Login successful', user: sessionData, redirectUrl: targetRoute });
  } catch (error) {
    console.error('[LOGIN CRITICAL ERROR]:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
"""
}

def apply_final_import_fix():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed import path back to lib/auth!")

if __name__ == "__main__":
    apply_final_import_fix()
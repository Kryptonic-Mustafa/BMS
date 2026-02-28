import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    
    // Compare Hash
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // Authoritative Role Check from Database
    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';

    // Fetch Permissions
    let permissionNames: string[] = [];
    if (isStaff) {
        try {
            const perms: any = await query(`
                SELECT p.name FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ?
            `, [user.role_id]);
            permissionNames = perms.map((p: any) => p.name);
        } catch (e) {
            console.warn("Permissions fetch failed.");
        }
    }

    // Create Session
    const sessionData = { 
        id: user.id, 
        name: user.name, 
        email: user.email, 
        role: roleName,
        permissions: permissionNames 
    };
    
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    
    // Set Cookies
    cookieStore.set('session', token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
    cookieStore.set('client_policy', JSON.stringify({ role: roleName, permissions: permissionNames }), { httpOnly: false, secure: false, maxAge: 86400, path: '/' });

    // Return the specific route this user MUST go to
    return NextResponse.json({ message: 'Login successful', user: sessionData, redirectUrl: targetRoute });
  } catch (error) {
    console.error('LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
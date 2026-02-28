import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';

    let permissionNames: string[] = [];
    if (isStaff) {
        try {
            const perms: any = await query('SELECT p.name FROM permissions p JOIN role_permissions rp ON p.id = rp.permission_id WHERE rp.role_id = ?', [user.role_id]);
            permissionNames = perms.map((p: any) => p.name);
        } catch (e) {}
    }

    const sessionData = { id: user.id, name: user.name, email: user.email, role: roleName, permissions: permissionNames };
    const token = await encrypt(sessionData);
    
    // THE FIX: Create the response first, then attach cookies directly to it
    const response = NextResponse.json({ message: 'Success', redirectUrl: targetRoute });
    
    response.cookies.set('session', token, { 
        httpOnly: true, 
        secure: true, 
        maxAge: 86400, 
        path: '/' 
    });
    
    response.cookies.set('client_policy', JSON.stringify({ role: roleName, permissions: permissionNames }), { 
        httpOnly: false, 
        secure: false, 
        maxAge: 86400, 
        path: '/' 
    });

    return response;
  } catch (error) {
    console.error('LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
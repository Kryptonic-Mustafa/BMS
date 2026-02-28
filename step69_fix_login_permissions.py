import os

files = {
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';
import { decryptData } from '@/lib/crypto';

export async function POST(request: Request) {
  try {
    const rawBody = await request.json();
    const body = rawBody.data ? decryptData(rawBody.data) : rawBody;
    const { email, password } = body;

    // 1. Authenticate User
    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // 2. FETCH PERMISSIONS (This was missing!)
    const perms: any = await query(`
        SELECT p.name FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id = ?
    `, [user.role_id]);
    
    const permissionNames = perms.map((p: any) => p.name);

    // 3. Log the Login Attempt (Security Center)
    const userAgent = request.headers.get('user-agent') || 'Unknown Device';
    const ip = request.headers.get('x-forwarded-for') || '127.0.0.1';
    
    await query(
        'INSERT INTO login_logs (user_id, ip_address, user_agent, location) VALUES (?, ?, ?, ?)',
        [user.id, ip, userAgent, 'Pune, India'] 
    );

    await query(
        'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
        [user.id, `New login detected from ${userAgent.substring(0, 30)}...`, 'info']
    );

    // 4. Create Session & Cookies
    const sessionData = { 
        id: user.id, 
        name: user.name, 
        email: user.email, 
        role: user.role,
        permissions: permissionNames // ADDED BACK TO SESSION
    };
    
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    
    // Server-side secure session cookie
    cookieStore.set('session', token, { httpOnly: true, secure: true, maxAge: 86400, path: '/' });
    
    // THE FIX: Client-side UI policy cookie so the Sidebar & pages know your permissions!
    cookieStore.set('client_policy', JSON.stringify({ role: user.role, permissions: permissionNames }), { httpOnly: false, secure: false, maxAge: 86400, path: '/' });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    console.error('Login Error:', error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
"""
}

def fix_login_permissions():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Login API fixed! Permissions and Cookies are fully restored.")

if __name__ == "__main__":
    fix_login_permissions()
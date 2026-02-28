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
    
    // Check password against the hash
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // 2. Fetch Permissions (Crucial for RBAC)
    let permissionNames: string[] = [];
    try {
        const perms: any = await query(`
            SELECT p.name FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        `, [user.role_id]);
        permissionNames = perms.map((p: any) => p.name);
    } catch (e) {
        console.warn("Permissions fetch failed, defaulting to empty array", e);
    }

    // 3. Log Activity (Wrapped in try/catch so it doesn't break login if table is missing)
    try {
        const userAgent = request.headers.get('user-agent') || 'Unknown';
        const ip = request.headers.get('x-forwarded-for') || '127.0.0.1';
        await query(
            'INSERT INTO login_logs (user_id, ip_address, user_agent, location) VALUES (?, ?, ?, ?)',
            [user.id, ip, userAgent.substring(0, 255), 'Cloud Production']
        );
    } catch (logError) {
        console.error("Non-critical logging error:", logError);
    }

    // 4. Create Session
    const sessionData = { 
        id: user.id, 
        name: user.name, 
        email: user.email, 
        role: user.role_id === 1 ? 'SuperAdmin' : (user.role_id === 2 ? 'Manager' : 'Customer'),
        permissions: permissionNames 
    };
    
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    
    // Set Cookies
    cookieStore.set('session', token, { httpOnly: true, secure: true, maxAge: 86400, path: '/' });
    cookieStore.set('client_policy', JSON.stringify({ role: sessionData.role, permissions: permissionNames }), { httpOnly: false, secure: false, maxAge: 86400, path: '/' });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    console.error('CRITICAL LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Login service temporarily unavailable' }, { status: 500 });
  }
}
"""
}

def apply_production_login():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Applied Production-Hardened Login API!")

if __name__ == "__main__":
    apply_production_login()
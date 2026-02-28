import os
import shutil

files = {
    # 1. THE FOUNDATION: A bulletproof session manager
    "lib/session.ts": """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

const secretKey = process.env.JWT_SECRET || "bms_super_secret_key_2026";
const key = new TextEncoder().encode(secretKey);

export async function encrypt(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(key);
}

export async function decrypt(input: string): Promise<any> {
  try {
    const { payload } = await jwtVerify(input, key, { algorithms: ['HS256'] });
    return payload;
  } catch (error) {
    return null;
  }
}

export async function getSession() {
  const sessionCookie = (await cookies()).get('session')?.value;
  if (!sessionCookie) return null;
  return await decrypt(sessionCookie);
}
""",

    # 2. THE DATABASE: Strict TiDB compatibility
    "lib/db.ts": """
import mysql from 'mysql2/promise';

export const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  port: parseInt(process.env.DB_PORT || '4000'),
  ssl: { minVersion: 'TLSv1.2', rejectUnauthorized: true }
});

export async function query(sql: string, params: any[] = []) {
  try {
    const [results] = await pool.query(sql, params);
    return results;
  } catch (error) {
    console.error('Database query failed:', error);
    throw error;
  }
}
""",

    # 3. THE SMART API: One login to rule them all
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/session';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // Single source of truth for routing
    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';

    let permissionNames: string[] = [];
    if (isStaff) {
        try {
            const perms: any = await query('SELECT p.name FROM permissions p JOIN role_permissions rp ON p.id = rp.permission_id WHERE rp.role_id = ?', [user.role_id]);
            permissionNames = perms.map((p: any) => p.name);
        } catch (e) {
            console.warn("Permissions fetch failed.");
        }
    }

    const sessionData = { id: user.id, name: user.name, email: user.email, role: roleName, permissions: permissionNames };
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    
    cookieStore.set('session', token, { httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 86400, path: '/' });
    cookieStore.set('client_policy', JSON.stringify({ role: roleName, permissions: permissionNames }), { httpOnly: false, secure: false, maxAge: 86400, path: '/' });

    return NextResponse.json({ message: 'Success', redirectUrl: targetRoute });
  } catch (error) {
    console.error('LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
""",

    # 4. THE UI: A beautiful, single unified login page
    "app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { Landmark } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) return setError('Please enter both email and password.');
    setError(''); setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Login failed');
        setLoading(false);
        return;
      }
      
      // Force redirect to the correct dashboard
      window.location.href = data.redirectUrl;
    } catch (err) {
      setError('Connection error');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 rounded-2xl shadow-2xl p-8 border border-slate-700">
        <div className="text-center mb-8">
          <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Landmark className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Secure Login</h1>
          <p className="text-slate-400">Welcome back to Babji Bank</p>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg mb-6 text-center text-sm font-medium">{error}</div>}

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" placeholder="admin@bank.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleLogin()} className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" placeholder="••••••••" />
          </div>
          <button type="button" onClick={handleLogin} disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors shadow-lg disabled:opacity-50">
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}
""",

    # 5. THE ROOT REDIRECT: Ensure visiting '/' goes straight to login
    "app/page.tsx": """
import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/login');
}
"""
}

def apply_nuclear_reset():
    # Remove old conflicting routes
    if os.path.exists('app/login'):
        shutil.rmtree('app/login')
    
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ NUCLEAR RESET COMPLETE. The system is rebuilt and unified.")

if __name__ == "__main__":
    apply_nuclear_reset()
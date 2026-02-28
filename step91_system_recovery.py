import os

files = {
    # 1. FIX THE ROOT PAGE: Auto-redirect to Login
    "app/page.tsx": """
import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/login');
}
""",

    # 2. FIX THE LOGIN API: Make it the ultimate authority on user roles
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
    
    // Compare Hash
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // THE FIX: Authoritative Role Check from Database
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
            console.warn("Permissions fetch failed, defaulting to empty.");
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
""",

    # 3. FIX THE FRONTEND LOGIN: Force it to obey the API's redirect path
    "app/login/page.tsx": """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Landmark } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isStaffLogin, setIsStaffLogin] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

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

      // THE MAGIC FIX: Ignore the frontend toggle and obey the database URL
      window.location.href = data.redirectUrl || '/customer';
      
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
          <h1 className="text-3xl font-bold text-white mb-2">
            {isStaffLogin ? 'Staff Portal' : 'Customer Login'}
          </h1>
          <p className="text-slate-400">Welcome back to Babji Bank</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg mb-6 text-center text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Enter your email"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors shadow-lg disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-8 text-center">
          <button
            onClick={() => setIsStaffLogin(!isStaffLogin)}
            className="text-slate-400 hover:text-white text-sm font-medium transition-colors uppercase tracking-wider"
          >
            Switch to {isStaffLogin ? 'Customer' : 'Staff'} Login &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}
"""
}

def apply_system_recovery():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ System Recovery Applied: Routing now strictly obeys Database Roles.")

if __name__ == "__main__":
    apply_system_recovery()
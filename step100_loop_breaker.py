import os

files = {
    # 1. THE FRONTEND: Proper <form> to kill the Chrome warning, and router.refresh() to kill the loop
    "app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { Landmark } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevents the native HTML refresh
    
    if (!email || !password) {
        setError('Please enter both email and password.');
        return;
    }
    
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
      
      // THE FIX: Push the route, then forcefully refresh the Next.js cache to recognize the new cookie
      router.push(data.redirectUrl || '/admin');
      router.refresh();
      
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
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg mb-6 text-center text-sm">{error}</div>}

        {/* RESTORED FORM PROPERLY TO REMOVE CHROME DOM WARNING */}
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
              autoComplete="username"
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" 
              placeholder="admin@bank.com" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              autoComplete="current-password"
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" 
              placeholder="••••••••" 
            />
          </div>
          <button 
            type="submit" 
            disabled={loading} 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg shadow-lg disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
""",

    # 2. THE LAYOUT: Force Vercel to stop caching the redirect wall
    "app/(dashboard)/layout.tsx": """
import Sidebar from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

// THE FIX: Forces Vercel to NEVER cache this layout, stopping the invisible redirect loop
export const dynamic = 'force-dynamic';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden pl-64">
        <Navbar user={session} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 dark:bg-slate-900 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
""",

    # 3. THE MIDDLEWARE KILLSWITCH: Neutralizes invisible redirect loops
    "middleware.ts": """
import { NextResponse } from 'next/server';

export function middleware(request: any) {
  return NextResponse.next();
}

export const config = {
  matcher: [], 
};
""",

    # 4. THE API ROUTE: Simplest, most reliable cookie setter
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

    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';

    const sessionData = { id: user.id, name: user.name, email: user.email, role: roleName };
    const token = await encrypt(sessionData);
    
    const cookieStore = await cookies();
    cookieStore.set('session', token, { 
        httpOnly: true, 
        secure: process.env.NODE_ENV === 'production', 
        sameSite: 'lax',
        maxAge: 86400, 
        path: '/' 
    });
    
    cookieStore.set('client_policy', JSON.stringify({ role: roleName }), { 
        httpOnly: false, 
        secure: false, 
        sameSite: 'lax',
        maxAge: 86400, 
        path: '/' 
    });

    return NextResponse.json({ message: 'Success', redirectUrl: targetRoute });
  } catch (error) {
    console.error('LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
"""
}

def break_the_loop():
    for path, content in files.items():
        # THE PYTHON FIX: Only try to create directories if a directory path actually exists
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Form fixed, cache bypassed, and middleware neutralized!")

if __name__ == "__main__":
    break_the_loop()
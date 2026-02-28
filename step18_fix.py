import os

files = {
    # --- 1. UPDATE LOGIN PAGE (Allow Managers) ---
    "app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ShieldCheck, User } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');

      // Role enforcement
      // UPDATED: Allow 'admin' OR 'manager' to use the Admin Portal
      if (isAdminLogin && !['admin', 'manager'].includes(data.user.role)) {
        throw new Error('Access Denied. Not a staff account.');
      }
      
      // Redirect Logic
      if (['admin', 'manager'].includes(data.user.role)) {
          router.push('/admin');
      } else {
          router.push('/customer');
      }
      router.refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 p-8 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 w-full max-w-md transition-all">
      <div className="flex justify-center mb-6">
        <div className={`p-4 rounded-full ${isAdminLogin ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
            {isAdminLogin ? <ShieldCheck size={32} /> : <User size={32} />}
        </div>
      </div>
      
      <h2 className="text-2xl font-bold text-center mb-2 dark:text-white">
        {isAdminLogin ? 'Staff Portal' : 'Customer Login'}
      </h2>
      <p className="text-slate-500 text-center mb-6 text-sm">
        {isAdminLogin ? 'Authorized personnel only' : 'Welcome back to your account'}
      </p>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Email Address" 
          type="email" 
          value={form.email} 
          onChange={(e) => setForm({ ...form, email: e.target.value })} 
          required 
        />
        <Input 
          label="Password" 
          type="password" 
          value={form.password} 
          onChange={(e) => setForm({ ...form, password: e.target.value })} 
          required 
        />
        
        <Button 
          type="submit" 
          className={`w-full ${isAdminLogin ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-900 hover:bg-blue-800'}`}
          disabled={loading}
        >
          {loading ? 'Authenticating...' : (isAdminLogin ? 'Access Dashboard' : 'Sign In')}
        </Button>
      </form>

      <div className="mt-6 text-center pt-4 border-t border-slate-100 dark:border-slate-800">
        <button 
            onClick={() => { setIsAdminLogin(!isAdminLogin); setError(''); }}
            className="text-xs font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 uppercase tracking-wider"
        >
            {isAdminLogin ? '← Switch to Customer Login' : 'Switch to Staff Login →'}
        </button>
      </div>

      {!isAdminLogin && (
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
            No account? <Link href="/register" className="text-blue-600 hover:underline">Register</Link>
        </p>
      )}
    </div>
  );
}
""",

    # --- 2. UPDATE MIDDLEWARE (Allow Managers in Admin Routes) ---
    "middleware.ts": """
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { decrypt } from '@/lib/auth';

export async function middleware(request: NextRequest) {
  const session = request.cookies.get('session')?.value;
  const path = request.nextUrl.pathname;

  const payload = session ? await decrypt(session) : null;

  const isDashboard = path.startsWith('/admin') || path.startsWith('/customer');
  const isAuthPage = path.startsWith('/login') || path.startsWith('/register');

  if (isDashboard && !payload) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  if (isAuthPage && payload) {
    // Redirect based on role
    if (['admin', 'manager'].includes(payload.role)) {
      return NextResponse.redirect(new URL('/admin', request.url));
    } else {
      return NextResponse.redirect(new URL('/customer', request.url));
    }
  }

  // Protect Admin Routes from Customers
  if (path.startsWith('/admin') && payload && !['admin', 'manager'].includes(payload.role)) {
     return NextResponse.redirect(new URL('/customer', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/customer/:path*', '/login', '/register'],
};
""",

    # --- 3. UPDATE SIDEBAR (Visually Hide Settings for Managers) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle },
  { name: 'BankMail', href: '/messages', icon: Mail },
  { name: 'Master Settings', href: '/admin/settings', icon: Settings },
];

const customerLinks = [
  { name: 'Overview', href: '/customer', icon: LayoutDashboard },
  { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
  { name: 'History', href: '/customer/history', icon: ShieldCheck },
  { name: 'BankMail', href: '/messages', icon: Mail },
  { name: 'Support', href: '/customer/support', icon: HelpCircle },
];

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  
  // FILTER: Only show 'Master Settings' if role is 'admin' (Super Admin)
  // Managers can see everything else
  const links = userRole === 'customer' 
    ? customerLinks 
    : (userRole === 'manager' ? adminLinks.filter(l => l.name !== 'Master Settings') : adminLinks);

  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    fetch('/api/admin/settings')
      .then(res => res.json())
      .then(data => {
        if(data.site_name) setSiteSettings(data);
      });
  }, []);

  const handleLogout = async () => {
    const result = await Swal.fire({
      title: 'Sign Out?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#EF4444',
      confirmButtonText: 'Yes, Sign Out'
    });

    if (result.isConfirmed) {
      await fetch('/api/auth/logout', { method: 'POST' });
      router.push('/login');
      router.refresh();
    }
  };

  return (
    <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col h-full border-r border-slate-800 shadow-xl shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50 gap-3">
        {siteSettings.site_logo ? (
            <img src={siteSettings.site_logo} className="w-8 h-8 rounded bg-white p-0.5" />
        ) : (
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="font-bold text-lg text-white">B</span>
            </div>
        )}
        <span className="font-bold text-xl tracking-tight text-slate-100 truncate">{siteSettings.site_name}</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          {userRole === 'customer' ? 'Customer Menu' : 'Staff Menu'}
        </p>
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <Icon size={18} className={`mr-3 ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`} />
              {link.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800/50">
        <button 
          onClick={handleLogout}
          className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
        >
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
"""
}

def add_manager():
    print("👔 Adding 'Manager' Role Logic...")
    for path, content in files.items():
        # --- FIX: Only create directory if path contains one ---
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Manager Role Active! Restart server.")

if __name__ == "__main__":
    add_manager()
import os

files = {
    # --- 1. LOGIN API (Sets the new 'client_policy' cookie) ---
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
    if (!body) return NextResponse.json({ error: 'Invalid payload' }, { status: 400 });

    const { email, password } = body;

    // 1. Validate User
    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // 2. Fetch Permissions
    let permissions: string[] = [];
    if (user.role_id) {
        const perms: any = await query(`
            SELECT p.name 
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        `, [user.role_id]);
        permissions = perms.map((p: any) => p.name);
    }

    // 3. Create Session Data
    const sessionData = {
      id: user.id,
      name: user.name,
      email: user.email,
      role_id: user.role_id,
      role: user.role, // 'manager', 'admin', etc.
      is_super_admin: user.is_super_admin === 1
    };

    // 4. Set Cookies
    const cookieStore = await cookies();

    // A. Secure Session (HttpOnly - For Server)
    const token = await encrypt(sessionData);
    cookieStore.set('session', token, {
      httpOnly: true, 
      secure: process.env.NODE_ENV === 'production', 
      maxAge: 60 * 60 * 24, 
      path: '/',
    });

    // B. Client Policy (Visible - For Sidebar/Guard)
    // We store role + permissions array as a simple JSON string
    const clientPolicy = JSON.stringify({ role: user.role, permissions });
    cookieStore.set('client_policy', clientPolicy, {
        httpOnly: false, // Allow JS to read this!
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24,
        path: '/'
    });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
""",

    # --- 2. LOGOUT API (Clear both cookies) ---
    "app/api/auth/logout/route.ts": """
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
  cookieStore.delete('client_policy');
  return NextResponse.json({ success: true });
}
""",

    # --- 3. COOKIE HELPER (To read it easily on Client) ---
    "lib/clientCookie.ts": """
export function getClientPolicy() {
  if (typeof document === 'undefined') return { role: '', permissions: [] };
  
  const match = document.cookie.match(new RegExp('(^| )client_policy=([^;]+)'));
  if (match) {
    try {
        // Decode URI component because cookies are often encoded
        const jsonStr = decodeURIComponent(match[2]);
        return JSON.parse(jsonStr);
    } catch (e) {
        return { role: '', permissions: [] };
    }
  }
  return { role: '', permissions: [] };
}
""",

    # --- 4. UPDATED SIDEBAR (Reads Cookie Directly) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock } from 'lucide-react';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';
import { getClientPolicy } from '@/lib/clientCookie';

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  
  // State for permissions (loaded from cookie)
  const [policy, setPolicy] = useState<{ role: string, permissions: string[] }>({ role: '', permissions: [] });
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    // 1. Read Permissions INSTANTLY from Cookie
    const data = getClientPolicy();
    setPolicy(data);

    // 2. Fetch Branding
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
  }, []);

  // --- MENU DEFINITIONS ---
  // Ensure requiredPerm matches exactly what is in your DB (Case Sensitive!)
  const adminMenuItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, requiredPerm: null },
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'AccountsView' },
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'TransactionsView' },
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: 'SupportView' },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: 'BankMailUse' },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'RolesManage' },
    // THE FIX: This requires 'SettingsView'
    { name: 'Master Settings', href: '/admin/settings', icon: Settings, requiredPerm: 'SettingsView' },
  ];

  const customerMenuItems = [
    { name: 'Overview', href: '/customer', icon: LayoutDashboard },
    { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
    { name: 'History', href: '/customer/history', icon: ShieldCheck },
    { name: 'BankMail', href: '/messages', icon: Mail },
    { name: 'Support', href: '/customer/support', icon: HelpCircle },
  ];

  // --- FILTER LOGIC ---
  const effectiveRole = policy.role || userRole; // Use cookie role if available
  const effectivePerms = policy.permissions || [];

  const links = effectiveRole === 'customer' 
    ? customerMenuItems 
    : adminMenuItems.filter(item => {
        if (effectiveRole === 'admin') return true; // Super Admin sees all
        if (!item.requiredPerm) return true; // Public items
        return effectivePerms.includes(item.requiredPerm); // Check Array
      });

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
          {effectiveRole === 'customer' ? 'Customer Menu' : 'Staff Menu'}
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
        <button onClick={handleLogout} className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors">
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
""",

    # --- 5. UPDATED ROUTE GUARD (Reads Cookie Directly) ---
    "components/auth/RouteGuard.tsx": """
'use client';
import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { getClientPolicy } from '@/lib/clientCookie';

const REQUIRED_PERMISSIONS: Record<string, string> = {
  '/admin/customers': 'CustomersView',
  '/admin/accounts': 'AccountsView',
  '/admin/transactions': 'TransactionsView',
  '/admin/settings': 'SettingsView', 
  '/admin/roles': 'RolesManage',
  '/admin/danger': 'DangerZoneAccess'
};

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const checkedRef = useRef('');

  useEffect(() => {
    // 1. Read Policy from Cookie
    const { role, permissions } = getClientPolicy();
    
    if (role === 'admin') return; // Bypass for SuperAdmin

    // 2. Check Permission
    const protectKey = Object.keys(REQUIRED_PERMISSIONS).find(key => pathname.startsWith(key));
    
    if (protectKey) {
      const requiredPerm = REQUIRED_PERMISSIONS[protectKey];
      
      // If permission is missing in the array
      if (!permissions.includes(requiredPerm)) {
        if (checkedRef.current === pathname) return;
        checkedRef.current = pathname;

        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: 'ACCESS DENIED',
            text: 'You do not have permission to view this page.',
            showConfirmButton: false,
            timer: 3000
        });

        router.replace('/admin');
      }
    }
  }, [pathname, router]);

  return <>{children}</>;
}
"""
}

def client_cookies():
    print("🍪 Setting up Client-Side Permission Cookies...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Done! Permissions are now stored in a visible cookie for instant access.")

if __name__ == "__main__":
    client_cookies()
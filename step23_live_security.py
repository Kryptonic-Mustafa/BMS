import os

files = {
    # --- 1. FIX PROFILE API (Fetch Fresh from DB) ---
    "app/api/auth/profile/route.ts": """
import { NextResponse } from 'next/server';
import { getSession } from '@/lib/session'; // FIXED: Use DB Session, not Auth

export async function GET() {
  // This now fetches the User + Role + FRESH Permissions from DB
  const session = await getSession();
  
  if (!session) return NextResponse.json({});
  
  // Return session with the latest permissions array
  return NextResponse.json(session);
}
""",

    # --- 2. PERMISSION HOOK (Client Side Helper) ---
    "hooks/usePermissions.ts": """
'use client';
import { useState, useEffect } from 'react';

export function usePermissions() {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [role, setRole] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch fresh data on mount
    fetch('/api/auth/profile')
      .then(res => res.json())
      .then(data => {
        if (data.permissions) {
            setPermissions(data.permissions);
            setRole(data.role);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const can = (permissionName: string) => {
    if (role === 'admin') return true; // Super Admin bypass
    return permissions.includes(permissionName);
  };

  return { permissions, role, can, loading };
}
""",

    # --- 3. ROUTE GUARD (The "Bouncer") ---
    "components/auth/RouteGuard.tsx": """
'use client';
import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { usePermissions } from '@/hooks/usePermissions';
import Swal from 'sweetalert2';

// MAP PATHS TO REQUIRED PERMISSIONS
const REQUIRED_PERMISSIONS: Record<string, string> = {
  '/admin/customers': 'CustomersView',
  '/admin/accounts': 'AccountsView',
  '/admin/transactions': 'TransactionsView',
  '/admin/settings': 'SettingsView', // Checks for SettingsView
  '/admin/roles': 'RolesManage',
  '/admin/danger': 'DangerZoneAccess'
};

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { permissions, role, loading } = usePermissions();
  const checkedRef = useRef('');

  useEffect(() => {
    if (loading) return;
    if (role === 'admin') return; // Super Admins go anywhere

    // Find if current path requires a permission
    // We check if the pathname STARTS with a protected route
    const protectKey = Object.keys(REQUIRED_PERMISSIONS).find(key => pathname.startsWith(key));
    
    if (protectKey) {
      const requiredPerm = REQUIRED_PERMISSIONS[protectKey];
      
      // If user DOES NOT have the permission
      if (!permissions.includes(requiredPerm)) {
        
        // Prevent double-firing
        if (checkedRef.current === pathname) return;
        checkedRef.current = pathname;

        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: 'ACCESS DENIED',
            text: `You do not have permission to view this page.`,
            showConfirmButton: false,
            timer: 3000
        });

        // Throw back to dashboard
        router.replace('/admin');
      }
    }
  }, [pathname, permissions, role, loading, router]);

  if (loading) return null; // Or a spinner

  return <>{children}</>;
}
""",

    # --- 4. INJECT GUARD INTO LAYOUT ---
    "app/(dashboard)/layout.tsx": """
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';
import { NotificationListener } from '@/components/layout/NotificationListener';
import { RouteGuard } from '@/components/auth/RouteGuard';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar userRole={session.role} /> 
      
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar user={{ name: session.name, role: session.role }} />
        <NotificationListener /> 
        
        <main className="flex-1 overflow-auto p-4 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* WRAP CONTENT IN GUARD */}
            <RouteGuard>
                {children}
            </RouteGuard>
          </div>
        </main>
      </div>
    </div>
  );
}
""",

    # --- 5. UPDATE SIDEBAR (Use Client Hook for Live Updates) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';
import { usePermissions } from '@/hooks/usePermissions';

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const { permissions, role, loading } = usePermissions();
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
  }, []);

  // --- MENU DEFINITIONS ---
  const adminMenuItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, requiredPerm: null },
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'AccountsView' },
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'TransactionsView' },
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: 'SupportView' },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: 'BankMailUse' },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'RolesManage' },
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
  const links = userRole === 'customer' 
    ? customerMenuItems 
    : adminMenuItems.filter(item => {
        if (role === 'admin') return true; // Super Admin sees all
        if (!item.requiredPerm) return true; // Public items (Dashboard)
        return permissions.includes(item.requiredPerm); // Check Permission
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

  if (loading && userRole !== 'customer') return <aside className="w-64 bg-slate-900 h-full border-r border-slate-800" />;

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
        <button onClick={handleLogout} className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors">
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
"""
}

def secure_live():
    print("🚦 Installing Route Guards & Live Permissions...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🔒 Security System Active. URLs are now protected.")

if __name__ == "__main__":
    secure_live()
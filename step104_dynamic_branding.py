import os
import re

files = {
    # 1. THE LAYOUT FIX: Dynamically generate browser tab title from TiDB
    "app/(dashboard)/layout.tsx": """
import Sidebar from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function generateMetadata() {
  try {
    const results: any = await query('SELECT site_name FROM settings WHERE id = 1');
    const siteName = results?.[0]?.site_name || 'Bank System';
    return { title: `${siteName} - Admin Portal` };
  } catch (e) {
    return { title: 'Admin Portal' };
  }
}

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
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900" suppressHydrationWarning>
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

    # 2. THE SIDEBAR FIX: Fetches dynamic settings from API to override hardcoded Babji Bank
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { LayoutDashboard, PieChart, Users, CreditCard, Landmark, ShieldCheck, Headset, Settings, LogOut } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const [brandName, setBrandName] = useState('Loading...');
  const [brandLogo, setBrandLogo] = useState('');

  useEffect(() => {
    const fetchBrand = async () => {
      try {
        const res = await fetch('/api/admin/settings');
        const data = await res.json();
        if (data.site_name) setBrandName(data.site_name);
        if (data.site_logo) setBrandLogo(data.site_logo);
      } catch (e) {
        setBrandName('Bank System');
      }
    };
    fetchBrand();
  }, []);

  const links = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    { name: 'Analytics', href: '/admin/analytics', icon: PieChart },
    { name: 'Customers', href: '/admin/customers', icon: Users },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard },
    { name: 'Loans', href: '/admin/loans', icon: Landmark },
    { name: 'KYC', href: '/admin/kyc', icon: ShieldCheck },
    { name: 'Support', href: '/admin/support', icon: Headset },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="w-64 bg-[#0f172a] text-white h-screen fixed left-0 top-0 border-r border-slate-800 flex flex-col z-50">
      <div className="p-6 flex items-center gap-3">
        {brandLogo ? (
          <img src={brandLogo} alt="Logo" className="w-8 h-8 rounded object-cover" />
        ) : (
          <Landmark className="text-blue-500" size={28} />
        )}
        <span className="text-xl font-bold tracking-tight truncate">{brandName}</span>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto">
        {links.map((link) => {
          const isActive = pathname === link.href || pathname?.startsWith(link.href + '/');
          const Icon = link.icon;
          return (
            <Link 
              key={link.name} 
              href={link.href} 
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-blue-600/10 text-blue-500 font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{link.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <Link href="/api/auth/logout" className="flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
          <LogOut size={20} />
          <span className="font-medium">Sign Out</span>
        </Link>
      </div>
    </div>
  );
}
"""
}

def apply_dynamic_branding():
    # 1. Write the layout and sidebar files
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    
    # 2. THE SURGICAL INJECTION: Safely patches your existing Settings UI to auto-reload
    search_dirs = ["app/admin/settings", "app/(dashboard)/admin/settings"]
    for dir_path in search_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                if file.endswith("page.tsx"):
                    filepath = os.path.join(dir_path, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if "window.location.reload()" not in content:
                        # Injects the reload command gracefully right after the server responds OK
                        content = re.sub(
                            r'(const\s+data\s*=\s*await\s+res\.json\(\);?[\s\S]*?if\s*\(\!res\.ok\)\s*\{[\s\S]*?return;?\s*\})',
                            r'\1\n\n      // THE FIX: Auto-reload the page so the Sidebar and Title update immediately\n      setTimeout(() => window.location.reload(), 1200);',
                            content
                        )
                        # Fallback: Injects it right before your Toast/Alert triggers if you have them
                        if "setTimeout(() => window.location.reload()" not in content:
                            content = content.replace("toast.success(", "setTimeout(() => window.location.reload(), 1200);\n      toast.success(")

                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        
    print("✅ Dynamic Browser Tab, Sidebar Branding, and Auto-Reload successfully applied!")

if __name__ == "__main__":
    apply_dynamic_branding()
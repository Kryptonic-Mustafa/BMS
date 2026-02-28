import os

files = {
    # FIX 1: Ensure the Dashboard fetches real recent activity from the DB
    "app/api/customer/dashboard/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const recentActivity = await query(
      'SELECT * FROM transactions WHERE account_id = (SELECT id FROM accounts WHERE user_id = ?) ORDER BY created_at DESC LIMIT 5',
      [session.id]
    );

    return NextResponse.json({ recentActivity });
  } catch (error) {
    console.error("Dashboard Fetch Error:", error);
    return NextResponse.json({ recentActivity: [] });
  }
}
""",

    # FIX 2: Force Sidebar to use absolute paths to prevent redirection issues
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, Users, CreditCard, PieChart, 
  Settings, ShieldCheck, LogOut, Landmark, FileText, 
  History, Send, Wallet, Headset, Mail
} from 'lucide-react';
import { getClientPolicy } from '@/lib/auth-client';

export default function Sidebar() {
  const pathname = usePathname();
  const policy = getClientPolicy();
  const isAdmin = policy.role === 'Admin' || policy.role === 'SuperAdmin';

  const menuItems = isAdmin ? [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/admin' },
    { name: 'Analytics', icon: PieChart, path: '/admin/analytics' },
    { name: 'Customers', icon: Users, path: '/admin/customers' },
    { name: 'Accounts', icon: CreditCard, path: '/admin/accounts' },
    { name: 'Loans', icon: Landmark, path: '/admin/loans' },
    { name: 'KYC', icon: ShieldCheck, path: '/admin/kyc' },
    { name: 'Support', icon: Headset, path: '/admin/support' },
    { name: 'Master Settings', icon: Settings, path: '/admin/settings' },
  ] : [
    { name: 'Dashboard', icon: LayoutDashboard, path: '/customer' },
    { name: 'Transfer', icon: Send, path: '/customer/transfer' },
    { name: 'History', icon: History, path: '/customer/history' },
    { name: 'Utilities', icon: Wallet, path: '/customer/utilities' },
    { name: 'KYC', icon: ShieldCheck, path: '/customer/kyc' },
    { name: 'Support', icon: Headset, path: '/customer/support' },
  ];

  return (
    <div className="w-64 bg-slate-900 text-white flex flex-col h-screen fixed left-0 top-0 border-r border-slate-800">
      <div className="p-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Landmark className="text-blue-500" /> Babji Bank
        </h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 overflow-y-auto">
        {menuItems.map((item) => (
          <Link 
            key={item.name} 
            href={item.path}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              pathname === item.path ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 text-slate-400'
            }`}
          >
            <item.icon size={20} />
            <span className="font-medium">{item.name}</span>
          </Link>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button 
          onClick={() => window.location.href = '/api/auth/logout'}
          className="flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-500/10 rounded-lg w-full transition-colors"
        >
          <LogOut size={20} />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </div>
  );
}
""",

    # FIX 3: Global CSS Force (Prevents White-on-White text issues)
    "app/globals.css": """
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary: #2563eb;
  --background: #ffffff;
  --foreground: #0f172a;
}

.dark {
  --background: #0f172a;
  --foreground: #f8fafc;
}

body {
  background: var(--background);
  color: var(--foreground);
}

/* Force specific dashboard text visibility */
.text-dashboard-heading {
  color: #1e293b !important;
}

.dark .text-dashboard-heading {
  color: #f8fafc !important;
}
"""
}

def apply_master_fix():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Applied Master Fix: Sidebar, Activity Table, and Color Contrast restored!")

if __name__ == "__main__":
    apply_master_fix()
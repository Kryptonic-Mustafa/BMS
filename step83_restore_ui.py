import os

files = {
    # 1. THE MISSING FILE: Creating lib/auth-client.ts to fix the Vercel Build Error
    "lib/auth-client.ts": """
import Cookies from 'js-cookie';

export function getClientPolicy() {
    const policy = Cookies.get('client_policy');
    if (policy) {
        try {
            return JSON.parse(policy);
        } catch (e) {
            return { role: 'Guest', permissions: [] };
        }
    }
    return { role: 'Guest', permissions: [] };
}
""",

    # 2. FIXED SIDEBAR: Ensuring correct imports and paths
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, Users, CreditCard, PieChart, 
  Settings, ShieldCheck, LogOut, Landmark, History, Send, Wallet, Headset
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

    # 3. FIXED RECENT ACTIVITY: Ensuring viewpoint and data matches local
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { CreditCard, Send, Wallet, Landmark, ShieldCheck, History } from 'lucide-react';
import Link from 'next/link';

export default function CustomerDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/customer/dashboard').then(res => res.json()).then(setData);
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-4">
      <h2 className="text-3xl font-bold text-slate-800 dark:text-white">Hello, {data?.profile?.name || 'Kryptonic'} 👋</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Card className="bg-slate-900 text-white p-8 rounded-3xl relative overflow-hidden h-64 shadow-2xl border-none">
            <div className="relative z-10 flex flex-col justify-between h-full">
              <div className="flex justify-between items-start">
                <CreditCard className="text-slate-400" size={32} />
                <span className="text-xl font-bold italic opacity-60 italic">VISA</span>
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-1">Available Balance</p>
                <h3 className="text-4xl font-bold">${Number(data?.profile?.balance || 0).toLocaleString()}</h3>
              </div>
              <p className="font-mono tracking-widest text-lg">{data?.profile?.account_number || 'ACC_ADMIN_001'}</p>
            </div>
            <div className="absolute top-[-50px] right-[-50px] w-64 h-64 bg-blue-600/20 rounded-full blur-3xl"></div>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Quick Actions</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Transfer', icon: Send, path: '/customer/transfer', color: 'bg-blue-600' },
              { label: 'Bills', icon: Wallet, path: '/customer/utilities', color: 'bg-emerald-600' },
              { label: 'Loans', icon: Landmark, path: '/customer/loans', color: 'bg-purple-600' },
              { label: 'KYC', icon: ShieldCheck, path: '/customer/kyc', color: 'bg-orange-600' }
            ].map((action) => (
              <Link key={action.label} href={action.path}>
                <Card className="p-6 text-center hover:shadow-xl transition-all cursor-pointer group bg-slate-900/5 border-none">
                  <div className={`w-12 h-12 ${action.color} text-white rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg group-hover:scale-110 transition-transform`}>
                    <action.icon size={24} />
                  </div>
                  <span className="font-bold text-slate-800 dark:text-white">{action.label}</span>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-bold text-slate-800 dark:text-white">Recent Activity</h3>
        <Card className="overflow-hidden border-none shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50 dark:bg-slate-800 border-b dark:border-slate-700">
                <tr>
                  <th className="p-4 font-bold text-slate-600 dark:text-slate-400">Description</th>
                  <th className="p-4 font-bold text-slate-600 dark:text-slate-400">Date</th>
                  <th className="p-4 font-bold text-slate-600 dark:text-slate-400 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-slate-700">
                {data?.recentActivity?.map((tx: any) => (
                  <tr key={tx.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="p-4 font-medium dark:text-white">{tx.description}</td>
                    <td className="p-4 text-slate-500 dark:text-slate-400">{new Date(tx.created_at).toLocaleDateString()}</td>
                    <td className={`p-4 font-bold text-right ${tx.type === 'credit' ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {tx.type === 'credit' ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                    </td>
                  </tr>
                )) || <tr><td colSpan={3} className="p-8 text-center text-slate-500">No recent transactions.</td></tr>}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
"""
}

def apply_restore():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Build fixed and UI Viewpoints restored!")

if __name__ == "__main__":
    apply_restore()
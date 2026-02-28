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
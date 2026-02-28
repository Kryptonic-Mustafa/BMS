import os
import shutil

files = {
    # 1. THE LAYOUT FIX: Responsive padding so mobile screens don't get squished
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
      {/* THE FIX: Changed pl-64 to md:pl-64 and added mobile top padding */}
      <div className="flex-1 flex flex-col overflow-hidden md:pl-64 pt-16 md:pt-0">
        <Navbar user={session} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 dark:bg-slate-900 p-4 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
""",

    # 2. THE SIDEBAR FIX: Slide-in mobile menu with a Hamburger Icon
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { LayoutDashboard, PieChart, Users, CreditCard, Landmark, ShieldCheck, Headset, Settings, LogOut, Menu, X } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const [brandName, setBrandName] = useState('Loading...');
  const [brandLogo, setBrandLogo] = useState('');
  const [isOpen, setIsOpen] = useState(false); // Mobile state

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
    <>
      {/* Mobile Hamburger Button */}
      <div className="md:hidden fixed top-0 left-0 w-full h-16 bg-[#0f172a] z-40 flex items-center px-4 border-b border-slate-800">
        <button onClick={() => setIsOpen(true)} className="text-white hover:text-blue-400 transition-colors">
          <Menu size={28} />
        </button>
        <span className="ml-4 text-white font-bold text-lg">{brandName}</span>
      </div>

      {/* Mobile Overlay Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm" onClick={() => setIsOpen(false)} />
      )}

      {/* Sidebar Core */}
      <div className={`w-64 bg-[#0f172a] text-white h-screen fixed left-0 top-0 border-r border-slate-800 flex flex-col z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
        <div className="p-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {brandLogo ? (
              <img src={brandLogo} alt="Logo" className="w-8 h-8 rounded object-cover" />
            ) : (
              <Landmark className="text-blue-500" size={28} />
            )}
            <span className="text-xl font-bold tracking-tight truncate">{brandName}</span>
          </div>
          {/* Mobile Close Button */}
          <button onClick={() => setIsOpen(false)} className="md:hidden text-slate-400 hover:text-white">
            <X size={24} />
          </button>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto">
          {links.map((link) => {
            const isActive = pathname === link.href || pathname?.startsWith(link.href + '/');
            const Icon = link.icon;
            return (
              <Link 
                key={link.name} 
                href={link.href} 
                onClick={() => setIsOpen(false)} // Close on click for mobile
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
    </>
  );
}
""",

    # 3. THE DANGER ZONE API: Secure Bcrypt validation
    "app/api/admin/settings/danger/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized: SuperAdmin access required' }, { status: 403 });
    }

    const { password, action } = await request.json();

    // 1. Verify SuperAdmin password against TiDB
    const users: any = await query('SELECT password FROM users WHERE id = ?', [session.id]);
    if (users.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });

    const isMatch = await bcrypt.compare(password, users[0].password);
    if (!isMatch) return NextResponse.json({ error: 'Incorrect password. Action denied.' }, { status: 401 });

    // 2. Execute requested Danger Action safely
    if (action === 'wipe_transactions') {
        await query('TRUNCATE TABLE transactions');
        await query('UPDATE accounts SET balance = 0');
    } else if (action === 'reset_kyc') {
        await query("UPDATE users SET kyc_status = 'unverified' WHERE role_id != 1");
    }

    return NextResponse.json({ message: 'Action completed successfully' });
  } catch (error) {
    console.error('[DANGER API ERROR]:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
""",

    # 4. MASTER SETTINGS UI: Responsive branding + Danger Zone UI
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { ShieldAlert, Save, ServerCrash } from 'lucide-react';

export default function MasterSettings() {
  const [settings, setSettings] = useState({
    site_name: '', contact_email: '', max_transfer_limit: '', site_logo: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // Danger Zone States
  const [dangerAction, setDangerAction] = useState('');
  const [password, setPassword] = useState('');
  const [dangerMessage, setDangerMessage] = useState('');

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => {
      setSettings(data);
    });
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        setMessage('Settings saved successfully!');
        setTimeout(() => window.location.reload(), 1200);
      } else {
        setMessage('Failed to save settings.');
      }
    } catch (err) {
      setMessage('Network error.');
    }
    setLoading(false);
  };

  const handleDangerAction = async () => {
    if (!password) return setDangerMessage('Password is required.');
    setDangerMessage('Processing...');
    
    try {
      const res = await fetch('/api/admin/settings/danger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: dangerAction, password })
      });
      const data = await res.json();
      
      if (res.ok) {
        setDangerMessage(`SUCCESS: ${data.message}`);
        setPassword('');
      } else {
        setDangerMessage(`ERROR: ${data.error}`);
      }
    } catch (err) {
      setDangerMessage('ERROR: Network failure.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Master Settings</h1>
        <p className="text-slate-500 mt-1">Configure global application parameters and security.</p>
      </div>

      {/* Global Branding Settings */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
          <Settings className="text-blue-500" /> System Configurations
        </h2>
        
        {message && <div className="mb-4 p-3 bg-blue-50 text-blue-600 rounded-lg">{message}</div>}

        <form onSubmit={handleSaveSettings} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Bank Name</label>
              <input type="text" value={settings.site_name} onChange={e => setSettings({...settings, site_name: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Support Email</label>
              <input type="email" value={settings.contact_email} onChange={e => setSettings({...settings, contact_email: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Max Transfer Limit ($)</label>
              <input type="number" value={settings.max_transfer_limit} onChange={e => setSettings({...settings, max_transfer_limit: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Logo URL</label>
              <input type="text" value={settings.site_logo} onChange={e => setSettings({...settings, site_logo: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" placeholder="https://..." />
            </div>
          </div>
          <div className="pt-4 flex justify-end">
            <button type="submit" disabled={loading} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg flex items-center gap-2">
              <Save size={18} /> {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>

      {/* DANGER ZONE */}
      <div className="bg-red-50 dark:bg-red-900/10 rounded-xl shadow-sm border border-red-200 dark:border-red-900/50 p-6">
        <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2 flex items-center gap-2">
          <ShieldAlert /> Danger Zone
        </h2>
        <p className="text-sm text-red-500 mb-6">These actions are destructive and cannot be undone. SuperAdmin password is required.</p>

        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg">
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><ServerCrash size={18} className="text-red-500" /> Wipe All Transactions</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Deletes all transaction history and resets all account balances to $0.</p>
            </div>
            <button onClick={() => setDangerAction('wipe_transactions')} className="px-4 py-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 rounded-lg font-medium whitespace-nowrap">
              Select Action
            </button>
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-center p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg">
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><Users size={18} className="text-red-500" /> Reset All KYC</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Changes all customer KYC statuses back to 'unverified'.</p>
            </div>
            <button onClick={() => setDangerAction('reset_kyc')} className="px-4 py-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 rounded-lg font-medium whitespace-nowrap">
              Select Action
            </button>
          </div>
        </div>

        {/* Password Verification Modal Area */}
        {dangerAction && (
          <div className="mt-6 p-4 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-lg">
            <label className="block text-sm font-bold text-red-700 dark:text-red-400 mb-2">
              Confirm Action: <span className="uppercase">{dangerAction.replace('_', ' ')}</span>
            </label>
            <div className="flex flex-col md:flex-row gap-3">
              <input 
                type="password" 
                placeholder="Enter SuperAdmin Password..." 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="flex-1 px-4 py-2 bg-white dark:bg-slate-900 border border-red-300 dark:border-red-700 rounded-lg text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-red-500"
              />
              <button 
                onClick={handleDangerAction}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md"
              >
                Execute
              </button>
              <button 
                onClick={() => {setDangerAction(''); setDangerMessage(''); setPassword('');}}
                className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-white font-medium rounded-lg"
              >
                Cancel
              </button>
            </div>
            {dangerMessage && <p className="mt-3 font-medium text-red-600 dark:text-red-400">{dangerMessage}</p>}
          </div>
        )}
      </div>

    </div>
  );
}
"""
}

def finalize_system():
    # Remove older redundant settings file to prevent Next.js conflicts
    if os.path.exists('app/admin/settings/page.tsx'):
        os.remove('app/admin/settings/page.tsx')
        
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ System fully responsive and Danger Zone secured!")

if __name__ == "__main__":
    finalize_system()
import os

files = {
    # --- 1. FIX: DASHBOARD STATS API (Was missing, causing "0" issue) ---
    "app/api/admin/stats/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ customers: 0, holdings: 0, transactions: 0 });

  // 1. Total Customers (Role ID 3)
  const users: any = await query('SELECT COUNT(*) as count FROM users WHERE role_id = 3');
  
  // 2. Total Holdings (Sum of all account balances)
  const money: any = await query('SELECT SUM(balance) as total FROM accounts');
  
  // 3. Total Transactions
  const tx: any = await query('SELECT COUNT(*) as count FROM transactions');

  return NextResponse.json({
    customers: users[0].count || 0,
    holdings: money[0].total || 0,
    transactions: tx[0].count || 0
  });
}
""",

    # --- 2. NEW: ANALYTICS DATA API ---
    "app/api/admin/analytics/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  // 1. Transaction Volume (Last 7 Days)
  const txVolume = await query(`
    SELECT DATE_FORMAT(created_at, '%Y-%m-%d') as date, 
           SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as income,
           SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as expense
    FROM transactions 
    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY date 
    ORDER BY date ASC
  `);

  // 2. User Growth (Last 6 Months)
  const userGrowth = await query(`
    SELECT DATE_FORMAT(created_at, '%M') as month, COUNT(*) as users
    FROM users
    WHERE role_id = 3 AND created_at >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
    GROUP BY month
    ORDER BY MIN(created_at) ASC
  `);

  // 3. Account Types Distribution
  const accDistribution = await query(`
    SELECT type as name, COUNT(*) as value FROM accounts GROUP BY type
  `);

  return NextResponse.json({ txVolume, userGrowth, accDistribution });
}
""",

    # --- 3. UI UPDATE: TABBED KYC PAGE ---
    "app/(dashboard)/admin/kyc/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, FileText, History, LayoutList, Clock } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function AdminKYCPage() {
  const [activeTab, setActiveTab] = useState<'requests' | 'history'>('requests');
  const [requests, setRequests] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  const fetchData = async () => {
    const res = await fetch('/api/admin/kyc');
    if (res.ok) {
        const data = await res.json();
        setRequests(data.requests || []);
        setHistory(data.history || []);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (userId: number, action: 'approve' | 'reject') => {
    let notes = '';
    if (action === 'reject') {
        const { value } = await Swal.fire({ title: 'Reject Reason', input: 'text', showCancelButton: true });
        if (!value) return; 
        notes = value;
    }

    await fetch('/api/admin/kyc', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ userId, action, notes })
    });

    Swal.fire('Success', `User ${action}ed`, 'success');
    fetchData();
    setSelectedDoc(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold dark:text-white">KYC Management</h2>
      </div>

      {/* TABS HEADER */}
      <div className="flex border-b border-slate-200 dark:border-slate-700">
        <button 
            onClick={() => setActiveTab('requests')}
            className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition ${
                activeTab === 'requests' 
                ? 'border-blue-600 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
        >
            <Clock size={16}/> Pending Requests 
            <span className="bg-slate-100 text-slate-600 px-2 rounded-full text-xs">{requests.length}</span>
        </button>
        <button 
            onClick={() => setActiveTab('history')}
            className={`px-6 py-3 text-sm font-medium flex items-center gap-2 border-b-2 transition ${
                activeTab === 'history' 
                ? 'border-blue-600 text-blue-600' 
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
        >
            <History size={16}/> Activity Log
        </button>
      </div>

      {/* TAB CONTENT */}
      <div className="pt-4">
        {activeTab === 'requests' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {requests.map((req: any) => (
                    <Card key={req.id} className="flex flex-col gap-4 border-t-4 border-t-blue-500">
                        <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
                            <div className="bg-blue-100 p-2 rounded-full text-blue-600"><FileText size={20}/></div>
                            <div>
                                <div className="font-bold text-slate-900">{req.name}</div>
                                <div className="text-xs text-slate-500">{req.email}</div>
                            </div>
                        </div>
                        <div className="text-sm space-y-2">
                             <div className="flex justify-between"><span className="text-slate-500">Doc:</span> <span className="font-medium capitalize">{req.document_type}</span></div>
                             <div className="flex justify-between"><span className="text-slate-500">Date:</span> <span>{new Date(req.submitted_at).toLocaleDateString()}</span></div>
                        </div>
                        <Button className="w-full mt-2" onClick={() => setSelectedDoc(req)}>Review Application</Button>
                    </Card>
                ))}
                {requests.length === 0 && (
                    <div className="col-span-3 text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                        <Check size={48} className="mx-auto text-slate-300 mb-2"/>
                        <p className="text-slate-500">All caught up! No pending requests.</p>
                    </div>
                )}
            </div>
        ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                {history.map((log: any) => (
                    <Card key={log.id} className="flex items-center gap-4 p-4">
                        <div className={`p-2 rounded-full ${log.action_type === 'KYC_APPROVE' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                            {log.action_type === 'KYC_APPROVE' ? <Check size={20}/> : <X size={20}/>}
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900">
                                {log.actor_name} <span className="text-slate-500 font-normal">marked</span> {log.target_name} <span className="text-slate-500 font-normal">as</span> {log.action_type === 'KYC_APPROVE' ? 'Verified' : 'Rejected'}
                            </p>
                            <p className="text-xs text-slate-400">{new Date(log.created_at).toLocaleString()}</p>
                        </div>
                        {log.details && log.details.includes('Reason:') && (
                            <span className="text-xs bg-slate-100 px-2 py-1 rounded text-slate-500 max-w-xs truncate">
                                {log.details.split('Reason: ')[1]}
                            </span>
                        )}
                    </Card>
                ))}
            </div>
        )}
      </div>

      <Modal isOpen={!!selectedDoc} onClose={() => setSelectedDoc(null)} title="Review Document">
        {selectedDoc && (
            <div className="space-y-6">
                <div className="bg-slate-100 p-4 rounded-lg flex justify-center">
                    <img src={selectedDoc.file_data} className="max-h-[60vh] object-contain shadow-lg rounded" />
                </div>
                <div className="flex justify-end gap-3">
                    <Button variant="danger" onClick={() => handleAction(selectedDoc.user_id, 'reject')}><X size={18} className="mr-2"/> Reject</Button>
                    <Button onClick={() => handleAction(selectedDoc.user_id, 'approve')}><Check size={18} className="mr-2"/> Approve</Button>
                </div>
            </div>
        )}
      </Modal>
    </div>
  );
}
""",

    # --- 4. NEW PAGE: ANALYTICS (Charts) ---
    "app/(dashboard)/admin/analytics/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from 'recharts';

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/admin/analytics').then(res => res.json()).then(setData);
  }, []);

  if (!data) return <div className="p-8 text-center text-slate-500">Loading Analytics...</div>;

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Financial Analytics</h2>

      {/* TOP ROW: Transaction Volume */}
      <Card className="p-6">
        <h3 className="text-lg font-bold mb-6 text-slate-700">Transaction Volume (Last 7 Days)</h3>
        <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.txVolume}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0"/>
                    <XAxis dataKey="date" tick={{fontSize: 12}} stroke="#64748b" />
                    <YAxis tick={{fontSize: 12}} stroke="#64748b"/>
                    <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                    <Legend />
                    <Line type="monotone" dataKey="income" name="Credits ($)" stroke="#10b981" strokeWidth={3} dot={{r: 4}} />
                    <Line type="monotone" dataKey="expense" name="Debits ($)" stroke="#ef4444" strokeWidth={3} dot={{r: 4}} />
                </LineChart>
            </ResponsiveContainer>
        </div>
      </Card>

      {/* BOTTOM ROW: Split Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Growth */}
        <Card className="p-6">
            <h3 className="text-lg font-bold mb-6 text-slate-700">User Growth (6 Months)</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.userGrowth}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0"/>
                        <XAxis dataKey="month" tick={{fontSize: 12}} stroke="#64748b"/>
                        <YAxis allowDecimals={false} stroke="#64748b"/>
                        <Tooltip cursor={{fill: '#f1f5f9'}} />
                        <Bar dataKey="users" name="New Users" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </Card>

        {/* Account Types */}
        <Card className="p-6">
            <h3 className="text-lg font-bold mb-6 text-slate-700">Account Distribution</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie 
                            data={data.accDistribution} 
                            cx="50%" cy="50%" 
                            innerRadius={60} 
                            outerRadius={100} 
                            fill="#8884d8" 
                            paddingAngle={5} 
                            dataKey="value"
                        >
                            {data.accDistribution.map((entry: any, index: number) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend verticalAlign="bottom" height={36}/>
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 5. UPDATE SIDEBAR (Add Analytics Link) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck, BarChart3 } from 'lucide-react';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';
import { getClientPolicy } from '@/lib/clientCookie';

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [policy, setPolicy] = useState<{ role: string, permissions: string[] }>({ role: '', permissions: [] });
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    const data = getClientPolicy();
    setPolicy(data);
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
  }, []);

  const adminMenuItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, requiredPerm: null },
    { name: 'Analytics', href: '/admin/analytics', icon: BarChart3, requiredPerm: 'Reports' }, // NEW
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'AccountsView' },
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'TransactionsView' },
    { name: 'KYC Requests', href: '/admin/kyc', icon: BadgeCheck, requiredPerm: 'KYCManage' },
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: 'SupportView' },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: 'BankMailUse' },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'RolesManage' },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings, requiredPerm: 'SettingsView' },
  ];

  const customerMenuItems = [
    { name: 'Overview', href: '/customer', icon: LayoutDashboard },
    { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
    { name: 'Verify Identity (KYC)', href: '/customer/kyc', icon: FileText },
    { name: 'History', href: '/customer/history', icon: ShieldCheck },
    { name: 'BankMail', href: '/messages', icon: Mail },
    { name: 'Support', href: '/customer/support', icon: HelpCircle },
  ];

  const effectiveRole = policy.role || userRole;
  const effectivePerms = policy.permissions || [];

  const links = effectiveRole === 'customer' 
    ? customerMenuItems 
    : adminMenuItems.filter(item => {
        if (effectiveRole === 'admin') return true;
        if (!item.requiredPerm) return true;
        return effectivePerms.includes(item.requiredPerm);
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
"""
}

def analytics_upgrade():
    print("📊 Installing Analytics Module & KYC Tabs...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Upgrade Complete!")
    print("⚠️  IMPORTANT: Please run 'npm install recharts' in your terminal.")

if __name__ == "__main__":
    analytics_upgrade()
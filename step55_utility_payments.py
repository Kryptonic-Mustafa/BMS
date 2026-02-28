import os

files = {
    # --- 1. UTILITY API (Fetch Providers & Pay) ---
    "app/api/customer/utilities/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export const dynamic = 'force-dynamic';

export async function GET() {
  const providers = await query('SELECT * FROM utility_providers ORDER BY category ASC');
  return NextResponse.json(providers);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { providerId, consumerNumber, amount, pin } = await request.json();

  // 1. Verify PIN & Balance
  const user: any = await query('SELECT pin FROM users WHERE id = ?', [session.id]);
  if (user[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

  const acc: any = await query('SELECT id, balance FROM accounts WHERE user_id = ?', [session.id]);
  if (Number(acc[0].balance) < Number(amount)) return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });

  // 2. Execute Payment
  await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, acc[0].id]);
  
  // 3. Log Transaction
  const provider: any = await query('SELECT name FROM utility_providers WHERE id = ?', [providerId]);
  const tx: any = await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)',
    [acc[0].id, amount, `Bill Pay: ${provider[0].name} (${consumerNumber})`]
  );

  // 4. Record Bill
  await query(
    'INSERT INTO bill_payments (user_id, provider_id, consumer_number, amount, transaction_id) VALUES (?, ?, ?, ?, ?)',
    [session.id, providerId, consumerNumber, amount, tx.insertId]
  );

  // 5. Notify & Audit
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'BILL_PAY',
    details: `Paid $${amount} to ${provider[0].name}`
  });

  await query(
    'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
    [session.id, `Payment of $${amount} to ${provider[0].name} was successful.`, 'success']
  );

  return NextResponse.json({ success: true });
}
""",

    # --- 2. COMPACT UTILITY PAGE UI ---
    "app/(dashboard)/customer/utilities/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Zap, Droplets, Wifi, Phone, Flame, Receipt, ArrowRight, ShieldCheck } from 'lucide-react';
import Swal from 'sweetalert2';

export default function UtilitiesPage() {
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState<any>(null);
  const [form, setForm] = useState({ consumerNumber: '', amount: '', pin: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/customer/utilities').then(res => res.json()).then(setProviders);
  }, []);

  const getIcon = (cat: string) => {
    switch(cat) {
        case 'electricity': return <Zap className="text-yellow-500"/>;
        case 'water': return <Droplets className="text-blue-500"/>;
        case 'internet': return <Wifi className="text-purple-500"/>;
        case 'mobile': return <Phone className="text-green-500"/>;
        case 'gas': return <Flame className="text-orange-500"/>;
        default: return <Receipt/>;
    }
  };

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('/api/customer/utilities', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, providerId: selected.id })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire('Success', 'Bill Paid Successfully', 'success');
        setForm({ consumerNumber: '', amount: '', pin: '' });
        setSelected(null);
    } else {
        Swal.fire('Error', data.error, 'error');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* LEFT: SELECT PROVIDER */}
        <div className="md:col-span-2 space-y-4 flex flex-col min-h-0">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <Receipt className="text-blue-600"/> Bill Payments
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Select a service provider to pay your utility bills.</p>
            </div>
            
            <Card className="flex-1 overflow-y-auto p-2 border-slate-200 dark:border-slate-800 shadow-md">
                <div className="grid grid-cols-1 gap-2">
                    {providers.map((p: any) => (
                        <button 
                            key={p.id} 
                            onClick={() => setSelected(p)}
                            className={`flex items-center gap-3 p-3 rounded-xl transition text-left border ${
                                selected?.id === p.id 
                                ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/30 dark:border-blue-700' 
                                : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-800/50'
                            }`}
                        >
                            <div className="bg-white dark:bg-slate-800 p-2 rounded-lg shadow-sm">{getIcon(p.category)}</div>
                            <div>
                                <p className="font-bold text-sm text-slate-800 dark:text-white">{p.name}</p>
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">{p.category}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </Card>
        </div>

        {/* RIGHT: PAYMENT FORM */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800 flex flex-col justify-center relative overflow-hidden">
            {selected ? (
                <form onSubmit={handlePay} className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded-lg">{getIcon(selected.category)}</div>
                        <div>
                            <h3 className="font-bold text-slate-800 dark:text-white">Paying {selected.name}</h3>
                            <p className="text-xs text-slate-500">Instant Settlement</p>
                        </div>
                    </div>

                    <Input 
                        label="Consumer / Account ID" 
                        placeholder="e.g. 1000928374"
                        value={form.consumerNumber}
                        onChange={e => setForm({...form, consumerNumber: e.target.value})}
                        required
                    />

                    <div className="grid grid-cols-2 gap-4">
                        <Input 
                            label="Amount ($)" 
                            type="number"
                            placeholder="0.00"
                            value={form.amount}
                            onChange={e => setForm({...form, amount: e.target.value})}
                            required
                        />
                        <Input 
                            label="Security PIN" 
                            type="password"
                            maxLength={4}
                            placeholder="****"
                            value={form.pin}
                            onChange={e => setForm({...form, pin: e.target.value})}
                            required
                        />
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center gap-3 text-xs text-blue-700 dark:text-blue-300">
                        <ShieldCheck size={18}/>
                        <p>Funds will be deducted from your primary savings account immediately.</p>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full py-3 flex items-center justify-center gap-2">
                        {loading ? 'Processing...' : <><span className="font-bold">Pay Bill Now</span> <ArrowRight size={18}/></>}
                    </Button>
                </form>
            ) : (
                <div className="text-center py-20 text-slate-400">
                    <Receipt size={48} className="mx-auto mb-4 opacity-10"/>
                    <p>Select a provider from the left to start</p>
                </div>
            )}
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 3. ADD TO SIDEBAR ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck, BarChart3, Banknote, Contact, Receipt } from 'lucide-react';
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
    { name: 'Analytics', href: '/admin/analytics', icon: BarChart3, requiredPerm: 'Reports' },
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'AccountsView' },
    { name: 'Loan Requests', href: '/admin/loans', icon: 'LoansManage' }, 
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
    { name: 'Bill Payments', href: '/customer/utilities', icon: Receipt }, // NEW
    { name: 'Beneficiaries', href: '/customer/beneficiaries', icon: Contact },
    { name: 'Loans', href: '/customer/loans', icon: Banknote },
    { name: 'Verify Identity (KYC)', href: '/customer/kyc', icon: FileText },
    { name: 'History', href: '/customer/history', icon: ShieldCheck },
    { name: 'BankMail', href: '/messages', icon: Mail },
    { name: 'Support', href: '/customer/support', icon: HelpCircle },
  ];

  const effectiveRole = policy.role || userRole;
  const effectivePerms = policy.permissions || [];

  const links = effectiveRole === 'customer' 
    ? customerMenuItems 
    : adminMenuItems.filter((item: any) => {
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
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-lg text-white">B</div>
        <span className="font-bold text-xl tracking-tight text-slate-100 truncate">{siteSettings.site_name}</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          {effectiveRole === 'customer' ? 'Customer Menu' : 'Staff Menu'}
        </p>
        {links.map((link: any) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          if (typeof Icon === 'string') return null; // Logic fix for icon rendering
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

def install_utilities():
    print("⚡ Installing Utility Billing System & Syncing Permissions...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    install_utilities()
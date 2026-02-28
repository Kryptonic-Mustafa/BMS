import os

files = {
    # --- 1. MERCHANT API (Verify QR & Pay) ---
    "app/api/customer/merchant/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export const dynamic = 'force-dynamic';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { merchantCode, amount, pin } = await request.json();

  // 1. Verify Merchant
  const merch: any = await query('SELECT * FROM merchants WHERE merchant_code = ?', [merchantCode]);
  if (merch.length === 0) return NextResponse.json({ error: 'Invalid QR Code / Merchant' }, { status: 404 });
  const merchant = merch[0];

  // 2. Verify User PIN & Balance
  const user: any = await query('SELECT pin, name FROM users WHERE id = ?', [session.id]);
  if (user[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

  const acc: any = await query('SELECT id, balance FROM accounts WHERE user_id = ?', [session.id]);
  if (Number(acc[0].balance) < Number(amount)) return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });

  // 3. Execute Payment (Move money from User to Merchant Account)
  await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, acc[0].id]);
  
  // 4. Log Transaction
  const tx: any = await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)',
    [acc[0].id, amount, `Merchant Payment: ${merchant.business_name}`]
  );

  // 5. Notify & Audit
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'MERCHANT_PAY',
    details: `Paid $${amount} to ${merchant.business_name} via QR`
  });

  await query(
    'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
    [session.id, `Payment of $${amount} to ${merchant.business_name} successful! 🛍️`, 'success']
  );

  return NextResponse.json({ success: true, merchant: merchant.business_name });
}
""",

    # --- 2. QR SCANNER UI (SIMULATION) ---
    "app/(dashboard)/customer/scan/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Scan, QrCode, Store, ArrowRight, ShieldCheck, X, Camera } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ScanPage() {
  const [step, setStep] = useState<'scan' | 'pay'>('scan');
  const [selectedMerch, setSelectedMerch] = useState<any>(null);
  const [form, setForm] = useState({ amount: '', pin: '' });
  const [loading, setLoading] = useState(false);

  // Simulation: Predefined Shop QR Codes
  const demoShops = [
    { name: 'SuperMart HQ', code: 'QR_SUPERMART', icon: <Store/> },
    { name: 'Star Coffee', code: 'QR_STARCOFFEE', icon: <Store/> },
    { name: 'City Fuel', code: 'QR_CITYFUEL', icon: <Store/> }
  ];

  const handleScanSimulation = (merch: any) => {
    setSelectedMerch(merch);
    setStep('pay');
  };

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('/api/customer/merchant', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, merchantCode: selectedMerch.code })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire({
            title: 'Payment Successful!',
            text: `Paid $${form.amount} to ${selectedMerch.name}`,
            icon: 'success',
            confirmButtonText: 'Great!'
        });
        setStep('scan');
        setForm({ amount: '', pin: '' });
    } else {
        Swal.fire('Error', data.error, 'error');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="flex flex-col items-center mb-8">
        <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
            <Scan className="text-blue-600"/> QR Pay
        </h2>
        <p className="text-slate-500 text-sm">Instant payments at your favorite merchants.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        
        {/* LEFT: SCANNER AREA */}
        <div className="relative group">
            <Card className="aspect-square flex flex-col items-center justify-center border-2 border-dashed border-blue-200 dark:border-blue-900 bg-slate-50 dark:bg-slate-900/50 relative overflow-hidden">
                {step === 'scan' ? (
                    <div className="text-center animate-pulse">
                        <Camera size={64} className="text-slate-300 mx-auto mb-4"/>
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Position QR code inside</p>
                        <div className="mt-8 grid grid-cols-1 gap-2">
                             <p className="text-[10px] text-slate-500 mb-2">Simulate Scan:</p>
                             {demoShops.map(shop => (
                                 <button key={shop.code} onClick={() => handleScanSimulation(shop)} className="text-xs bg-white dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-500 transition shadow-sm">
                                     Scan {shop.name}
                                 </button>
                             ))}
                        </div>
                    </div>
                ) : (
                    <div className="text-center">
                        <div className="bg-green-100 text-green-600 p-4 rounded-full inline-block mb-4">
                            <Store size={48}/>
                        </div>
                        <h3 className="text-xl font-bold">{selectedMerch.name}</h3>
                        <p className="text-xs text-slate-500">Verified Merchant ✅</p>
                    </div>
                )}
                
                {/* Scanner corners */}
                <div className="absolute top-4 left-4 w-8 h-8 border-t-4 border-l-4 border-blue-500 rounded-tl-lg"></div>
                <div className="absolute top-4 right-4 w-8 h-8 border-t-4 border-r-4 border-blue-500 rounded-tr-lg"></div>
                <div className="absolute bottom-4 left-4 w-8 h-8 border-b-4 border-l-4 border-blue-500 rounded-bl-lg"></div>
                <div className="absolute bottom-4 right-4 w-8 h-8 border-b-4 border-r-4 border-blue-500 rounded-br-lg"></div>
            </Card>
        </div>

        {/* RIGHT: PAYMENT FORM */}
        <Card className="p-6 shadow-2xl border-slate-200 dark:border-slate-800 h-fit">
            {step === 'pay' ? (
                <form onSubmit={handlePayment} className="space-y-5 animate-in slide-in-from-right-4 duration-300">
                    <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Complete Payment</span>
                        <button onClick={() => setStep('scan')} className="text-slate-400 hover:text-red-500 transition"><X size={18}/></button>
                    </div>

                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Pay Amount ($)</label>
                        <Input 
                            type="number" placeholder="0.00" autoFocus
                            value={form.amount} onChange={e => setForm({...form, amount: e.target.value})}
                            required className="text-2xl font-bold py-3"
                        />
                    </div>

                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Security PIN</label>
                        <Input 
                            type="password" maxLength={4} placeholder="****"
                            value={form.pin} onChange={e => setForm({...form, pin: e.target.value})}
                            required className="tracking-[1em] text-center text-lg"
                        />
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center gap-3 text-xs text-blue-700 dark:text-blue-300">
                        <ShieldCheck size={18} className="shrink-0"/>
                        <p>This payment will be settled instantly and is non-reversible.</p>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full py-4 text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-500/20">
                        {loading ? 'Processing...' : 'Pay Instant'}
                    </Button>
                </form>
            ) : (
                <div className="text-center py-16 text-slate-400">
                    <QrCode size={48} className="mx-auto mb-4 opacity-10"/>
                    <p className="text-sm">Scan a merchant QR code to start payment</p>
                </div>
            )}
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 3. UPDATE SIDEBAR (Add Scan Link) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck, BarChart3, Banknote, Contact, Receipt, Scan } from 'lucide-react';
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
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'TransactionsView' },
    { name: 'KYC Requests', href: '/admin/kyc', icon: BadgeCheck, requiredPerm: 'KYCManage' },
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: 'SupportView' },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: 'BankMailUse' },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'RolesManage' },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings, requiredPerm: 'SettingsView' },
  ];

  const customerMenuItems = [
    { name: 'Overview', href: '/customer', icon: LayoutDashboard },
    { name: 'QR Pay', href: '/customer/scan', icon: Scan }, // NEW
    { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
    { name: 'Bill Payments', href: '/customer/utilities', icon: Receipt },
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

def install_qr_pay():
    print("📸 Installing QR Pay Simulation...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    install_qr_pay()
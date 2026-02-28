import os

files = {
    # --- 1. LOAN API (Apply & View) ---
    "app/api/customer/loans/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const loans = await query('SELECT * FROM loans WHERE user_id = ? ORDER BY created_at DESC', [session.id]);
  return NextResponse.json(loans);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { amount, duration, purpose, emi, rate } = await request.json();

  await query(
    'INSERT INTO loans (user_id, amount, duration_months, interest_rate, monthly_emi, purpose) VALUES (?, ?, ?, ?, ?, ?)',
    [session.id, amount, duration, rate, emi, purpose]
  );

  return NextResponse.json({ success: true });
}
""",

    # --- 2. ADMIN LOAN API (Approve & Disburse) ---
    "app/api/admin/loans/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  // Fetch pending loans with user info
  const loans = await query(`
    SELECT l.*, u.name, u.email, a.account_number
    FROM loans l
    JOIN users u ON l.user_id = u.id
    LEFT JOIN accounts a ON u.id = a.user_id
    ORDER BY l.created_at DESC
  `);
  
  return NextResponse.json(loans);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.permissions?.includes('LoansManage') && session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const { loanId, action } = await request.json();
  const status = action === 'approve' ? 'approved' : 'rejected';

  // 1. Get Loan Details
  const loan: any = await query('SELECT * FROM loans WHERE id = ?', [loanId]);
  if (!loan.length) return NextResponse.json({ error: 'Loan not found' }, { status: 404 });
  const loanData = loan[0];

  // 2. IF APPROVED: Credit Money to User Account
  if (status === 'approved') {
      // Find user's primary account
      const acc: any = await query('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', [loanData.user_id]);
      if (acc.length > 0) {
          // Add Balance
          await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [loanData.amount, acc[0].id]);
          
          // Log Transaction
          await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)',
             [acc[0].id, loanData.amount, `Loan Disbursement: #${loanId}`]
          );
      }
  }

  // 3. Update Loan Status
  await query('UPDATE loans SET status = ?, approved_by = ? WHERE id = ?', [status, session.id, loanId]);

  // 4. Audit Log
  await logActivity({
      actorId: session.id,
      actorName: session.name,
      targetId: loanData.user_id,
      action: 'LOAN_DECISION',
      details: `Loan #${loanId} was ${status}`
  });

  return NextResponse.json({ success: true });
}
""",

    # --- 3. CUSTOMER LOAN PAGE (Calculator + List) ---
    "app/(dashboard)/customer/loans/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DollarSign, Calculator, Clock, CheckCircle, XCircle } from 'lucide-react';
import Swal from 'sweetalert2';

export default function LoanPage() {
  const [loans, setLoans] = useState([]);
  const [amount, setAmount] = useState(5000);
  const [duration, setDuration] = useState(12);
  const [purpose, setPurpose] = useState('Personal Use');
  
  const interestRate = 12; // Flat 12% for demo

  // EMI Calculator Logic
  const calculateEMI = () => {
    const r = interestRate / 12 / 100;
    const emi = amount * r * (Math.pow(1 + r, duration) / (Math.pow(1 + r, duration) - 1));
    return Math.round(emi);
  };

  const fetchLoans = async () => {
    const res = await fetch('/api/customer/loans');
    if (res.ok) setLoans(await res.json());
  };

  useEffect(() => { fetchLoans(); }, []);

  const handleApply = async () => {
    const result = await Swal.fire({
        title: 'Confirm Application',
        text: `Apply for $${amount} loan? Monthly EMI will be $${calculateEMI()}`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Yes, Apply'
    });

    if (result.isConfirmed) {
        await fetch('/api/customer/loans', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                amount,
                duration,
                purpose,
                rate: interestRate,
                emi: calculateEMI()
            })
        });
        Swal.fire('Success', 'Loan application submitted!', 'success');
        fetchLoans();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Loan Services</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CALCULATOR */}
        <div className="lg:col-span-1">
            <Card className="bg-slate-900 text-white p-6">
                <div className="flex items-center gap-2 mb-6">
                    <Calculator className="text-blue-400"/>
                    <h3 className="font-bold text-lg">Loan Calculator</h3>
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="text-sm text-slate-400 mb-1 block">Amount ($)</label>
                        <input 
                            type="range" min="1000" max="50000" step="1000"
                            className="w-full accent-blue-500"
                            value={amount} onChange={e => setAmount(Number(e.target.value))}
                        />
                        <div className="text-right font-bold text-xl">${amount.toLocaleString()}</div>
                    </div>

                    <div>
                        <label className="text-sm text-slate-400 mb-1 block">Duration (Months)</label>
                        <input 
                            type="range" min="6" max="60" step="6"
                            className="w-full accent-green-500"
                            value={duration} onChange={e => setDuration(Number(e.target.value))}
                        />
                        <div className="text-right font-bold text-xl">{duration} Months</div>
                    </div>

                    <div className="bg-white/10 p-4 rounded-lg mt-4">
                        <p className="text-sm text-slate-300">Monthly EMI</p>
                        <p className="text-3xl font-bold text-green-400">${calculateEMI().toLocaleString()}</p>
                        <p className="text-xs text-slate-400 mt-1">@ {interestRate}% Interest Rate</p>
                    </div>

                    <Input 
                        label="Purpose" 
                        value={purpose} 
                        onChange={e => setPurpose(e.target.value)}
                        className="bg-white/10 border-none text-white placeholder-slate-500"
                    />

                    <Button onClick={handleApply} className="w-full bg-blue-600 hover:bg-blue-500 mt-2">Apply Now</Button>
                </div>
            </Card>
        </div>

        {/* ACTIVE LOANS LIST */}
        <div className="lg:col-span-2 space-y-4">
            <h3 className="font-bold text-slate-500 uppercase text-sm">Your Applications</h3>
            {loans.map((loan: any) => (
                <Card key={loan.id} className="flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-4">
                        <div className="bg-blue-100 p-3 rounded-full text-blue-600">
                            <DollarSign size={24}/>
                        </div>
                        <div>
                            <h4 className="font-bold text-lg text-slate-800 dark:text-white">${Number(loan.amount).toLocaleString()}</h4>
                            <p className="text-sm text-slate-500">{loan.purpose} • {loan.duration_months} Months</p>
                        </div>
                    </div>
                    
                    <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                            loan.status === 'approved' ? 'bg-green-100 text-green-700' :
                            loan.status === 'rejected' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                        }`}>
                            {loan.status}
                        </span>
                        <p className="text-xs text-slate-400 mt-2">EMI: ${Number(loan.monthly_emi).toLocaleString()}/mo</p>
                    </div>
                </Card>
            ))}
            {loans.length === 0 && <p className="text-slate-400 p-4">No active loans.</p>}
        </div>
      </div>
    </div>
  );
}
""",

    # --- 4. ADMIN LOAN REVIEW PAGE ---
    "app/(dashboard)/admin/loans/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, DollarSign } from 'lucide-react';
import Swal from 'sweetalert2';

export default function AdminLoansPage() {
  const [loans, setLoans] = useState([]);

  const fetchLoans = async () => {
    const res = await fetch('/api/admin/loans');
    if (res.ok) setLoans(await res.json());
  };

  useEffect(() => { fetchLoans(); }, []);

  const handleDecision = async (loanId: number, action: 'approve' | 'reject') => {
    const result = await Swal.fire({
        title: `${action.toUpperCase()} Loan?`,
        text: action === 'approve' ? "Funds will be credited instantly." : "This will reject the application.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: `Yes, ${action}`
    });

    if (result.isConfirmed) {
        await fetch('/api/admin/loans', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ loanId, action })
        });
        Swal.fire('Updated', `Loan has been ${action}d.`, 'success');
        fetchLoans();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Loan Requests</h2>

      <div className="grid grid-cols-1 gap-4">
        {loans.map((loan: any) => (
            <Card key={loan.id} className="flex flex-col md:flex-row justify-between gap-4 border-l-4 border-l-blue-500">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-lg dark:text-white">{loan.name}</span>
                        <span className="text-xs bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-slate-600 dark:text-slate-300">Acc: {loan.account_number}</span>
                    </div>
                    <p className="text-sm text-slate-500 mb-2">Requesting <span className="font-bold text-slate-900 dark:text-white">${Number(loan.amount).toLocaleString()}</span> for {loan.purpose}</p>
                    <div className="flex gap-4 text-xs text-slate-400">
                        <span>Duration: {loan.duration_months} Months</span>
                        <span>EMI: ${Number(loan.monthly_emi).toLocaleString()}</span>
                        <span>Rate: {loan.interest_rate}%</span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {loan.status === 'pending' ? (
                        <>
                            <Button variant="danger" onClick={() => handleDecision(loan.id, 'reject')}><X size={16} className="mr-2"/> Reject</Button>
                            <Button onClick={() => handleDecision(loan.id, 'approve')}><Check size={16} className="mr-2"/> Approve</Button>
                        </>
                    ) : (
                        <span className={`px-4 py-2 rounded-lg font-bold text-sm uppercase ${
                            loan.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                            {loan.status}
                        </span>
                    )}
                </div>
            </Card>
        ))}
        {loans.length === 0 && <p className="text-slate-500 text-center py-8">No loan requests found.</p>}
      </div>
    </div>
  );
}
""",

    # --- 5. UPDATE SIDEBAR ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck, BarChart3, Banknote } from 'lucide-react';
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
    { name: 'Loan Requests', href: '/admin/loans', icon: Banknote, requiredPerm: 'LoansManage' }, // NEW
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
    { name: 'Loans', href: '/customer/loans', icon: Banknote }, // NEW
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

def loan_system():
    print("💰 Installing Loan Management System...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Loan System Ready! Customers can apply, Admins can approve.")

if __name__ == "__main__":
    loan_system()
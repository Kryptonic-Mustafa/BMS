import os

files = {
    # --- 1. SETUP DATABASE ---
    "sql_beneficiaries.sql": """
USE bank_app;

CREATE TABLE IF NOT EXISTS beneficiaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL, -- Who owns this contact
    saved_name VARCHAR(100), -- Nickname (e.g. "Dad", "Office")
    account_number VARCHAR(20) NOT NULL, -- The target account
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
""",

    # --- 2. BENEFICIARY API ---
    "app/api/customer/beneficiaries/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);
  
  // Fetch saved contacts
  const list = await query('SELECT * FROM beneficiaries WHERE user_id = ? ORDER BY saved_name ASC', [session.id]);
  return NextResponse.json(list);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { name, accountNumber } = await request.json();

  // 1. Validate Account Exists
  const target: any = await query('SELECT id FROM accounts WHERE account_number = ?', [accountNumber]);
  if (target.length === 0) return NextResponse.json({ error: 'Invalid Account Number' }, { status: 404 });

  // 2. Prevent Duplicate
  const check: any = await query('SELECT id FROM beneficiaries WHERE user_id = ? AND account_number = ?', [session.id, accountNumber]);
  if (check.length > 0) return NextResponse.json({ error: 'Contact already saved' }, { status: 400 });

  // 3. Save
  await query('INSERT INTO beneficiaries (user_id, saved_name, account_number) VALUES (?, ?, ?)', [session.id, name, accountNumber]);
  
  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const session = await getSession();
  const { id } = await request.json();
  await query('DELETE FROM beneficiaries WHERE id = ? AND user_id = ?', [id, session.id]);
  return NextResponse.json({ success: true });
}
""",

    # --- 3. CONTACTS PAGE UI ---
    "app/(dashboard)/customer/beneficiaries/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UserPlus, Trash2, Users, Search } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [form, setForm] = useState({ name: '', accountNumber: '' });

  const fetchContacts = async () => {
    const res = await fetch('/api/customer/beneficiaries');
    if (res.ok) setContacts(await res.json());
  };

  useEffect(() => { fetchContacts(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/customer/beneficiaries', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(form)
    });
    const data = await res.json();
    
    if (res.ok) {
        Swal.fire('Saved', 'Beneficiary added successfully', 'success');
        setForm({ name: '', accountNumber: '' });
        fetchContacts();
    } else {
        Swal.fire('Error', data.error, 'error');
    }
  };

  const handleDelete = async (id: number) => {
    const res = await Swal.fire({ title: 'Delete Contact?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Yes, delete', confirmButtonColor: '#d33' });
    if (res.isConfirmed) {
        await fetch('/api/customer/beneficiaries', { method: 'DELETE', body: JSON.stringify({ id }) });
        fetchContacts();
        Swal.fire('Deleted', 'Contact removed.', 'success');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
        <Users className="text-blue-600"/> My Beneficiaries
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* ADD FORM */}
        <Card className="md:col-span-1 h-fit">
            <h3 className="font-bold mb-4 flex items-center gap-2"><UserPlus size={18}/> Add New</h3>
            <form onSubmit={handleAdd} className="space-y-4">
                <Input label="Nick Name" placeholder="e.g. Dad, Office" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
                <Input label="Account Number" placeholder="e.g. ACC..." value={form.accountNumber} onChange={e => setForm({...form, accountNumber: e.target.value})} required />
                <Button type="submit" className="w-full">Save Contact</Button>
            </form>
        </Card>

        {/* LIST */}
        <Card className="md:col-span-2">
            <h3 className="font-bold mb-4 flex items-center gap-2"><Search size={18}/> Saved Contacts</h3>
            <div className="space-y-3">
                {contacts.map((c: any) => (
                    <div key={c.id} className="flex justify-between items-center p-3 border border-slate-100 dark:border-slate-800 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold">
                                {c.saved_name.substring(0, 1).toUpperCase()}
                            </div>
                            <div>
                                <p className="font-bold text-slate-800 dark:text-white">{c.saved_name}</p>
                                <p className="text-xs text-slate-500 font-mono">{c.account_number}</p>
                            </div>
                        </div>
                        <button onClick={() => handleDelete(c.id)} className="text-slate-400 hover:text-red-500 p-2"><Trash2 size={18}/></button>
                    </div>
                ))}
                {contacts.length === 0 && <p className="text-slate-400 text-center py-8">No contacts saved yet.</p>}
            </div>
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 4. UPGRADE TRANSFER PAGE (Add Dropdown) ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard } from 'lucide-react';
import Swal from 'sweetalert2';

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [useContact, setUseContact] = useState(false); // Toggle between Manual/Contact
  const [form, setForm] = useState({ accountNumber: '', amount: '', pin: '' });

  useEffect(() => {
    // Load contacts for dropdown
    fetch('/api/customer/beneficiaries').then(res => res.json()).then(setContacts);
  }, []);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const res = await fetch('/api/customer/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });

    const data = await res.json();
    if (res.ok) {
      Swal.fire({ title: 'Success!', text: 'Transfer completed.', icon: 'success' });
      setForm({ accountNumber: '', amount: '', pin: '' });
    } else {
      Swal.fire({ title: 'Error', text: data.error, icon: 'error' });
    }
    setLoading(false);
  };

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Money Transfer</h2>
      
      <Card>
        <div className="flex justify-end mb-4">
            <button 
                onClick={() => setUseContact(!useContact)}
                className="text-sm flex items-center gap-2 text-blue-600 font-medium hover:underline"
            >
                {useContact ? <><Keyboard size={16}/> Type Manually</> : <><Users size={16}/> Select Beneficiary</>}
            </button>
        </div>

        <form onSubmit={handleTransfer} className="space-y-6">
          {useContact ? (
              <div>
                  <label className="block text-sm font-medium mb-2 dark:text-slate-300">Select Beneficiary</label>
                  <select 
                      className="w-full p-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
                      onChange={e => setForm({...form, accountNumber: e.target.value})}
                      value={form.accountNumber}
                  >
                      <option value="">-- Select Contact --</option>
                      {contacts.map((c: any) => (
                          <option key={c.id} value={c.account_number}>
                              {c.saved_name} ({c.account_number})
                          </option>
                      ))}
                  </select>
              </div>
          ) : (
              <Input
                label="Recipient Account Number"
                placeholder="ACC..."
                value={form.accountNumber}
                onChange={(e) => setForm({ ...form, accountNumber: e.target.value })}
                required
              />
          )}

          <Input
            label="Amount ($)"
            type="number"
            placeholder="0.00"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            required
          />

          <Input
            label="Security PIN"
            type="password"
            placeholder="****"
            maxLength={4}
            value={form.pin}
            onChange={(e) => setForm({ ...form, pin: e.target.value })}
            required
          />

          <Button type="submit" className="w-full flex items-center justify-center" disabled={loading}>
            {loading ? 'Processing...' : <><span className="mr-2">Transfer Now</span> <ArrowRight size={18} /></>}
          </Button>
        </form>
      </Card>
    </div>
  );
}
""",

    # --- 5. UPDATE SIDEBAR (Add Beneficiaries Link) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck, BarChart3, Banknote, Contact } from 'lucide-react';
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
    { name: 'Loan Requests', href: '/admin/loans', icon: Banknote, requiredPerm: 'LoansManage' },
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
    { name: 'Beneficiaries', href: '/customer/beneficiaries', icon: Contact }, // NEW LINK
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

def install_beneficiaries():
    print("👥 Installing Beneficiary Management System...")
    
    # Write SQL first so user sees it
    with open("sql_beneficiaries.sql", "w") as f:
        f.write(files["sql_beneficiaries.sql"])
        
    for path, content in files.items():
        if path.endswith(".sql"): continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n👉 ACTION REQUIRED: Run 'sql_beneficiaries.sql' in MySQL Workbench first!")

if __name__ == "__main__":
    install_beneficiaries()
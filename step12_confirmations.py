import os

files = {
    # --- 1. ADMIN DEPOSIT (Input Modal -> Confirmation Alert -> API) ---
    "app/(dashboard)/admin/customers/DepositButton.tsx": """
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import Swal from 'sweetalert2';

export default function DepositButton({ accountId }: { accountId: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Validation
    if (!amount || parseFloat(amount) <= 0) {
      Swal.fire('Invalid Amount', 'Please enter a valid amount', 'warning');
      return;
    }

    // 2. SweetAlert Confirmation
    const result = await Swal.fire({
      title: 'Confirm Deposit?',
      text: `Are you sure you want to add $${amount} to this user's account?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#1E3A8A', // Blue 900
      cancelButtonColor: '#64748B', // Slate 500
      confirmButtonText: 'Yes, Deposit it!'
    });

    if (!result.isConfirmed) return;

    // 3. API Call
    setLoading(true);
    try {
      const res = await fetch('/api/admin/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId, amount: parseFloat(amount) }),
      });
      
      if (res.ok) {
        setIsOpen(false);
        setAmount('');
        Swal.fire({
          toast: true, 
          position: 'top-end', 
          icon: 'success', 
          title: 'Deposit Successful', 
          timer: 3000, 
          showConfirmButton: false
        });
        router.refresh(); 
      } else {
        Swal.fire('Error', 'Deposit failed', 'error');
      }
    } catch (e) {
      Swal.fire('Error', 'Network error', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setIsOpen(true)}>
        + Deposit
      </Button>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Add Funds">
        <form onSubmit={handleDeposit} className="space-y-4">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Enter the amount to deposit. An admin log will be created.
          </p>
          <Input 
            label="Amount ($)" 
            type="number" 
            min="1" 
            placeholder="1000.00" 
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="ghost" onClick={() => setIsOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Confirm Deposit'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
""",

    # --- 2. CUSTOMER TRANSFER (Form -> Confirmation Alert -> API) ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import Swal from 'sweetalert2';

export default function TransferPage() {
  const router = useRouter();
  const [form, setForm] = useState({ account: '', amount: '', desc: '' });
  const [loading, setLoading] = useState(false);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Validation
    if (!form.account || !form.amount) {
       Swal.fire('Missing Details', 'Please fill in all fields', 'warning');
       return;
    }

    // 2. SweetAlert Confirmation
    const result = await Swal.fire({
      title: 'Confirm Transfer',
      html: `
        <div class="text-left text-sm">
          <p><strong>To Account:</strong> ${form.account}</p>
          <p><strong>Amount:</strong> $${form.amount}</p>
          <p class="text-xs text-slate-500 mt-2">This action cannot be undone.</p>
        </div>
      `,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#1E3A8A',
      cancelButtonColor: '#64748B',
      confirmButtonText: 'Yes, Send Money'
    });

    if (!result.isConfirmed) return;

    // 3. API Call
    setLoading(true);
    try {
      const res = await fetch('/api/customer/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          receiverAccount: form.account,
          amount: form.amount,
          description: form.desc
        }),
      });

      const data = await res.json();

      if (res.ok) {
        await Swal.fire({
            title: 'Transfer Successful!',
            text: `$${form.amount} sent successfully.`,
            icon: 'success',
            confirmButtonColor: '#1E3A8A'
        });
        
        setForm({ account: '', amount: '', desc: '' });
        router.push('/customer'); 
        router.refresh();
      } else {
        Swal.fire({
            title: 'Transfer Failed',
            text: data.error || 'Something went wrong',
            icon: 'error',
            confirmButtonColor: '#EF4444'
        });
      }
    } catch (err) {
      Swal.fire('Error', 'Network error occurred', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-6">Transfer Money</h2>
      <Card>
        <form onSubmit={handleTransfer} className="space-y-6">
          <Input 
            label="Receiver Account Number" 
            placeholder="ACC..."
            value={form.account}
            onChange={(e) => setForm({...form, account: e.target.value})}
            required
          />
          <Input 
            label="Amount ($)" 
            type="number"
            min="1"
            placeholder="0.00"
            value={form.amount}
            onChange={(e) => setForm({...form, amount: e.target.value})}
            required
          />
          <Input 
            label="Description (Optional)" 
            placeholder="Rent, Dinner, etc."
            value={form.desc}
            onChange={(e) => setForm({...form, desc: e.target.value})}
          />
          <Button type="submit" className="w-full h-12 text-lg" disabled={loading}>
            {loading ? 'Processing...' : 'Send Money'}
          </Button>
        </form>
      </Card>
    </div>
  );
}
""",

    # --- 3. SIDEBAR (Add Logout Confirmation) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle },
  { name: 'BankMail', href: '/messages', icon: Mail },
];

const customerLinks = [
  { name: 'Overview', href: '/customer', icon: LayoutDashboard },
  { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
  { name: 'History', href: '/customer/history', icon: ShieldCheck },
  { name: 'BankMail', href: '/messages', icon: Mail },
  { name: 'Support', href: '/customer/support', icon: HelpCircle },
];

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const links = userRole === 'admin' ? adminLinks : customerLinks;

  const handleLogout = async () => {
    const result = await Swal.fire({
      title: 'Sign Out?',
      text: "You will be returned to the login screen.",
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#EF4444',
      cancelButtonColor: '#64748B',
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
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
          <span className="font-bold text-lg text-white">B</span>
        </div>
        <span className="font-bold text-xl tracking-tight text-slate-100">BankSystem</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          {userRole === 'admin' ? 'Admin Menu' : 'Customer Menu'}
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
        <button 
          onClick={handleLogout}
          className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
        >
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
"""
}

def add_confirmations():
    print("🔒 Adding Secure Confirmations to Major Actions...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ System Secured! Restart server to test.")

if __name__ == "__main__":
    add_confirmations()
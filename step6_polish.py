import os

files = {
    # --- 1. NOTIFICATION API (Fetch & Mark Read) ---
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
    [session.id]
  );
  
  return NextResponse.json(notifications);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  return NextResponse.json({ success: true });
}
""",

    # --- 2. UPDATE DEPOSIT API (To Send Notification) ---
    "app/api/admin/deposit/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session || session.role !== 'admin') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    const { accountId, amount } = await request.json();

    // 1. Add Money
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, accountId]);

    // 2. Get User ID for Notification
    const accounts: any = await query('SELECT user_id FROM accounts WHERE id = ?', [accountId]);
    const userId = accounts[0].user_id;

    // 3. Log Transaction
    await query(
      'INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)',
      [accountId, 'deposit', amount, 'Admin Deposit', 'completed']
    );

    // 4. Send Notification
    await query(
      'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
      [userId, `You received a deposit of $${amount} from Admin`, 'success']
    );

    return NextResponse.json({ message: 'Deposit successful' });
  } catch (error) {
    return NextResponse.json({ error: 'Deposit failed' }, { status: 500 });
  }
}
""",

    # --- 3. UPDATE TRANSFER API (To Send Notification) ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query, pool } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function POST(request: Request) {
  const connection = await pool.getConnection();
  
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, receiverAccount, description } = await request.json();
    const transferAmount = parseFloat(amount);

    await connection.beginTransaction();

    // ... (Validation Logic same as before) ...
    const [senders]: any = await connection.execute('SELECT id, balance FROM accounts WHERE user_id = ? FOR UPDATE', [session.id]);
    const sender = senders[0];

    if (!sender || sender.balance < transferAmount) {
        await connection.rollback();
        return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    const [receivers]: any = await connection.execute('SELECT id, user_id FROM accounts WHERE account_number = ?', [receiverAccount]);
    const receiver = receivers[0];

    if (!receiver) {
        await connection.rollback();
        return NextResponse.json({ error: 'Receiver not found' }, { status: 404 });
    }

    // Update Balances
    await connection.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', [transferAmount, sender.id]);
    await connection.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', [transferAmount, receiver.id]);

    // Log Transactions
    await connection.execute('INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)', [sender.id, 'transfer', transferAmount, `Sent to ${receiverAccount}`, 'completed']);
    await connection.execute('INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)', [receiver.id, 'deposit', transferAmount, `Received from ${session.name}`, 'completed']);

    // --- NEW: Insert Notifications ---
    // 1. Notify Receiver
    await connection.execute(
        'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
        [receiver.user_id, `You received $${transferAmount} from ${session.name}`, 'success']
    );

    await connection.commit();
    return NextResponse.json({ message: 'Transfer successful' });

  } catch (error) {
    await connection.rollback();
    return NextResponse.json({ error: 'Transfer failed' }, { status: 500 });
  } finally {
    connection.release();
  }
}
""",

    # --- 4. GLOBAL LISTENER (Pop-up Toasts) ---
    "components/layout/NotificationListener.tsx": """
'use client';
import { useEffect } from 'react';
import Swal from 'sweetalert2';

export function NotificationListener() {
  useEffect(() => {
    const checkNotifications = async () => {
      try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        // Filter for unread
        const unread = data.filter((n: any) => !n.is_read);

        if (unread.length > 0) {
          // Show Toast for the latest one
          const latest = unread[0];
          
          const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 4000,
            timerProgressBar: true,
          });

          Toast.fire({
            icon: latest.type,
            title: latest.message
          });

          // Mark as read immediately to avoid looping
          await fetch('/api/notifications', { method: 'PUT' });
        }
      } catch (error) {
        console.error('Notification poll error', error);
      }
    };

    // Poll every 5 seconds
    const interval = setInterval(checkNotifications, 5000);
    return () => clearInterval(interval);
  }, []);

  return null; // This component renders nothing visually
}
""",

    # --- 5. UPDATED NAVBAR (With Real Bell) ---
    "components/layout/Navbar.tsx": """
'use client';
import { Bell, Search } from 'lucide-react';
import { useState, useEffect } from 'react';

interface NavbarProps {
  user: { name: string; role: string; };
}

export function Navbar({ user }: NavbarProps) {
  const [hasUnread, setHasUnread] = useState(false);
  const initials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2);

  // Simple poll to check for red dot status
  useEffect(() => {
    const check = async () => {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        setHasUnread(data.some((n: any) => !n.is_read));
    };
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-10 shadow-sm">
      <div className="flex items-center w-96">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input type="text" placeholder="Search..." className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-900/10 focus:border-blue-900 transition-all" />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell size={20} />
          {hasUnread && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border border-white animate-pulse"></span>
          )}
        </button>
        
        <div className="h-8 w-[1px] bg-slate-200"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-slate-800">{user.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user.role}</p>
          </div>
          <div className="w-10 h-10 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold border border-blue-200">
            {initials}
          </div>
        </div>
      </div>
    </header>
  );
}
""",

    # --- 6. ADD LISTENER TO LAYOUT ---
    "app/(dashboard)/layout.tsx": """
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';
import { NotificationListener } from '@/components/layout/NotificationListener';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar userRole={session.role} /> 
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar user={{ name: session.name, role: session.role }} />
        <NotificationListener /> 
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
""",

    # --- 7. FIX CUSTOMER DASHBOARD (Text White) ---
    "app/(dashboard)/customer/page.tsx": """
import { getSession } from '@/lib/auth';
import { query } from '@/lib/db';
import Link from 'next/link';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

async function getAccountData(userId: number) {
  const accounts: any = await query('SELECT * FROM accounts WHERE user_id = ?', [userId]);
  const transactions: any = await query(
    'SELECT * FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.user_id = ? ORDER BY t.created_at DESC LIMIT 5', 
    [userId]
  );
  return { account: accounts[0], transactions };
}

export default async function CustomerDashboard() {
  const session = await getSession();
  const { account, transactions } = await getAccountData(session.id);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-slate-800 mb-4">Overview</h2>
        {/* Added text-white to ensure visibility */}
        <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-8 rounded-2xl text-white shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 w-64 h-64 bg-white/5 rounded-full -mr-16 -mt-16 blur-3xl"></div>
          
          <div className="relative z-10">
            <p className="text-blue-100 mb-2 font-medium">Available Balance</p>
            <h3 className="text-5xl font-bold mb-6 text-white">
              ${Number(account?.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </h3>
            
            <div className="flex gap-4">
              <Link href="/customer/transfer" className="bg-white text-blue-900 px-6 py-2.5 rounded-lg font-bold shadow hover:bg-slate-100 transition flex items-center">
                <ArrowUpRight size={18} className="mr-2" /> Transfer
              </Link>
              <Link href="/customer/history" className="bg-blue-700/50 text-white px-6 py-2.5 rounded-lg font-semibold border border-blue-500/30 hover:bg-blue-700/70 transition flex items-center">
                View History
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-slate-800 mb-4">Recent Activity</h3>
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 divide-y divide-slate-100">
          {transactions.map((tx: any) => (
            <div key={tx.id} className="p-4 flex justify-between items-center hover:bg-slate-50 transition">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  tx.type === 'deposit' ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-600'
                }`}>
                  {tx.type === 'deposit' ? <ArrowDownLeft size={20} /> : <ArrowUpRight size={20} />}
                </div>
                <div>
                  <p className="font-medium text-slate-900">{tx.description || 'Transaction'}</p>
                  <p className="text-xs text-slate-500">{new Date(tx.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              <span className={`font-bold ${
                tx.type === 'deposit' ? 'text-green-600' : 'text-slate-900'
              }`}>
                {tx.type === 'deposit' ? '+' : '-'}${Number(tx.amount).toLocaleString()}
              </span>
            </div>
          ))}
          {transactions.length === 0 && (
            <div className="p-8 text-center text-slate-500">No recent transactions.</div>
          )}
        </div>
      </div>
    </div>
  );
}
""",

    # --- 8. UPDATE DEPOSIT BUTTON (SweetAlert) ---
    "app/(dashboard)/admin/customers/DepositButton.tsx": """
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';

export default function DepositButton({ accountId }: { accountId: number }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleDeposit = async () => {
    // SweetAlert Confirmation
    const result = await Swal.fire({
      title: 'Confirm Deposit',
      text: "Add $1,000 to this customer's account?",
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#1E3A8A',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, deposit it!'
    });

    if (!result.isConfirmed) return;
    
    setLoading(true);
    try {
      const res = await fetch('/api/admin/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId, amount: 1000 }),
      });
      
      if (res.ok) {
        Swal.fire({
            title: 'Success!',
            text: '$1,000 has been deposited.',
            icon: 'success',
            timer: 2000
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
    <Button size="sm" variant="secondary" onClick={handleDeposit} disabled={loading}>
      {loading ? '...' : '+ $1k'}
    </Button>
  );
}
""",

    # --- 9. UPDATE TRANSFER PAGE (SweetAlert) ---
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

    // 1. SweetAlert Confirmation
    const result = await Swal.fire({
      title: 'Confirm Transfer',
      text: `Send $${form.amount} to account ${form.account}?`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#1E3A8A',
      cancelButtonColor: '#64748B',
      confirmButtonText: 'Yes, send money'
    });

    if (!result.isConfirmed) return;

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
        // 2. SweetAlert Success
        await Swal.fire({
            title: 'Transfer Successful!',
            text: `$${form.amount} sent successfully.`,
            icon: 'success',
            confirmButtonColor: '#1E3A8A'
        });
        
        setForm({ account: '', amount: '', desc: '' });
        router.push('/customer'); // Redirect to dashboard
        router.refresh();
      } else {
        // 3. SweetAlert Error
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
      <h2 className="text-2xl font-bold text-slate-800 mb-6">Transfer Money</h2>
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
"""
}

def polish_project():
    print("✨ Polishing UI & Adding Notifications...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🎉 Done! Restart server with 'npm run dev' to see the changes.")

if __name__ == "__main__":
    polish_project()
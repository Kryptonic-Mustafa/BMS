import os

files = {
    # --- 1. BACKEND: SECURE TRANSFER API ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query, pool } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function POST(request: Request) {
  const connection = await pool.getConnection();
  
  try {
    // 1. Authenticate
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, receiverAccount, description } = await request.json();
    const transferAmount = parseFloat(amount);

    if (!receiverAccount || transferAmount <= 0) {
      return NextResponse.json({ error: 'Invalid details' }, { status: 400 });
    }

    // 2. Start Database Transaction
    await connection.beginTransaction();

    // 3. Get Sender Info (Lock row for update)
    const [senders]: any = await connection.execute(
      'SELECT id, balance FROM accounts WHERE user_id = ? FOR UPDATE', 
      [session.id]
    );
    
    const sender = senders[0];
    if (!sender || sender.balance < transferAmount) {
      await connection.rollback();
      return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    // 4. Get Receiver Info
    const [receivers]: any = await connection.execute(
      'SELECT id FROM accounts WHERE account_number = ?', 
      [receiverAccount]
    );
    
    const receiver = receivers[0];
    if (!receiver) {
      await connection.rollback();
      return NextResponse.json({ error: 'Receiver account not found' }, { status: 404 });
    }

    if (sender.id === receiver.id) {
        await connection.rollback();
        return NextResponse.json({ error: 'Cannot send to yourself' }, { status: 400 });
    }

    // 5. Perform Transfer
    // Deduct from sender
    await connection.execute(
      'UPDATE accounts SET balance = balance - ? WHERE id = ?',
      [transferAmount, sender.id]
    );

    // Add to receiver
    await connection.execute(
      'UPDATE accounts SET balance = balance + ? WHERE id = ?',
      [transferAmount, receiver.id]
    );

    // 6. Log Transactions
    // Sender Log
    await connection.execute(
      'INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)',
      [sender.id, 'transfer', transferAmount, `Sent to ${receiverAccount}`, 'completed']
    );

    // Receiver Log
    await connection.execute(
      'INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)',
      [receiver.id, 'deposit', transferAmount, `Received from ${session.name}`, 'completed']
    );

    // 7. Commit Transaction
    await connection.commit();
    
    return NextResponse.json({ message: 'Transfer successful' });

  } catch (error) {
    await connection.rollback();
    console.error(error);
    return NextResponse.json({ error: 'Transfer failed' }, { status: 500 });
  } finally {
    connection.release();
  }
}
""",

    # --- 2. FRONTEND: TRANSFER PAGE ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

export default function TransferPage() {
  const router = useRouter();
  const [form, setForm] = useState({ account: '', amount: '', desc: '' });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: '', msg: '' });

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus({ type: '', msg: '' });

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
        setStatus({ type: 'success', msg: 'Transfer Successful!' });
        setForm({ account: '', amount: '', desc: '' });
        router.refresh();
      } else {
        setStatus({ type: 'error', msg: data.error || 'Transfer failed' });
      }
    } catch (err) {
      setStatus({ type: 'error', msg: 'An error occurred' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-6">Transfer Money</h2>
      
      <Card>
        {status.msg && (
          <div className={`p-4 mb-4 rounded-lg text-sm ${
            status.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {status.msg}
          </div>
        )}

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

    # --- 3. FRONTEND: TRANSACTION HISTORY ---
    "app/(dashboard)/customer/history/page.tsx": """
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';

async function getHistory(userId: number) {
  return await query(`
    SELECT t.* FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.user_id = ?
    ORDER BY t.created_at DESC
  `, [userId]);
}

export default async function HistoryPage() {
  const session = await getSession();
  const transactions: any = await getHistory(session.id);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Transaction History</h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Description</TableHeader>
            <TableHeader>Type</TableHeader>
            <TableHeader>Amount</TableHeader>
            <TableHeader>Date</TableHeader>
            <TableHeader>Status</TableHeader>
          </TableHead>
          <tbody>
            {transactions.map((tx: any) => (
              <TableRow key={tx.id}>
                <TableCell className="font-medium text-slate-900">
                  {tx.description || 'No description'}
                </TableCell>
                <TableCell>
                  <span className="capitalize">{tx.type}</span>
                </TableCell>
                <TableCell className={`font-bold ${
                    tx.type === 'deposit' ? 'text-green-600' : 'text-slate-800'
                }`}>
                  {tx.type === 'deposit' ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                </TableCell>
                <TableCell className="text-slate-500">
                  {new Date(tx.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  <Badge variant={tx.status === 'completed' ? 'success' : 'neutral'}>
                    {tx.status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-slate-500">No transactions found.</td>
              </tr>
            )}
          </tbody>
        </Table>
      </div>
    </div>
  );
}
""",

    # --- 4. UPDATE DASHBOARD HOME (With Recent Transactions) ---
    "app/(dashboard)/customer/page.tsx": """
import { getSession } from '@/lib/auth';
import { query } from '@/lib/db';
import Link from 'next/link';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

async function getAccountData(userId: number) {
  const accounts: any = await query('SELECT * FROM accounts WHERE user_id = ?', [userId]);
  const transactions: any = await query(`
    SELECT * FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.user_id = ?
    ORDER BY t.created_at DESC LIMIT 5
  `, [userId]);
  
  return { account: accounts[0], transactions };
}

export default async function CustomerDashboard() {
  const session = await getSession();
  const { account, transactions } = await getAccountData(session.id);

  return (
    <div className="space-y-8">
      {/* Welcome & Balance */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800 mb-4">Overview</h2>
        <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-8 rounded-2xl text-white shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 w-64 h-64 bg-white/5 rounded-full -mr-16 -mt-16 blur-3xl"></div>
          
          <div className="relative z-10">
            <p className="opacity-80 mb-2 font-medium">Available Balance</p>
            <h3 className="text-5xl font-bold mb-6">
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

      {/* Recent Activity */}
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
"""
}

def create_customer_features():
    print("💳 Building Customer Transfer System...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n🎉 Project Core Complete! You can now Transfer Money.")

if __name__ == "__main__":
    create_customer_features()
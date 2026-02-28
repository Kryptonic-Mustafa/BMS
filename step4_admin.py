import os

files = {
    # --- 1. REUSABLE TABLE COMPONENT (For clean lists) ---
    "components/ui/Table.tsx": """
import React from 'react';

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-slate-200 shadow-sm">
      <table className="w-full text-sm text-left text-slate-600">
        {children}
      </table>
    </div>
  );
}

export function TableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-50 text-xs uppercase text-slate-500 font-semibold">
      <tr>{children}</tr>
    </thead>
  );
}

export function TableRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <tr className={`border-b border-slate-100 hover:bg-slate-50/50 transition-colors ${className}`}>{children}</tr>;
}

export function TableHeader({ children }: { children: React.ReactNode }) {
  return <th className="px-6 py-4 font-medium">{children}</th>;
}

export function TableCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-6 py-4 ${className}`}>{children}</td>;
}
""",

    # --- 2. ADMIN API: DEPOSIT MONEY (The "God Mode" tool) ---
    "app/api/admin/deposit/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    // 1. Verify Admin
    const session = await getSession();
    if (!session || session.role !== 'admin') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    const { accountId, amount } = await request.json();

    if (!accountId || !amount || amount <= 0) {
      return NextResponse.json({ error: 'Invalid data' }, { status: 400 });
    }

    // 2. Add Money
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, accountId]);

    // 3. Log Transaction
    await query(
      'INSERT INTO transactions (account_id, type, amount, description, status) VALUES (?, ?, ?, ?, ?)',
      [accountId, 'deposit', amount, 'Admin Deposit', 'completed']
    );

    return NextResponse.json({ message: 'Deposit successful' });
  } catch (error) {
    return NextResponse.json({ error: 'Deposit failed' }, { status: 500 });
  }
}
""",

    # --- 3. ADMIN DASHBOARD OVERVIEW ---
    "app/(dashboard)/admin/page.tsx": """
import { query } from '@/lib/db';
import { Card } from '@/components/ui/Card';
import { Users, DollarSign, Activity } from 'lucide-react';

async function getStats() {
  const users: any = await query('SELECT COUNT(*) as count FROM users WHERE role = "customer"');
  const balance: any = await query('SELECT SUM(balance) as total FROM accounts');
  const transactions: any = await query('SELECT COUNT(*) as count FROM transactions');
  
  return {
    totalUsers: users[0].count,
    totalMoney: balance[0].total || 0,
    totalTx: transactions[0].count
  };
}

export default async function AdminDashboard() {
  const stats = await getStats();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">System Overview</h2>
      
      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex items-center p-6 space-x-4 border-l-4 border-l-blue-900">
          <div className="p-3 bg-blue-100 text-blue-900 rounded-full">
            <Users size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Total Customers</p>
            <h3 className="text-2xl font-bold text-slate-800">{stats.totalUsers}</h3>
          </div>
        </Card>

        <Card className="flex items-center p-6 space-x-4 border-l-4 border-l-teal-600">
          <div className="p-3 bg-teal-100 text-teal-600 rounded-full">
            <DollarSign size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Total Holdings</p>
            <h3 className="text-2xl font-bold text-slate-800">
              ${Number(stats.totalMoney).toLocaleString()}
            </h3>
          </div>
        </Card>

        <Card className="flex items-center p-6 space-x-4 border-l-4 border-l-purple-600">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-full">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-slate-500 text-sm font-medium">Total Transactions</p>
            <h3 className="text-2xl font-bold text-slate-800">{stats.totalTx}</h3>
          </div>
        </Card>
      </div>
      
      <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg text-blue-800 text-sm">
        <strong>💡 Tip:</strong> Go to the "Customers" tab to deposit money into user accounts for testing.
      </div>
    </div>
  );
}
""",

    # --- 4. CUSTOMER MANAGEMENT LIST ---
    "app/(dashboard)/admin/customers/page.tsx": """
import { query } from '@/lib/db';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import DepositButton from './DepositButton'; 

// Fetch users and their account info
async function getCustomers() {
  return await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
    ORDER BY u.created_at DESC
  `);
}

export default async function CustomersPage() {
  const customers: any = await getCustomers();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">Customer Management</h2>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Customer</TableHeader>
            <TableHeader>Account No</TableHeader>
            <TableHeader>Balance</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableHead>
          <tbody>
            {customers.map((user: any) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="font-medium text-slate-900">{user.name}</div>
                  <div className="text-xs text-slate-500">{user.email}</div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded">
                    {user.account_number}
                  </span>
                </TableCell>
                <TableCell className="font-bold text-slate-700">
                  ${Number(user.balance).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge variant="success">Active</Badge>
                </TableCell>
                <TableCell>
                   {/* Client Component for Interactivity */}
                   <DepositButton accountId={user.account_id} />
                </TableCell>
              </TableRow>
            ))}
            {customers.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-500">No customers found.</td>
              </tr>
            )}
          </tbody>
        </Table>
      </div>
    </div>
  );
}
""",

    # --- 5. DEPOSIT BUTTON (Client Component) ---
    "app/(dashboard)/admin/customers/DepositButton.tsx": """
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';

export default function DepositButton({ accountId }: { accountId: number }) {
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleDeposit = async () => {
    if (!confirm('Deposit $1,000 to this account?')) return;
    
    setLoading(true);
    try {
      const res = await fetch('/api/admin/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId, amount: 1000 }),
      });
      
      if (res.ok) {
        alert('Deposit Successful!');
        router.refresh(); // Refresh data
      } else {
        alert('Deposit Failed');
      }
    } catch (e) {
      alert('Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button size="sm" variant="secondary" onClick={handleDeposit} disabled={loading}>
      {loading ? 'Adding...' : '+ $1k'}
    </Button>
  );
}
""",

    # --- 6. TRANSACTION LOGS ---
    "app/(dashboard)/admin/transactions/page.tsx": """
import { query } from '@/lib/db';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';

async function getTransactions() {
  return await query(`
    SELECT t.*, u.name as user_name, a.account_number 
    FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    JOIN users u ON a.user_id = u.id
    ORDER BY t.created_at DESC
    LIMIT 50
  `);
}

export default async function AdminTransactions() {
  const transactions: any = await getTransactions();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Global Transactions</h2>
      
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>User</TableHeader>
            <TableHeader>Type</TableHeader>
            <TableHeader>Amount</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Date</TableHeader>
          </TableHead>
          <tbody>
            {transactions.map((tx: any) => (
              <TableRow key={tx.id}>
                <TableCell>
                  <div className="font-medium">{tx.user_name}</div>
                  <div className="text-xs text-slate-500">{tx.account_number}</div>
                </TableCell>
                <TableCell>
                   <span className="capitalize">{tx.type}</span>
                </TableCell>
                <TableCell className={`font-bold ${
                    tx.type === 'deposit' ? 'text-green-600' : 'text-slate-800'
                }`}>
                  {tx.type === 'deposit' ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Badge variant={tx.status === 'completed' ? 'success' : 'warning'}>
                    {tx.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-slate-500 text-sm">
                  {new Date(tx.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );
}
"""
}

def create_admin_features():
    print("👔 Building Admin Dashboard & Tools...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n🚀 Admin Panel Ready!")

if __name__ == "__main__":
    create_admin_features()
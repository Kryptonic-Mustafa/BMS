import os

files = {
    # --- 1. CREATE THE MISSING TRANSACTION API ---
    "app/api/customer/transactions/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // 1. Get User's Account ID
  const acc: any = await query('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', [session.id]);
  if (acc.length === 0) return NextResponse.json([]); // No account yet

  // 2. Fetch Transactions (Both Credit & Debit)
  // We limit to 20 for history page, or 5 for dashboard
  const transactions = await query(`
    SELECT * FROM transactions 
    WHERE account_id = ? 
    ORDER BY created_at DESC 
    LIMIT 20
  `, [acc[0].id]);

  return NextResponse.json(transactions);
}
""",

    # --- 2. UPDATE DASHBOARD TO USE THE CORRECT API ---
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { ArrowUpRight, ArrowDownLeft, Wallet } from 'lucide-react';
import Link from 'next/link';

export default function CustomerDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
        try {
            // 1. Fetch Profile (for Balance)
            const userRes = await fetch('/api/profile');
            const userData = await userRes.json();
            
            // 2. Fetch Transactions (Using the NEW Valid API)
            const txRes = await fetch('/api/customer/transactions'); 
            const txData = txRes.ok ? await txRes.json() : [];
            
            setData({
                balance: userData.balance || 0,
                recent: Array.isArray(txData) ? txData.slice(0, 5) : []
            });
        } catch (e) {
            console.error("Dashboard Load Failed", e);
        }
    };
    loadData();
  }, []);

  if (!data) return <div className="p-8 text-slate-500">Loading Dashboard...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Overview</h2>

      {/* BALANCE CARD */}
      <div className="bg-blue-800 text-white rounded-2xl p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10">
            <Wallet size={128} />
        </div>
        <div className="relative z-10">
            <p className="text-blue-200 font-medium mb-1">Available Balance</p>
            <h1 className="text-5xl font-bold mb-6">${Number(data.balance).toLocaleString()}</h1>
            
            <div className="flex gap-3">
                <Link href="/customer/transfer">
                    <button className="bg-white text-blue-900 px-6 py-2.5 rounded-lg font-bold hover:bg-blue-50 transition flex items-center gap-2">
                        <ArrowUpRight size={18}/> Transfer
                    </button>
                </Link>
                <Link href="/customer/history">
                    <button className="bg-blue-700 text-white px-6 py-2.5 rounded-lg font-bold hover:bg-blue-600 transition">
                        View History
                    </button>
                </Link>
            </div>
        </div>
      </div>

      {/* RECENT ACTIVITY */}
      <div>
        <h3 className="font-bold text-lg text-slate-800 dark:text-white mb-4">Recent Activity</h3>
        <div className="space-y-4">
            {data.recent.map((tx: any) => {
                const isCredit = tx.type === 'credit';
                return (
                    <Card key={tx.id} className="flex items-center justify-between p-4 hover:shadow-md transition duration-200">
                        <div className="flex items-center gap-4">
                            <div className={`h-12 w-12 rounded-full flex items-center justify-center ${
                                isCredit ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-600'
                            }`}>
                                {isCredit ? <ArrowDownLeft size={24}/> : <ArrowUpRight size={24}/>}
                            </div>
                            <div>
                                <p className="font-bold text-slate-900 dark:text-white text-lg">{tx.description}</p>
                                <p className="text-xs text-slate-500">
                                    {new Date(tx.created_at).toLocaleDateString()} • {new Date(tx.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </p>
                            </div>
                        </div>
                        
                        <div className={`text-xl font-bold ${isCredit ? 'text-green-600' : 'text-slate-900 dark:text-white'}`}>
                            {isCredit ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                        </div>
                    </Card>
                );
            })}
            
            {data.recent.length === 0 && (
                <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
                    <p className="text-slate-500">No recent transactions.</p>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}
""",

    # --- 3. FIX HISTORY PAGE TO ALSO USE THIS API ---
    "app/(dashboard)/customer/history/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { ArrowUpRight, ArrowDownLeft } from 'lucide-react';

export default function HistoryPage() {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetch('/api/customer/transactions').then(res => res.json()).then(setTransactions);
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Transaction History</h2>
      
      <div className="space-y-4">
        {transactions.map((tx: any) => {
             const isCredit = tx.type === 'credit';
             return (
                <Card key={tx.id} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                            isCredit ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-600'
                        }`}>
                            {isCredit ? <ArrowDownLeft size={20}/> : <ArrowUpRight size={20}/>}
                        </div>
                        <div>
                            <p className="font-bold text-slate-900 dark:text-white">{tx.description}</p>
                            <p className="text-xs text-slate-500">{new Date(tx.created_at).toLocaleString()}</p>
                        </div>
                    </div>
                    <div className={`font-bold ${isCredit ? 'text-green-600' : 'text-slate-900 dark:text-white'}`}>
                        {isCredit ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                    </div>
                </Card>
             );
        })}
        {transactions.length === 0 && <p className="text-slate-500 text-center py-8">No transaction history found.</p>}
      </div>
    </div>
  );
}
"""
}

def fix_crash():
    print("🚑 Creating Missing API Endpoints to Fix Dashboard Crash...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created/Updated: {path}")

if __name__ == "__main__":
    fix_crash()
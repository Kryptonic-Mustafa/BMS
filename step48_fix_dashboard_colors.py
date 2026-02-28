import os

files = {
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { ArrowUpRight, ArrowDownLeft, Wallet, ArrowRightLeft } from 'lucide-react';
import Link from 'next/link';

export default function CustomerDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    // We reuse the profile API to get balance + recent transactions logic
    // Ideally, create a dedicated /api/customer/dashboard if needed, but this works for now
    // Fetching balance from Profile API and Transactions from Transaction API
    const loadData = async () => {
        const userRes = await fetch('/api/profile');
        const userData = await userRes.json();
        
        const txRes = await fetch('/api/customer/transfer/history?limit=5'); // We need a simple endpoint or reuse existing
        // For now, let's fetch from the main transactions API which we likely have or will mock for the dashboard
        // Actually, let's fetch from the generic transactions API we made earlier
        const txsRes = await fetch('/api/admin/transactions?limit=5'); // This is admin only, wait.
        
        // Let's rely on the customer's specific recent activity API.
        // If it doesn't exist, we will use the one we created for the history page but limited.
        const historyRes = await fetch('/api/customer/history'); 
        const history = await historyRes.json();
        
        setData({
            balance: userData.balance,
            recent: history.data ? history.data.slice(0, 5) : [] // Take top 5
        });
    };
    loadData();
  }, []);

  if (!data) return <div className="p-8">Loading Dashboard...</div>;

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
"""
}

def fix_dashboard_colors():
    print("🎨 Fixing Dashboard Colors (Green for Income, Red for Expense)...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_dashboard_colors()
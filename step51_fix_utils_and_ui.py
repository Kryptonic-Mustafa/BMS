import os

files = {
    # --- 1. CREATE THE MISSING UTILITY FILE ---
    "lib/utils.ts": """
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
""",

    # --- 2. FIX CREDIT CARD TEXT COLOR (Force White) ---
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { ArrowUpRight, ArrowDownLeft, Send, CreditCard, ShieldCheck, Banknote, MoreHorizontal, Copy } from 'lucide-react';
import Link from 'next/link';
import Swal from 'sweetalert2';

export default function CustomerDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
        try {
            const userRes = await fetch('/api/profile');
            const userData = await userRes.json();
            const txRes = await fetch('/api/customer/transactions'); 
            const txData = txRes.ok ? await txRes.json() : [];
            
            setData({
                user: userData,
                balance: userData.balance || 0,
                accountNumber: userData.account_number || '****',
                recent: Array.isArray(txData) ? txData.slice(0, 5) : []
            });
        } catch (e) { console.error(e); }
    };
    loadData();
  }, []);

  const copyToClipboard = () => {
    if(!data) return;
    navigator.clipboard.writeText(data.accountNumber);
    const Toast = Swal.mixin({ toast: true, position: 'top', showConfirmButton: false, timer: 1500 });
    Toast.fire({ icon: 'success', title: 'Account Number Copied' });
  };

  if (!data) return <div className="p-12 text-center text-slate-400 animate-pulse">Loading secure dashboard...</div>;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      
      {/* 1. WELCOME HEADER */}
      <div className="flex justify-between items-end">
        <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                Hello, {data.user.name.split(' ')[0]} 👋
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Welcome back to your financial hub.</p>
        </div>
        <div className="hidden md:block text-right">
            <p className="text-xs font-mono text-slate-400">SERVER TIME</p>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-300">{new Date().toLocaleTimeString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* 2. PREMIUM CREDIT CARD WIDGET (Fixed: Forced White Text) */}
        <div className="lg:col-span-1">
            <div className="relative h-56 w-full rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 dark:from-blue-900 dark:to-slate-900 shadow-2xl overflow-hidden text-white transition transform hover:scale-[1.02] duration-300">
                {/* Decorative Circles */}
                <div className="absolute top-[-50%] left-[-20%] w-64 h-64 rounded-full bg-blue-500/20 blur-3xl"></div>
                <div className="absolute bottom-[-50%] right-[-20%] w-64 h-64 rounded-full bg-purple-500/20 blur-3xl"></div>
                
                <div className="relative z-10 p-6 flex flex-col justify-between h-full text-white">
                    <div className="flex justify-between items-start">
                        <div className="bg-white/20 p-2 rounded backdrop-blur-md">
                            <CreditCard size={20} className="text-white"/>
                        </div>
                        <span className="font-bold tracking-widest italic text-white/50">VISA</span>
                    </div>

                    <div className="mt-4">
                        <p className="text-blue-200 text-xs font-medium mb-1">Total Balance</p>
                        <h2 className="text-3xl font-bold tracking-tight text-white">
                            ${Number(data.balance).toLocaleString()}
                        </h2>
                    </div>

                    <div className="flex justify-between items-end mt-4 text-white">
                        <div>
                            <p className="text-xs text-blue-200 mb-1">Account Number</p>
                            <button onClick={copyToClipboard} className="font-mono text-sm tracking-widest flex items-center gap-2 hover:text-blue-300 transition text-white">
                                {data.accountNumber} <Copy size={12}/>
                            </button>
                        </div>
                        <div className="text-right">
                             <p className="text-[10px] text-white/60">VALID THRU</p>
                             <p className="text-sm font-mono text-white">12/29</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        {/* 3. QUICK ACTIONS GRID */}
        <div className="lg:col-span-2 flex flex-col justify-center">
            <h3 className="font-bold text-slate-800 dark:text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/customer/transfer" className="group">
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-md transition cursor-pointer h-full">
                        <div className="h-10 w-10 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                            <Send size={20}/>
                        </div>
                        <span className="text-sm font-bold text-slate-700 dark:text-slate-300">Transfer</span>
                    </div>
                </Link>

                <Link href="/customer/loans" className="group">
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-green-500 dark:hover:border-green-500 hover:shadow-md transition cursor-pointer h-full">
                        <div className="h-10 w-10 rounded-full bg-green-50 dark:bg-green-900/30 text-green-600 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                            <Banknote size={20}/>
                        </div>
                        <span className="text-sm font-bold text-slate-700 dark:text-slate-300">Get Loan</span>
                    </div>
                </Link>

                <Link href="/customer/kyc" className="group">
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-purple-500 dark:hover:border-purple-500 hover:shadow-md transition cursor-pointer h-full">
                        <div className="h-10 w-10 rounded-full bg-purple-50 dark:bg-purple-900/30 text-purple-600 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                            <ShieldCheck size={20}/>
                        </div>
                        <span className="text-sm font-bold text-slate-700 dark:text-slate-300">Verify ID</span>
                    </div>
                </Link>

                <Link href="/customer/beneficiaries" className="group">
                    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-orange-500 dark:hover:border-orange-500 hover:shadow-md transition cursor-pointer h-full">
                        <div className="h-10 w-10 rounded-full bg-orange-50 dark:bg-orange-900/30 text-orange-600 flex items-center justify-center mb-3 group-hover:scale-110 transition">
                            <MoreHorizontal size={20}/>
                        </div>
                        <span className="text-sm font-bold text-slate-700 dark:text-slate-300">More</span>
                    </div>
                </Link>
            </div>
        </div>
      </div>

      {/* 4. MODERN TRANSACTION LIST */}
      <div>
        <div className="flex justify-between items-center mb-4">
            <h3 className="font-bold text-lg text-slate-800 dark:text-white">Recent Transactions</h3>
            <Link href="/customer/history" className="text-sm text-blue-600 hover:underline font-medium">View All</Link>
        </div>
        
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            {data.recent.length > 0 ? (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {data.recent.map((tx: any) => {
                        const isCredit = tx.type === 'credit';
                        return (
                            <div key={tx.id} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition duration-150">
                                <div className="flex items-center gap-4">
                                    <div className={`h-10 w-10 rounded-full flex items-center justify-center shrink-0 ${
                                        isCredit ? 'bg-green-100 text-green-600 dark:bg-green-900/30' : 'bg-red-100 text-red-600 dark:bg-red-900/30'
                                    }`}>
                                        {isCredit ? <ArrowDownLeft size={18}/> : <ArrowUpRight size={18}/>}
                                    </div>
                                    <div>
                                        <p className="font-bold text-sm text-slate-900 dark:text-white">{tx.description}</p>
                                        <p className="text-xs text-slate-500">
                                            {new Date(tx.created_at).toLocaleDateString()} at {new Date(tx.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                        </p>
                                    </div>
                                </div>
                                <div className={`font-bold text-sm ${isCredit ? 'text-green-600' : 'text-slate-900 dark:text-white'}`}>
                                    {isCredit ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                <div className="p-12 text-center text-slate-400">
                    <div className="bg-slate-50 dark:bg-slate-800 h-16 w-16 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Banknote size={32} className="opacity-20"/>
                    </div>
                    <p>No transactions yet. Start by adding funds!</p>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}
"""
}

def fix_utils_and_ui():
    print("🛠️ Creating utility library & Fixing Credit Card UI...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created/Updated: {path}")

if __name__ == "__main__":
    fix_utils_and_ui()
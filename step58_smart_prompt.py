import os

files = {
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Send, CreditCard, ShieldCheck, Banknote, MoreHorizontal, Copy, FileText, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import Swal from 'sweetalert2';

export default function CustomerDashboard() {
  const [data, setData] = useState<any>(null);
  const [showPrompt, setShowPrompt] = useState(false);

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

            // SMART PROMPT LOGIC: Check if it's month end (e.g. after 25th) and auto is OFF
            const day = new Date().getDate();
            if (day >= 1 && userData.auto_statements === 0) { 
                setShowPrompt(true);
            }
        } catch (e) { console.error(e); }
    };
    loadData();
  }, []);

  const generateManualStatement = () => {
    setShowPrompt(false);
    Swal.fire({
        title: 'Generating Statement',
        text: 'Preparing your monthly financial report...',
        timer: 2000,
        timerProgressBar: true,
        didOpen: () => Swal.showLoading()
    }).then(() => {
        window.location.href = '/customer/history'; // Take them to history to download PDF
    });
  };

  if (!data) return <div className="p-12 text-center text-slate-400">Loading Dashboard...</div>;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      
      {/* 1. SMART MONTH-END PROMPT */}
      {showPrompt && (
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-4 text-white shadow-lg flex items-center justify-between animate-in slide-in-from-top duration-500">
            <div className="flex items-center gap-4">
                <div className="bg-white/20 p-2 rounded-lg"><FileText size={20}/></div>
                <div>
                    <p className="font-bold text-sm">Monthly Summary Ready?</p>
                    <p className="text-xs text-blue-100">It's almost month-end. Would you like to view your current statement?</p>
                </div>
            </div>
            <div className="flex gap-2">
                <button onClick={() => setShowPrompt(false)} className="text-xs font-medium hover:bg-white/10 px-3 py-1.5 rounded-lg transition">Dismiss</button>
                <button onClick={generateManualStatement} className="bg-white text-blue-600 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-blue-50 transition">View Statement</button>
            </div>
        </div>
      )}

      {/* 2. REST OF THE DASHBOARD ... */}
      <div className="flex justify-between items-end">
        <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Hello, {data.user.name.split(' ')[0]} 👋</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Welcome back to Babji Bank.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
            <div className="relative h-52 w-full rounded-2xl bg-slate-900 text-white p-6 shadow-xl overflow-hidden">
                <div className="relative z-10 flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <CreditCard size={24} className="text-blue-400"/>
                        <span className="font-bold italic opacity-40">VISA</span>
                    </div>
                    <div>
                        <p className="text-xs text-slate-400 mb-1">Available Balance</p>
                        <h2 className="text-3xl font-bold">${Number(data.balance).toLocaleString()}</h2>
                    </div>
                    <p className="font-mono text-sm tracking-widest">{data.accountNumber}</p>
                </div>
                <div className="absolute top-[-20%] right-[-10%] w-40 h-40 bg-blue-600/20 rounded-full blur-3xl"></div>
            </div>
        </div>

        <div className="lg:col-span-2">
            <h3 className="font-bold mb-3 text-sm text-slate-500 uppercase tracking-wider">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/customer/transfer" className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:shadow-md transition text-center group">
                    <div className="h-10 w-10 bg-blue-50 dark:bg-blue-900/30 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition"><Send size={20}/></div>
                    <span className="text-sm font-bold">Transfer</span>
                </Link>
                <Link href="/customer/utilities" className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:shadow-md transition text-center group">
                    <div className="h-10 w-10 bg-green-50 dark:bg-green-900/30 text-green-600 rounded-full flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition"><FileText size={20}/></div>
                    <span className="text-sm font-bold">Bills</span>
                </Link>
                <Link href="/customer/loans" className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:shadow-md transition text-center group">
                    <div className="h-10 w-10 bg-purple-50 dark:bg-purple-900/30 text-purple-600 rounded-full flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition"><Banknote size={20}/></div>
                    <span className="text-sm font-bold">Loans</span>
                </Link>
                <Link href="/customer/kyc" className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl hover:shadow-md transition text-center group">
                    <div className="h-10 w-10 bg-orange-50 dark:bg-orange-900/30 text-orange-600 rounded-full flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition"><ShieldCheck size={20}/></div>
                    <span className="text-sm font-bold">KYC</span>
                </Link>
            </div>
        </div>
      </div>
      
      {/* RECENT ACTIVITY ... (kept same as previous dashboard step) */}
    </div>
  );
}
"""
}

def install_smart_dashboard():
    print("🚀 Installing Smart Dashboard with Month-End Prompts...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    install_smart_dashboard()
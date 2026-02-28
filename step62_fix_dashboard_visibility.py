import os

files = {
    "app/(dashboard)/customer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Send, CreditCard, ShieldCheck, Banknote, FileText, Copy, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
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

            if (userData.auto_statements === 0) { 
                setShowPrompt(true);
            }
        } catch (e) { console.error(e); }
    };
    loadData();
  }, []);

  if (!data) return <div className="p-12 text-center text-slate-400 animate-pulse">Loading secure dashboard...</div>;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      
      {/* 1. SMART PROMPT */}
      {showPrompt && (
        <div className="bg-blue-600 rounded-xl p-4 text-white shadow-lg flex items-center justify-between">
            <div className="flex items-center gap-4">
                <FileText size={20}/>
                <p className="text-sm font-bold">Your monthly statement is ready for review.</p>
            </div>
            <button onClick={() => setShowPrompt(false)} className="bg-white text-blue-600 px-4 py-1.5 rounded-lg text-xs font-bold">View</button>
        </div>
      )}

      <div className="flex justify-between items-end">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Hello, {data.user.name.split(' ')[0]} 👋</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* 2. PREMIUM CARD (FIXED TEXT COLORS) */}
        <div className="lg:col-span-1">
            <div className="relative h-56 w-full rounded-2xl bg-slate-900 shadow-2xl overflow-hidden p-6 flex flex-col justify-between">
                <div className="relative z-10 flex flex-col justify-between h-full">
                    <div className="flex justify-between items-start">
                        <CreditCard size={24} className="text-blue-400"/>
                        <span className="font-bold italic text-white/40">VISA</span>
                    </div>

                    <div>
                        <p className="text-xs text-blue-200 mb-1">Available Balance</p>
                        {/* FORCED WHITE TEXT HERE */}
                        <h2 className="text-4xl font-bold text-white tracking-tight">
                            ${Number(data.balance).toLocaleString()}
                        </h2>
                    </div>

                    <div className="flex justify-between items-end">
                        <p className="font-mono text-sm tracking-widest text-white/90">{data.accountNumber}</p>
                        <div className="text-right">
                             <p className="text-[10px] text-white/40">EXP</p>
                             <p className="text-xs font-mono text-white">12/29</p>
                        </div>
                    </div>
                </div>
                {/* Decorative glow */}
                <div className="absolute top-[-20%] right-[-10%] w-48 h-48 bg-blue-600/20 rounded-full blur-3xl"></div>
            </div>
        </div>

        {/* 3. QUICK ACTIONS */}
        <div className="lg:col-span-2">
            <h3 className="font-bold text-slate-500 text-xs uppercase tracking-widest mb-4">Quick Actions</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                    { name: 'Transfer', href: '/customer/transfer', icon: Send, color: 'text-blue-600', bg: 'bg-blue-50' },
                    { name: 'Bills', href: '/customer/utilities', icon: FileText, color: 'text-green-600', bg: 'bg-green-50' },
                    { name: 'Loans', href: '/customer/loans', icon: Banknote, color: 'text-purple-600', bg: 'bg-purple-50' },
                    { name: 'KYC', href: '/customer/kyc', icon: ShieldCheck, color: 'text-orange-600', bg: 'bg-orange-50' }
                ].map((item) => (
                    <Link key={item.name} href={item.href}>
                        <Card className="p-4 text-center hover:shadow-md transition group">
                            <div className={`h-12 w-12 ${item.bg} ${item.color} rounded-full flex items-center justify-center mx-auto mb-2 group-hover:scale-110 transition`}>
                                <item.icon size={24}/>
                            </div>
                            <span className="text-sm font-bold">{item.name}</span>
                        </Card>
                    </Link>
                ))}
            </div>
        </div>
      </div>

      {/* 4. RECENT ACTIVITY */}
      <div className="mt-8">
          <h3 className="font-bold text-lg mb-4">Recent Activity</h3>
          <div className="space-y-3">
              {data.recent.map((tx: any) => (
                  <Card key={tx.id} className="p-4 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                          <div className={`p-2 rounded-full ${tx.type === 'credit' ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-600'}`}>
                              {tx.type === 'credit' ? <ArrowDownLeft size={20}/> : <ArrowUpRight size={20}/>}
                          </div>
                          <div>
                              <p className="font-bold text-sm">{tx.description}</p>
                              <p className="text-xs text-slate-500">{new Date(tx.created_at).toLocaleDateString()}</p>
                          </div>
                      </div>
                      <div className={`font-bold ${tx.type === 'credit' ? 'text-green-600' : 'text-slate-900 dark:text-white'}`}>
                          {tx.type === 'credit' ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                      </div>
                  </Card>
              ))}
          </div>
      </div>
    </div>
  );
}
"""
}

def fix_visibility():
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Dashboard visibility fixed! The balance is now forced to white text.")

if __name__ == "__main__":
    fix_visibility()
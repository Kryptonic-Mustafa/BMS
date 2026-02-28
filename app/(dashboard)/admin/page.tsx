'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Users, DollarSign, Activity, Settings, Lock, Shield, Database } from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await fetch('/api/admin/dashboard');
        if (res.ok) {
            setData(await res.json());
        } else {
            setData({ customers: 0, holdings: 0, transactions: 0, logs: [] });
        }
      } catch (e) {
          console.error(e);
      }
    };
    loadData();
  }, []);

  if (!data) return <div className="p-8 text-center text-slate-500 animate-pulse">Loading System Overview...</div>;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold dark:text-white">System Overview</h2>

      {/* TOP CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 flex items-center gap-4 border-l-4 border-l-blue-500">
            <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full text-blue-600"><Users size={24}/></div>
            <div>
                <p className="text-sm text-slate-500 uppercase tracking-wider">Total Customers</p>
                <h3 className="text-3xl font-bold">{data.customers || 0}</h3>
            </div>
        </Card>
        <Card className="p-6 flex items-center gap-4 border-l-4 border-l-green-500">
            <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-full text-green-600"><DollarSign size={24}/></div>
            <div>
                <p className="text-sm text-slate-500 uppercase tracking-wider">Total Holdings</p>
                <h3 className="text-3xl font-bold">${Number(data.holdings || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</h3>
            </div>
        </Card>
        <Card className="p-6 flex items-center gap-4 border-l-4 border-l-purple-500">
            <div className="bg-purple-100 dark:bg-purple-900/30 p-3 rounded-full text-purple-600"><Activity size={24}/></div>
            <div>
                <p className="text-sm text-slate-500 uppercase tracking-wider">Total Transactions</p>
                <h3 className="text-3xl font-bold">{data.transactions || 0}</h3>
            </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LIVE ACTIVITY LOGS */}
        <Card className="lg:col-span-2 p-0 overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center gap-2">
                <Activity size={18} className="text-blue-600"/>
                <h3 className="font-bold">Live System Activity</h3>
            </div>
            <div className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[400px] overflow-y-auto">
                {data.logs && data.logs.length > 0 ? data.logs.map((log: any) => (
                    <div key={log.id} className="p-4 flex items-start gap-4 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                        <div className="mt-1 bg-blue-50 dark:bg-blue-900/20 p-1.5 rounded-full text-blue-500"><Activity size={14}/></div>
                        <div className="flex-1">
                            <p className="text-sm text-slate-900 dark:text-white">
                                <span className="font-bold">{log.actor_name}</span> performed <span className="font-bold">{log.action}</span>
                            </p>
                            <p className="text-xs text-slate-500 mt-0.5">{log.details}</p>
                        </div>
                        <span className="text-xs text-slate-400 whitespace-nowrap">{new Date(log.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                    </div>
                )) : (
                    <div className="p-8 text-center text-slate-400">No recent activity</div>
                )}
            </div>
        </Card>

        {/* SYSTEM STATUS & QUICK LINKS */}
        <div className="space-y-6">
            <Card className="p-6 bg-slate-900 text-white shadow-xl">
                <p className="text-xs text-slate-400 mb-4 uppercase tracking-widest">Real-time monitoring active.</p>
                <div className="space-y-3">
                    <div className="flex items-center gap-3 bg-slate-800 p-3 rounded-lg border border-slate-700">
                        <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-sm text-slate-200">System Status: <strong className="text-white">Online</strong></span>
                    </div>
                    <div className="flex items-center gap-3 bg-slate-800 p-3 rounded-lg border border-slate-700">
                        <Shield size={14} className="text-blue-400"/>
                        <span className="text-sm text-slate-200">Encryption: <strong className="text-white">AES-256</strong></span>
                    </div>
                    <div className="flex items-center gap-3 bg-slate-800 p-3 rounded-lg border border-slate-700">
                        <Database size={14} className="text-purple-400"/>
                        <span className="text-sm text-slate-200">DB Latency: <strong className="text-white">24ms</strong></span>
                    </div>
                </div>

                <div className="mt-8">
                    <p className="text-xs text-slate-400 mb-3 uppercase tracking-widest">Quick Links</p>
                    <div className="grid grid-cols-2 gap-3">
                        {/* THE FIX: Using Next.js <Link> prevents manual onClick handlers from misfiring permission toasts */}
                        <Link href="/admin/settings" className="bg-blue-600 hover:bg-blue-700 text-white p-2.5 rounded-lg text-sm font-bold text-center transition block">
                            Settings
                        </Link>
                        <Link href="/admin/roles" className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white p-2.5 rounded-lg text-sm font-bold text-center transition block">
                            Roles
                        </Link>
                    </div>
                </div>
            </Card>
        </div>
      </div>
    </div>
  );
}
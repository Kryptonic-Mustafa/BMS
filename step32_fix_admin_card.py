import os

files = {
    "app/(dashboard)/admin/page.tsx": """
'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Users, DollarSign, Activity, FileText, Shield, Settings, Lock } from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboard() {
  const [stats, setStats] = useState({ customers: 0, holdings: 0, transactions: 0 });
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    fetch('/api/admin/stats').then(res => res.json()).then(setStats);
    fetch('/api/admin/activity').then(res => res.json()).then(setActivity);
  }, []);

  const getIcon = (type: string) => {
    if (type.includes('DEPOSIT') || type.includes('TRANSFER')) return <DollarSign size={16} />;
    if (type.includes('KYC')) return <FileText size={16} />;
    return <Activity size={16} />;
  };

  const getColor = (type: string) => {
    if (type.includes('APPROVE') || type.includes('DEPOSIT')) return 'bg-green-100 text-green-700';
    if (type.includes('REJECT') || type.includes('DELETE')) return 'bg-red-100 text-red-700';
    return 'bg-blue-100 text-blue-700';
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">System Overview</h2>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex items-center p-6 border-l-4 border-blue-600">
          <div className="bg-blue-100 p-4 rounded-full text-blue-600 mr-4"><Users size={24} /></div>
          <div><p className="text-sm text-slate-500">Total Customers</p><h3 className="text-2xl font-bold">{stats.customers}</h3></div>
        </Card>
        <Card className="flex items-center p-6 border-l-4 border-green-500">
          <div className="bg-green-100 p-4 rounded-full text-green-600 mr-4"><DollarSign size={24} /></div>
          <div><p className="text-sm text-slate-500">Total Holdings</p><h3 className="text-2xl font-bold">${Number(stats.holdings).toLocaleString()}</h3></div>
        </Card>
        <Card className="flex items-center p-6 border-l-4 border-purple-500">
          <div className="bg-purple-100 p-4 rounded-full text-purple-600 mr-4"><Activity size={24} /></div>
          <div><p className="text-sm text-slate-500">Total Transactions</p><h3 className="text-2xl font-bold">{stats.transactions}</h3></div>
        </Card>
      </div>

      {/* Global Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
            <Card>
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-slate-800 dark:text-white">
                    <Activity className="text-blue-600"/> Live System Activity
                </h3>
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                    {activity.map((log: any) => (
                        <div key={log.id} className="flex items-start gap-3 pb-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
                            <div className={`p-2 rounded-full mt-1 shrink-0 ${getColor(log.action_type)}`}>
                                {getIcon(log.action_type)}
                            </div>
                            <div className="flex-1">
                                <div className="flex justify-between items-start">
                                    <p className="text-sm font-medium text-slate-800 dark:text-white">
                                        <span className="font-bold">{log.actor_name}</span> 
                                        <span className="text-slate-500 mx-1">performed</span> 
                                        {log.action_type.replace('_', ' ')}
                                    </p>
                                    <span className="text-xs text-slate-400 whitespace-nowrap">
                                        {new Date(log.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-500 mt-1 dark:text-slate-400">
                                    {log.details}
                                </p>
                            </div>
                        </div>
                    ))}
                    {activity.length === 0 && <p className="text-slate-400 text-center py-4">No recent activity logged.</p>}
                </div>
            </Card>
        </div>

        {/* Quick Actions / Status (FIXED: Using div instead of Card to force dark bg) */}
        <div>
            <div className="bg-slate-900 text-white h-full p-6 rounded-xl shadow-lg border border-slate-800">
                <h3 className="font-bold mb-2 flex items-center gap-2"><Shield size={18}/> Admin Controls</h3>
                <p className="text-slate-400 text-sm mb-6">Real-time monitoring active.</p>
                
                <div className="space-y-3">
                    <div className="p-3 bg-white/10 rounded-lg text-sm flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]"></div> 
                        <span>System Status: <strong>Online</strong></span>
                    </div>
                    <div className="p-3 bg-white/10 rounded-lg text-sm flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.5)]"></div> 
                        <span>Encryption: <strong>AES-256</strong></span>
                    </div>
                     <div className="p-3 bg-white/10 rounded-lg text-sm flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(192,132,252,0.5)]"></div> 
                        <span>DB Latency: <strong>24ms</strong></span>
                    </div>
                </div>

                <div className="mt-6 pt-6 border-t border-slate-700">
                    <p className="text-xs text-slate-500 uppercase font-bold mb-3">Quick Links</p>
                    <div className="grid grid-cols-2 gap-2">
                        <Link href="/admin/settings" className="block text-center py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs font-bold transition">Settings</Link>
                        <Link href="/admin/roles" className="block text-center py-2 bg-slate-700 hover:bg-slate-600 rounded text-xs font-bold transition">Roles</Link>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
"""
}

def fix_admin_ui():
    print("🎨 Fixing Admin Control Card Colors...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_admin_ui()
import os
import random
from datetime import datetime, timedelta

# --- 1. GENERATE SQL FOR FAKE DATA (To make charts/logs look alive) ---
def generate_seed_sql():
    sql = ["USE bank_app;", "SET SQL_SAFE_UPDATES = 0;"]
    
    # A. Fake Transactions (For Charts)
    # Generate ~20 transactions over last 7 days
    types = ['credit', 'debit']
    for i in range(20):
        days_ago = random.randint(0, 7)
        amount = random.randint(100, 5000)
        t_type = random.choice(types)
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Assume account ID 1 exists (Super Admin or first user)
        sql.append(
            f"INSERT INTO transactions (account_id, type, amount, status, description, created_at) "
            f"VALUES (1, '{t_type}', {amount}, 'completed', 'Test Transaction', '{date}');"
        )

    # B. Fake Audit Logs (For Dashboard Activity)
    actions = [
        ('Super Admin', 'ADMIN_LOGIN', 'Logged into the system'),
        ('Manager', 'KYC_APPROVE', 'Verified Customer John Doe'),
        ('Super Admin', 'SETTINGS_UPDATE', 'Changed Site Logo'),
        ('System', 'AUTO_BACKUP', 'Daily database backup completed'),
        ('Manager', 'DEPOSIT', 'Added $500 to Account ACC123')
    ]
    
    for actor, action, details in actions:
        date = (datetime.now() - timedelta(hours=random.randint(1, 24))).strftime('%Y-%m-%d %H:%M:%S')
        sql.append(
            f"INSERT INTO audit_logs (actor_name, action_type, details, created_at) "
            f"VALUES ('{actor}', '{action}', '{details}', '{date}');"
        )
    
    sql.append("SET SQL_SAFE_UPDATES = 1;")
    return "\n".join(sql)

# Write SQL file
with open("seed_analytics.sql", "w") as f:
    f.write(generate_seed_sql())


files = {
    # --- 2. UPDATE DASHBOARD UI (Fixing the "Dots" issue) ---
    "app/(dashboard)/admin/page.tsx": """
'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Users, DollarSign, Activity, FileText, Server, Shield } from 'lucide-react';

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
          <div><p className="text-sm text-slate-500">Total Holdings</p><h3 className="text-2xl font-bold">${stats.holdings.toLocaleString()}</h3></div>
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

        {/* Quick Actions / Status (FIXED STYLING) */}
        <div>
            <Card className="bg-slate-900 text-white h-full p-6">
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
                        <a href="/admin/settings" className="block text-center py-2 bg-blue-600 hover:bg-blue-500 rounded text-xs font-bold transition">Settings</a>
                        <a href="/admin/roles" className="block text-center py-2 bg-slate-700 hover:bg-slate-600 rounded text-xs font-bold transition">Roles</a>
                    </div>
                </div>
            </Card>
        </div>
      </div>
    </div>
  );
}
""",

    # --- 3. LOG SETTINGS UPDATES ---
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const settings = await query('SELECT * FROM settings LIMIT 1');
  return NextResponse.json(settings[0] || {});
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.permissions?.includes('SettingsManage') && session.role !== 'admin') {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const { site_name, site_logo, site_favicon } = await request.json();

  const check: any = await query('SELECT id FROM settings LIMIT 1');
  
  if (check.length === 0) {
    await query('INSERT INTO settings (site_name, site_logo, site_favicon) VALUES (?, ?, ?)', 
      [site_name, site_logo, site_favicon]);
  } else {
    await query('UPDATE settings SET site_name = ?, site_logo = ?, site_favicon = ? WHERE id = ?', 
      [site_name, site_logo, site_favicon, check[0].id]);
  }

  // AUDIT LOG
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    action: 'SETTINGS_UPDATE',
    details: 'Updated Global Site Configuration'
  });

  return NextResponse.json({ success: true });
}
"""
}

def fix_dashboard():
    print("🛠️ Fixing Dashboard & Generating Seed Data...")
    
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n📝 Created 'seed_analytics.sql'.") 
    print("👉 ACTION REQUIRED: Run this SQL file in MySQL Workbench to see data in charts!")

if __name__ == "__main__":
    fix_dashboard()
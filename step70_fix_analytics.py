import os

files = {
    # --- 1. THE BACKEND API FIX (Convert Strings to Numbers & Add Fallbacks) ---
    "app/api/admin/analytics/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
      const session = await getSession();
      if (!session || (session.role !== 'admin' && !session.permissions?.includes('Reports'))) {
          return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }

      // 1. Transaction Volume (Fixing string vs number issue & empty states)
      const rawTx: any = await query(`
          SELECT 
              DATE_FORMAT(created_at, '%b %d') as date,
              SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as credits,
              SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as debits
          FROM transactions
          WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
          GROUP BY DATE(created_at)
          ORDER BY DATE(created_at) ASC
      `);

      // FORCE CONVERSION TO NUMBERS
      let txData = rawTx.map((row: any) => ({
          date: row.date,
          credits: Number(row.credits || 0),
          debits: Number(row.debits || 0)
      }));

      // FALLBACK: If no data in last 7 days, provide flatlines so the chart doesn't break
      if (txData.length === 0) {
          const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
          txData = days.map(day => ({ date: day, credits: 0, debits: 0 }));
      }

      // 2. User Growth Data
      const rawUsers: any = await query(`
          SELECT DATE_FORMAT(created_at, '%b') as month, COUNT(*) as users
          FROM users
          WHERE role_id = (SELECT id FROM roles WHERE name='Customer' LIMIT 1)
          GROUP BY month
          ORDER BY created_at ASC LIMIT 6
      `);
      let userGrowth = rawUsers.map((row: any) => ({ month: row.month, users: Number(row.users) }));
      if (userGrowth.length === 0) userGrowth = [{ month: 'Current', users: 1 }];

      // 3. Account Types Distribution
      const rawAccts: any = await query(`
          SELECT type as name, COUNT(*) as value
          FROM accounts
          GROUP BY type
      `);
      let accountDist = rawAccts.map((row: any) => ({ 
          name: row.name ? row.name.toUpperCase() : 'UNKNOWN', 
          value: Number(row.value) 
      }));
      if (accountDist.length === 0) accountDist = [{ name: 'SAVINGS', value: 1 }];

      return NextResponse.json({ txData, userGrowth, accountDist });
  } catch (error) {
      console.error('Analytics API Error:', error);
      return NextResponse.json({ error: 'Failed to fetch analytics' }, { status: 500 });
  }
}
""",

    # --- 2. THE FRONTEND UI (Clean Recharts Implementation) ---
    "app/(dashboard)/admin/analytics/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Legend } from 'recharts';

const COLORS = ['#2563EB', '#16A34A', '#D97706', '#DC2626'];

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/admin/analytics').then(res => res.json()).then(setData);
  }, []);

  if (!data) return <div className="p-12 text-center text-slate-500 animate-pulse">Loading Financial Analytics...</div>;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold dark:text-white mb-6">Financial Analytics</h2>

      {/* CHART 1: TRANSACTIONS (Fixed) */}
      <Card className="p-6 shadow-sm">
        <h3 className="font-bold mb-6 text-slate-800 dark:text-white">Transaction Volume (Last 7 Days)</h3>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.txData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2}/>
              <XAxis dataKey="date" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false}/>
              <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`}/>
              <Tooltip 
                 contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none', color: '#fff' }}
                 itemStyle={{ color: '#fff' }}
              />
              <Legend verticalAlign="bottom" height={36}/>
              <Line type="monotone" dataKey="credits" name="Credits ($)" stroke="#16A34A" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }}/>
              <Line type="monotone" dataKey="debits" name="Debits ($)" stroke="#DC2626" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }}/>
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        
        {/* CHART 2: USER GROWTH */}
        <Card className="p-6 shadow-sm">
          <h3 className="font-bold mb-6 text-slate-800 dark:text-white">User Growth (6 Months)</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.userGrowth} margin={{ top: 5, right: 0, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.1}/>
                <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false}/>
                <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false}/>
                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px' }}/>
                <Bar dataKey="users" name="New Users" fill="#2563EB" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* CHART 3: ACCOUNT TYPES */}
        <Card className="p-6 shadow-sm">
          <h3 className="font-bold mb-6 text-slate-800 dark:text-white">Account Distribution</h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                    data={data.accountDist} 
                    cx="50%" cy="50%" 
                    innerRadius={60} outerRadius={80} 
                    paddingAngle={5} 
                    dataKey="value"
                >
                  {data.accountDist.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

    </div>
  );
}
"""
}

def fix_analytics():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Analytics fixed! Numbers are properly parsed and fallbacks added.")

if __name__ == "__main__":
    fix_analytics()
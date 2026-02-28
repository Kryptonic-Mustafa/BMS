import os

files = {
    # --- 1. THE BACKEND API FIX (Real Data, Safe Queries, No Fallbacks) ---
    "app/api/admin/analytics/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
      const session = await getSession();
      if (!session || (session.role !== 'admin' && session.role !== 'SuperAdmin' && !session.permissions?.includes('Reports'))) {
          return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }

      // 1. Transaction Volume (REAL DATA: Groups existing transactions by date)
      const rawTx: any = await query(`
          SELECT 
              DATE_FORMAT(created_at, '%b %d') as date,
              SUM(CASE WHEN type = 'credit' THEN amount ELSE 0 END) as credits,
              SUM(CASE WHEN type = 'debit' THEN amount ELSE 0 END) as debits
          FROM transactions
          GROUP BY DATE(created_at), DATE_FORMAT(created_at, '%b %d')
          ORDER BY DATE(created_at) ASC
          LIMIT 30
      `);

      const txData = rawTx.map((row: any) => ({
          date: row.date,
          credits: Number(row.credits || 0),
          debits: Number(row.debits || 0)
      }));

      // 2. User Growth Data (REAL DATA: Safe Grouping)
      const rawUsers: any = await query(`
          SELECT DATE_FORMAT(created_at, '%b %Y') as month, COUNT(*) as users
          FROM users
          WHERE role_id = (SELECT id FROM roles WHERE name='Customer' LIMIT 1)
          GROUP BY DATE_FORMAT(created_at, '%b %Y')
          ORDER BY MIN(created_at) ASC 
          LIMIT 6
      `);
      const userGrowth = rawUsers.map((row: any) => ({ month: row.month, users: Number(row.users) }));

      // 3. Transaction Distribution (Credits vs Debits count - Guaranteed to work)
      const rawTxDist: any = await query(`
          SELECT UPPER(type) as name, COUNT(*) as value
          FROM transactions
          GROUP BY type
      `);
      const accountDist = rawTxDist.map((row: any) => ({ 
          name: row.name, 
          value: Number(row.value) 
      }));

      return NextResponse.json({ txData, userGrowth, accountDist });
  } catch (error: any) {
      console.error('Analytics API Error:', error);
      // Send the actual error message to the frontend so we know what went wrong
      return NextResponse.json({ error: error.message || 'Failed to fetch analytics' }, { status: 500 });
  }
}
""",

    # --- 2. THE FRONTEND UI (Added Error Catching so React doesn't crash) ---
    "app/(dashboard)/admin/analytics/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Legend } from 'recharts';
import { AlertTriangle } from 'lucide-react';

const COLORS = ['#2563EB', '#16A34A', '#D97706', '#DC2626'];

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/admin/analytics')
        .then(res => res.json())
        .then(setData)
        .catch(err => setData({ error: 'Network Error: Could not reach API.' }));
  }, []);

  if (!data) return <div className="p-12 text-center text-slate-500 animate-pulse">Loading Financial Analytics...</div>;
  
  // SAFEGUARD: If the API sends an error, show it cleanly instead of crashing React
  if (data.error) return (
      <div className="p-12 max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl flex items-start gap-4">
              <AlertTriangle className="shrink-0 mt-1"/>
              <div>
                  <h3 className="font-bold text-lg">Failed to load data</h3>
                  <p className="text-sm mt-1">{data.error}</p>
              </div>
          </div>
      </div>
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold dark:text-white mb-6">Financial Analytics</h2>

      {/* CHART 1: TRANSACTIONS (Real Data Timeline) */}
      <Card className="p-6 shadow-sm">
        <h3 className="font-bold mb-6 text-slate-800 dark:text-white">Transaction Volume</h3>
        <div className="h-80 w-full">
          {data.txData && data.txData.length > 0 ? (
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
          ) : (
              <div className="h-full flex items-center justify-center text-slate-400">No transactions recorded yet.</div>
          )}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        
        {/* CHART 2: USER GROWTH */}
        <Card className="p-6 shadow-sm">
          <h3 className="font-bold mb-6 text-slate-800 dark:text-white">User Growth</h3>
          <div className="h-64 w-full">
            {data.userGrowth && data.userGrowth.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.userGrowth} margin={{ top: 5, right: 0, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.1}/>
                    <XAxis dataKey="month" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false}/>
                    <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false}/>
                    <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '8px' }}/>
                    <Bar dataKey="users" name="New Users" fill="#2563EB" radius={[4, 4, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
            ) : (
                <div className="h-full flex items-center justify-center text-slate-400">No user data available.</div>
            )}
          </div>
        </Card>

        {/* CHART 3: TRANSACTION DISTRIBUTION */}
        <Card className="p-6 shadow-sm">
          <h3 className="font-bold mb-6 text-slate-800 dark:text-white">Transaction Distribution</h3>
          <div className="h-64 w-full">
            {data.accountDist && data.accountDist.length > 0 ? (
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
            ) : (
                <div className="h-full flex items-center justify-center text-slate-400">No distribution data.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
"""
}

def apply_real_analytics():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Applied Real Data Analytics and React Error Boundaries!")

if __name__ == "__main__":
    apply_real_analytics()
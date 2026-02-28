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
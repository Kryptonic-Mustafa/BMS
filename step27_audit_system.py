import os

files = {
    # --- 1. AUDIT LOGGER HELPER ---
    "lib/audit.ts": """
import { query } from '@/lib/db';

interface AuditParams {
  actorId: number;
  actorName: string;
  targetId?: number;
  targetName?: string;
  action: string;
  details: string;
  status?: 'SUCCESS' | 'FAILED' | 'PENDING';
}

export async function logActivity({ actorId, actorName, targetId, targetName, action, details, status = 'SUCCESS' }: AuditParams) {
  try {
    await query(
      `INSERT INTO audit_logs (actor_id, actor_name, target_id, target_name, action_type, details, status) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [actorId, actorName, targetId || null, targetName || 'System', action, details, status]
    );
  } catch (e) {
    console.error('Failed to write audit log:', e);
  }
}
""",

    # --- 2. UPDATE DEPOSIT API (To Log Activity) ---
    "app/api/admin/deposit/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { accountId, amount } = await request.json();

  // 1. Get Account & User Details
  const acc: any = await query('SELECT u.id as user_id, u.name, u.email FROM accounts a JOIN users u ON a.user_id = u.id WHERE a.id = ?', [accountId]);
  if (acc.length === 0) return NextResponse.json({ error: 'Account not found' }, { status: 404 });
  const targetUser = acc[0];

  // 2. Perform Deposit
  await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, accountId]);

  // 3. Create Transaction Record
  await query(
    'INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, ?, ?, ?, ?)',
    [accountId, 'credit', amount, 'completed', 'Admin Deposit']
  );

  // 4. AUDIT LOG (The New Part)
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    targetId: targetUser.user_id,
    targetName: targetUser.name,
    action: 'ADMIN_DEPOSIT',
    details: `Deposited $${amount} into account`
  });

  return NextResponse.json({ success: true });
}
""",

    # --- 3. UPDATE KYC API (To Log Approval/Rejection) ---
    "app/api/admin/kyc/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get Pending Requests
  const requests = await query(`
    SELECT k.id, k.document_type, k.document_number, k.file_data, k.submitted_at, 
           u.id as user_id, u.name, u.email 
    FROM kyc_documents k
    JOIN users u ON k.user_id = u.id
    WHERE u.kyc_status = 'pending'
    ORDER BY k.submitted_at DESC
  `);
  
  // Also fetch Audit History for this page (Recent Activity)
  const history = await query(`
    SELECT * FROM audit_logs 
    WHERE action_type IN ('KYC_APPROVE', 'KYC_REJECT') 
    ORDER BY created_at DESC LIMIT 5
  `);

  return NextResponse.json({ requests, history });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { userId, action, notes } = await request.json();
  const status = action === 'approve' ? 'verified' : 'rejected';

  // 1. Get Target User Name for logging
  const target: any = await query('SELECT name FROM users WHERE id = ?', [userId]);
  const targetName = target[0]?.name || 'Unknown';

  // 2. Update Status
  await query('UPDATE users SET kyc_status = ? WHERE id = ?', [status, userId]);
  
  // 3. AUDIT LOG
  await logActivity({
    actorId: session.id,
    actorName: session.name,
    targetId: userId,
    targetName: targetName,
    action: action === 'approve' ? 'KYC_APPROVE' : 'KYC_REJECT',
    details: `KYC verification ${action}d. ${notes ? 'Reason: ' + notes : ''}`
  });

  return NextResponse.json({ success: true });
}
""",

    # --- 4. NEW API: GLOBAL ACTIVITY FEED (For Admin Dashboard) ---
    "app/api/admin/activity/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const logs = await query(`
    SELECT * FROM audit_logs 
    ORDER BY created_at DESC 
    LIMIT 20
  `);
  
  return NextResponse.json(logs);
}
""",

    # --- 5. UPDATE ADMIN DASHBOARD (Show Live Activity) ---
    "app/(dashboard)/admin/page.tsx": """
'use client';
import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Users, DollarSign, Activity, FileText, CheckCircle, XCircle, ArrowUpRight } from 'lucide-react';

export default function AdminDashboard() {
  const [stats, setStats] = useState({ customers: 0, holdings: 0, transactions: 0 });
  const [activity, setActivity] = useState([]);

  useEffect(() => {
    // Fetch Stats
    fetch('/api/admin/stats').then(res => res.json()).then(data => setStats(data));
    
    // Fetch Activity Feed
    fetch('/api/admin/activity').then(res => res.json()).then(data => setActivity(data));
  }, []);

  const getIcon = (type: string) => {
    if (type.includes('DEPOSIT') || type.includes('TRANSFER')) return <DollarSign size={16} />;
    if (type.includes('KYC')) return <FileText size={16} />;
    return <Activity size={16} />;
  };

  const getColor = (type: string) => {
    if (type.includes('APPROVE') || type.includes('DEPOSIT')) return 'bg-green-100 text-green-700';
    if (type.includes('REJECT')) return 'bg-red-100 text-red-700';
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
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                    <Activity className="text-blue-600"/> Live System Activity
                </h3>
                <div className="space-y-4">
                    {activity.map((log: any) => (
                        <div key={log.id} className="flex items-start gap-3 pb-3 border-b border-slate-100 last:border-0">
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
                                        {new Date(log.created_at).toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-500 mt-1">
                                    Target: <span className="font-medium text-slate-700 dark:text-slate-300">{log.target_name}</span> • {log.details}
                                </p>
                            </div>
                        </div>
                    ))}
                    {activity.length === 0 && <p className="text-slate-400 text-center py-4">No recent activity logged.</p>}
                </div>
            </Card>
        </div>

        {/* Quick Actions / Tips */}
        <div>
            <Card className="bg-slate-900 text-white h-full">
                <h3 className="font-bold mb-2">Admin Controls</h3>
                <p className="text-slate-400 text-sm mb-4">You have full access to the audit trail.</p>
                <div className="space-y-2">
                    <div className="p-3 bg-white/10 rounded-lg text-sm">
                        <span className="text-green-400 font-bold">●</span> System Status: Online
                    </div>
                    <div className="p-3 bg-white/10 rounded-lg text-sm">
                        <span className="text-blue-400 font-bold">●</span> Encryption: AES-256
                    </div>
                </div>
            </Card>
        </div>
      </div>
    </div>
  );
}
""",

    # --- 6. UPDATE KYC PAGE (Show History) ---
    "app/(dashboard)/admin/kyc/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, FileText, History } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function AdminKYCPage() {
  const [requests, setRequests] = useState([]);
  const [history, setHistory] = useState([]); // New History State
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  const fetchData = async () => {
    const res = await fetch('/api/admin/kyc');
    if (res.ok) {
        const data = await res.json();
        setRequests(data.requests || []);
        setHistory(data.history || []);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleAction = async (userId: number, action: 'approve' | 'reject') => {
    let notes = '';
    if (action === 'reject') {
        const { value } = await Swal.fire({
            title: 'Reject Reason',
            input: 'text',
            inputPlaceholder: 'Reason...',
            showCancelButton: true
        });
        if (!value) return; 
        notes = value;
    }

    await fetch('/api/admin/kyc', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ userId, action, notes })
    });

    Swal.fire(action === 'approve' ? 'Approved' : 'Rejected', 'User status updated.', 'success');
    fetchData();
    setSelectedDoc(null);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">KYC Management</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* LEFT: REQUESTS QUEUE */}
          <div className="lg:col-span-2 space-y-4">
              <h3 className="font-bold text-slate-500 text-sm uppercase">Pending Requests</h3>
              {requests.map((req: any) => (
                <Card key={req.id} className="flex flex-col gap-4">
                    <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
                        <div className="bg-blue-100 p-2 rounded-full text-blue-600"><FileText size={20}/></div>
                        <div>
                            <div className="font-bold text-slate-900">{req.name}</div>
                            <div className="text-xs text-slate-500">{req.email}</div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <Button variant="secondary" className="flex-1" onClick={() => setSelectedDoc(req)}>Review Document</Button>
                    </div>
                </Card>
              ))}
              {requests.length === 0 && <Card className="text-center py-8 text-slate-400">No pending requests.</Card>}
          </div>

          {/* RIGHT: RECENT HISTORY */}
          <div>
              <h3 className="font-bold text-slate-500 text-sm uppercase mb-4">Recent Actions</h3>
              <div className="space-y-3">
                  {history.map((log: any) => (
                      <Card key={log.id} className="p-3 text-sm">
                          <div className="flex items-center justify-between mb-1">
                              <span className={`font-bold text-xs px-2 py-0.5 rounded ${log.action_type === 'KYC_APPROVE' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                  {log.action_type === 'KYC_APPROVE' ? 'APPROVED' : 'REJECTED'}
                              </span>
                              <span className="text-xs text-slate-400">{new Date(log.created_at).toLocaleDateString()}</span>
                          </div>
                          <p className="text-slate-600">
                              <span className="font-medium">{log.actor_name}</span> decided for <span className="font-medium">{log.target_name}</span>.
                          </p>
                      </Card>
                  ))}
                  {history.length === 0 && <p className="text-xs text-slate-400">No history yet.</p>}
              </div>
          </div>
      </div>

      <Modal isOpen={!!selectedDoc} onClose={() => setSelectedDoc(null)} title="Review Document">
        {selectedDoc && (
            <div className="space-y-6">
                <div className="bg-slate-100 p-4 rounded-lg flex justify-center">
                    <img src={selectedDoc.file_data} className="max-h-[60vh] object-contain shadow-lg rounded" />
                </div>
                <div className="flex justify-end gap-3">
                    <Button variant="danger" onClick={() => handleAction(selectedDoc.user_id, 'reject')}><X size={18} className="mr-2"/> Reject</Button>
                    <Button onClick={() => handleAction(selectedDoc.user_id, 'approve')}><Check size={18} className="mr-2"/> Approve</Button>
                </div>
            </div>
        )}
      </Modal>
    </div>
  );
}
"""
}

def audit_system():
    print("📜 Installing Enterprise Audit Logging...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n✅ System Live! Actions (Deposit, KYC) are now logged to 'audit_logs'.")

if __name__ == "__main__":
    audit_system()
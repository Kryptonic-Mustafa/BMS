import os

files = {
    # --- 1. UPDATE ADMIN LOAN PAGE (Add Comment Input) ---
    "app/(dashboard)/admin/loans/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, DollarSign, MessageSquare } from 'lucide-react';
import Swal from 'sweetalert2';

export default function AdminLoansPage() {
  const [loans, setLoans] = useState([]);

  const fetchLoans = async () => {
    const res = await fetch('/api/admin/loans');
    if (res.ok) setLoans(await res.json());
  };

  useEffect(() => { fetchLoans(); }, []);

  const handleDecision = async (loanId: number, action: 'approve' | 'reject') => {
    // 1. Ask for Comment/Reason
    const { value: comment } = await Swal.fire({
        title: `${action.toUpperCase()} Loan?`,
        input: 'textarea',
        inputLabel: action === 'reject' ? 'Reason for Rejection' : 'Approval Terms / Notes',
        inputPlaceholder: action === 'reject' ? 'e.g. Low Credit Score' : 'e.g. Approved as per policy...',
        inputAttributes: { 'aria-label': 'Type your message here' },
        icon: action === 'approve' ? 'question' : 'warning',
        showCancelButton: true,
        confirmButtonText: `Yes, ${action}`,
        confirmButtonColor: action === 'approve' ? '#10B981' : '#EF4444',
        inputValidator: (value) => {
            if (!value && action === 'reject') return 'You need to write a reason for rejection!';
        }
    });

    if (comment !== undefined) { // If not cancelled
        await fetch('/api/admin/loans', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ loanId, action, comment })
        });
        Swal.fire('Updated', `Loan has been ${action}d.`, 'success');
        fetchLoans();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Loan Requests</h2>

      <div className="grid grid-cols-1 gap-4">
        {loans.map((loan: any) => (
            <Card key={loan.id} className="flex flex-col md:flex-row justify-between gap-4 border-l-4 border-l-blue-500">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-lg dark:text-white">{loan.name}</span>
                        <span className="text-xs bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-slate-600 dark:text-slate-300">Acc: {loan.account_number}</span>
                    </div>
                    <p className="text-sm text-slate-500 mb-2">Requesting <span className="font-bold text-slate-900 dark:text-white">${Number(loan.amount).toLocaleString()}</span> for {loan.purpose}</p>
                    <div className="flex gap-4 text-xs text-slate-400">
                        <span>Duration: {loan.duration_months} Months</span>
                        <span>EMI: ${Number(loan.monthly_emi).toLocaleString()}</span>
                    </div>
                    {/* Show existing comment if processed */}
                    {loan.admin_comment && (
                        <div className="mt-2 text-xs bg-slate-50 dark:bg-slate-800 p-2 rounded text-slate-600 dark:text-slate-400 italic border border-slate-100 dark:border-slate-700">
                            <MessageSquare size={12} className="inline mr-1"/> "{loan.admin_comment}"
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-3">
                    {loan.status === 'pending' ? (
                        <>
                            <Button variant="danger" onClick={() => handleDecision(loan.id, 'reject')}><X size={16} className="mr-2"/> Reject</Button>
                            <Button onClick={() => handleDecision(loan.id, 'approve')}><Check size={16} className="mr-2"/> Approve</Button>
                        </>
                    ) : (
                        <span className={`px-4 py-2 rounded-lg font-bold text-sm uppercase ${
                            loan.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}>
                            {loan.status}
                        </span>
                    )}
                </div>
            </Card>
        ))}
        {loans.length === 0 && <p className="text-slate-500 text-center py-8">No loan requests found.</p>}
      </div>
    </div>
  );
}
""",

    # --- 2. UPDATE LOAN API (Handle Comments & Detailed Notification) ---
    "app/api/admin/loans/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { logActivity } from '@/lib/audit';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const loans = await query(`
    SELECT l.*, u.name, u.email, a.account_number
    FROM loans l
    JOIN users u ON l.user_id = u.id
    LEFT JOIN accounts a ON u.id = a.user_id
    ORDER BY l.created_at DESC
  `);
  
  return NextResponse.json(loans);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.permissions?.includes('LoansManage') && session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const { loanId, action, comment } = await request.json();
  const status = action === 'approve' ? 'approved' : 'rejected';

  // 1. Get Loan Details
  const loan: any = await query('SELECT * FROM loans WHERE id = ?', [loanId]);
  if (!loan.length) return NextResponse.json({ error: 'Loan not found' }, { status: 404 });
  const loanData = loan[0];

  // 2. Process Approval
  if (status === 'approved') {
      const acc: any = await query('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', [loanData.user_id]);
      if (acc.length > 0) {
          await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [loanData.amount, acc[0].id]);
          await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)',
             [acc[0].id, loanData.amount, `Loan Disbursement: #${loanId}`]
          );
      }
  }

  // 3. Update Loan with Comment
  await query('UPDATE loans SET status = ?, approved_by = ?, admin_comment = ? WHERE id = ?', 
    [status, session.id, comment, loanId]);

  // 4. Detailed Notification for User
  const msgTitle = status === 'approved' ? 'Loan Approved! 🎉' : 'Loan Rejected ⚠️';
  const msgBody = status === 'approved' 
    ? `Your loan of $${Number(loanData.amount).toLocaleString()} has been disbursed. Note: ${comment}`
    : `Your loan application was rejected. Reason: ${comment}`;

  await query(
      'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
      [loanData.user_id, `${msgTitle} ${msgBody}`, status === 'approved' ? 'success' : 'error']
  );

  // 5. Audit Log
  await logActivity({
      actorId: session.id,
      actorName: session.name,
      targetId: loanData.user_id,
      action: 'LOAN_DECISION',
      details: `Loan #${loanId} ${status}. Note: ${comment}`
  });

  return NextResponse.json({ success: true });
}
""",

    # --- 3. GLOBAL TOAST POLLER (Inside NotificationBell) ---
    "components/layout/NotificationBell.tsx": """
'use client';
import { useState, useEffect, useRef } from 'react';
import { Bell, Check, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<any[]>([]);
  const lastNotifIdRef = useRef<number>(0); // Track the last seen ID
  const dropdownRef = useRef<any>(null);
  const router = useRouter();

  const fetchNotifications = async (isPolling = false) => {
    try {
        const res = await fetch('/api/notifications');
        if (res.ok) {
            const data = await res.json();
            const list = data.notifications || [];
            
            setNotifications(list);
            setUnreadCount(data.unreadCount || 0);

            // --- GLOBAL TOAST LOGIC ---
            // If we are polling (not first load), and we found a NEW notification that is newer than what we last saw...
            if (isPolling && list.length > 0) {
                const latest = list[0];
                
                // If latest ID is greater than our ref, it's new!
                if (latest.id > lastNotifIdRef.current) {
                    // Trigger Toast
                    Swal.fire({
                        toast: true,
                        position: 'top-end',
                        icon: latest.type === 'success' ? 'success' : latest.type === 'error' ? 'error' : 'info',
                        title: latest.type === 'success' ? 'Good News!' : 'New Alert',
                        text: latest.message,
                        showConfirmButton: false,
                        timer: 5000,
                        timerProgressBar: true,
                        didOpen: (toast) => {
                            toast.addEventListener('mouseenter', Swal.stopTimer)
                            toast.addEventListener('mouseleave', Swal.resumeTimer)
                        }
                    });
                }
            }

            // Update ref to the latest ID so we don't show it again
            if (list.length > 0) {
                lastNotifIdRef.current = list[0].id;
            }
        }
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    // Initial Fetch
    fetchNotifications(false);
    
    // Poll every 5 seconds (Fast enough for "Real-time" feel)
    const interval = setInterval(() => fetchNotifications(true), 5000);
    return () => clearInterval(interval);
  }, []);

  // ... (Rest of UI Logic remains the same) ...

  const markAsRead = async (id?: number) => {
    await fetch('/api/notifications', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, markAll: !id, status: true })
    });
    fetchNotifications(false); // Refresh list
  };

  const getIcon = (type: string) => {
    switch(type) {
        case 'success': return <CheckCircle size={16} className="text-green-600" />;
        case 'error': return <AlertTriangle size={16} className="text-red-500" />;
        default: return <Info size={16} className="text-blue-500" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition relative"
      >
        <Bell size={20} className="text-slate-600 dark:text-slate-300" />
        {unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 ring-2 ring-white dark:ring-slate-900"></span>
            </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                <h3 className="font-bold text-sm text-slate-800 dark:text-white">Notifications</h3>
                {unreadCount > 0 && (
                    <button onClick={() => markAsRead()} className="text-xs text-blue-600 hover:text-blue-500 flex items-center gap-1 font-medium">
                        <Check size={12}/> Mark all read
                    </button>
                )}
            </div>

            <div className="max-h-[350px] overflow-y-auto">
                {notifications.length > 0 ? (
                    notifications.map((n) => (
                        <div 
                            key={n.id} 
                            onClick={() => !n.is_read && markAsRead(n.id)}
                            className={`p-4 border-b border-slate-50 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer flex gap-3 ${
                                n.is_read ? 'bg-white dark:bg-slate-900' : 'bg-blue-50/50 dark:bg-blue-900/10'
                            }`}
                        >
                            <div className="mt-1 shrink-0">{getIcon(n.type)}</div>
                            <div>
                                <p className={`text-sm ${n.is_read ? 'text-slate-700 dark:text-slate-300' : 'text-slate-900 dark:text-white font-bold'}`}>
                                    {n.message}
                                </p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </p>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="p-8 text-center text-slate-500">
                        <Bell size={32} className="mx-auto mb-2 opacity-20"/>
                        <p className="text-sm">No notifications yet.</p>
                    </div>
                )}
            </div>
            
            <div className="p-2 bg-slate-50 dark:bg-slate-800 text-center border-t border-slate-100 dark:border-slate-800">
                <button 
                    onClick={() => { setIsOpen(false); router.push('/notifications'); }} 
                    className="text-xs font-bold text-blue-600 hover:text-blue-800 uppercase tracking-wide"
                >
                    View Full History
                </button>
            </div>
        </div>
      )}
    </div>
  );
}
"""
}

def global_toasts():
    print("🍞 Installing Global Toast System & Admin Comments...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    global_toasts()
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
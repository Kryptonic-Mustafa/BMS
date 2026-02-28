'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Paperclip } from 'lucide-react';
import Swal from 'sweetalert2';

export default function AdminSupportPage() {
  const [tickets, setTickets] = useState([]);

  const fetchTickets = async () => {
    const res = await fetch('/api/tickets');
    setTickets(await res.json());
  };

  useEffect(() => { fetchTickets(); }, []);

  const handleReply = async (ticketId: number) => {
    const { value: text } = await Swal.fire({
        input: 'textarea',
        inputLabel: 'Reply to User',
        inputPlaceholder: 'Type your response...',
        showCancelButton: true
    });

    if (text) {
        await fetch('/api/tickets', {
            method: 'POST',
            body: JSON.stringify({ action: 'reply', ticketId, reply: text })
        });
        fetchTickets();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Support Tickets</h2>
      <div className="grid gap-4">
        {tickets.map((t: any) => (
            <div key={t.id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                    <div className="flex gap-2 items-center mb-1">
                        <h3 className="font-bold text-lg">{t.subject}</h3>
                        <span className="text-sm text-slate-500">by {t.user_email}</span>
                        <Badge variant={t.status === 'resolved' ? 'success' : 'warning'}>{t.status}</Badge>
                    </div>
                    <p className="text-slate-700 mb-4">{t.message}</p>
                    
                    {/* Admin Proof View */}
                    {t.attachment && (
                        <div className="mb-4">
                            <p className="text-xs font-bold text-slate-500 uppercase mb-2 flex items-center gap-1"><Paperclip size={12}/> User Attachment:</p>
                            <img src={t.attachment} className="max-h-40 rounded border border-slate-200 cursor-pointer hover:scale-105 transition" onClick={() => Swal.fire({ imageUrl: t.attachment, showConfirmButton: false })} />
                        </div>
                    )}

                    {t.admin_reply ? (
                         <p className="text-sm text-green-700 bg-green-50 p-2 rounded border border-green-100">✅ Replied: {t.admin_reply}</p>
                    ) : (
                        <Button size="sm" onClick={() => handleReply(t.id)}>Reply & Solve</Button>
                    )}
                </div>
            </div>
        ))}
      </div>
    </div>
  );
}
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Paperclip, X } from 'lucide-react';
import Swal from 'sweetalert2';

export default function SupportPage() {
  const [tickets, setTickets] = useState([]);
  const [form, setForm] = useState({ subject: '', message: '' });
  const [attachment, setAttachment] = useState<string | null>(null);

  const fetchTickets = async () => {
    const res = await fetch('/api/tickets');
    setTickets(await res.json());
  };

  useEffect(() => { fetchTickets(); }, []);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) return Swal.fire('Error', 'File too large', 'error');
      const reader = new FileReader();
      reader.onloadend = () => setAttachment(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/tickets', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, attachment }) 
    });
    Swal.fire('Submitted', 'Ticket created successfully', 'success');
    setForm({ subject: '', message: '' });
    setAttachment(null);
    fetchTickets();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* File Ticket */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-fit">
        <h2 className="text-xl font-bold mb-4">Report an Issue</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
            <Input placeholder="Subject" value={form.subject} onChange={e => setForm({...form, subject: e.target.value})} required />
            <textarea 
                className="w-full p-3 border border-slate-200 rounded-lg h-32 text-sm focus:outline-none focus:ring-2 focus:ring-blue-900/20" 
                placeholder="Describe your issue..." 
                value={form.message} 
                onChange={e => setForm({...form, message: e.target.value})}
                required
            />
            
            {/* Attachment Area */}
            <div className="flex items-center gap-4">
                <label className="cursor-pointer px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 flex items-center gap-2">
                    <Paperclip size={16} /> {attachment ? 'Change File' : 'Attach Proof'}
                    <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
                </label>
                {attachment && (
                    <span className="text-xs text-green-600 flex items-center gap-1">
                        Image Attached <button type="button" onClick={() => setAttachment(null)}><X size={12}/></button>
                    </span>
                )}
            </div>

            <Button type="submit" className="w-full">Submit Ticket</Button>
        </form>
      </div>

      {/* Ticket History */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">My Tickets</h2>
        {tickets.map((t: any) => (
            <div key={t.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                    <h3 className="font-bold text-blue-900">{t.subject}</h3>
                    <Badge variant={t.status === 'resolved' ? 'success' : 'warning'}>{t.status}</Badge>
                </div>
                <p className="text-sm text-slate-600 mb-3 whitespace-pre-wrap">{t.message}</p>
                {t.attachment && (
                    <div className="mb-3">
                        <img src={t.attachment} className="h-20 rounded border border-slate-200" alt="proof" />
                    </div>
                )}
                {t.admin_reply && (
                    <div className="bg-blue-50 p-3 rounded-lg text-sm border border-blue-100 mt-2">
                        <span className="font-bold text-blue-800">Admin Reply:</span> {t.admin_reply}
                    </div>
                )}
                <p className="text-xs text-slate-400 mt-2">{new Date(t.created_at).toLocaleDateString()}</p>
            </div>
        ))}
      </div>
    </div>
  );
}
import os

files = {
    # --- 1. NEW API: USER SEARCH (For Autocomplete) ---
    "app/api/users/search/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const { searchParams } = new URL(request.url);
  const q = searchParams.get('q') || '';

  if (q.length < 2) return NextResponse.json([]);

  // Search users by name or email (exclude self)
  const users = await query(
    'SELECT id, name, email FROM users WHERE (name LIKE ? OR email LIKE ?) AND id != ? LIMIT 5',
    [`%${q}%`, `%${q}%`, session.id]
  );
  
  return NextResponse.json(users);
}
""",

    # --- 2. UPDATE MESSAGES API (Handle Attachments) ---
    "app/api/messages/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'inbox'; 

  let sql = '';
  // Include attachment column
  if (type === 'inbox') {
    sql = `
      SELECT m.*, u.name as sender_name, u.email as sender_email 
      FROM messages m 
      JOIN users u ON m.sender_id = u.id 
      WHERE m.receiver_id = ? 
      ORDER BY m.created_at DESC`;
  } else {
    sql = `
      SELECT m.*, u.name as receiver_name, u.email as receiver_email 
      FROM messages m 
      JOIN users u ON m.receiver_id = u.id 
      WHERE m.sender_id = ? 
      ORDER BY m.created_at DESC`;
  }

  const messages = await query(sql, [session.id]);
  return NextResponse.json(messages);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { to, subject, body, attachment } = await request.json();

  // 'to' is now an array of emails or a single email string
  const emails = Array.isArray(to) ? to : [to];

  for (const email of emails) {
    const receivers: any = await query('SELECT id FROM users WHERE email = ?', [email]);
    if (receivers.length > 0) {
        const receiverId = receivers[0].id;
        
        await query(
            'INSERT INTO messages (sender_id, receiver_id, subject, body, attachment) VALUES (?, ?, ?, ?, ?)',
            [session.id, receiverId, subject, body, attachment || null]
        );

        await query(
            'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
            [receiverId, `New Message: ${subject}`, 'info']
        );
    }
  }

  return NextResponse.json({ success: true });
}
""",

    # --- 3. UPDATE TICKETS API (Handle Attachments) ---
    "app/api/tickets/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let sql = 'SELECT t.*, u.name as user_name, u.email as user_email FROM support_tickets t JOIN users u ON t.user_id = u.id';
  const params = [];

  if (session.role !== 'admin') {
    sql += ' WHERE t.user_id = ?';
    params.push(session.id);
  }
  
  sql += ' ORDER BY t.created_at DESC';

  const tickets = await query(sql, params);
  return NextResponse.json(tickets);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json();

  if (body.action === 'reply' && session.role === 'admin') {
    await query('UPDATE support_tickets SET admin_reply = ?, status = ? WHERE id = ?', 
      [body.reply, 'resolved', body.ticketId]);
    return NextResponse.json({ success: true });
  } else {
    // Insert with attachment
    await query('INSERT INTO support_tickets (user_id, subject, message, attachment) VALUES (?, ?, ?, ?)', 
      [session.id, body.subject, body.message, body.attachment || null]);
    return NextResponse.json({ success: true });
  }
}
""",

    # --- 4. NEW COMPONENT: AUTOCOMPLETE INPUT ---
    "components/ui/EmailInput.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

interface EmailInputProps {
  selected: string[];
  onChange: (emails: string[]) => void;
}

export function EmailInput({ selected, onChange }: EmailInputProps) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<any[]>([]);

  useEffect(() => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = setTimeout(async () => {
      const res = await fetch(`/api/users/search?q=${query}`);
      setSuggestions(await res.json());
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const addEmail = (email: string) => {
    if (!selected.includes(email)) {
      onChange([...selected, email]);
    }
    setQuery('');
    setSuggestions([]);
  };

  const removeEmail = (email: string) => {
    onChange(selected.filter(e => e !== email));
  };

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-2 p-2 border border-slate-300 rounded-lg bg-white focus-within:ring-2 focus-within:ring-blue-900/20">
        {selected.map(email => (
          <span key={email} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs flex items-center gap-1">
            {email}
            <button onClick={() => removeEmail(email)}><X size={12} /></button>
          </span>
        ))}
        <input 
          className="flex-1 outline-none min-w-[120px] text-sm"
          placeholder={selected.length === 0 ? "To: (Type name...)" : ""}
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
      </div>
      
      {suggestions.length > 0 && (
        <div className="absolute z-50 w-full bg-white border border-slate-200 shadow-lg rounded-lg mt-1 max-h-48 overflow-auto">
          {suggestions.map(user => (
            <div 
              key={user.id} 
              className="p-2 hover:bg-slate-50 cursor-pointer flex flex-col"
              onClick={() => addEmail(user.email)}
            >
              <span className="font-medium text-sm text-slate-900">{user.name}</span>
              <span className="text-xs text-slate-500">{user.email}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
""",

    # --- 5. NEW COMPONENT: GMAIL COMPOSE MODAL ---
    "components/mail/ComposeModal.tsx": """
'use client';
import { useState } from 'react';
import { X, Minimize2, Paperclip, Send } from 'lucide-react';
import { EmailInput } from '@/components/ui/EmailInput';
import Swal from 'sweetalert2';

interface ComposeModalProps {
  isOpen: boolean;
  onClose: () => void;
  replyTo?: { email: string; subject: string };
}

export function ComposeModal({ isOpen, onClose, replyTo }: ComposeModalProps) {
  const [to, setTo] = useState<string[]>(replyTo ? [replyTo.email] : []);
  const [subject, setSubject] = useState(replyTo ? `Re: ${replyTo.subject}` : '');
  const [body, setBody] = useState('');
  const [attachment, setAttachment] = useState<string | null>(null);
  const [minimized, setMinimized] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) { // 2MB Limit
        Swal.fire('Error', 'File too large (Max 2MB)', 'error');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => setAttachment(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const send = async () => {
    if (to.length === 0) return Swal.fire('Error', 'Add a recipient', 'warning');
    setLoading(true);
    
    try {
      const res = await fetch('/api/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ to, subject, body, attachment })
      });
      
      if (res.ok) {
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Sent!', timer: 2000, showConfirmButton: false });
        onClose();
        setTo([]); setSubject(''); setBody(''); setAttachment(null);
      }
    } catch (e) {
      Swal.fire('Error', 'Failed to send', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (minimized) {
    return (
      <div className="fixed bottom-0 right-10 w-64 bg-slate-900 text-white p-3 rounded-t-lg shadow-xl cursor-pointer flex justify-between items-center z-50" onClick={() => setMinimized(false)}>
        <span className="font-bold text-sm">Draft: {subject || 'New Message'}</span>
        <div className="flex gap-2">
            <button onClick={(e) => { e.stopPropagation(); onClose(); }}><X size={16} /></button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-0 right-4 md:right-10 w-96 md:w-[32rem] bg-white shadow-2xl rounded-t-xl border border-slate-200 z-50 flex flex-col h-[600px] animate-in slide-in-from-bottom-10">
      {/* Header */}
      <div className="bg-slate-900 text-white p-3 rounded-t-xl flex justify-between items-center shrink-0">
        <h3 className="font-bold text-sm">New Message</h3>
        <div className="flex gap-3 text-slate-300">
          <button onClick={() => setMinimized(true)} className="hover:text-white"><Minimize2 size={16}/></button>
          <button onClick={onClose} className="hover:text-white"><X size={16}/></button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 flex flex-col p-2 gap-2 overflow-y-auto">
        <EmailInput selected={to} onChange={setTo} />
        <input 
          className="w-full p-2 border-b border-slate-100 focus:outline-none text-sm font-medium" 
          placeholder="Subject"
          value={subject}
          onChange={e => setSubject(e.target.value)}
        />
        <textarea 
          className="flex-1 p-2 focus:outline-none resize-none text-sm" 
          placeholder="Type your message..."
          value={body}
          onChange={e => setBody(e.target.value)}
        />
        
        {attachment && (
            <div className="bg-slate-50 p-2 rounded flex justify-between items-center border border-slate-200">
                <span className="text-xs text-slate-500 truncate max-w-[200px]">Attached Image</span>
                <button onClick={() => setAttachment(null)} className="text-red-500"><X size={14}/></button>
            </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-100 flex justify-between items-center bg-slate-50">
        <div className="flex gap-2">
          <label className="cursor-pointer p-2 hover:bg-slate-200 rounded-full text-slate-600 transition">
            <Paperclip size={20} />
            <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
          </label>
        </div>
        <button 
          onClick={send} 
          disabled={loading}
          className="bg-blue-900 text-white px-6 py-2 rounded-full font-bold text-sm shadow-md hover:bg-blue-800 transition flex items-center gap-2"
        >
           {loading ? 'Sending...' : <>Send <Send size={14} /></>}
        </button>
      </div>
    </div>
  );
}
""",

    # --- 6. REFURBISHED MAIL PAGE (Inbox + Detail View) ---
    "app/(dashboard)/messages/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Inbox, Send, Search, Paperclip, Reply, ArrowLeft } from 'lucide-react';
import { ComposeModal } from '@/components/mail/ComposeModal';

export default function MailSystem() {
  const [view, setView] = useState('inbox'); 
  const [messages, setMessages] = useState<any[]>([]);
  const [selectedMsg, setSelectedMsg] = useState<any | null>(null);
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [replyData, setReplyData] = useState<any>(null);

  const fetchMessages = async (type: string) => {
    const res = await fetch(`/api/messages?type=${type}`);
    setMessages(await res.json());
  };

  useEffect(() => { fetchMessages(view); }, [view]);

  const openCompose = (replyTo?: any) => {
    if (replyTo) {
        setReplyData({ 
            email: view === 'inbox' ? replyTo.sender_email : replyTo.receiver_email,
            subject: replyTo.subject 
        });
    } else {
        setReplyData(null);
    }
    setIsComposeOpen(true);
  };

  return (
    <div className="h-[85vh] flex bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
      {/* Sidebar */}
      <div className="w-16 md:w-64 bg-slate-50 border-r border-slate-200 flex flex-col py-4">
        <button 
          onClick={() => openCompose()}
          className="mx-2 md:mx-4 mb-6 bg-white border border-slate-200 hover:shadow-md p-3 md:px-4 md:py-3 rounded-xl flex items-center justify-center md:justify-start gap-3 transition text-slate-700"
        >
          <span className="text-2xl md:text-xl text-red-500">+</span> 
          <span className="hidden md:block font-semibold">Compose</span>
        </button>

        <nav className="space-y-1 px-2">
          <button onClick={() => { setView('inbox'); setSelectedMsg(null); }} className={`w-full flex items-center gap-3 p-3 rounded-lg text-sm font-medium ${view === 'inbox' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-200'}`}>
            <Inbox size={18} /> <span className="hidden md:block">Inbox</span>
          </button>
          <button onClick={() => { setView('sent'); setSelectedMsg(null); }} className={`w-full flex items-center gap-3 p-3 rounded-lg text-sm font-medium ${view === 'sent' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-200'}`}>
            <Send size={18} /> <span className="hidden md:block">Sent</span>
          </button>
        </nav>
      </div>

      {/* Message List or Detail View */}
      <div className="flex-1 flex flex-col min-w-0">
        {!selectedMsg ? (
           // LIST VIEW
           <>
             <div className="h-16 border-b border-slate-200 flex items-center px-6">
                <div className="relative w-full max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input className="w-full bg-slate-100 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none" placeholder="Search mail" />
                </div>
             </div>
             <div className="flex-1 overflow-y-auto">
               {messages.map((msg) => (
                 <div key={msg.id} onClick={() => setSelectedMsg(msg)} className="group px-4 py-3 border-b border-slate-100 hover:bg-slate-50 cursor-pointer flex items-center gap-4 transition">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold shrink-0 ${view === 'inbox' ? 'bg-indigo-500' : 'bg-teal-500'}`}>
                        {(view === 'inbox' ? msg.sender_name : msg.receiver_name)[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-baseline mb-1">
                            <h4 className="font-semibold text-slate-900 truncate">{view === 'inbox' ? msg.sender_name : msg.receiver_name}</h4>
                            <span className="text-xs text-slate-400 shrink-0">{new Date(msg.created_at).toLocaleDateString()}</span>
                        </div>
                        <p className="text-sm text-slate-800 font-medium truncate">{msg.subject}</p>
                        <p className="text-xs text-slate-500 truncate">{msg.body}</p>
                    </div>
                    {msg.attachment && <Paperclip size={16} className="text-slate-400" />}
                 </div>
               ))}
               {messages.length === 0 && <div className="p-10 text-center text-slate-400">Nothing here yet.</div>}
             </div>
           </>
        ) : (
           // DETAIL VIEW
           <div className="flex-1 flex flex-col h-full">
             <div className="h-16 border-b border-slate-200 flex items-center px-4 gap-4">
                <button onClick={() => setSelectedMsg(null)} className="p-2 hover:bg-slate-100 rounded-full"><ArrowLeft size={20} /></button>
                <h3 className="font-bold text-lg truncate flex-1">{selectedMsg.subject}</h3>
             </div>
             <div className="flex-1 p-6 overflow-y-auto">
                <div className="flex justify-between items-center mb-6">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold text-xl">
                            {(view === 'inbox' ? selectedMsg.sender_name : selectedMsg.receiver_name)[0]}
                        </div>
                        <div>
                            <p className="font-bold text-slate-900">{view === 'inbox' ? selectedMsg.sender_name : selectedMsg.receiver_name}</p>
                            <p className="text-xs text-slate-500">&lt;{view === 'inbox' ? selectedMsg.sender_email : selectedMsg.receiver_email}&gt;</p>
                        </div>
                    </div>
                    <span className="text-sm text-slate-500">{new Date(selectedMsg.created_at).toLocaleString()}</span>
                </div>
                
                <div className="prose text-slate-800 whitespace-pre-wrap mb-8 text-sm md:text-base">
                    {selectedMsg.body}
                </div>

                {selectedMsg.attachment && (
                    <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-xl">
                        <p className="text-xs font-bold text-slate-500 uppercase mb-3 flex items-center gap-2">
                            <Paperclip size={14}/> Attachment
                        </p>
                        <img src={selectedMsg.attachment} alt="Attachment" className="max-w-full md:max-w-sm rounded-lg shadow-sm border border-slate-200" />
                    </div>
                )}
             </div>
             <div className="p-4 border-t border-slate-200 bg-slate-50">
                <button 
                  onClick={() => openCompose(selectedMsg)}
                  className="px-6 py-2 border border-slate-300 bg-white rounded-full text-sm font-semibold text-slate-700 hover:bg-slate-100 hover:border-slate-400 transition flex items-center gap-2 w-fit"
                >
                    <Reply size={16} /> Reply
                </button>
             </div>
           </div>
        )}
      </div>

      {/* The Global Compose Modal */}
      <ComposeModal 
        isOpen={isComposeOpen} 
        onClose={() => setIsComposeOpen(false)} 
        replyTo={replyData}
      />
    </div>
  );
}
""",

    # --- 7. UPGRADED CUSTOMER SUPPORT (With Attachment) ---
    "app/(dashboard)/customer/support/page.tsx": """
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
""",

    # --- 8. UPGRADED ADMIN SUPPORT (View Proof) ---
    "app/(dashboard)/admin/support/page.tsx": """
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
"""
}

def mail_upgrade():
    print("📧 Transforming Mail System to Gmail-Style...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n🎉 Mail System Upgraded! Restart your server.")

if __name__ == "__main__":
    mail_upgrade()
import os

files = {
    # --- 1. UPDATED SIDEBAR (Adding Links) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, Settings, LogOut, ShieldCheck, Mail, HelpCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle },
  { name: 'BankMail', href: '/messages', icon: Mail },
];

const customerLinks = [
  { name: 'Overview', href: '/customer', icon: LayoutDashboard },
  { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
  { name: 'History', href: '/customer/history', icon: ShieldCheck },
  { name: 'BankMail', href: '/messages', icon: Mail },
  { name: 'Support', href: '/customer/support', icon: HelpCircle },
];

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const links = userRole === 'admin' ? adminLinks : customerLinks;

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  };

  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col h-full border-r border-slate-800 shadow-xl">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
          <span className="font-bold text-lg text-white">B</span>
        </div>
        <span className="font-bold text-xl tracking-tight text-slate-100">BankSystem</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          {userRole === 'admin' ? 'Admin Menu' : 'Customer Menu'}
        </p>
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <Icon size={18} className={`mr-3 ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`} />
              {link.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800/50">
        <button 
          onClick={handleLogout}
          className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
        >
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
""",

    # --- 2. GMAIL-STYLE INBOX (Shared for Admin & Customer) ---
    "app/(dashboard)/messages/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Mail, Send, Inbox, FileText } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import Swal from 'sweetalert2';

export default function MessagesPage() {
  const [view, setView] = useState('inbox'); // inbox, sent, compose
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Compose State
  const [compose, setCompose] = useState({ to: '', subject: '', body: '' });

  const fetchMessages = async (type: string) => {
    setLoading(true);
    const res = await fetch(`/api/messages?type=${type}`);
    const data = await res.json();
    setMessages(data);
    setLoading(false);
  };

  useEffect(() => {
    if (view !== 'compose') {
        fetchMessages(view);
    }
  }, [view]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/messages', {
        method: 'POST',
        body: JSON.stringify(compose)
    });
    if (res.ok) {
        Swal.fire('Sent!', 'Message sent successfully', 'success');
        setCompose({ to: '', subject: '', body: '' });
        setView('sent');
    } else {
        Swal.fire('Error', 'User not found', 'error');
    }
  };

  return (
    <div className="flex h-[80vh] bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-slate-50 border-r border-slate-200 p-4 flex flex-col gap-2">
        <Button 
            className="w-full justify-start gap-2 mb-4" 
            onClick={() => setView('compose')}
            variant={view === 'compose' ? 'primary' : 'secondary'}
        >
            <FileText size={18} /> Compose
        </Button>
        <button 
            onClick={() => setView('inbox')}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium ${view === 'inbox' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-100'}`}
        >
            <Inbox size={18} /> Inbox
        </button>
        <button 
            onClick={() => setView('sent')}
            className={`flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium ${view === 'sent' ? 'bg-blue-100 text-blue-900' : 'text-slate-600 hover:bg-slate-100'}`}
        >
            <Send size={18} /> Sent
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6 overflow-auto">
        {view === 'compose' ? (
            <div className="max-w-2xl mx-auto">
                <h2 className="text-xl font-bold mb-4">New Message</h2>
                <form onSubmit={handleSend} className="space-y-4">
                    <Input placeholder="To: email@example.com" value={compose.to} onChange={e => setCompose({...compose, to: e.target.value})} required />
                    <Input placeholder="Subject" value={compose.subject} onChange={e => setCompose({...compose, subject: e.target.value})} required />
                    <textarea 
                        className="w-full p-4 border border-slate-200 rounded-lg h-64 focus:ring-2 focus:ring-blue-900 focus:outline-none resize-none"
                        placeholder="Type your message here..."
                        value={compose.body}
                        onChange={e => setCompose({...compose, body: e.target.value})}
                        required
                    ></textarea>
                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="ghost" onClick={() => setView('inbox')}>Discard</Button>
                        <Button type="submit">Send Message</Button>
                    </div>
                </form>
            </div>
        ) : (
            <div>
                <h2 className="text-xl font-bold mb-4 capitalize">{view}</h2>
                <div className="space-y-2">
                    {messages.map((msg: any) => (
                        <div key={msg.id} className="p-4 border border-slate-100 rounded-lg hover:shadow-md transition cursor-pointer bg-white">
                            <div className="flex justify-between mb-1">
                                <span className="font-bold text-slate-800">
                                    {view === 'inbox' ? msg.sender_name : `To: ${msg.receiver_name}`}
                                </span>
                                <span className="text-xs text-slate-500">
                                    {new Date(msg.created_at).toLocaleDateString()}
                                </span>
                            </div>
                            <h3 className="text-sm font-semibold text-blue-900">{msg.subject}</h3>
                            <p className="text-slate-600 text-sm mt-1 truncate">{msg.body}</p>
                        </div>
                    ))}
                    {messages.length === 0 && <p className="text-slate-400 text-center py-10">No messages found.</p>}
                </div>
            </div>
        )}
      </div>
    </div>
  );
}
""",

    # --- 3. CUSTOMER SUPPORT PAGE ---
    "app/(dashboard)/customer/support/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import Swal from 'sweetalert2';

export default function SupportPage() {
  const [tickets, setTickets] = useState([]);
  const [form, setForm] = useState({ subject: '', message: '' });

  const fetchTickets = async () => {
    const res = await fetch('/api/tickets');
    setTickets(await res.json());
  };

  useEffect(() => { fetchTickets(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/tickets', { method: 'POST', body: JSON.stringify(form) });
    Swal.fire('Submitted', 'Ticket created successfully', 'success');
    setForm({ subject: '', message: '' });
    fetchTickets();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* File Ticket */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-fit">
        <h2 className="text-xl font-bold mb-4">Report an Issue</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
            <Input placeholder="Subject (e.g. Name Correction)" value={form.subject} onChange={e => setForm({...form, subject: e.target.value})} required />
            <textarea 
                className="w-full p-3 border border-slate-200 rounded-lg h-32" 
                placeholder="Describe your issue..." 
                value={form.message} 
                onChange={e => setForm({...form, message: e.target.value})}
                required
            />
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
                <p className="text-sm text-slate-600 mb-3">{t.message}</p>
                {t.admin_reply && (
                    <div className="bg-blue-50 p-3 rounded-lg text-sm border border-blue-100">
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

    # --- 4. ADMIN SUPPORT DASHBOARD ---
    "app/(dashboard)/admin/support/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
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
        Swal.fire('Replied', 'Response sent', 'success');
        fetchTickets();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Support Tickets</h2>
      <div className="grid gap-4">
        {tickets.map((t: any) => (
            <div key={t.id} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex justify-between items-start">
                <div>
                    <div className="flex gap-2 items-center mb-1">
                        <h3 className="font-bold text-lg">{t.subject}</h3>
                        <span className="text-sm text-slate-500">by {t.user_email}</span>
                    </div>
                    <p className="text-slate-700 mb-2">{t.message}</p>
                    {t.admin_reply ? (
                         <p className="text-sm text-green-700">✅ Replied: {t.admin_reply}</p>
                    ) : (
                        <Button size="sm" onClick={() => handleReply(t.id)}>Reply & Solve</Button>
                    )}
                </div>
                <Badge variant={t.status === 'resolved' ? 'success' : 'warning'}>{t.status}</Badge>
            </div>
        ))}
      </div>
    </div>
  );
}
""",

    # --- 5. UPDATED ADMIN CUSTOMER TABLE (With Edit/Delete) ---
    "app/(dashboard)/admin/customers/UserActions.tsx": """
'use client';
import { Button } from '@/components/ui/Button';
import { Trash2, Edit } from 'lucide-react';
import Swal from 'sweetalert2';
import { useRouter } from 'next/navigation';

export default function UserActions({ user }: { user: any }) {
  const router = useRouter();

  const handleDelete = async () => {
    const res = await Swal.fire({
        title: 'Delete User?',
        text: 'This will delete all their accounts and history!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, Delete'
    });

    if (res.isConfirmed) {
        await fetch(`/api/admin/users?id=${user.id}`, { method: 'DELETE' });
        router.refresh();
        Swal.fire('Deleted', 'User removed', 'success');
    }
  };

  const handleEdit = async () => {
    const { value: formValues } = await Swal.fire({
        title: 'Edit User',
        html:
            `<input id="swal-input1" class="swal2-input" value="${user.name}">` +
            `<input id="swal-input2" class="swal2-input" value="${user.email}">`,
        focusConfirm: false,
        preConfirm: () => {
            return [
                (document.getElementById('swal-input1') as HTMLInputElement).value,
                (document.getElementById('swal-input2') as HTMLInputElement).value
            ]
        }
    });

    if (formValues) {
        await fetch('/api/admin/users', {
            method: 'PUT',
            body: JSON.stringify({ id: user.id, name: formValues[0], email: formValues[1] })
        });
        router.refresh();
        Swal.fire('Updated', 'User details updated', 'success');
    }
  };

  return (
    <div className="flex gap-2">
        <button onClick={handleEdit} className="text-blue-600 hover:bg-blue-50 p-2 rounded"><Edit size={16}/></button>
        <button onClick={handleDelete} className="text-red-600 hover:bg-red-50 p-2 rounded"><Trash2 size={16}/></button>
    </div>
  );
}
""",

    # --- 6. INJECT ACTIONS INTO TABLE ---
    "app/(dashboard)/admin/customers/page.tsx": """
import { query } from '@/lib/db';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import DepositButton from './DepositButton'; 
import UserActions from './UserActions';

async function getCustomers() {
  return await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
    ORDER BY u.created_at DESC
  `);
}

export default async function CustomersPage() {
  const customers: any = await getCustomers();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800">Customer Management</h2>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Customer</TableHeader>
            <TableHeader>Account Info</TableHeader>
            <TableHeader>Balance</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableHead>
          <tbody>
            {customers.map((user: any) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="font-medium text-slate-900">{user.name}</div>
                  <div className="text-xs text-slate-500">{user.email}</div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-slate-600 bg-slate-100 px-2 py-1 rounded">
                    {user.account_number}
                  </span>
                </TableCell>
                <TableCell className="font-bold text-slate-700">
                  ${Number(user.balance).toLocaleString()}
                </TableCell>
                <TableCell>
                   <div className="flex items-center gap-3">
                     <DepositButton accountId={user.account_id} />
                     <div className="h-4 w-[1px] bg-slate-300"></div>
                     <UserActions user={user} />
                   </div>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );
}
"""
}

def upgrade_frontend():
    print("🎨 Building UI: Gmail Inbox, Support Tickets & Admin Tools...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n🎉 Upgrade Complete! Restart your server.")

if __name__ == "__main__":
    upgrade_frontend()
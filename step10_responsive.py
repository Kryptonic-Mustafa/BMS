import os

files = {
    # --- 1. NEW COMPONENT: MOBILE MENU (Slide-over Sidebar) ---
    "components/layout/MobileMenu.tsx": """
'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut } from 'lucide-react';
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

export function MobileMenu({ userRole }: { userRole: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const links = userRole === 'admin' ? adminLinks : customerLinks;

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  };

  return (
    <div className="md:hidden mr-4">
      {/* Trigger Button */}
      <button onClick={() => setIsOpen(true)} className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg">
        <Menu size={24} />
      </button>

      {/* Overlay & Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* Dark Overlay */}
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setIsOpen(false)}></div>
          
          {/* Sidebar Drawer */}
          <div className="relative bg-slate-900 text-white w-64 h-full shadow-2xl flex flex-col p-4 animate-in slide-in-from-left">
            <div className="flex justify-between items-center mb-8 px-2">
                <span className="font-bold text-xl tracking-tight text-slate-100">BankSystem</span>
                <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
                    <X size={24} />
                </button>
            </div>

            <nav className="flex-1 space-y-1">
                {links.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href;
                return (
                    <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsOpen(false)}
                    className={`flex items-center px-3 py-3 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                        ? 'bg-blue-600 text-white'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                    }`}
                    >
                    <Icon size={18} className="mr-3" />
                    {link.name}
                    </Link>
                );
                })}
            </nav>

            <div className="border-t border-slate-800 pt-4">
                <button 
                onClick={handleLogout}
                className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                >
                <LogOut size={18} className="mr-3" />
                Sign Out
                </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
""",

    # --- 2. UPDATE NAVBAR (Add Mobile Menu Trigger) ---
    "components/layout/Navbar.tsx": """
'use client';
import { Bell, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { MobileMenu } from './MobileMenu';

interface NavbarProps {
  user: { name: string; role: string; };
}

export function Navbar({ user }: NavbarProps) {
  const [hasUnread, setHasUnread] = useState(false);
  const initials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2);

  useEffect(() => {
    const check = async () => {
        try {
            const res = await fetch('/api/notifications');
            const data = await res.json();
            if(Array.isArray(data)) setHasUnread(data.some((n: any) => !n.is_read));
        } catch(e) {}
    };
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 md:px-6 sticky top-0 z-20 shadow-sm">
      <div className="flex items-center">
        {/* Mobile Menu Trigger */}
        <MobileMenu userRole={user.role} />

        {/* Search Bar (Hidden on small mobile) */}
        <div className="hidden md:block relative w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input type="text" placeholder="Search..." className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-900/10 focus:border-blue-900 transition-all" />
        </div>
      </div>

      <div className="flex items-center gap-3 md:gap-4">
        <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell size={20} />
          {hasUnread && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border border-white animate-pulse"></span>
          )}
        </button>
        
        <div className="h-8 w-[1px] bg-slate-200 hidden md:block"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-slate-800">{user.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user.role}</p>
          </div>
          <div className="w-9 h-9 md:w-10 md:h-10 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold border border-blue-200 text-sm md:text-base">
            {initials}
          </div>
        </div>
      </div>
    </header>
  );
}
""",

    # --- 3. UPDATE SIDEBAR (Hide on Mobile) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut } from 'lucide-react';
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
    // HIDDEN ON MOBILE (hidden md:flex)
    <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col h-full border-r border-slate-800 shadow-xl shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
          <span className="font-bold text-lg text-white">B</span>
        </div>
        <span className="font-bold text-xl tracking-tight text-slate-100">BankSystem</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
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

    # --- 4. UPDATE TABLE (Scroll Wrapper) ---
    "components/ui/Table.tsx": """
import React from 'react';

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-slate-200 shadow-sm">
      <div className="overflow-x-auto"> {/* Added Scroll Wrapper */}
        <table className="w-full text-sm text-left text-slate-600 whitespace-nowrap"> {/* Added whitespace-nowrap */}
            {children}
        </table>
      </div>
    </div>
  );
}

export function TableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-50 text-xs uppercase text-slate-500 font-semibold">
      <tr>{children}</tr>
    </thead>
  );
}

export function TableRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <tr className={`border-b border-slate-100 hover:bg-slate-50/50 transition-colors ${className}`}>{children}</tr>;
}

export function TableHeader({ children }: { children: React.ReactNode }) {
  return <th className="px-6 py-4 font-medium">{children}</th>;
}

export function TableCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-6 py-4 ${className}`}>{children}</td>;
}
""",

    # --- 5. UPDATE DASHBOARD LAYOUT (Padding Fixes) ---
    "app/(dashboard)/layout.tsx": """
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';
import { NotificationListener } from '@/components/layout/NotificationListener';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar userRole={session.role} /> 
      
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar user={{ name: session.name, role: session.role }} />
        <NotificationListener /> 
        
        <main className="flex-1 overflow-auto p-4 md:p-8"> {/* Responsive Padding */}
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
""",

    # --- 6. UPDATE COMPOSE MODAL (Full Screen on Mobile) ---
    "components/mail/ComposeModal.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { X, Minimize2, Paperclip, Send } from 'lucide-react';
import { EmailInput } from '@/components/ui/EmailInput';
import Swal from 'sweetalert2';

interface ComposeModalProps {
  isOpen: boolean;
  onClose: () => void;
  replyTo?: { email: string; subject: string; originalBody?: string } | null;
}

export function ComposeModal({ isOpen, onClose, replyTo }: ComposeModalProps) {
  const [to, setTo] = useState<string[]>([]);
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [attachment, setAttachment] = useState<string | null>(null);
  const [minimized, setMinimized] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && replyTo) {
      setTo([replyTo.email]);
      setSubject(replyTo.subject.startsWith('Re:') ? replyTo.subject : `Re: ${replyTo.subject}`);
      setBody(`\\n\\n------ Original Message ------\\nFrom: ${replyTo.email}\\n\\n${replyTo.originalBody?.substring(0, 200)}...`);
    } else if (isOpen && !replyTo) {
      setTo([]); setSubject(''); setBody(''); setAttachment(null);
    }
  }, [isOpen, replyTo]);

  if (!isOpen) return null;

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) { 
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
      }
    } catch (e) {
      Swal.fire('Error', 'Failed to send', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (minimized) {
    return (
      <div className="fixed bottom-0 right-4 md:right-10 w-64 bg-slate-900 text-white p-3 rounded-t-lg shadow-xl cursor-pointer flex justify-between items-center z-50 hover:bg-slate-800 transition" onClick={() => setMinimized(false)}>
        <span className="font-bold text-sm truncate">Draft: {subject || 'New Message'}</span>
        <button onClick={(e) => { e.stopPropagation(); onClose(); }}><X size={16} /></button>
      </div>
    );
  }

  // UPDATED CLASSES: w-full h-full on mobile (inset-0), specific size on desktop
  return (
    <div className="fixed inset-0 md:inset-auto md:bottom-0 md:right-10 z-50 flex flex-col animate-in slide-in-from-bottom-10">
      <div className="w-full h-full md:w-[32rem] md:h-[600px] bg-white shadow-2xl md:rounded-t-xl border border-slate-200 flex flex-col">
        
        {/* Header */}
        <div className="bg-slate-900 text-white p-3 md:rounded-t-xl flex justify-between items-center shrink-0">
          <h3 className="font-bold text-sm">{replyTo ? 'Reply' : 'New Message'}</h3>
          <div className="flex gap-3 text-slate-300">
            <button onClick={() => setMinimized(true)} className="hidden md:block hover:text-white"><Minimize2 size={16}/></button>
            <button onClick={onClose} className="hover:text-white"><X size={20}/></button>
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
            className="flex-1 p-2 focus:outline-none resize-none text-base md:text-sm font-sans" 
            placeholder="Type your message..."
            value={body}
            onChange={e => setBody(e.target.value)}
            autoFocus={!replyTo}
          />
          
          {attachment && (
              <div className="bg-slate-50 p-2 rounded flex justify-between items-center border border-slate-200">
                  <span className="text-xs text-slate-500 truncate max-w-[200px]">Attachment Ready</span>
                  <button onClick={() => setAttachment(null)} className="text-red-500"><X size={14}/></button>
              </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 flex justify-between items-center bg-slate-50 pb-safe">
          <label className="cursor-pointer p-2 hover:bg-slate-200 rounded-full text-slate-600 transition">
            <Paperclip size={24} />
            <input type="file" accept="image/*" className="hidden" onChange={handleFile} />
          </label>
          <button 
            onClick={send} 
            disabled={loading}
            className="bg-blue-900 text-white px-6 py-2 rounded-full font-bold text-sm shadow-md hover:bg-blue-800 transition flex items-center gap-2"
          >
             {loading ? 'Sending...' : <>Send <Send size={16} /></>}
          </button>
        </div>
      </div>
    </div>
  );
}
"""
}

def make_responsive():
    print("📱 Making UI Fully Responsive...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✨ Done! Your Bank System is now Mobile-Ready.")

if __name__ == "__main__":
    make_responsive()
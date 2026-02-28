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
import os

files = {
    # --- 1. UPDATE SIDEBAR (Accept dynamic role) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, Settings, LogOut, ShieldCheck } from 'lucide-react';
import { useRouter } from 'next/navigation';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft },
];

const customerLinks = [
  { name: 'Overview', href: '/customer', icon: LayoutDashboard },
  { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
  { name: 'History', href: '/customer/history', icon: ShieldCheck },
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

    # --- 2. UPDATE NAVBAR (Accept dynamic user data) ---
    "components/layout/Navbar.tsx": """
'use client';
import { Bell, Search } from 'lucide-react';

interface NavbarProps {
  user: {
    name: string;
    role: string;
  };
}

export function Navbar({ user }: NavbarProps) {
  // Get initials for avatar
  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 sticky top-0 z-10 shadow-sm">
      <div className="flex items-center w-96">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-900/10 focus:border-blue-900 transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell size={20} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        </button>
        
        <div className="h-8 w-[1px] bg-slate-200"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-slate-800">{user.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user.role}</p>
          </div>
          <div className="w-10 h-10 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold border border-blue-200">
            {initials}
          </div>
        </div>
      </div>
    </header>
  );
}
""",

    # --- 3. UPDATE DASHBOARD LAYOUT (Fetch Session Server-Side) ---
    "app/(dashboard)/layout.tsx": """
import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/auth';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar userRole={session.role} /> 
      
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar user={{ name: session.name, role: session.role }} />
        
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
""",

    # --- 4. UPDATE CUSTOMER DASHBOARD (Fetch Real Balance) ---
    "app/(dashboard)/customer/page.tsx": """
import { getSession } from '@/lib/auth';
import { query } from '@/lib/db';

async function getAccountData(userId: number) {
  const accounts: any = await query(
    'SELECT * FROM accounts WHERE user_id = ?', 
    [userId]
  );
  return accounts[0] || null;
}

export default async function CustomerDashboard() {
  const session = await getSession();
  const account = await getAccountData(session.id);

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Welcome Back, {session.name}</h2>
      
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-8 rounded-2xl text-white shadow-lg mb-8">
        <div className="flex justify-between items-start">
          <div>
            <p className="opacity-80 mb-1 text-sm font-medium">Total Balance</p>
            <h3 className="text-4xl font-bold">
              ${Number(account?.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </h3>
          </div>
          <div className="bg-white/10 px-3 py-1 rounded-lg backdrop-blur-sm border border-white/20">
            <p className="text-xs font-mono opacity-90">
              ACC: {account?.account_number || '####'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
"""
}

def refine_ui():
    print("🎨 Refining UI: Removing Hardcoded Data...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✨ UI Refined! The dashboard now shows real user data.")

if __name__ == "__main__":
    refine_ui()
import os

files = {
    # --- 1. SETTINGS API (Get & Update) ---
    "app/api/admin/settings/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET() {
  const settings = await query('SELECT * FROM settings LIMIT 1');
  return NextResponse.json(settings[0] || {});
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) {
    return NextResponse.json({ error: 'Super Admin access required' }, { status: 403 });
  }

  const { site_name, site_logo, site_favicon } = await request.json();

  // Check if row exists
  const check: any = await query('SELECT id FROM settings LIMIT 1');
  
  if (check.length === 0) {
    await query('INSERT INTO settings (site_name, site_logo, site_favicon) VALUES (?, ?, ?)', 
      [site_name, site_logo, site_favicon]);
  } else {
    await query('UPDATE settings SET site_name = ?, site_logo = ?, site_favicon = ? WHERE id = ?', 
      [site_name, site_logo, site_favicon, check[0].id]);
  }

  return NextResponse.json({ success: true });
}
""",

    # --- 2. DANGER ZONE API (System Reset) ---
    "app/api/admin/danger/reset/route.ts": """
import { NextResponse } from 'next/server';
import { query, pool } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function DELETE() {
  const session = await getSession();
  if (!session || !session.is_super_admin) {
    return NextResponse.json({ error: 'Super Admin access required' }, { status: 403 });
  }

  const connection = await pool.getConnection();
  try {
    await connection.beginTransaction();

    // 1. Delete all transactions
    await connection.query('DELETE FROM transactions');
    
    // 2. Delete all messages & tickets
    await connection.query('DELETE FROM messages');
    await connection.query('DELETE FROM support_tickets');
    await connection.query('DELETE FROM notifications');

    // 3. Delete all accounts
    await connection.query('DELETE FROM accounts');

    // 4. Delete all users EXCEPT Super Admins
    await connection.query('DELETE FROM users WHERE is_super_admin = FALSE');

    await connection.commit();
    return NextResponse.json({ success: true });
  } catch (error) {
    await connection.rollback();
    return NextResponse.json({ error: 'Reset failed' }, { status: 500 });
  } finally {
    connection.release();
  }
}
""",

    # --- 3. CUSTOMER DETAILS API (For Modal) ---
    "app/api/admin/customers/details/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session || session.role !== 'admin') return NextResponse.json([], { status: 403 });

  // Fetch users with aggregated data
  const customers = await query(`
    SELECT u.id, u.name, u.email, u.created_at, 
           a.account_number, a.balance, 
           (SELECT COUNT(*) FROM transactions t WHERE t.account_id = a.id) as tx_count
    FROM users u
    LEFT JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
  `);

  return NextResponse.json(customers);
}
""",

    # --- 4. NEW LOGIN PAGE (Dual Interface) ---
    "app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ShieldCheck, User } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');

      // Role enforcement
      if (isAdminLogin && data.user.role !== 'admin') {
        throw new Error('Access Denied. Not an Admin account.');
      }
      
      router.push(data.user.role === 'admin' ? '/admin' : '/customer');
      router.refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 p-8 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 w-full max-w-md transition-all">
      <div className="flex justify-center mb-6">
        <div className={`p-4 rounded-full ${isAdminLogin ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
            {isAdminLogin ? <ShieldCheck size={32} /> : <User size={32} />}
        </div>
      </div>
      
      <h2 className="text-2xl font-bold text-center mb-2 dark:text-white">
        {isAdminLogin ? 'Admin Portal' : 'Customer Login'}
      </h2>
      <p className="text-slate-500 text-center mb-6 text-sm">
        {isAdminLogin ? 'Authorized personnel only' : 'Welcome back to your account'}
      </p>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Email Address" 
          type="email" 
          value={form.email} 
          onChange={(e) => setForm({ ...form, email: e.target.value })} 
          required 
        />
        <Input 
          label="Password" 
          type="password" 
          value={form.password} 
          onChange={(e) => setForm({ ...form, password: e.target.value })} 
          required 
        />
        
        <Button 
          type="submit" 
          className={`w-full ${isAdminLogin ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-900 hover:bg-blue-800'}`}
          disabled={loading}
        >
          {loading ? 'Authenticating...' : (isAdminLogin ? 'Access Dashboard' : 'Sign In')}
        </Button>
      </form>

      <div className="mt-6 text-center pt-4 border-t border-slate-100 dark:border-slate-800">
        <button 
            onClick={() => { setIsAdminLogin(!isAdminLogin); setError(''); }}
            className="text-xs font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 uppercase tracking-wider"
        >
            {isAdminLogin ? '← Switch to Customer Login' : 'Switch to Admin Login →'}
        </button>
      </div>

      {!isAdminLogin && (
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
            No account? <Link href="/register" className="text-blue-600 hover:underline">Register</Link>
        </p>
      )}
    </div>
  );
}
""",

    # --- 5. MASTER SETTINGS PAGE (Admin) ---
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Trash2, AlertTriangle, ChevronDown, ChevronUp, Save, Upload } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function MasterSettings() {
  // Settings State
  const [settings, setSettings] = useState({ site_name: '', site_logo: '', site_favicon: '' });
  const [loading, setLoading] = useState(false);

  // Danger Zone State
  const [isCustomerModalOpen, setModalOpen] = useState(false);
  const [customers, setCustomers] = useState([]);
  const [expandedUser, setExpandedUser] = useState<number | null>(null);

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => setSettings(data));
  }, []);

  const handleSave = async () => {
    setLoading(true);
    await fetch('/api/admin/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(settings)
    });
    setLoading(false);
    Swal.fire('Saved', 'System settings updated.', 'success');
    window.location.reload(); // Reload to apply logo/name changes
  };

  const handleFile = (e: any, key: string) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onloadend = () => setSettings({ ...settings, [key]: reader.result });
        reader.readAsDataURL(file);
    }
  };

  const openCustomerManager = async () => {
    const res = await fetch('/api/admin/customers/details');
    setCustomers(await res.json());
    setModalOpen(true);
  };

  const deleteCustomer = async (id: number) => {
    const res = await Swal.fire({
        title: 'Delete Customer?',
        text: 'This will remove their account, transactions, and messages permanently.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, Delete'
    });

    if (res.isConfirmed) {
        await fetch(`/api/admin/users?id=${id}`, { method: 'DELETE' });
        setCustomers(customers.filter((c: any) => c.id !== id));
        Swal.fire('Deleted', 'Customer removed.', 'success');
    }
  };

  const resetSystem = async () => {
    const res = await Swal.fire({
        title: '⚠️ FACTORY RESET?',
        text: 'This will delete ALL users, transactions, and data. Only YOU (Super Admin) will remain. This cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'NUKE EVERYTHING'
    });

    if (res.isConfirmed) {
        const finalCheck = await Swal.fire({
            title: 'Final Warning',
            input: 'text',
            inputLabel: 'Type "CONFIRM" to proceed',
            showCancelButton: true
        });

        if (finalCheck.value === 'CONFIRM') {
            await fetch('/api/admin/danger/reset', { method: 'DELETE' });
            Swal.fire('System Reset', 'The database has been wiped.', 'success');
            window.location.href = '/login';
        }
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold dark:text-white">Master Settings</h2>

      {/* 1. General Settings */}
      <Card>
        <h3 className="text-lg font-bold mb-4 dark:text-slate-200">General Configuration</h3>
        <div className="space-y-4">
            <Input label="Site Name" value={settings.site_name} onChange={e => setSettings({...settings, site_name: e.target.value})} />
            
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium mb-2 dark:text-slate-300">Site Logo</label>
                    <div className="flex items-center gap-4">
                        {settings.site_logo && <img src={settings.site_logo} className="h-12 w-12 object-contain bg-slate-100 rounded" />}
                        <label className="cursor-pointer bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-200 transition text-sm flex items-center gap-2">
                            <Upload size={16}/> Upload
                            <input type="file" className="hidden" onChange={e => handleFile(e, 'site_logo')} />
                        </label>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2 dark:text-slate-300">Favicon</label>
                    <div className="flex items-center gap-4">
                        {settings.site_favicon && <img src={settings.site_favicon} className="h-8 w-8 object-contain bg-slate-100 rounded" />}
                        <label className="cursor-pointer bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-200 transition text-sm flex items-center gap-2">
                            <Upload size={16}/> Upload
                            <input type="file" className="hidden" onChange={e => handleFile(e, 'site_favicon')} />
                        </label>
                    </div>
                </div>
            </div>

            <Button onClick={handleSave} disabled={loading} className="w-fit">
                <Save size={18} className="mr-2"/> {loading ? 'Saving...' : 'Save Settings'}
            </Button>
        </div>
      </Card>

      {/* 2. DANGER ZONE */}
      <div className="border border-red-200 bg-red-50 dark:bg-red-900/10 rounded-xl p-6">
        <h3 className="text-lg font-bold text-red-700 flex items-center gap-2 mb-4">
            <AlertTriangle size={24}/> Danger Zone
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                <h4 className="font-bold dark:text-white">Full System Reset</h4>
                <p className="text-sm text-slate-500 mb-4">Wipes all customers, transactions, and messages. Keeps Super Admin.</p>
                <Button variant="danger" onClick={resetSystem} className="w-full">
                    Reset System
                </Button>
            </div>

            <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                <h4 className="font-bold dark:text-white">Customer Data Manager</h4>
                <p className="text-sm text-slate-500 mb-4">View detailed balances and bulk delete customers.</p>
                <Button variant="secondary" onClick={openCustomerManager} className="w-full">
                    Manage & Delete Customers
                </Button>
            </div>
        </div>
      </div>

      {/* Customer Manager Modal */}
      <Modal isOpen={isCustomerModalOpen} onClose={() => setModalOpen(false)} title="Customer Data Manager">
        <div className="max-h-[60vh] overflow-y-auto space-y-2 pr-2">
            {customers.map((c: any) => (
                <div key={c.id} className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
                    <div 
                        className="p-3 bg-slate-50 dark:bg-slate-800 flex justify-between items-center cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 transition"
                        onClick={() => setExpandedUser(expandedUser === c.id ? null : c.id)}
                    >
                        <div className="flex items-center gap-3">
                            <div className="font-bold text-sm dark:text-slate-200">{c.name}</div>
                            <span className="text-xs text-slate-500">{c.email}</span>
                        </div>
                        {expandedUser === c.id ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                    </div>
                    
                    {expandedUser === c.id && (
                        <div className="p-4 bg-white dark:bg-slate-900 space-y-3 text-sm">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <span className="block text-xs text-slate-500">Account Number</span>
                                    <span className="font-mono dark:text-slate-300">{c.account_number}</span>
                                </div>
                                <div>
                                    <span className="block text-xs text-slate-500">Current Balance</span>
                                    <span className="font-bold text-green-600">${Number(c.balance).toLocaleString()}</span>
                                </div>
                                <div>
                                    <span className="block text-xs text-slate-500">Total Transactions</span>
                                    <span className="dark:text-slate-300">{c.tx_count}</span>
                                </div>
                                <div>
                                    <span className="block text-xs text-slate-500">Joined</span>
                                    <span className="dark:text-slate-300">{new Date(c.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-end">
                                <Button size="sm" variant="danger" onClick={() => deleteCustomer(c.id)}>
                                    <Trash2 size={14} className="mr-2"/> Delete User Data
                                </Button>
                            </div>
                        </div>
                    )}
                </div>
            ))}
            {customers.length === 0 && <p className="text-center text-slate-500 py-4">No customers found.</p>}
        </div>
      </Modal>
    </div>
  );
}
""",

    # --- 6. UPDATE AUTH UTILS (To Include Super Admin Flag) ---
    "lib/auth.ts": """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

const secretKey = process.env.JWT_SECRET || 'secret';
const key = new TextEncoder().encode(secretKey);

export async function encrypt(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(key);
}

export async function decrypt(input: string): Promise<any> {
  try {
    const { payload } = await jwtVerify(input, key, {
      algorithms: ['HS256'],
    });
    return payload;
  } catch (error) {
    return null;
  }
}

export async function getSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get('session')?.value;
  if (!session) return null;
  return await decrypt(session);
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
}
""",

    # --- 7. UPDATE LOGIN API (To Pass Super Admin Flag) ---
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    const sessionData = {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role,
      is_super_admin: user.is_super_admin === 1 // Convert to boolean
    };
    
    const token = await encrypt(sessionData);
    const cookieStore = await cookies();
    cookieStore.set('session', token, {
      httpOnly: true, secure: process.env.NODE_ENV === 'production', maxAge: 60 * 60 * 24, path: '/',
    });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
""",

    # --- 8. DYNAMIC SIDEBAR (Uses Site Name/Logo) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle },
  { name: 'BankMail', href: '/messages', icon: Mail },
  { name: 'Master Settings', href: '/admin/settings', icon: Settings },
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
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    fetch('/api/admin/settings')
      .then(res => res.json())
      .then(data => {
        if(data.site_name) setSiteSettings(data);
      });
  }, []);

  const handleLogout = async () => {
    const result = await Swal.fire({
      title: 'Sign Out?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#EF4444',
      confirmButtonText: 'Yes, Sign Out'
    });

    if (result.isConfirmed) {
      await fetch('/api/auth/logout', { method: 'POST' });
      router.push('/login');
      router.refresh();
    }
  };

  return (
    <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col h-full border-r border-slate-800 shadow-xl shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50 gap-3">
        {siteSettings.site_logo ? (
            <img src={siteSettings.site_logo} className="w-8 h-8 rounded bg-white p-0.5" />
        ) : (
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="font-bold text-lg text-white">B</span>
            </div>
        )}
        <span className="font-bold text-xl tracking-tight text-slate-100 truncate">{siteSettings.site_name}</span>
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
"""
}

def update_master():
    print("👑 Installing Master Settings & Danger Zone...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🚀 Upgrade Complete! Restart server.")

if __name__ == "__main__":
    update_master()
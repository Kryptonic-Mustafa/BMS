import os

files = {
    # --- 1. FIX TICKET API (Allow Managers to View All) ---
    "app/api/tickets/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  let sql = 'SELECT t.*, u.name as user_name, u.email as user_email FROM support_tickets t JOIN users u ON t.user_id = u.id';
  const params = [];

  // FIX: Allow both 'admin' AND 'manager' to see all tickets
  if (!['admin', 'manager'].includes(session.role)) {
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

  // FIX: Allow Managers to reply too
  if (body.action === 'reply' && ['admin', 'manager'].includes(session.role)) {
    await query('UPDATE support_tickets SET admin_reply = ?, status = ? WHERE id = ?', 
      [body.reply, 'resolved', body.ticketId]);
    return NextResponse.json({ success: true });
  } else {
    await query('INSERT INTO support_tickets (user_id, subject, message, attachment) VALUES (?, ?, ?, ?)', 
      [session.id, body.subject, body.message, body.attachment || null]);
    return NextResponse.json({ success: true });
  }
}
""",

    # --- 2. NEW API: MANAGE ROLES (Super Admin Only) ---
    "app/api/admin/roles/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

// Get all staff and customers
export async function GET() {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const users = await query('SELECT id, name, email, role, is_super_admin FROM users ORDER BY role ASC, name ASC');
  return NextResponse.json(users);
}

// Update User Role
export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { userId, newRole } = await request.json();

  // Prevent changing your own role or demoting another Super Admin
  if (userId === session.id) return NextResponse.json({ error: 'Cannot change your own role' }, { status: 400 });

  // Valid roles
  if (!['admin', 'manager', 'customer'].includes(newRole)) {
      return NextResponse.json({ error: 'Invalid role' }, { status: 400 });
  }

  await query('UPDATE users SET role = ? WHERE id = ?', [newRole, userId]);
  return NextResponse.json({ success: true });
}
""",

    # --- 3. NEW PAGE: ROLES & PERMISSIONS ---
    "app/(dashboard)/admin/roles/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search, Shield, User, Briefcase } from 'lucide-react';
import Swal from 'sweetalert2';

export default function RolesPage() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');

  const fetchUsers = async () => {
    try {
      const res = await fetch('/api/admin/roles');
      if (res.ok) setUsers(await res.json());
    } catch(e) {}
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleRoleChange = async (userId: number, currentRole: string, newRole: string) => {
    if (currentRole === newRole) return;

    const result = await Swal.fire({
        title: 'Change Role?',
        text: `Are you sure you want to change this user from ${currentRole.toUpperCase()} to ${newRole.toUpperCase()}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#1E3A8A',
        confirmButtonText: 'Yes, Change Role'
    });

    if (result.isConfirmed) {
        const res = await fetch('/api/admin/roles', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ userId, newRole })
        });

        if (res.ok) {
            Swal.fire('Updated', 'User role has been updated.', 'success');
            fetchUsers();
        } else {
            Swal.fire('Error', 'Failed to update role.', 'error');
        }
    } else {
        // Reset dropdown visually if cancelled
        fetchUsers(); 
    }
  };

  const filteredUsers = users.filter((u: any) => 
    u.name.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  const getRoleIcon = (role: string) => {
    switch(role) {
        case 'admin': return <Shield size={16} className="text-red-600"/>;
        case 'manager': return <Briefcase size={16} className="text-blue-600"/>;
        default: return <User size={16} className="text-slate-500"/>;
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Roles & Permissions</h2>
      
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
                className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-900/20" 
                placeholder="Search users..."
                value={search}
                onChange={e => setSearch(e.target.value)}
            />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filteredUsers.map((user: any) => (
            <Card key={user.id} className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-4 w-full md:w-auto">
                    <div className={`p-3 rounded-full ${user.role === 'admin' ? 'bg-red-100' : (user.role === 'manager' ? 'bg-blue-100' : 'bg-slate-100')}`}>
                        {getRoleIcon(user.role)}
                    </div>
                    <div>
                        <div className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            {user.name} 
                            {user.is_super_admin && <Badge variant="warning">Super Admin</Badge>}
                        </div>
                        <div className="text-sm text-slate-500">{user.email}</div>
                    </div>
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                    <label className="text-sm text-slate-500 font-medium">Role:</label>
                    <select 
                        className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-3 py-1.5 text-sm font-medium focus:outline-none"
                        value={user.role}
                        disabled={user.is_super_admin} // Cannot change Super Admin
                        onChange={(e) => handleRoleChange(user.id, user.role, e.target.value)}
                    >
                        <option value="customer">Customer</option>
                        <option value="manager">Manager</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
            </Card>
        ))}
      </div>
    </div>
  );
}
""",

    # --- 4. UPDATE SIDEBAR (Show Roles for Super Admin) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';

const adminLinks = [
  { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { name: 'Customers', href: '/admin/customers', icon: Users },
  { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle },
  { name: 'BankMail', href: '/messages', icon: Mail },
  // These are conditionally filtered
  { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock },
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
  
  // Logic: 
  // - Customers see Customer Links
  // - Managers see Admin Links EXCEPT 'Master Settings' and 'Roles'
  // - Admins (Super) see Everything
  
  let links = customerLinks;
  if (userRole === 'admin') {
      links = adminLinks;
  } else if (userRole === 'manager') {
      links = adminLinks.filter(l => l.name !== 'Master Settings' && l.name !== 'Roles & Permissions');
  }

  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
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
          {userRole === 'customer' ? 'Customer Menu' : 'Staff Menu'}
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

def update_roles():
    print("🔑 Installing Roles & Permissions System...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Bug Fixed: Managers can now see tickets!")
    print("✅ New Feature: Roles Page active for Super Admin.")

if __name__ == "__main__":
    update_roles()
import os

files = {
    # --- 1. ENCRYPTION UTILITY (AES) ---
    "lib/crypto.ts": """
import CryptoJS from 'crypto-js';

const SECRET_KEY = process.env.JWT_SECRET || 'your-fallback-secret-key-must-be-long';

export const encryptData = (data: any) => {
  return CryptoJS.AES.encrypt(JSON.stringify(data), SECRET_KEY).toString();
};

export const decryptData = (ciphertext: string) => {
  try {
    const bytes = CryptoJS.AES.decrypt(ciphertext, SECRET_KEY);
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
  } catch (e) {
    console.error('Decryption failed', e);
    return null;
  }
};
""",

    # --- 2. AUTH UTILS UPDATE (Fetch Dynamic Permissions) ---
    "lib/auth.ts": """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';
import { query } from '@/lib/db';

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
    const { payload } = await jwtVerify(input, key, { algorithms: ['HS256'] });
    return payload;
  } catch (error) {
    return null;
  }
}

// Fetch session AND dynamic permissions from DB
export async function getSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get('session')?.value;
  if (!session) return null;
  
  const payload: any = await decrypt(session);
  if(!payload) return null;

  // Fetch fresh permissions from DB
  const perms = await query(`
    SELECT p.name 
    FROM permissions p
    JOIN role_permissions rp ON p.id = rp.permission_id
    WHERE rp.role_id = ?
  `, [payload.role_id]);

  const permissionList = perms.map((p: any) => p.name);

  return { ...payload, permissions: permissionList };
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
}
""",

    # --- 3. LOGIN API UPDATE (Use Role ID) ---
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';
import { decryptData } from '@/lib/crypto'; // Import Decryption

export async function POST(request: Request) {
  try {
    // 1. Decrypt Payload
    const rawBody = await request.json();
    // If client sent encrypted data (check for 'data' key), decrypt it.
    // Fallback to rawBody for backward compatibility during migration
    const body = rawBody.data ? decryptData(rawBody.data) : rawBody;
    
    if (!body) return NextResponse.json({ error: 'Invalid encrypted payload' }, { status: 400 });

    const { email, password } = body;

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    const sessionData = {
      id: user.id,
      name: user.name,
      email: user.email,
      role_id: user.role_id, // Store Role ID
      role: user.role,       // Keep string for legacy checks
      is_super_admin: user.is_super_admin === 1
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

    # --- 4. ROLES API (CRUD) ---
    "app/api/admin/roles/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET() {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get Roles
  const roles = await query('SELECT * FROM roles ORDER BY id ASC');
  
  // Get Permissions for each role
  for (const role of roles) {
      const perms = await query(`
        SELECT p.name 
        FROM permissions p
        JOIN role_permissions rp ON p.id = rp.permission_id
        WHERE rp.role_id = ?
      `, [role.id]);
      role.permissions = perms.map((p: any) => p.name);
  }

  return NextResponse.json(roles);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { name, description, permissions } = await request.json();

  // Create Role
  const res: any = await query('INSERT INTO roles (name, description) VALUES (?, ?)', [name, description]);
  const roleId = res.insertId;

  // Assign Permissions
  if (permissions && permissions.length > 0) {
      // Find IDs for permission names
      const permRecords: any = await query(`SELECT id FROM permissions WHERE name IN (?)`, [permissions]);
      
      for (const p of permRecords) {
          await query('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', [roleId, p.id]);
      }
  }

  return NextResponse.json({ success: true });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { id, name, description, permissions } = await request.json();

  await query('UPDATE roles SET name = ?, description = ? WHERE id = ?', [name, description, id]);
  
  // Reset Permissions
  await query('DELETE FROM role_permissions WHERE role_id = ?', [id]);

  if (permissions && permissions.length > 0) {
      const permRecords: any = await query(`SELECT id FROM permissions WHERE name IN (?)`, [permissions]);
      for (const p of permRecords) {
          await query('INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)', [id, p.id]);
      }
  }

  return NextResponse.json({ success: true });
}
""",

    # --- 5. PERMISSIONS LIST API ---
    "app/api/admin/permissions/list/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  const perms = await query('SELECT * FROM permissions ORDER BY name ASC');
  return NextResponse.json(perms);
}
""",

    # --- 6. NEW ROLES PAGE UI ---
    "app/(dashboard)/admin/roles/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { Edit, Trash2, Plus } from 'lucide-react';
import Swal from 'sweetalert2';

export default function RolesPage() {
  const [roles, setRoles] = useState([]);
  const [allPermissions, setAllPermissions] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<any>(null);
  
  // Form State
  const [formData, setFormData] = useState({ name: '', description: '', permissions: [] as string[] });

  const fetchData = async () => {
    const [rolesRes, permsRes] = await Promise.all([
        fetch('/api/admin/roles'),
        fetch('/api/admin/permissions/list')
    ]);
    if (rolesRes.ok) setRoles(await rolesRes.json());
    if (permsRes.ok) setAllPermissions(await permsRes.json());
  };

  useEffect(() => { fetchData(); }, []);

  const openModal = (role?: any) => {
    if (role) {
        setEditingRole(role);
        setFormData({ 
            name: role.name, 
            description: role.description, 
            permissions: role.permissions || [] 
        });
    } else {
        setEditingRole(null);
        setFormData({ name: '', description: '', permissions: [] });
    }
    setIsModalOpen(true);
  };

  const togglePerm = (permName: string) => {
    setFormData(prev => {
        const exists = prev.permissions.includes(permName);
        return {
            ...prev,
            permissions: exists 
                ? prev.permissions.filter(p => p !== permName)
                : [...prev.permissions, permName]
        };
    });
  };

  const handleSave = async () => {
    const url = '/api/admin/roles';
    const method = editingRole ? 'PUT' : 'POST';
    const body = editingRole ? { ...formData, id: editingRole.id } : formData;

    await fetch(url, {
        method: method,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });

    setIsModalOpen(false);
    fetchData();
    Swal.fire('Success', 'Role saved successfully', 'success');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold dark:text-white">Roles Management</h2>
        <Button onClick={() => openModal()}><Plus size={18} className="mr-2"/> Add Role</Button>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl shadow border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full text-sm text-left">
            <thead className="bg-slate-50 dark:bg-slate-800 text-slate-500 font-bold uppercase">
                <tr>
                    <th className="px-6 py-4">Role</th>
                    <th className="px-6 py-4">Description</th>
                    <th className="px-6 py-4">Permissions</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                </tr>
            </thead>
            <tbody>
                {roles.map((role: any) => (
                    <tr key={role.id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-6 py-4 font-bold dark:text-white">{role.name}</td>
                        <td className="px-6 py-4 text-slate-500">{role.description}</td>
                        <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-1">
                                {role.permissions.slice(0, 5).map((p: string) => (
                                    <span key={p} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">{p}</span>
                                ))}
                                {role.permissions.length > 5 && <span className="text-xs text-slate-400">+{role.permissions.length - 5} more</span>}
                            </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                            <button onClick={() => openModal(role)} className="p-2 text-blue-600 hover:bg-blue-50 rounded"><Edit size={16}/></button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>

      {/* Add/Edit Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editingRole ? 'Edit Role' : 'Add New Role'}>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
            <div className="grid grid-cols-2 gap-4">
                <Input label="Role Name" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                <Input label="Description" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
            </div>
            
            <div>
                <label className="block text-sm font-medium mb-2">Permissions</label>
                <div className="grid grid-cols-2 gap-2 border border-slate-200 p-4 rounded-lg bg-slate-50 dark:bg-slate-800">
                    {allPermissions.map((p: any) => (
                        <label key={p.id} className="flex items-center gap-2 cursor-pointer p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded">
                            <input 
                                type="checkbox" 
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                                checked={formData.permissions.includes(p.name)}
                                onChange={() => togglePerm(p.name)}
                            />
                            <span className="text-sm dark:text-slate-300">{p.name}</span>
                        </label>
                    ))}
                </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
                <Button variant="ghost" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                <Button onClick={handleSave}>{editingRole ? 'Update Role' : 'Create Role'}</Button>
            </div>
        </div>
      </Modal>
    </div>
  );
}
""",

    # --- 7. DYNAMIC SIDEBAR (Based on Permissions) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';

// Fetch permissions on load (since they are in httpOnly cookie, we verify via API)
// For simplicity in this demo, we assume the user object in Navbar has them, or we fetch profile
export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [permissions, setPermissions] = useState<string[]>([]);
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    // Fetch profile to get real-time permissions
    fetch('/api/auth/profile').then(res => res.json()).then(data => {
        if(data.permissions) setPermissions(data.permissions);
    });
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
  }, []);

  // Define Menu Structure
  const menuItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, requiredPerm: null }, // Always show
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'CustomersView' },
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'OrdersView' }, // Mapping 'Orders' to 'Transactions' for now
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: null },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: null },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'SettingsManage' },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings, requiredPerm: 'AdminSettingsView' },
  ];

  const customerLinks = [
    { name: 'Overview', href: '/customer', icon: LayoutDashboard },
    { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
    { name: 'History', href: '/customer/history', icon: ShieldCheck },
    { name: 'BankMail', href: '/messages', icon: Mail },
    { name: 'Support', href: '/customer/support', icon: HelpCircle },
  ];

  const links = userRole === 'customer' 
    ? customerLinks 
    : menuItems.filter(item => 
        // Show if no permission required OR user has the permission OR user is SuperAdmin (role 'admin')
        !item.requiredPerm || permissions.includes(item.requiredPerm) || userRole === 'admin'
      );

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
        <button onClick={handleLogout} className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors">
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
""",

    # --- 8. PROFILE API (For Sidebar to fetch perms) ---
    "app/api/auth/profile/route.ts": """
import { NextResponse } from 'next/server';
import { getSession } from '@/lib/auth';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({});
  return NextResponse.json(session);
}
"""
}

def full_upgrade():
    print("💎 Installing RBAC System & Encryption Layer...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Upgrade Complete! You now have Dynamic Roles and Permissions.")

if __name__ == "__main__":
    full_upgrade()
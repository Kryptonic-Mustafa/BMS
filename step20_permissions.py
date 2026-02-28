import os

files = {
    # --- 1. NEW API: MANAGE PERMISSIONS ---
    "app/api/admin/permissions/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

export async function GET() {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  // Get only Manager permissions for now (Admins have full access by default)
  const perms = await query("SELECT * FROM permissions WHERE role = 'manager'");
  return NextResponse.json(perms);
}

export async function POST(request: Request) {
  const session = await getSession();
  if (!session || !session.is_super_admin) return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const { resource, action, is_allowed } = await request.json();

  // Upsert Permission
  await query(
    `INSERT INTO permissions (role, resource, action, is_allowed) 
     VALUES ('manager', ?, ?, ?) 
     ON DUPLICATE KEY UPDATE is_allowed = ?`,
    [resource, action, is_allowed, is_allowed]
  );

  return NextResponse.json({ success: true });
}
""",

    # --- 2. UPDATE USER API (Enforce Permissions on Delete/Edit) ---
    "app/api/admin/users/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';

// Helper to check permission
async function checkPermission(role: string, resource: string, action: string) {
  if (role === 'admin') return true; // Admins can do everything
  
  const rows: any = await query(
    "SELECT is_allowed FROM permissions WHERE role = ? AND resource = ? AND action = ?", 
    [role, resource, action]
  );
  
  return rows.length > 0 && rows[0].is_allowed === 1;
}

// DELETE USER
export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // SECURITY CHECK
  const canDelete = await checkPermission(session.role, 'customers', 'delete');
  if (!canDelete) {
      return NextResponse.json({ error: 'Permission Denied: You cannot delete customers.' }, { status: 403 });
  }

  const { searchParams } = new URL(request.url);
  const id = searchParams.get('id');

  if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

  await query('DELETE FROM users WHERE id = ?', [id]);
  return NextResponse.json({ success: true });
}

// EDIT USER
export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  // SECURITY CHECK
  const canEdit = await checkPermission(session.role, 'customers', 'edit');
  if (!canEdit) {
      return NextResponse.json({ error: 'Permission Denied: You cannot edit customers.' }, { status: 403 });
  }

  const body = await request.json();
  const { id, name, email } = body;

  await query('UPDATE users SET name = ?, email = ? WHERE id = ?', [name, email, id]);
  return NextResponse.json({ success: true });
}
""",

    # --- 3. UPGRADED ROLES PAGE (With Permissions Matrix) ---
    "app/(dashboard)/admin/roles/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search, Shield, User, Briefcase, Lock, Check, X } from 'lucide-react';
import Swal from 'sweetalert2';

export default function RolesPage() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [permissions, setPermissions] = useState<any[]>([]);

  const fetchData = async () => {
    const [usersRes, permsRes] = await Promise.all([
        fetch('/api/admin/roles'),
        fetch('/api/admin/permissions')
    ]);
    if (usersRes.ok) setUsers(await usersRes.json());
    if (permsRes.ok) setPermissions(await permsRes.json());
  };

  useEffect(() => { fetchData(); }, []);

  // --- ROLE ASSIGNMENT LOGIC ---
  const handleRoleChange = async (userId: number, currentRole: string, newRole: string) => {
    if (currentRole === newRole) return;

    const result = await Swal.fire({
        title: 'Change Role?',
        text: `Change this user from ${currentRole.toUpperCase()} to ${newRole.toUpperCase()}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#1E3A8A',
        confirmButtonText: 'Yes, Confirm'
    });

    if (result.isConfirmed) {
        await fetch('/api/admin/roles', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ userId, newRole })
        });
        Swal.fire('Success', 'Role updated', 'success');
        fetchData();
    } else {
        fetchData(); // Reset UI
    }
  };

  // --- PERMISSION TOGGLE LOGIC ---
  const togglePermission = async (resource: string, action: string, currentValue: boolean) => {
    // Optimistic UI Update
    const updatedPerms = permissions.map(p => 
        (p.resource === resource && p.action === action) ? { ...p, is_allowed: !currentValue } : p
    );
    setPermissions(updatedPerms);

    await fetch('/api/admin/permissions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ resource, action, is_allowed: !currentValue })
    });
  };

  const getPerm = (resource: string, action: string) => {
    const p = permissions.find(p => p.resource === resource && p.action === action);
    return p ? !!p.is_allowed : false; // Default false if missing
  };

  const filteredUsers = users.filter((u: any) => 
    u.name.toLowerCase().includes(search.toLowerCase()) || 
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      
      {/* 1. PERMISSIONS MATRIX (Manager Only for now) */}
      <Card>
        <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-2">
            <Lock className="text-blue-900" size={20}/>
            <h3 className="text-lg font-bold">Manager Permissions Configuration</h3>
        </div>
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
                <thead className="bg-slate-50 text-slate-500 uppercase text-xs">
                    <tr>
                        <th className="px-4 py-3">Resource</th>
                        <th className="px-4 py-3 text-center">Can View</th>
                        <th className="px-4 py-3 text-center">Can Edit</th>
                        <th className="px-4 py-3 text-center">Can Delete</th>
                    </tr>
                </thead>
                <tbody>
                    <tr className="border-b border-slate-100">
                        <td className="px-4 py-3 font-medium">Customer Data</td>
                        <td className="px-4 py-3 text-center"><Badge variant="success">Always Yes</Badge></td>
                        <td className="px-4 py-3 text-center">
                            <button onClick={() => togglePermission('customers', 'edit', getPerm('customers', 'edit'))}>
                                {getPerm('customers', 'edit') ? <Check className="mx-auto text-green-600"/> : <X className="mx-auto text-red-400"/>}
                            </button>
                        </td>
                        <td className="px-4 py-3 text-center">
                            <button onClick={() => togglePermission('customers', 'delete', getPerm('customers', 'delete'))}>
                                {getPerm('customers', 'delete') ? <Check className="mx-auto text-green-600"/> : <X className="mx-auto text-red-400"/>}
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
            <p className="text-xs text-slate-400 mt-2">* Click icons to toggle permissions. Admins have full access by default.</p>
        </div>
      </Card>

      {/* 2. USER ROLE ASSIGNMENT */}
      <div>
        <h2 className="text-xl font-bold mb-4">User Role Assignment</h2>
        <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input className="w-full pl-10 pr-4 py-2 border rounded-lg" placeholder="Search users..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <div className="grid grid-cols-1 gap-4">
            {filteredUsers.map((user: any) => (
                <Card key={user.id} className="flex flex-col md:flex-row justify-between items-center gap-4 py-4">
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <div className={`p-3 rounded-full ${user.role === 'admin' ? 'bg-red-100 text-red-600' : (user.role === 'manager' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100')}`}>
                            {user.role === 'admin' ? <Shield size={20}/> : (user.role === 'manager' ? <Briefcase size={20}/> : <User size={20}/>)}
                        </div>
                        <div>
                            <div className="font-bold text-slate-900 flex items-center gap-2">
                                {user.name} 
                                {user.is_super_admin && <Badge variant="warning">Super Admin</Badge>}
                            </div>
                            <div className="text-sm text-slate-500">{user.email}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                        <span className="text-sm font-medium text-slate-500">Current Role:</span>
                        <select 
                            className="bg-slate-50 border border-slate-200 rounded px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={user.role}
                            disabled={user.is_super_admin}
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
    </div>
  );
}
""",

    # --- 4. UPDATE CUSTOMER PAGE (Pass Permissions to Client) ---
    "app/(dashboard)/admin/customers/page.tsx": """
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import DepositButton from './DepositButton'; 
import UserActions from './UserActions';
import { Pagination } from '@/components/ui/Pagination';

// Fetch perms for the current user
async function getMyPermissions(role: string) {
  if (role === 'admin') return { canEdit: true, canDelete: true }; // Admin override
  
  const perms: any = await query("SELECT resource, action, is_allowed FROM permissions WHERE role = ?", [role]);
  
  const check = (act: string) => perms.some((p: any) => p.resource === 'customers' && p.action === act && p.is_allowed === 1);
  
  return {
    canEdit: check('edit'),
    canDelete: check('delete')
  };
}

async function getCustomers(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  const customers: any = await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
    ORDER BY u.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  const count: any = await query('SELECT COUNT(*) as total FROM users WHERE role = "customer"');
  return { data: customers, totalPages: Math.ceil(count[0].total / limit) };
}

export default async function CustomersPage({ searchParams }: { searchParams: { page?: string } }) {
  const session = await getSession();
  const page = Number(searchParams.page) || 1;
  const { data: customers, totalPages } = await getCustomers(page);
  
  // Get Permissions
  const permissions = await getMyPermissions(session.role);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Customer Management</h2>
      </div>

      <div className="hidden md:block bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
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
                  <div className="font-medium text-slate-900 dark:text-white">{user.name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{user.email}</div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {user.account_number}
                  </span>
                </TableCell>
                <TableCell className="font-bold text-slate-700 dark:text-slate-200">
                  ${Number(user.balance).toLocaleString()}
                </TableCell>
                <TableCell>
                   <div className="flex items-center gap-3">
                     <DepositButton accountId={user.account_id} />
                     {(permissions.canEdit || permissions.canDelete) && (
                        <>
                            <div className="h-4 w-[1px] bg-slate-300 dark:bg-slate-700"></div>
                            <UserActions user={user} permissions={permissions} />
                        </>
                     )}
                   </div>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </div>

      <Pagination totalPages={totalPages} />
    </div>
  );
}
""",

    # --- 5. UPDATE ACTIONS COMPONENT (Hide Buttons Visually) ---
    "app/(dashboard)/admin/customers/UserActions.tsx": """
'use client';
import { Button } from '@/components/ui/Button';
import { Trash2, Edit } from 'lucide-react';
import Swal from 'sweetalert2';
import { useRouter } from 'next/navigation';

interface Props {
    user: any;
    permissions: { canEdit: boolean; canDelete: boolean };
}

export default function UserActions({ user, permissions }: Props) {
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
        const apiRes = await fetch(`/api/admin/users?id=${user.id}`, { method: 'DELETE' });
        
        if (apiRes.ok) {
            router.refresh();
            Swal.fire('Deleted', 'User removed', 'success');
        } else {
            const data = await apiRes.json();
            Swal.fire('Permission Denied', data.error, 'error');
        }
    }
  };

  const handleEdit = async () => {
    const { value: formValues } = await Swal.fire({
        title: 'Edit User',
        html:
            `<input id="swal-input1" class="swal2-input" value="${user.name}">` +
            `<input id="swal-input2" class="swal2-input" value="${user.email}">`,
        focusConfirm: false,
        preConfirm: () => [
            (document.getElementById('swal-input1') as HTMLInputElement).value,
            (document.getElementById('swal-input2') as HTMLInputElement).value
        ]
    });

    if (formValues) {
        const apiRes = await fetch('/api/admin/users', {
            method: 'PUT',
            body: JSON.stringify({ id: user.id, name: formValues[0], email: formValues[1] })
        });
        
        if (apiRes.ok) {
            router.refresh();
            Swal.fire('Updated', 'User details updated', 'success');
        } else {
            const data = await apiRes.json();
            Swal.fire('Permission Denied', data.error, 'error');
        }
    }
  };

  return (
    <div className="flex gap-2">
        {permissions.canEdit && (
            <button onClick={handleEdit} className="text-blue-600 hover:bg-blue-50 p-2 rounded" title="Edit">
                <Edit size={16}/>
            </button>
        )}
        {permissions.canDelete && (
            <button onClick={handleDelete} className="text-red-600 hover:bg-red-50 p-2 rounded" title="Delete">
                <Trash2 size={16}/>
            </button>
        )}
    </div>
  );
}
"""
}

def install_permissions():
    print("🛡️ Installing Dynamic Permissions System...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✅ Permissions Matrix Live! Super Admins can now control Manager access.")

if __name__ == "__main__":
    install_permissions()
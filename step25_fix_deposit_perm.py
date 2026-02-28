import os

files = {
    "app/(dashboard)/admin/customers/page.tsx": """
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import DepositButton from './DepositButton'; 
import UserActions from './UserActions';
import { Pagination } from '@/components/ui/Pagination';

async function getCustomers(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  const customers: any = await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role_id = 3
    ORDER BY u.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  const count: any = await query('SELECT COUNT(*) as total FROM users WHERE role_id = 3');
  return { data: customers, totalPages: Math.ceil(count[0].total / limit) };
}

export default async function CustomersPage({ searchParams }: { searchParams: { page?: string } }) {
  const session = await getSession();
  const page = Number(searchParams.page) || 1;
  const { data: customers, totalPages } = await getCustomers(page);
  
  // --- 1. PERMISSION CHECKS ---
  const perms = session?.permissions || [];
  const isAdmin = session?.role === 'admin'; // Super Admin

  const canDeposit = isAdmin || perms.includes('AccountsDeposit');
  const canEdit = isAdmin || perms.includes('CustomersEdit');
  const canDelete = isAdmin || perms.includes('CustomersDelete');

  // --- 2. CALCULATE COLUMN VISIBILITY ---
  // Only show the "Actions" column if the user can do AT LEAST one action
  const showActionsColumn = canDeposit || canEdit || canDelete;

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
            {/* CONDITIONAL HEADER */}
            {showActionsColumn && <TableHeader>Actions</TableHeader>}
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
                
                {/* CONDITIONAL BODY CELL */}
                {showActionsColumn && (
                    <TableCell>
                    <div className="flex items-center gap-3">
                        {/* Only show Deposit Button if allowed */}
                        {canDeposit && <DepositButton accountId={user.account_id} />}
                        
                        {/* Divider if both groups exist */}
                        {canDeposit && (canEdit || canDelete) && (
                            <div className="h-4 w-[1px] bg-slate-300 dark:bg-slate-700"></div>
                        )}

                        {/* Edit/Delete Actions */}
                        {(canEdit || canDelete) && (
                            <UserActions user={user} permissions={{ canEdit, canDelete }} />
                        )}
                    </div>
                    </TableCell>
                )}
              </TableRow>
            ))}
          </tbody>
        </Table>
      </div>

      <Pagination totalPages={totalPages} />
    </div>
  );
}
"""
}

def fix_deposit_ui():
    print("🔒 Securing Deposit Button & Hiding Empty Columns...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_deposit_ui()
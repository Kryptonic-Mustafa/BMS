import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import DepositButton from './DepositButton'; 
import UserActions from './UserActions';
import { Pagination } from '@/components/ui/Pagination';

async function getCustomers(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  // 1. Fetch Data
  const customers: any = await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role_id = 3
    ORDER BY u.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  // 2. Fetch Total Count
  const count: any = await query('SELECT COUNT(*) as total FROM users WHERE role_id = 3');
  const total = count[0].total;
  
  return { 
    data: customers, 
    totalPages: Math.ceil(total / limit),
    totalRecords: total 
  };
}

export default async function CustomersPage({ searchParams }: { searchParams: { page?: string } }) {
  const session = await getSession();
  const page = Number(searchParams.page) || 1;
  const limit = 10;
  const { data: customers, totalPages, totalRecords } = await getCustomers(page, limit);
  
  // --- Permission Logic ---
  const perms = session?.permissions || [];
  const isAdmin = session?.role === 'admin';
  const canDeposit = isAdmin || perms.includes('AccountsDeposit');
  const canEdit = isAdmin || perms.includes('CustomersEdit');
  const canDelete = isAdmin || perms.includes('CustomersDelete');
  const showActionsColumn = canDeposit || canEdit || canDelete;

  // --- Pagination Text Logic ---
  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, totalRecords);

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
                {showActionsColumn && (
                    <TableCell>
                    <div className="flex items-center gap-3">
                        {canDeposit && <DepositButton accountId={user.account_id} />}
                        {canDeposit && (canEdit || canDelete) && (
                            <div className="h-4 w-[1px] bg-slate-300 dark:bg-slate-700"></div>
                        )}
                        {(canEdit || canDelete) && (
                            <UserActions user={user} permissions={{ canEdit, canDelete }} />
                        )}
                    </div>
                    </TableCell>
                )}
              </TableRow>
            ))}
            {customers.length === 0 && (
                <tr><td colSpan={4} className="p-8 text-center text-slate-500">No customers found.</td></tr>
            )}
          </tbody>
        </Table>
      </div>

      {/* FOOTER: Showing X of Y + Pagination */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4 pt-2">
        <p className="text-sm text-slate-500 dark:text-slate-400">
            Showing <span className="font-bold text-slate-800 dark:text-white">{totalRecords > 0 ? start : 0}-{end}</span> of <span className="font-bold text-slate-800 dark:text-white">{totalRecords}</span> results
        </p>
        <Pagination totalPages={totalPages} />
      </div>
    </div>
  );
}
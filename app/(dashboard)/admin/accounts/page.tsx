import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';

async function getAccounts(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  const accounts: any = await query(`
    SELECT a.id, a.account_number, a.balance, a.status, a.type, u.name, u.email
    FROM accounts a
    JOIN users u ON a.user_id = u.id
    ORDER BY a.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  const count: any = await query('SELECT COUNT(*) as total FROM accounts');
  const total = count[0].total;

  return { 
    data: accounts, 
    totalPages: Math.ceil(total / limit),
    totalRecords: total
  };
}

export default async function AccountsPage({ searchParams }: { searchParams: { page?: string } }) {
  await getSession();
  const page = Number(searchParams.page) || 1;
  const limit = 10;
  const { data: accounts, totalPages, totalRecords } = await getAccounts(page, limit);

  // Pagination Text
  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, totalRecords);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">All Bank Accounts</h2>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Account Number</TableHeader>
            <TableHeader>Owner</TableHeader>
            <TableHeader>Type</TableHeader>
            <TableHeader>Status</TableHeader>
            <TableHeader>Balance</TableHeader>
          </TableHead>
          <tbody>
            {accounts.map((acc: any) => (
              <TableRow key={acc.id}>
                <TableCell>
                  <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-slate-700 dark:text-slate-300">
                    {acc.account_number}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="font-medium text-slate-900 dark:text-white">{acc.name}</div>
                  <div className="text-xs text-slate-500">{acc.email}</div>
                </TableCell>
                <TableCell className="capitalize text-slate-600 dark:text-slate-400">{acc.type}</TableCell>
                <TableCell>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    acc.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {acc.status.toUpperCase()}
                  </span>
                </TableCell>
                <TableCell className="font-bold text-slate-700 dark:text-slate-200">
                  ${Number(acc.balance).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
            {accounts.length === 0 && (
                <tr><td colSpan={5} className="p-8 text-center text-slate-500">No accounts found.</td></tr>
            )}
          </tbody>
        </Table>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-center gap-4 pt-2">
        <p className="text-sm text-slate-500 dark:text-slate-400">
            Showing <span className="font-bold text-slate-800 dark:text-white">{totalRecords > 0 ? start : 0}-{end}</span> of <span className="font-bold text-slate-800 dark:text-white">{totalRecords}</span> results
        </p>
        <Pagination totalPages={totalPages} />
      </div>
    </div>
  );
}
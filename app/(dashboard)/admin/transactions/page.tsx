import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Pagination } from '@/components/ui/Pagination';

async function getTransactions(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  const transactions: any = await query(`
    SELECT t.id, t.created_at, t.type, t.amount, t.status, t.description, a.account_number
    FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    ORDER BY t.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  const count: any = await query('SELECT COUNT(*) as total FROM transactions');
  const total = count[0].total;

  return { 
    data: transactions, 
    totalPages: Math.ceil(total / limit),
    totalRecords: total
  };
}

export default async function TransactionsPage({ searchParams }: { searchParams: { page?: string } }) {
  await getSession();
  const page = Number(searchParams.page) || 1;
  const limit = 10;
  const { data: txs, totalPages, totalRecords } = await getTransactions(page, limit);

  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, totalRecords);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Global Transactions</h2>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Date</TableHeader>
            <TableHeader>Account</TableHeader>
            <TableHeader>Description</TableHeader>
            <TableHeader>Type</TableHeader>
            <TableHeader>Amount</TableHeader>
            <TableHeader>Status</TableHeader>
          </TableHead>
          <tbody>
            {txs.map((t: any) => (
              <TableRow key={t.id}>
                <TableCell className="text-slate-500 text-xs">
                    {new Date(t.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <span className="font-mono bg-slate-50 dark:bg-slate-800 px-1 rounded text-xs">
                    {t.account_number}
                  </span>
                </TableCell>
                <TableCell className="text-slate-700 dark:text-slate-300 font-medium">
                    {t.description}
                </TableCell>
                <TableCell>
                  <span className={`text-xs px-2 py-0.5 rounded uppercase font-bold ${
                      t.type === 'credit' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                      {t.type}
                  </span>
                </TableCell>
                <TableCell className={`font-bold ${t.type === 'credit' ? 'text-green-600' : 'text-slate-800 dark:text-white'}`}>
                  {t.type === 'credit' ? '+' : '-'}${Number(t.amount).toLocaleString()}
                </TableCell>
                <TableCell>
                    <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded capitalize">
                        {t.status}
                    </span>
                </TableCell>
              </TableRow>
            ))}
            {txs.length === 0 && (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">No transactions found.</td></tr>
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
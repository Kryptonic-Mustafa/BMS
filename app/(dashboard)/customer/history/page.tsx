'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { ArrowUpRight, ArrowDownLeft, Download, FileSpreadsheet, FileText, Table } from 'lucide-react';
import { exportToExcel, exportToCSV, exportToPDF } from '@/lib/export-utils';

export default function HistoryPage() {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetch('/api/customer/transactions').then(res => res.json()).then(setTransactions);
  }, []);

  const handleExportExcel = () => exportToExcel(transactions, 'MyTransactions');
  const handleExportCSV = () => exportToCSV(transactions, 'MyTransactions');
  const handleExportPDF = () => {
    const headers = [["Date", "Description", "Type", "Amount", "Status"]];
    const data = transactions.map((t: any) => [
        new Date(t.created_at).toLocaleString(),
        t.description,
        t.type.toUpperCase(),
        `$${t.amount}`,
        t.status
    ]);
    exportToPDF("Transaction History Statement", headers, data, "MyTransactions");
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
            <h2 className="text-3xl font-bold dark:text-white">Transaction History</h2>
            <p className="text-slate-500">Download and track your financial activities.</p>
        </div>
        
        <div className="flex gap-2 bg-white dark:bg-slate-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
            <button onClick={handleExportExcel} className="p-2 hover:bg-green-50 text-green-600 rounded-lg transition" title="Export Excel"><FileSpreadsheet size={20}/></button>
            <button onClick={handleExportCSV} className="p-2 hover:bg-blue-50 text-blue-600 rounded-lg transition" title="Export CSV"><Table size={20}/></button>
            <button onClick={handleExportPDF} className="p-2 hover:bg-red-50 text-red-600 rounded-lg transition" title="Export PDF"><FileText size={20}/></button>
        </div>
      </div>
      
      <div className="space-y-3">
        {transactions.map((tx: any) => {
             const isCredit = tx.type === 'credit';
             return (
                <Card key={tx.id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                    <div className="flex items-center gap-4">
                        <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                            isCredit ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-600'
                        }`}>
                            {isCredit ? <ArrowDownLeft size={20}/> : <ArrowUpRight size={20}/>}
                        </div>
                        <div>
                            <p className="font-bold text-slate-900 dark:text-white">{tx.description}</p>
                            <p className="text-xs text-slate-500">{new Date(tx.created_at).toLocaleString()}</p>
                        </div>
                    </div>
                    <div className={`font-bold ${isCredit ? 'text-green-600' : 'text-slate-900 dark:text-white'}`}>
                        {isCredit ? '+' : '-'}${Number(tx.amount).toLocaleString()}
                    </div>
                </Card>
             );
        })}
      </div>
    </div>
  );
}
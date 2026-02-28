'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UserPlus, Trash2, Users, Search, CreditCard } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ContactsPage() {
  const [contacts, setContacts] = useState([]);
  const [form, setForm] = useState({ name: '', accountNumber: '' });

  const fetchContacts = async () => {
    const res = await fetch('/api/customer/beneficiaries');
    if (res.ok) setContacts(await res.json());
  };

  useEffect(() => { fetchContacts(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/customer/beneficiaries', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(form)
    });
    
    if (res.ok) {
        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Saved', timer: 1500, showConfirmButton: false });
        setForm({ name: '', accountNumber: '' });
        fetchContacts();
    } else {
        const data = await res.json();
        Swal.fire({ toast: true, position: 'top-end', icon: 'error', title: data.error, timer: 1500, showConfirmButton: false });
    }
  };

  const handleDelete = async (id: number) => {
    const res = await Swal.fire({ title: 'Delete?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Yes', confirmButtonColor: '#d33' });
    if (res.isConfirmed) {
        await fetch('/api/customer/beneficiaries', { method: 'DELETE', body: JSON.stringify({ id }) });
        fetchContacts();
    }
  };

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <Users className="text-orange-600"/> 
        <h2 className="text-xl font-bold dark:text-white">Beneficiaries</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* ADD FORM */}
        <Card className="md:col-span-1 h-fit p-5 shadow-md border-slate-200 dark:border-slate-800">
            <h3 className="font-bold mb-4 flex items-center gap-2 text-sm text-slate-800 dark:text-white"><UserPlus size={16}/> Add New</h3>
            <form onSubmit={handleAdd} className="space-y-3">
                <Input label="Nick Name" placeholder="e.g. Dad" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required className="py-2" />
                <Input label="Account Number" placeholder="ACC..." value={form.accountNumber} onChange={e => setForm({...form, accountNumber: e.target.value})} required className="py-2" />
                <Button type="submit" className="w-full py-2 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:text-slate-900 font-bold text-sm">Save</Button>
            </form>
        </Card>

        {/* LIST (Scrollable Area) */}
        <Card className="md:col-span-2 p-0 shadow-md border-slate-200 dark:border-slate-800 overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <h3 className="font-bold flex items-center gap-2 text-sm"><Search size={16}/> Saved Contacts ({contacts.length})</h3>
            </div>
            <div className="overflow-y-auto p-4 space-y-2 flex-1">
                {contacts.map((c: any) => (
                    <div key={c.id} className="flex justify-between items-center p-3 border border-slate-100 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition group">
                        <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center font-bold text-xs">
                                {c.saved_name.substring(0, 1).toUpperCase()}
                            </div>
                            <div>
                                <p className="font-bold text-slate-900 dark:text-white text-sm">{c.saved_name}</p>
                                <div className="flex items-center gap-1 text-slate-500 text-xs">
                                    <CreditCard size={10}/> <span className="font-mono">{c.account_number}</span>
                                </div>
                            </div>
                        </div>
                        <button onClick={() => handleDelete(c.id)} className="text-slate-300 hover:text-red-500 p-1.5 transition opacity-0 group-hover:opacity-100"><Trash2 size={16}/></button>
                    </div>
                ))}
                {contacts.length === 0 && <p className="text-center text-slate-400 text-sm py-10">No contacts found.</p>}
            </div>
        </Card>
      </div>
    </div>
  );
}
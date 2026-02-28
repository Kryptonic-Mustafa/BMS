import os

files = {
    # --- 1. COMPACT TRANSFER PAGE (No Scroll) ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard, Send, CreditCard, Lock } from 'lucide-react';
import Swal from 'sweetalert2';

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [useContact, setUseContact] = useState(false);
  const [form, setForm] = useState({ accountNumber: '', amount: '', pin: '' });
  const [addToReceiver, setAddToReceiver] = useState(true);

  useEffect(() => {
    fetch('/api/customer/beneficiaries').then(res => res.json()).then(setContacts);
  }, []);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const res = await fetch('/api/customer/transfer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, addToReceiver }),
    });

    const data = await res.json();
    if (res.ok) {
      Swal.fire({ title: 'Success!', text: 'Transfer completed.', icon: 'success' });
      setForm({ accountNumber: '', amount: '', pin: '' });
    } else {
      Swal.fire({ title: 'Error', text: data.error, icon: 'error' });
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 h-full md:h-auto">
        
        {/* LEFT: INFO HEADER */}
        <div className="md:col-span-2 flex flex-col justify-center space-y-4">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <Send className="text-blue-600"/> Money Transfer
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                    Send funds instantly to any bank account. Secure, fast, and reliable.
                </p>
            </div>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800 text-sm text-blue-800 dark:text-blue-200">
                <p className="font-bold mb-1">Transfer Limits</p>
                <div className="flex justify-between">
                    <span>Daily Limit:</span> <span>$50,000</span>
                </div>
                <div className="flex justify-between">
                    <span>Per Transaction:</span> <span>$10,000</span>
                </div>
            </div>
        </div>

        {/* RIGHT: COMPACT FORM */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800 flex flex-col justify-center">
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-bold text-slate-800 dark:text-white text-lg">Transaction Details</h3>
                <button 
                    onClick={() => setUseContact(!useContact)}
                    className="text-xs flex items-center gap-1 text-blue-600 font-bold hover:bg-blue-50 dark:hover:bg-blue-900/30 px-2 py-1 rounded transition"
                >
                    {useContact ? <><Keyboard size={14}/> Type Manually</> : <><Users size={14}/> Select Contact</>}
                </button>
            </div>

            <form onSubmit={handleTransfer} className="space-y-4">
                {/* ACCOUNT INPUT */}
                <div>
                    {useContact ? (
                        <select 
                            className="w-full p-2.5 border border-slate-300 rounded-lg bg-white dark:bg-slate-900 dark:border-slate-700 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition"
                            onChange={e => setForm({...form, accountNumber: e.target.value})}
                            value={form.accountNumber}
                        >
                            <option value="">-- Choose Beneficiary --</option>
                            {contacts.map((c: any) => (
                                <option key={c.id} value={c.account_number}>{c.saved_name} ({c.account_number})</option>
                            ))}
                        </select>
                    ) : (
                        <div className="relative">
                            <CreditCard className="absolute left-3 top-2.5 text-slate-400" size={18}/>
                            <Input
                                placeholder="Recipient Account Number"
                                value={form.accountNumber}
                                onChange={(e) => setForm({ ...form, accountNumber: e.target.value })}
                                required
                                className="pl-10 py-2" 
                            />
                        </div>
                    )}
                </div>

                {/* ROW: AMOUNT & PIN */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Amount ($)</label>
                        <Input
                            type="number"
                            placeholder="0.00"
                            value={form.amount}
                            onChange={(e) => setForm({ ...form, amount: e.target.value })}
                            required
                            className="py-2 font-mono"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">PIN</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-2.5 text-slate-400" size={16}/>
                            <Input
                                type="password"
                                placeholder="****"
                                maxLength={4}
                                value={form.pin}
                                onChange={(e) => setForm({ ...form, pin: e.target.value })}
                                required
                                className="pl-9 py-2 tracking-widest"
                            />
                        </div>
                    </div>
                </div>

                {/* CHECKBOX */}
                <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
                    <input 
                        type="checkbox" 
                        id="addReceiver"
                        className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer accent-blue-600"
                        checked={addToReceiver}
                        onChange={(e) => setAddToReceiver(e.target.checked)}
                    />
                    <label htmlFor="addReceiver" className="text-xs text-slate-600 dark:text-slate-400 cursor-pointer select-none">
                        Save as beneficiary automatically
                    </label>
                </div>

                <Button type="submit" className="w-full py-2.5 text-base shadow-lg shadow-blue-500/20" disabled={loading}>
                    {loading ? 'Processing...' : <><span className="mr-2">Send Money</span> <ArrowRight size={18} /></>}
                </Button>
            </form>
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 2. COMPACT KYC PAGE ---
    "app/(dashboard)/customer/kyc/page.tsx": """
'use client';
import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UploadCloud, ShieldCheck } from 'lucide-react';
import Swal from 'sweetalert2';

export default function KYCPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('National ID');
  const [docNumber, setDocNumber] = useState('');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return Swal.fire('Error', 'Please upload a document', 'error');

    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = async () => {
      const base64 = reader.result;
      const res = await fetch('/api/customer/kyc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentType: docType, documentNumber: docNumber, fileData: base64 }),
      });

      if (res.ok) {
        Swal.fire('Submitted', 'KYC documents uploaded successfully.', 'success');
        setFile(null); setDocNumber('');
      } else {
        Swal.fire('Error', 'Upload failed', 'error');
      }
    };
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* LEFT: INFO */}
        <div className="md:col-span-2 space-y-4 flex flex-col justify-center">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <ShieldCheck className="text-purple-600"/> Verification
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                    To comply with banking regulations, we need to verify your identity.
                </p>
            </div>
            <ul className="text-xs text-slate-500 dark:text-slate-400 space-y-2 list-disc pl-4">
                <li>Ensure text is readable.</li>
                <li>Upload both sides if required.</li>
                <li>Supported formats: JPG, PNG.</li>
                <li>Max file size: 5MB.</li>
            </ul>
        </div>

        {/* RIGHT: FORM */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800">
            <form onSubmit={handleUpload} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Doc Type</label>
                        <select 
                            className="w-full p-2 border border-slate-300 rounded-lg bg-white dark:bg-slate-900 dark:border-slate-700 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
                            value={docType} onChange={e => setDocType(e.target.value)}
                        >
                            <option>National ID Card</option>
                            <option>Passport</option>
                            <option>Driving License</option>
                        </select>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Doc Number</label>
                        <Input 
                            placeholder="e.g. A1234..." 
                            value={docNumber} onChange={e => setDocNumber(e.target.value)} 
                            required 
                            className="py-2"
                        />
                    </div>
                </div>

                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer group relative">
                    <input 
                        type="file" accept="image/*" 
                        onChange={e => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div className="flex flex-col items-center justify-center">
                        <div className="bg-purple-50 dark:bg-purple-900/20 p-3 rounded-full mb-2 text-purple-600 group-hover:scale-110 transition">
                            <UploadCloud size={24} />
                        </div>
                        {file ? (
                            <p className="font-bold text-green-600 text-sm">{file.name}</p>
                        ) : (
                            <p className="text-sm font-bold text-slate-600 dark:text-slate-300">Click to Upload Image</p>
                        )}
                    </div>
                </div>

                <Button type="submit" className="w-full py-2.5 bg-purple-600 hover:bg-purple-700">
                    Submit Document
                </Button>
            </form>
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 3. COMPACT BENEFICIARIES PAGE ---
    "app/(dashboard)/customer/beneficiaries/page.tsx": """
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
"""
}

def compact_layout():
    print("📏 Applying Compact Layout (No Scroll) to Key Pages...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    compact_layout()
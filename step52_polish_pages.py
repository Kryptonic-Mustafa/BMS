import os

files = {
    # --- 1. POLISH TRANSFER PAGE ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard, Send } from 'lucide-react';
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
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
            <Send className="text-blue-600"/> Money Transfer
        </h2>
        <p className="text-slate-500 dark:text-slate-400">Send money securely to any account.</p>
      </div>
      
      <Card className="p-8 shadow-lg border-slate-200 dark:border-slate-800">
        <div className="flex justify-end mb-6">
            <button 
                onClick={() => setUseContact(!useContact)}
                className="text-sm flex items-center gap-2 text-blue-600 font-bold hover:bg-blue-50 px-3 py-1.5 rounded-lg transition"
            >
                {useContact ? <><Keyboard size={16}/> Type Account Manually</> : <><Users size={16}/> Select from Beneficiaries</>}
            </button>
        </div>

        <form onSubmit={handleTransfer} className="space-y-6">
          {useContact ? (
              <div>
                  <label className="block text-sm font-bold mb-2 text-slate-700 dark:text-slate-300">Select Beneficiary</label>
                  <select 
                      className="w-full p-3 border border-slate-300 rounded-xl bg-white dark:bg-slate-900 dark:border-slate-700 focus:ring-2 focus:ring-blue-500 outline-none transition"
                      onChange={e => setForm({...form, accountNumber: e.target.value})}
                      value={form.accountNumber}
                  >
                      <option value="">-- Choose Contact --</option>
                      {contacts.map((c: any) => (
                          <option key={c.id} value={c.account_number}>
                              {c.saved_name} ({c.account_number})
                          </option>
                      ))}
                  </select>
              </div>
          ) : (
              <Input
                label="Recipient Account Number"
                placeholder="e.g. ACC837482..."
                value={form.accountNumber}
                onChange={(e) => setForm({ ...form, accountNumber: e.target.value })}
                required
                className="p-3"
              />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
                label="Amount ($)"
                type="number"
                placeholder="0.00"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
                className="p-3 font-mono text-lg"
            />

            <Input
                label="Security PIN"
                type="password"
                placeholder="****"
                maxLength={4}
                value={form.pin}
                onChange={(e) => setForm({ ...form, pin: e.target.value })}
                required
                className="p-3 text-center tracking-widest text-lg"
            />
          </div>

          <div className="flex items-start gap-3 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-700">
             <input 
                type="checkbox" 
                id="addReceiver"
                className="mt-1 w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer accent-blue-600"
                checked={addToReceiver}
                onChange={(e) => setAddToReceiver(e.target.checked)}
             />
             <label htmlFor="addReceiver" className="text-sm text-slate-600 dark:text-slate-400 cursor-pointer select-none">
                <span className="font-bold text-slate-900 dark:text-white block mb-0.5">Add me to their contacts</span>
                Automatically save my details in the receiver's list.
             </label>
          </div>

          <Button type="submit" className="w-full py-4 text-lg shadow-xl shadow-blue-500/20" disabled={loading}>
            {loading ? 'Processing...' : <><span className="mr-2">Confirm Transfer</span> <ArrowRight size={20} /></>}
          </Button>
        </form>
      </Card>
    </div>
  );
}
""",

    # --- 2. POLISH KYC PAGE ---
    "app/(dashboard)/customer/kyc/page.tsx": """
'use client';
import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UploadCloud, ShieldCheck, FileText } from 'lucide-react';
import Swal from 'sweetalert2';

export default function KYCPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('National ID');
  const [docNumber, setDocNumber] = useState('');

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return Swal.fire('Error', 'Please upload a document', 'error');

    // Simulate Upload
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
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
            <ShieldCheck className="text-purple-600"/> Identity Verification
        </h2>
        <p className="text-slate-500 dark:text-slate-400">Upload documents to verify your account.</p>
      </div>

      <Card className="p-8 shadow-lg border-slate-200 dark:border-slate-800">
        <form onSubmit={handleUpload} className="space-y-6">
            
            <div>
                <label className="block text-sm font-bold mb-2 text-slate-700 dark:text-slate-300">Document Type</label>
                <select 
                    className="w-full p-3 border border-slate-300 rounded-xl bg-white dark:bg-slate-900 dark:border-slate-700 focus:ring-2 focus:ring-purple-500 outline-none transition"
                    value={docType} onChange={e => setDocType(e.target.value)}
                >
                    <option>National ID Card</option>
                    <option>Passport</option>
                    <option>Driving License</option>
                </select>
            </div>

            <Input 
                label="Document Number" 
                placeholder="e.g. A12345678" 
                value={docNumber} onChange={e => setDocNumber(e.target.value)} 
                required 
                className="p-3"
            />

            <div>
                <label className="block text-sm font-bold mb-2 text-slate-700 dark:text-slate-300">Upload Document Image</label>
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-10 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer group relative">
                    <input 
                        type="file" accept="image/*" 
                        onChange={e => setFile(e.target.files?.[0] || null)}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <div className="flex flex-col items-center">
                        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-full mb-4 text-purple-600 group-hover:scale-110 transition">
                            <UploadCloud size={32} />
                        </div>
                        {file ? (
                            <p className="font-bold text-green-600">{file.name}</p>
                        ) : (
                            <>
                                <p className="font-bold text-slate-700 dark:text-slate-300">Click to Upload</p>
                                <p className="text-sm text-slate-500 mt-1">JPG, PNG up to 5MB</p>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <Button type="submit" className="w-full py-4 text-lg bg-purple-600 hover:bg-purple-700 shadow-xl shadow-purple-500/20">
                Submit for Verification
            </Button>
        </form>
      </Card>
    </div>
  );
}
""",

    # --- 3. POLISH BENEFICIARIES PAGE ---
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
    const data = await res.json();
    
    if (res.ok) {
        Swal.fire('Saved', 'Beneficiary added successfully', 'success');
        setForm({ name: '', accountNumber: '' });
        fetchContacts();
    } else {
        Swal.fire('Error', data.error, 'error');
    }
  };

  const handleDelete = async (id: number) => {
    const res = await Swal.fire({ title: 'Delete Contact?', icon: 'warning', showCancelButton: true, confirmButtonText: 'Yes, delete', confirmButtonColor: '#d33' });
    if (res.isConfirmed) {
        await fetch('/api/customer/beneficiaries', { method: 'DELETE', body: JSON.stringify({ id }) });
        fetchContacts();
        Swal.fire('Deleted', 'Contact removed.', 'success');
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
            <Users className="text-orange-600"/> My Beneficiaries
        </h2>
        <p className="text-slate-500 dark:text-slate-400">Manage your saved contacts for quick transfers.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* ADD FORM */}
        <Card className="md:col-span-1 h-fit p-6 shadow-lg border-slate-200 dark:border-slate-800">
            <h3 className="font-bold mb-6 flex items-center gap-2 text-lg text-slate-800 dark:text-white"><UserPlus size={20}/> Add New Contact</h3>
            <form onSubmit={handleAdd} className="space-y-5">
                <Input label="Nick Name" placeholder="e.g. Dad, Office" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required className="p-3" />
                <Input label="Account Number" placeholder="e.g. ACC..." value={form.accountNumber} onChange={e => setForm({...form, accountNumber: e.target.value})} required className="p-3" />
                <Button type="submit" className="w-full py-3 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:text-slate-900 font-bold">Save Contact</Button>
            </form>
        </Card>

        {/* LIST */}
        <Card className="md:col-span-2 p-6 shadow-lg border-slate-200 dark:border-slate-800 min-h-[400px]">
            <h3 className="font-bold mb-6 flex items-center gap-2 text-lg text-slate-800 dark:text-white"><Search size={20}/> Saved Contacts</h3>
            <div className="space-y-3">
                {contacts.map((c: any) => (
                    <div key={c.id} className="flex justify-between items-center p-4 border border-slate-100 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition group">
                        <div className="flex items-center gap-4">
                            <div className="h-12 w-12 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center font-bold text-lg">
                                {c.saved_name.substring(0, 1).toUpperCase()}
                            </div>
                            <div>
                                <p className="font-bold text-slate-900 dark:text-white text-lg">{c.saved_name}</p>
                                <div className="flex items-center gap-2 text-slate-500 text-sm">
                                    <CreditCard size={14}/> <span className="font-mono">{c.account_number}</span>
                                </div>
                            </div>
                        </div>
                        <button onClick={() => handleDelete(c.id)} className="text-slate-300 hover:text-red-500 p-2 transition opacity-0 group-hover:opacity-100"><Trash2 size={20}/></button>
                    </div>
                ))}
                {contacts.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                        <Users size={48} className="mb-4 opacity-20"/>
                        <p>No contacts saved yet.</p>
                    </div>
                )}
            </div>
        </Card>
      </div>
    </div>
  );
}
"""
}

def polish_pages():
    print("✨ Polishing Layouts for Transfer, KYC & Beneficiaries...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    polish_pages()
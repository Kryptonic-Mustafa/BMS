'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { User, Lock, CreditCard, Shield, Edit2, Save, X, FileText, Download, Cloud } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState({ name: '', email: '' });
  const [autoStatement, setAutoStatement] = useState(false);
  const [statements, setStatements] = useState([]);
  
  const [showPin, setShowPin] = useState(false);
  const [revealedPin, setRevealedPin] = useState('****');

  useEffect(() => {
    fetch('/api/profile').then(res => res.json()).then(data => {
        setUser(data);
        setForm({ name: data.name, email: data.email });
        setAutoStatement(data.auto_statements === 1);
    });
    // Load Statement History
    fetch('/api/customer/statements').then(res => res.json()).then(setStatements);
  }, []);

  const handleToggleAuto = async () => {
    const newValue = !autoStatement;
    setAutoStatement(newValue);
    await fetch('/api/profile', {
        method: 'PUT',
        body: JSON.stringify({ action: 'toggle_auto_statements', value: newValue })
    });
  };

  const handleRevealPin = async () => {
    if (showPin) { setShowPin(false); setRevealedPin('****'); return; }
    const { value: password } = await Swal.fire({
        title: 'Enter Password',
        input: 'password',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Reveal'
    });
    if (password) {
        const res = await fetch('/api/profile', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ action: 'reveal_pin', password })
        });
        const data = await res.json();
        if (res.ok) { setRevealedPin(data.pin); setShowPin(true); }
        else { Swal.fire('Error', 'Incorrect Password', 'error'); }
    }
  };

  if (!user) return <div className="p-8 text-center text-slate-400">Loading Profile...</div>;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold dark:text-white">Profile & Preferences</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* INFO CARD */}
        <div className="lg:col-span-1 space-y-6">
            <Card className="p-6">
                <div className="text-center mb-6">
                    <div className="h-20 w-20 mx-auto bg-blue-100 rounded-full flex items-center justify-center text-2xl font-bold text-blue-600 mb-4">
                        {user.name.charAt(0).toUpperCase()}
                    </div>
                    {isEditing ? (
                        <div className="space-y-3">
                            <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} label="Name" />
                            <Input value={form.email} onChange={e => setForm({...form, email: e.target.value})} label="Email" />
                            <div className="flex gap-2 justify-center">
                                <Button onClick={() => setIsEditing(false)} variant="secondary" size="sm">Cancel</Button>
                                <Button onClick={() => { setIsEditing(false); setUser({...user, ...form}); }} size="sm">Save</Button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <h3 className="text-xl font-bold dark:text-white">{user.name}</h3>
                            <p className="text-slate-500 text-sm">{user.email}</p>
                            <Button onClick={() => setIsEditing(true)} variant="secondary" size="sm" className="mt-4">Edit Profile</Button>
                        </>
                    )}
                </div>
                <div className="space-y-3 pt-6 border-t border-slate-100 dark:border-slate-800">
                    <div className="flex justify-between text-sm"><span className="text-slate-500">Account</span> <span className="font-mono font-bold">{user.account_number}</span></div>
                    <div className="flex justify-between text-sm items-center">
                        <span className="text-slate-500">Security PIN</span> 
                        <div className="flex items-center gap-2">
                            <span className="font-bold">{revealedPin}</span>
                            <button onClick={handleRevealPin} className="text-blue-600 text-xs">Reveal</button>
                        </div>
                    </div>
                </div>
            </Card>

            {/* AUTO GENERATE SETTING */}
            <Card className="p-6 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-blue-100 p-2 rounded-lg text-blue-600"><FileText size={20}/></div>
                        <div>
                            <p className="font-bold text-sm">Auto-Generate Statements</p>
                            <p className="text-xs text-slate-500">Generate PDF every month</p>
                        </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" checked={autoStatement} onChange={handleToggleAuto} className="sr-only peer" />
                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                </div>
            </Card>
        </div>

        {/* STATEMENT STORAGE (DROPBOX TYPE) */}
        <Card className="lg:col-span-2 flex flex-col min-h-[400px]">
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <h3 className="font-bold flex items-center gap-2"><Cloud className="text-blue-600"/> Statement Vault</h3>
                <span className="text-xs text-slate-500 tracking-widest uppercase">Secure Storage</span>
            </div>
            <div className="p-6 grid grid-cols-2 md:grid-cols-3 gap-4">
                {statements.map((s: any) => (
                    <div key={s.id} className="group p-4 border border-slate-100 dark:border-slate-800 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 transition cursor-pointer relative">
                        <FileText size={40} className="text-blue-500 mb-3"/>
                        <p className="font-bold text-sm truncate">{s.month_year}</p>
                        <p className="text-[10px] text-slate-400">PDF Document</p>
                        <button className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition text-blue-600">
                            <Download size={18}/>
                        </button>
                    </div>
                ))}
                {statements.length === 0 && (
                    <div className="col-span-full py-20 text-center text-slate-400">
                        <Cloud size={48} className="mx-auto mb-4 opacity-10"/>
                        <p>No monthly statements generated yet.</p>
                        <p className="text-xs">Turn on auto-generation to start tracking.</p>
                    </div>
                )}
            </div>
        </Card>
      </div>
    </div>
  );
}
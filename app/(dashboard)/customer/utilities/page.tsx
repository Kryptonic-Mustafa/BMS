'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Zap, Droplets, Wifi, Phone, Flame, Receipt, ArrowRight, ShieldCheck } from 'lucide-react';
import Swal from 'sweetalert2';

export default function UtilitiesPage() {
  const [providers, setProviders] = useState([]);
  const [selected, setSelected] = useState<any>(null);
  const [form, setForm] = useState({ consumerNumber: '', amount: '', pin: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/customer/utilities').then(res => res.json()).then(setProviders);
  }, []);

  const getIcon = (cat: string) => {
    switch(cat) {
        case 'electricity': return <Zap className="text-yellow-500"/>;
        case 'water': return <Droplets className="text-blue-500"/>;
        case 'internet': return <Wifi className="text-purple-500"/>;
        case 'mobile': return <Phone className="text-green-500"/>;
        case 'gas': return <Flame className="text-orange-500"/>;
        default: return <Receipt/>;
    }
  };

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('/api/customer/utilities', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, providerId: selected.id })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire('Success', 'Bill Paid Successfully', 'success');
        setForm({ consumerNumber: '', amount: '', pin: '' });
        setSelected(null);
    } else {
        Swal.fire('Error', data.error, 'error');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* LEFT: SELECT PROVIDER */}
        <div className="md:col-span-2 space-y-4 flex flex-col min-h-0">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <Receipt className="text-blue-600"/> Bill Payments
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Select a service provider to pay your utility bills.</p>
            </div>
            
            <Card className="flex-1 overflow-y-auto p-2 border-slate-200 dark:border-slate-800 shadow-md">
                <div className="grid grid-cols-1 gap-2">
                    {providers.map((p: any) => (
                        <button 
                            key={p.id} 
                            onClick={() => setSelected(p)}
                            className={`flex items-center gap-3 p-3 rounded-xl transition text-left border ${
                                selected?.id === p.id 
                                ? 'bg-blue-50 border-blue-200 dark:bg-blue-900/30 dark:border-blue-700' 
                                : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-800/50'
                            }`}
                        >
                            <div className="bg-white dark:bg-slate-800 p-2 rounded-lg shadow-sm">{getIcon(p.category)}</div>
                            <div>
                                <p className="font-bold text-sm text-slate-800 dark:text-white">{p.name}</p>
                                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-widest">{p.category}</p>
                            </div>
                        </button>
                    ))}
                </div>
            </Card>
        </div>

        {/* RIGHT: PAYMENT FORM */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800 flex flex-col justify-center relative overflow-hidden">
            {selected ? (
                <form onSubmit={handlePay} className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="bg-slate-100 dark:bg-slate-800 p-2 rounded-lg">{getIcon(selected.category)}</div>
                        <div>
                            <h3 className="font-bold text-slate-800 dark:text-white">Paying {selected.name}</h3>
                            <p className="text-xs text-slate-500">Instant Settlement</p>
                        </div>
                    </div>

                    <Input 
                        label="Consumer / Account ID" 
                        placeholder="e.g. 1000928374"
                        value={form.consumerNumber}
                        onChange={e => setForm({...form, consumerNumber: e.target.value})}
                        required
                    />

                    <div className="grid grid-cols-2 gap-4">
                        <Input 
                            label="Amount ($)" 
                            type="number"
                            placeholder="0.00"
                            value={form.amount}
                            onChange={e => setForm({...form, amount: e.target.value})}
                            required
                        />
                        <Input 
                            label="Security PIN" 
                            type="password"
                            maxLength={4}
                            placeholder="****"
                            value={form.pin}
                            onChange={e => setForm({...form, pin: e.target.value})}
                            required
                        />
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center gap-3 text-xs text-blue-700 dark:text-blue-300">
                        <ShieldCheck size={18}/>
                        <p>Funds will be deducted from your primary savings account immediately.</p>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full py-3 flex items-center justify-center gap-2">
                        {loading ? 'Processing...' : <><span className="font-bold">Pay Bill Now</span> <ArrowRight size={18}/></>}
                    </Button>
                </form>
            ) : (
                <div className="text-center py-20 text-slate-400">
                    <Receipt size={48} className="mx-auto mb-4 opacity-10"/>
                    <p>Select a provider from the left to start</p>
                </div>
            )}
        </Card>
      </div>
    </div>
  );
}
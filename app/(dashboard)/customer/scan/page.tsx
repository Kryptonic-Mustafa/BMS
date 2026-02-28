'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Scan, QrCode, Store, ArrowRight, ShieldCheck, X, Camera } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ScanPage() {
  const [step, setStep] = useState<'scan' | 'pay'>('scan');
  const [selectedMerch, setSelectedMerch] = useState<any>(null);
  const [form, setForm] = useState({ amount: '', pin: '' });
  const [loading, setLoading] = useState(false);

  // Simulation: Predefined Shop QR Codes
  const demoShops = [
    { name: 'SuperMart HQ', code: 'QR_SUPERMART', icon: <Store/> },
    { name: 'Star Coffee', code: 'QR_STARCOFFEE', icon: <Store/> },
    { name: 'City Fuel', code: 'QR_CITYFUEL', icon: <Store/> }
  ];

  const handleScanSimulation = (merch: any) => {
    setSelectedMerch(merch);
    setStep('pay');
  };

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('/api/customer/merchant', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, merchantCode: selectedMerch.code })
    });
    const data = await res.json();
    if (res.ok) {
        Swal.fire({
            title: 'Payment Successful!',
            text: `Paid $${form.amount} to ${selectedMerch.name}`,
            icon: 'success',
            confirmButtonText: 'Great!'
        });
        setStep('scan');
        setForm({ amount: '', pin: '' });
    } else {
        Swal.fire('Error', data.error, 'error');
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="flex flex-col items-center mb-8">
        <h2 className="text-3xl font-bold dark:text-white flex items-center gap-2">
            <Scan className="text-blue-600"/> QR Pay
        </h2>
        <p className="text-slate-500 text-sm">Instant payments at your favorite merchants.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        
        {/* LEFT: SCANNER AREA */}
        <div className="relative group">
            <Card className="aspect-square flex flex-col items-center justify-center border-2 border-dashed border-blue-200 dark:border-blue-900 bg-slate-50 dark:bg-slate-900/50 relative overflow-hidden">
                {step === 'scan' ? (
                    <div className="text-center animate-pulse">
                        <Camera size={64} className="text-slate-300 mx-auto mb-4"/>
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Position QR code inside</p>
                        <div className="mt-8 grid grid-cols-1 gap-2">
                             <p className="text-[10px] text-slate-500 mb-2">Simulate Scan:</p>
                             {demoShops.map(shop => (
                                 <button key={shop.code} onClick={() => handleScanSimulation(shop)} className="text-xs bg-white dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-500 transition shadow-sm">
                                     Scan {shop.name}
                                 </button>
                             ))}
                        </div>
                    </div>
                ) : (
                    <div className="text-center">
                        <div className="bg-green-100 text-green-600 p-4 rounded-full inline-block mb-4">
                            <Store size={48}/>
                        </div>
                        <h3 className="text-xl font-bold">{selectedMerch.name}</h3>
                        <p className="text-xs text-slate-500">Verified Merchant ✅</p>
                    </div>
                )}
                
                {/* Scanner corners */}
                <div className="absolute top-4 left-4 w-8 h-8 border-t-4 border-l-4 border-blue-500 rounded-tl-lg"></div>
                <div className="absolute top-4 right-4 w-8 h-8 border-t-4 border-r-4 border-blue-500 rounded-tr-lg"></div>
                <div className="absolute bottom-4 left-4 w-8 h-8 border-b-4 border-l-4 border-blue-500 rounded-bl-lg"></div>
                <div className="absolute bottom-4 right-4 w-8 h-8 border-b-4 border-r-4 border-blue-500 rounded-br-lg"></div>
            </Card>
        </div>

        {/* RIGHT: PAYMENT FORM */}
        <Card className="p-6 shadow-2xl border-slate-200 dark:border-slate-800 h-fit">
            {step === 'pay' ? (
                <form onSubmit={handlePayment} className="space-y-5 animate-in slide-in-from-right-4 duration-300">
                    <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Complete Payment</span>
                        <button onClick={() => setStep('scan')} className="text-slate-400 hover:text-red-500 transition"><X size={18}/></button>
                    </div>

                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Pay Amount ($)</label>
                        <Input 
                            type="number" placeholder="0.00" autoFocus
                            value={form.amount} onChange={e => setForm({...form, amount: e.target.value})}
                            required className="text-2xl font-bold py-3"
                        />
                    </div>

                    <div>
                        <label className="text-xs font-bold text-slate-500 mb-1 block">Security PIN</label>
                        <Input 
                            type="password" maxLength={4} placeholder="****"
                            value={form.pin} onChange={e => setForm({...form, pin: e.target.value})}
                            required className="tracking-[1em] text-center text-lg"
                        />
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center gap-3 text-xs text-blue-700 dark:text-blue-300">
                        <ShieldCheck size={18} className="shrink-0"/>
                        <p>This payment will be settled instantly and is non-reversible.</p>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full py-4 text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-500/20">
                        {loading ? 'Processing...' : 'Pay Instant'}
                    </Button>
                </form>
            ) : (
                <div className="text-center py-16 text-slate-400">
                    <QrCode size={48} className="mx-auto mb-4 opacity-10"/>
                    <p className="text-sm">Scan a merchant QR code to start payment</p>
                </div>
            )}
        </Card>
      </div>
    </div>
  );
}
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DollarSign, Calculator, Sliders, Keyboard, Banknote, Percent } from 'lucide-react';
import Swal from 'sweetalert2';

export default function LoanPage() {
  const [loans, setLoans] = useState([]);
  const [amount, setAmount] = useState(5000);
  const [duration, setDuration] = useState(12);
  const [purpose, setPurpose] = useState('Personal Use');
  const [mode, setMode] = useState<'slider' | 'manual'>('slider');
  
  const interestRate = 12; // Flat 12%

  const calculateEMI = () => {
    const r = interestRate / 12 / 100;
    const emi = amount * r * (Math.pow(1 + r, duration) / (Math.pow(1 + r, duration) - 1));
    return Math.round(emi) || 0;
  };

  const fetchLoans = async () => {
    const res = await fetch('/api/customer/loans');
    if (res.ok) setLoans(await res.json());
  };

  useEffect(() => { fetchLoans(); }, []);

  const handleApply = async () => {
    const result = await Swal.fire({
        title: 'Confirm Application',
        text: `Apply for $${amount.toLocaleString()} loan? EMI: $${calculateEMI().toLocaleString()}/mo`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#2563EB',
        confirmButtonText: 'Yes, Apply'
    });

    if (result.isConfirmed) {
        await fetch('/api/customer/loans', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ amount, duration, purpose, rate: interestRate, emi: calculateEMI() })
        });
        Swal.fire('Success', 'Application submitted!', 'success');
        fetchLoans();
    }
  };

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 h-full md:h-auto">
        
        {/* LEFT: INFO & HISTORY */}
        <div className="md:col-span-2 flex flex-col gap-4 min-h-0">
            <div>
                <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                    <Banknote className="text-green-600"/> Loan Services
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Get instant funds with flexible repayment options.
                </p>
            </div>

            {/* COMPACT HISTORY LIST */}
            <Card className="flex-1 min-h-0 flex flex-col p-0 overflow-hidden border-slate-200 dark:border-slate-800 shadow-md">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
                    <h3 className="font-bold text-xs uppercase text-slate-500 tracking-wider">Your Active Applications</h3>
                </div>
                <div className="overflow-y-auto p-3 space-y-2 flex-1">
                    {loans.map((loan: any) => (
                        <div key={loan.id} className="p-3 border border-slate-100 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold text-slate-800 dark:text-white">${Number(loan.amount).toLocaleString()}</span>
                                <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase ${
                                    loan.status === 'approved' ? 'bg-green-100 text-green-700' :
                                    loan.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                                }`}>{loan.status}</span>
                            </div>
                            <div className="flex justify-between text-xs text-slate-500">
                                <span>{loan.duration_months} Mo</span>
                                <span>EMI: ${Number(loan.monthly_emi).toLocaleString()}</span>
                            </div>
                        </div>
                    ))}
                    {loans.length === 0 && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
                            <Banknote size={32} className="mb-2"/>
                            <p className="text-xs">No active loans.</p>
                        </div>
                    )}
                </div>
            </Card>
        </div>

        {/* RIGHT: CALCULATOR */}
        <Card className="md:col-span-3 p-6 shadow-lg border-slate-200 dark:border-slate-800 flex flex-col justify-center">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-100 p-1.5 rounded text-blue-600"><Calculator size={18}/></div>
                    <h3 className="font-bold text-lg text-slate-800 dark:text-white">Calculator</h3>
                </div>
                <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                    <button onClick={() => setMode('slider')} className={`p-1 rounded ${mode === 'slider' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-400'}`}><Sliders size={14}/></button>
                    <button onClick={() => setMode('manual')} className={`p-1 rounded ${mode === 'manual' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-400'}`}><Keyboard size={14}/></button>
                </div>
            </div>

            <div className="space-y-5">
                {/* AMOUNT */}
                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">Loan Amount</label>
                        <span className="font-bold text-blue-600 text-lg">${amount.toLocaleString()}</span>
                    </div>
                    {mode === 'slider' ? (
                        <input type="range" min="1000" max="50000" step="500" className="w-full accent-blue-600 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer" value={amount} onChange={e => setAmount(Number(e.target.value))} />
                    ) : (
                        <Input type="number" value={amount} onChange={e => setAmount(Number(e.target.value))} className="py-2" />
                    )}
                </div>

                {/* DURATION */}
                <div>
                    <div className="flex justify-between mb-2">
                        <label className="text-xs font-bold text-slate-500 uppercase">Duration</label>
                        <span className="font-bold text-blue-600 text-lg">{duration} Months</span>
                    </div>
                    {mode === 'slider' ? (
                        <input type="range" min="6" max="60" step="6" className="w-full accent-blue-600 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer" value={duration} onChange={e => setDuration(Number(e.target.value))} />
                    ) : (
                        <Input type="number" value={duration} onChange={e => setDuration(Number(e.target.value))} className="py-2" />
                    )}
                </div>

                {/* SUMMARY BOX */}
                <div className="bg-slate-900 text-white p-4 rounded-xl flex items-center justify-between shadow-lg">
                    <div>
                        <p className="text-xs text-slate-400 mb-1">Monthly Payment (EMI)</p>
                        <p className="text-2xl font-bold">${calculateEMI().toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                        <div className="flex items-center gap-1 text-green-400 text-sm font-bold justify-end">
                            <Percent size={14}/> {interestRate}%
                        </div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider">Fixed Rate</p>
                    </div>
                </div>

                {/* PURPOSE */}
                <div>
                    <label className="text-xs font-bold text-slate-500 uppercase mb-1 block">Purpose</label>
                    <Input value={purpose} onChange={e => setPurpose(e.target.value)} placeholder="e.g. Home Renovation" className="py-2" />
                </div>

                <Button onClick={handleApply} className="w-full py-3 text-base shadow-xl shadow-blue-500/20 bg-blue-600 hover:bg-blue-700">
                    Submit Application
                </Button>
            </div>
        </Card>
      </div>
    </div>
  );
}
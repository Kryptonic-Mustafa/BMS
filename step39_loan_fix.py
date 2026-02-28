import os

files = {
    "app/(dashboard)/customer/loans/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DollarSign, Calculator, Sliders, Keyboard } from 'lucide-react';
import Swal from 'sweetalert2';

export default function LoanPage() {
  const [loans, setLoans] = useState([]);
  const [amount, setAmount] = useState(5000);
  const [duration, setDuration] = useState(12);
  const [purpose, setPurpose] = useState('Personal Use');
  const [mode, setMode] = useState<'slider' | 'manual'>('slider'); // NEW: Toggle Mode
  
  const interestRate = 12; // Flat 12%

  // EMI Formula
  const calculateEMI = () => {
    const r = interestRate / 12 / 100;
    const emi = amount * r * (Math.pow(1 + r, duration) / (Math.pow(1 + r, duration) - 1));
    return Math.round(emi);
  };

  const fetchLoans = async () => {
    const res = await fetch('/api/customer/loans');
    if (res.ok) setLoans(await res.json());
  };

  useEffect(() => { fetchLoans(); }, []);

  const handleApply = async () => {
    const result = await Swal.fire({
        title: 'Confirm Application',
        text: `Apply for $${amount.toLocaleString()} loan? Monthly EMI: $${calculateEMI().toLocaleString()}`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#2563EB',
        confirmButtonText: 'Yes, Apply'
    });

    if (result.isConfirmed) {
        await fetch('/api/customer/loans', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                amount,
                duration,
                purpose,
                rate: interestRate,
                emi: calculateEMI()
            })
        });
        Swal.fire('Success', 'Loan application submitted!', 'success');
        fetchLoans();
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Loan Services</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* CALCULATOR CARD */}
        <div className="lg:col-span-1">
            <Card className="p-6 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <div className="bg-blue-100 p-2 rounded text-blue-600"><Calculator size={20}/></div>
                        <h3 className="font-bold text-lg text-slate-800 dark:text-white">Calculator</h3>
                    </div>
                    {/* MODE TABS */}
                    <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                        <button 
                            onClick={() => setMode('slider')}
                            className={`p-1.5 rounded transition ${mode === 'slider' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-400'}`}
                            title="Slider Mode"
                        >
                            <Sliders size={16}/>
                        </button>
                        <button 
                            onClick={() => setMode('manual')}
                            className={`p-1.5 rounded transition ${mode === 'manual' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-400'}`}
                            title="Manual Input"
                        >
                            <Keyboard size={16}/>
                        </button>
                    </div>
                </div>

                <div className="space-y-6">
                    {/* AMOUNT INPUT */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-sm font-semibold text-slate-600 dark:text-slate-400">Loan Amount</label>
                            <span className="font-bold text-blue-600">${amount.toLocaleString()}</span>
                        </div>
                        {mode === 'slider' ? (
                            <input 
                                type="range" min="1000" max="50000" step="500"
                                className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
                                value={amount} onChange={e => setAmount(Number(e.target.value))}
                            />
                        ) : (
                            <div className="relative">
                                <span className="absolute left-3 top-2.5 text-slate-400">$</span>
                                <input 
                                    type="number" min="1000" max="100000"
                                    className="w-full pl-8 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 dark:border-slate-600 dark:text-white"
                                    value={amount} onChange={e => setAmount(Number(e.target.value))}
                                />
                            </div>
                        )}
                        <div className="flex justify-between text-xs text-slate-400 mt-1">
                            <span>$1k</span>
                            <span>$50k</span>
                        </div>
                    </div>

                    {/* DURATION INPUT */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-sm font-semibold text-slate-600 dark:text-slate-400">Duration</label>
                            <span className="font-bold text-blue-600">{duration} Months</span>
                        </div>
                        {mode === 'slider' ? (
                            <input 
                                type="range" min="6" max="60" step="6"
                                className="w-full accent-blue-600 cursor-pointer h-2 bg-slate-200 rounded-lg appearance-none"
                                value={duration} onChange={e => setDuration(Number(e.target.value))}
                            />
                        ) : (
                            <div className="relative">
                                <input 
                                    type="number" min="6" max="120"
                                    className="w-full pl-4 pr-12 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none dark:bg-slate-800 dark:border-slate-600 dark:text-white"
                                    value={duration} onChange={e => setDuration(Number(e.target.value))}
                                />
                                <span className="absolute right-3 top-2.5 text-slate-400 text-sm">Months</span>
                            </div>
                        )}
                        <div className="flex justify-between text-xs text-slate-400 mt-1">
                            <span>6 Mo</span>
                            <span>60 Mo</span>
                        </div>
                    </div>

                    {/* SUMMARY BOX */}
                    <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700">
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-sm text-slate-500">Monthly Payment</span>
                            <span className="text-xs font-bold bg-green-100 text-green-700 px-2 py-0.5 rounded">{interestRate}% Rate</span>
                        </div>
                        <p className="text-3xl font-bold text-slate-800 dark:text-white">
                            ${calculateEMI().toLocaleString()}
                        </p>
                    </div>

                    {/* PURPOSE INPUT */}
                    <div>
                        <label className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2 block">Purpose</label>
                        <Input 
                            value={purpose} 
                            onChange={e => setPurpose(e.target.value)}
                            placeholder="e.g. Home Renovation"
                        />
                    </div>

                    <Button onClick={handleApply} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 shadow-lg shadow-blue-500/30 transition-all">
                        Apply Now
                    </Button>
                </div>
            </Card>
        </div>

        {/* ACTIVE LOANS LIST */}
        <div className="lg:col-span-2 space-y-4">
            <h3 className="font-bold text-slate-500 uppercase text-sm tracking-wider">Your Applications</h3>
            {loans.map((loan: any) => (
                <Card key={loan.id} className="flex flex-col md:flex-row justify-between items-center gap-4 p-5 hover:shadow-md transition">
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        <div className="bg-blue-100 p-3 rounded-full text-blue-600 shrink-0">
                            <DollarSign size={24}/>
                        </div>
                        <div>
                            <h4 className="font-bold text-xl text-slate-800 dark:text-white">${Number(loan.amount).toLocaleString()}</h4>
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                                <span className="font-medium text-slate-700 dark:text-slate-300">{loan.purpose}</span>
                                <span>•</span>
                                <span>{loan.duration_months} Months</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex items-center justify-between w-full md:w-auto gap-6">
                        <div className="text-right">
                            <p className="text-xs text-slate-400 uppercase font-bold">Monthly EMI</p>
                            <p className="font-bold text-slate-700 dark:text-slate-200">${Number(loan.monthly_emi).toLocaleString()}</p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${
                            loan.status === 'approved' ? 'bg-green-100 text-green-700' :
                            loan.status === 'rejected' ? 'bg-red-100 text-red-700' :
                            'bg-yellow-100 text-yellow-700'
                        }`}>
                            {loan.status}
                        </span>
                    </div>
                </Card>
            ))}
            {loans.length === 0 && (
                <div className="text-center py-12 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-dashed border-slate-300">
                    <p className="text-slate-500">No active loans found.</p>
                </div>
            )}
        </div>
      </div>
    </div>
  );
}
"""
}

def fix_loan_ui():
    print("🔧 Fixing Loan Calculator UI (Tabs + Visibility)...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_loan_ui()
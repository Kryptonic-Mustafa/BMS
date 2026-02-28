'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard, Send, ShieldCheck, ArrowLeft, RefreshCw } from 'lucide-react';
import Swal from 'sweetalert2';

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [useContact, setUseContact] = useState(false);
  
  // WIZARD STATE: 'form' or 'otp'
  const [step, setStep] = useState<'form' | 'otp'>('form');
  
  const [form, setForm] = useState({ accountNumber: '', amount: '', pin: '' });
  const [otp, setOtp] = useState('');
  const [addToReceiver, setAddToReceiver] = useState(true);

  useEffect(() => {
    fetch('/api/customer/beneficiaries').then(res => res.json()).then(setContacts);
  }, []);

  // STEP 1: Request OTP
  const requestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const otpRes = await fetch('/api/customer/otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'request' })
    });

    setLoading(false);

    if (otpRes.ok) {
        setStep('otp'); // Switch UI to OTP mode
        // Note: The GlobalToastListener will automatically pick up the notification 
        // and show the toast without closing this UI.
    } else {
        Swal.fire('Error', 'System busy. Try again.', 'error');
    }
  };

  // STEP 2: Verify & Transfer
  const verifyAndTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if(otp.length < 6) return Swal.fire('Invalid OTP', 'Code must be 6 digits', 'warning');

    setLoading(true);
    const res = await fetch('/api/customer/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, otp, addToReceiver }),
    });

    const data = await res.json();
    setLoading(false);

    if (res.ok) {
        Swal.fire({ title: 'Success!', text: 'Funds transferred successfully.', icon: 'success' });
        // Reset Everything
        setForm({ accountNumber: '', amount: '', pin: '' });
        setOtp('');
        setStep('form');
    } else {
        Swal.fire({ title: 'Transfer Failed', text: data.error, icon: 'error' });
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        
        {/* LEFT SIDE: INSTRUCTIONS */}
        <div className="md:col-span-2 space-y-4 flex flex-col justify-center">
            <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
                <Send className="text-blue-600"/> Smart Transfer
            </h2>
            <p className="text-sm text-slate-500">
                {step === 'form' 
                    ? "Enter beneficiary details. For security, we will ask for a 2nd factor authentication."
                    : "A 6-digit verification code has been sent to your Notification Bell."}
            </p>
            
            {step === 'otp' && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg border border-yellow-100 dark:border-yellow-800 text-xs text-yellow-800 dark:text-yellow-200">
                    <p className="font-bold mb-1">Check Notification Bell 🔔</p>
                    <p>Click the bell icon in the top right corner to view your code without losing this page.</p>
                </div>
            )}
        </div>

        {/* RIGHT SIDE: WIZARD CARD */}
        <Card className="md:col-span-3 p-6 shadow-lg relative overflow-hidden">
            
            {/* --- VIEW 1: DETAILS FORM --- */}
            {step === 'form' && (
                <div className="animate-in fade-in slide-in-from-left-4 duration-300">
                    <div className="flex justify-end mb-4">
                        <button onClick={() => setUseContact(!useContact)} className="text-xs text-blue-600 font-bold hover:underline">
                            {useContact ? 'Switch to Manual Entry' : 'Select Beneficiary'}
                        </button>
                    </div>
                    <form onSubmit={requestOTP} className="space-y-4">
                        {useContact ? (
                            <select className="w-full p-3 border rounded-xl bg-white dark:bg-slate-900 dark:border-slate-700" onChange={e => setForm({...form, accountNumber: e.target.value})} value={form.accountNumber} required>
                                <option value="">-- Choose Contact --</option>
                                {contacts.map((c: any) => <option key={c.id} value={c.account_number}>{c.saved_name}</option>)}
                            </select>
                        ) : (
                            <Input placeholder="Recipient Account Number" value={form.accountNumber} onChange={e => setForm({...form, accountNumber: e.target.value})} required className="py-3"/>
                        )}
                        <div className="grid grid-cols-2 gap-4">
                            <Input label="Amount ($)" type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required className="py-3"/>
                            <Input label="PIN" type="password" maxLength={4} value={form.pin} onChange={e => setForm({...form, pin: e.target.value})} required className="py-3 text-center tracking-widest"/>
                        </div>
                        <Button type="submit" className="w-full py-3 text-base shadow-lg shadow-blue-500/20" disabled={loading}>
                            {loading ? 'Verifying...' : 'Next: Verify Identity'}
                        </Button>
                    </form>
                </div>
            )}

            {/* --- VIEW 2: OTP ENTRY --- */}
            {step === 'otp' && (
                <div className="animate-in fade-in slide-in-from-right-4 duration-300 text-center">
                    <div className="flex justify-start mb-6">
                        <button onClick={() => setStep('form')} className="flex items-center text-xs text-slate-400 hover:text-slate-600">
                            <ArrowLeft size={14} className="mr-1"/> Back to details
                        </button>
                    </div>

                    <div className="bg-blue-50 dark:bg-blue-900/20 h-16 w-16 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-600">
                        <ShieldCheck size={32}/>
                    </div>

                    <h3 className="font-bold text-xl mb-2">Enter Verification Code</h3>
                    <p className="text-xs text-slate-500 mb-6">We sent a 6-digit code to your secure inbox.</p>

                    <form onSubmit={verifyAndTransfer} className="space-y-6">
                        <input 
                            type="text" 
                            maxLength={6} 
                            placeholder="0 0 0 0 0 0"
                            value={otp}
                            onChange={e => setOtp(e.target.value)}
                            className="w-full text-center text-3xl font-mono font-bold tracking-[0.5em] py-4 border-b-2 border-slate-200 dark:border-slate-700 bg-transparent focus:border-blue-600 focus:outline-none transition"
                            autoFocus
                        />

                        <Button type="submit" className="w-full py-3 text-base" disabled={loading}>
                            {loading ? 'Processing Transfer...' : 'Confirm & Send Money'}
                        </Button>
                    </form>

                    <button 
                        onClick={requestOTP}
                        disabled={loading}
                        className="mt-4 text-xs text-slate-400 hover:text-blue-600 flex items-center justify-center gap-1 mx-auto w-fit"
                    >
                        <RefreshCw size={12}/> Resend Code
                    </button>
                </div>
            )}

        </Card>
      </div>
    </div>
  );
}
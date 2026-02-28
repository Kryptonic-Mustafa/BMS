import os

files = {
    # --- 1. UPDATED TRANSFER API (Requires OTP) ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, accountNumber, pin, otp, addToReceiver } = await request.json();

    // 1. Verify User & PIN
    const users: any = await query('SELECT pin, name FROM users WHERE id = ?', [session.id]);
    if (users[0].pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

    // 2. VERIFY OTP (The Smart Part)
    const otpCheck: any = await query(
        'SELECT * FROM otp_codes WHERE user_id = ? AND code = ? AND expires_at > CURRENT_TIMESTAMP',
        [session.id, otp]
    );

    if (otpCheck.length === 0) {
        return NextResponse.json({ 
            error: 'Invalid or Expired OTP. If funds were debited, they will be refunded within 3 days.' 
        }, { status: 400 });
    }

    // 3. Balance Check
    const senderAcc: any = await query('SELECT id, balance, account_number FROM accounts WHERE user_id = ?', [session.id]);
    if (Number(senderAcc[0].balance) < Number(amount)) {
        return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    // 4. Find Receiver
    const receiverAcc: any = await query('SELECT id, user_id FROM accounts WHERE account_number = ?', [accountNumber]);
    if (receiverAcc.length === 0) return NextResponse.json({ error: 'Receiver not found' }, { status: 404 });

    // 5. Execute Transfer
    await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, senderAcc[0].id]);
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, receiverAcc[0].id]);

    // 6. Logs & Cleanup
    await query('DELETE FROM otp_codes WHERE user_id = ?', [session.id]);
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)', 
        [senderAcc[0].id, amount, `Transfer to ${accountNumber}`]);

    // Reciprocal Beneficiary Logic
    if (addToReceiver) {
        const exists: any = await query('SELECT id FROM beneficiaries WHERE user_id = ? AND account_number = ?', [receiverAcc[0].user_id, senderAcc[0].account_number]);
        if (exists.length === 0) {
            await query('INSERT INTO beneficiaries (user_id, saved_name, account_number) VALUES (?, ?, ?)', [receiverAcc[0].user_id, users[0].name, senderAcc[0].account_number]);
        }
    }

    return NextResponse.json({ success: true });
  } catch (e) {
    return NextResponse.json({ error: 'Transaction failed' }, { status: 500 });
  }
}
""",

    # --- 2. UPDATED TRANSFER UI (With OTP Popup) ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard, Send, Lock, ShieldCheck } from 'lucide-react';
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

  const triggerTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // 1. Request OTP first
    const otpRes = await fetch('/api/customer/otp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'request' })
    });

    if (otpRes.ok) {
        setLoading(false);
        // 2. Open OTP Verification Modal
        const { value: otpCode } = await Swal.fire({
            title: 'Verify Transaction',
            text: 'A 6-digit security code was sent to your notification bell.',
            input: 'text',
            inputPlaceholder: 'Enter 6-digit OTP',
            icon: 'shield',
            showCancelButton: true,
            confirmButtonText: 'Verify & Pay',
            confirmButtonColor: '#2563EB',
            inputAttributes: { maxlength: '6', style: 'text-align: center; letter-spacing: 0.5em; font-weight: bold;' },
            inputValidator: (value) => {
                if (!value || value.length < 6) return 'Please enter the full 6-digit code!';
            }
        });

        if (otpCode) {
            setLoading(true);
            const res = await fetch('/api/customer/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...form, otp: otpCode, addToReceiver }),
            });

            const data = await res.json();
            if (res.ok) {
                Swal.fire({ title: 'Success!', text: 'Funds transferred successfully.', icon: 'success' });
                setForm({ accountNumber: '', amount: '', pin: '' });
            } else {
                Swal.fire({ title: 'Transfer Failed', text: data.error, icon: 'error' });
            }
            setLoading(false);
        }
    } else {
        Swal.fire('Error', 'Could not generate OTP. Try again.', 'error');
        setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col justify-center">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="md:col-span-2 space-y-4 flex flex-col justify-center">
            <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2"><Send className="text-blue-600"/> Smart Transfer</h2>
            <p className="text-sm text-slate-500">Enhanced with 2-Layer Security (PIN + OTP).</p>
        </div>

        <Card className="md:col-span-3 p-6 shadow-lg">
            <div className="flex justify-end mb-4">
                <button onClick={() => setUseContact(!useContact)} className="text-xs text-blue-600 font-bold">{useContact ? 'Manual Entry' : 'Use Beneficiary'}</button>
            </div>
            <form onSubmit={triggerTransfer} className="space-y-4">
                {useContact ? (
                    <select className="w-full p-2.5 border rounded-lg dark:bg-slate-900" onChange={e => setForm({...form, accountNumber: e.target.value})} value={form.accountNumber}>
                        <option value="">-- Choose Contact --</option>
                        {contacts.map((c: any) => <option key={c.id} value={c.account_number}>{c.saved_name}</option>)}
                    </select>
                ) : (
                    <Input placeholder="Recipient Account" value={form.accountNumber} onChange={e => setForm({...form, accountNumber: e.target.value})} required />
                )}
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Amount ($)" type="number" value={form.amount} onChange={e => setForm({...form, amount: e.target.value})} required />
                    <Input label="Security PIN" type="password" maxLength={4} value={form.pin} onChange={e => setForm({...form, pin: e.target.value})} required />
                </div>
                <Button type="submit" className="w-full py-3" disabled={loading}>{loading ? 'Processing...' : 'Proceed to OTP'}</Button>
            </form>
        </Card>
      </div>
    </div>
  );
}
"""
}

def install_smart_otp():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("🚀 Smart OTP System installed!")

if __name__ == "__main__":
    install_smart_otp()
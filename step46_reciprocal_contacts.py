import os

files = {
    # --- 1. UPDATE TRANSFER API (Add Logic to Save Sender to Receiver's List) ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, accountNumber, pin, addToReceiver } = await request.json(); // Read checkbox

    // 1. Verify Sender & PIN
    const users: any = await query('SELECT * FROM users WHERE id = ?', [session.id]);
    const user = users[0];

    if (user.pin !== pin) return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });

    const senderAcc: any = await query('SELECT * FROM accounts WHERE user_id = ?', [session.id]);
    if (senderAcc.length === 0 || Number(senderAcc[0].balance) < Number(amount)) {
        return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    // 2. Find Receiver
    const receiverAcc: any = await query('SELECT * FROM accounts WHERE account_number = ?', [accountNumber]);
    if (receiverAcc.length === 0) return NextResponse.json({ error: 'Receiver account not found' }, { status: 404 });
    const receiverId = receiverAcc[0].user_id;

    // 3. Execute Transfer
    await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, senderAcc[0].id]);
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, receiverAcc[0].id]);

    // 4. Log Transactions
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)', 
        [senderAcc[0].id, amount, `Transfer to ${accountNumber}`]);
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)', 
        [receiverAcc[0].id, amount, `Received from ${user.name}`]);

    // --- 5. RECIPROCAL BENEFICIARY LOGIC ---
    if (addToReceiver) {
        // Check if Sender is already in Receiver's list
        const exists: any = await query(
            'SELECT id FROM beneficiaries WHERE user_id = ? AND account_number = ?', 
            [receiverId, senderAcc[0].account_number]
        );

        if (exists.length === 0) {
            // Add Sender to Receiver's Beneficiaries
            await query(
                'INSERT INTO beneficiaries (user_id, saved_name, account_number) VALUES (?, ?, ?)',
                [receiverId, user.name, senderAcc[0].account_number]
            );
            
            // Optional: Notify Receiver they have a new contact
            await query(
                'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
                [receiverId, `${user.name} added themselves to your beneficiaries list after sending money.`, 'info']
            );
        }
    }

    return NextResponse.json({ success: true });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: 'Transfer failed' }, { status: 500 });
  }
}
""",

    # --- 2. UPDATE TRANSFER PAGE (Add Checkbox) ---
    "app/(dashboard)/customer/transfer/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ArrowRight, Users, Keyboard, UserPlus } from 'lucide-react';
import Swal from 'sweetalert2';

export default function TransferPage() {
  const [loading, setLoading] = useState(false);
  const [contacts, setContacts] = useState([]);
  const [useContact, setUseContact] = useState(false);
  const [form, setForm] = useState({ accountNumber: '', amount: '', pin: '' });
  const [addToReceiver, setAddToReceiver] = useState(true); // Default checked

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
    <div className="max-w-xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">Money Transfer</h2>
      
      <Card>
        <div className="flex justify-end mb-4">
            <button 
                onClick={() => setUseContact(!useContact)}
                className="text-sm flex items-center gap-2 text-blue-600 font-medium hover:underline"
            >
                {useContact ? <><Keyboard size={16}/> Type Manually</> : <><Users size={16}/> Select Beneficiary</>}
            </button>
        </div>

        <form onSubmit={handleTransfer} className="space-y-6">
          {useContact ? (
              <div>
                  <label className="block text-sm font-medium mb-2 dark:text-slate-300">Select Beneficiary</label>
                  <select 
                      className="w-full p-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
                      onChange={e => setForm({...form, accountNumber: e.target.value})}
                      value={form.accountNumber}
                  >
                      <option value="">-- Select Contact --</option>
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
                placeholder="ACC..."
                value={form.accountNumber}
                onChange={(e) => setForm({ ...form, accountNumber: e.target.value })}
                required
              />
          )}

          <Input
            label="Amount ($)"
            type="number"
            placeholder="0.00"
            value={form.amount}
            onChange={(e) => setForm({ ...form, amount: e.target.value })}
            required
          />

          <Input
            label="Security PIN"
            type="password"
            placeholder="****"
            maxLength={4}
            value={form.pin}
            onChange={(e) => setForm({ ...form, pin: e.target.value })}
            required
          />

          {/* RECIPROCAL CHECKBOX */}
          <div className="flex items-start gap-3 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-100 dark:border-blue-800">
             <input 
                type="checkbox" 
                id="addReceiver"
                className="mt-1 w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500 cursor-pointer"
                checked={addToReceiver}
                onChange={(e) => setAddToReceiver(e.target.checked)}
             />
             <label htmlFor="addReceiver" className="text-sm text-slate-600 dark:text-slate-300 cursor-pointer">
                <span className="font-bold text-slate-800 dark:text-white block mb-0.5">Add me to their contacts</span>
                Save my details in the receiver's beneficiary list so they can easily pay me back.
             </label>
          </div>

          <Button type="submit" className="w-full flex items-center justify-center" disabled={loading}>
            {loading ? 'Processing...' : <><span className="mr-2">Transfer Now</span> <ArrowRight size={18} /></>}
          </Button>
        </form>
      </Card>
    </div>
  );
}
"""
}

def reciprocal_beneficiaries():
    print("🤝 Enabling Reciprocal Beneficiary Logic...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    reciprocal_beneficiaries()
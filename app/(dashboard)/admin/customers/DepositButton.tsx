'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import Swal from 'sweetalert2';

export default function DepositButton({ accountId }: { accountId: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 1. Validation
    if (!amount || parseFloat(amount) <= 0) {
      Swal.fire('Invalid Amount', 'Please enter a valid amount', 'warning');
      return;
    }

    // 2. SweetAlert Confirmation
    const result = await Swal.fire({
      title: 'Confirm Deposit?',
      text: `Are you sure you want to add $${amount} to this user's account?`,
      icon: 'question',
      showCancelButton: true,
      confirmButtonColor: '#1E3A8A', // Blue 900
      cancelButtonColor: '#64748B', // Slate 500
      confirmButtonText: 'Yes, Deposit it!'
    });

    if (!result.isConfirmed) return;

    // 3. API Call
    setLoading(true);
    try {
      const res = await fetch('/api/admin/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId, amount: parseFloat(amount) }),
      });
      
      if (res.ok) {
        setIsOpen(false);
        setAmount('');
        Swal.fire({
          toast: true, 
          position: 'top-end', 
          icon: 'success', 
          title: 'Deposit Successful', 
          timer: 3000, 
          showConfirmButton: false
        });
        router.refresh(); 
      } else {
        Swal.fire('Error', 'Deposit failed', 'error');
      }
    } catch (e) {
      Swal.fire('Error', 'Network error', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setIsOpen(true)}>
        + Deposit
      </Button>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Add Funds">
        <form onSubmit={handleDeposit} className="space-y-4">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Enter the amount to deposit. An admin log will be created.
          </p>
          <Input 
            label="Amount ($)" 
            type="number" 
            min="1" 
            placeholder="1000.00" 
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="ghost" onClick={() => setIsOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Confirm Deposit'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
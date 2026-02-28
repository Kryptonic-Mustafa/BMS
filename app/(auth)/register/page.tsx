'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || 'Registration failed');

      // Redirect to login on success
      router.push('/login?registered=true');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200 w-full max-w-md">
      <h2 className="text-2xl font-bold text-blue-900 mb-2 text-center">Create Account</h2>
      <p className="text-slate-500 text-center mb-6">Join our secure banking platform</p>
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Full Name" 
          placeholder="John Doe"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
        />
        <Input 
          label="Email Address" 
          type="email" 
          placeholder="john@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <Input 
          label="Password" 
          type="password" 
          placeholder="••••••••"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        
        <Button 
          type="submit" 
          className="w-full" 
          disabled={loading}
          variant="secondary"
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account? <Link href="/login" className="text-blue-900 font-semibold hover:underline">Login</Link>
      </p>
    </div>
  );
}
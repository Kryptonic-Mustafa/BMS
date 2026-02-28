'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ShieldCheck, User } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isAdminLogin, setIsAdminLogin] = useState(false);
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed');

      // Role enforcement
      // UPDATED: Allow 'admin' OR 'manager' to use the Admin Portal
      if (isAdminLogin && !['admin', 'manager'].includes(data.user.role)) {
        throw new Error('Access Denied. Not a staff account.');
      }
      
      // Redirect Logic
      if (['admin', 'manager'].includes(data.user.role)) {
          router.push('/admin');
      } else {
          router.push('/customer');
      }
      router.refresh();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 p-8 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 w-full max-w-md transition-all">
      <div className="flex justify-center mb-6">
        <div className={`p-4 rounded-full ${isAdminLogin ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
            {isAdminLogin ? <ShieldCheck size={32} /> : <User size={32} />}
        </div>
      </div>
      
      <h2 className="text-2xl font-bold text-center mb-2 dark:text-white">
        {isAdminLogin ? 'Staff Portal' : 'Customer Login'}
      </h2>
      <p className="text-slate-500 text-center mb-6 text-sm">
        {isAdminLogin ? 'Authorized personnel only' : 'Welcome back to your account'}
      </p>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Email Address" 
          type="email" 
          value={form.email} 
          onChange={(e) => setForm({ ...form, email: e.target.value })} 
          required 
        />
        <Input 
          label="Password" 
          type="password" 
          value={form.password} 
          onChange={(e) => setForm({ ...form, password: e.target.value })} 
          required 
        />
        
        <Button 
          type="submit" 
          className={`w-full ${isAdminLogin ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-900 hover:bg-blue-800'}`}
          disabled={loading}
        >
          {loading ? 'Authenticating...' : (isAdminLogin ? 'Access Dashboard' : 'Sign In')}
        </Button>
      </form>

      <div className="mt-6 text-center pt-4 border-t border-slate-100 dark:border-slate-800">
        <button 
            onClick={() => { setIsAdminLogin(!isAdminLogin); setError(''); }}
            className="text-xs font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 uppercase tracking-wider"
        >
            {isAdminLogin ? '← Switch to Customer Login' : 'Switch to Staff Login →'}
        </button>
      </div>

      {!isAdminLogin && (
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
            No account? <Link href="/register" className="text-blue-600 hover:underline">Register</Link>
        </p>
      )}
    </div>
  );
}
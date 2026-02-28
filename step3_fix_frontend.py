import os

files = {
    # --- 1. INTERACTIVE REGISTER PAGE ---
    "app/(auth)/register/page.tsx": """
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
""",

    # --- 2. INTERACTIVE LOGIN PAGE ---
    "app/(auth)/login/page.tsx": """
'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const registered = searchParams.get('registered');

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

      // Redirect based on role
      if (data.user.role === 'admin') {
        router.push('/admin');
      } else {
        router.push('/customer');
      }
      
      router.refresh(); // Refresh to update middleware state
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200 w-full max-w-md">
      <h2 className="text-2xl font-bold text-blue-900 mb-2 text-center">Welcome Back</h2>
      <p className="text-slate-500 text-center mb-6">Sign in to your account</p>

      {registered && (
        <div className="bg-green-50 text-green-700 p-3 rounded-lg text-sm mb-4 border border-green-200">
          Account created! Please log in.
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4 border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input 
          label="Email Address" 
          type="email" 
          placeholder="admin@bank.com"
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
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>

      <p className="mt-4 text-center text-sm text-slate-600">
        Don't have an account? <Link href="/register" className="text-blue-900 font-semibold hover:underline">Register</Link>
      </p>
    </div>
  );
}
"""
}

def fix_frontend():
    print("🔌 Connecting Frontend to Backend API...")
    for path, content in files.items():
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Write file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n🚀 Frontend connected! Refresh your browser and try again.")

if __name__ == "__main__":
    fix_frontend()
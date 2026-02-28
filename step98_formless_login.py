import os

files = {
    "app/(auth)/login/page.tsx": """
'use client';
import { useState } from 'react';
import { Landmark } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    // No more e.preventDefault() needed because there is no form!
    
    if (!email || !password) {
        setError('Please enter both email and password.');
        return;
    }
    
    setError(''); 
    setLoading(true);

    try {
      console.log(`[FRONTEND] Fetching API for: ${email}`);
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      console.log('[FRONTEND] API Response received:', data);

      if (!res.ok) {
        setError(data.error || 'Login failed');
        setLoading(false);
        return;
      }
      
      console.log(`[FRONTEND] Login Success! Redirecting in 500ms...`);
      
      // THE FIX: A small delay ensures the browser saves the secure cookie before moving
      setTimeout(() => {
          window.location.href = data.redirectUrl || '/customer';
      }, 500);
      
    } catch (err) {
      console.error('[FRONTEND] Connection error:', err);
      setError('Connection error');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-800 rounded-2xl shadow-2xl p-8 border border-slate-700">
        <div className="text-center mb-8">
          <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Landmark className="text-white" size={32} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Secure Login</h1>
          <p className="text-slate-400">Welcome back to Babji Bank</p>
        </div>

        {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg mb-6 text-center text-sm font-medium">{error}</div>}

        {/* THE FIX: Changed <form> to a simple <div> */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" 
              placeholder="admin@bank.com" 
              autoComplete="username" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
              className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500 transition-colors" 
              placeholder="••••••••" 
              autoComplete="current-password" 
            />
          </div>
          {/* THE FIX: Explicitly set to type="button" to prevent ANY default submissions */}
          <button 
            type="button" 
            onClick={handleLogin}
            disabled={loading} 
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors shadow-lg disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}
"""
}

def apply_formless_login():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Form replaced with div. The page physically cannot reload on its own anymore!")

if __name__ == "__main__":
    apply_formless_login()
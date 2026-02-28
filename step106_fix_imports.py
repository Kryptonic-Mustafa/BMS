import os

files = {
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
// THE FIX: Added Settings and Users to the import list
import { ShieldAlert, Save, ServerCrash, Settings, Users } from 'lucide-react';

export default function MasterSettings() {
  const [settings, setSettings] = useState({
    site_name: '', contact_email: '', max_transfer_limit: '', site_logo: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // Danger Zone States
  const [dangerAction, setDangerAction] = useState('');
  const [password, setPassword] = useState('');
  const [dangerMessage, setDangerMessage] = useState('');

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => {
      setSettings(data);
    });
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) {
        setMessage('Settings saved successfully!');
        setTimeout(() => window.location.reload(), 1200);
      } else {
        setMessage('Failed to save settings.');
      }
    } catch (err) {
      setMessage('Network error.');
    }
    setLoading(false);
  };

  const handleDangerAction = async () => {
    if (!password) return setDangerMessage('Password is required.');
    setDangerMessage('Processing...');
    
    try {
      const res = await fetch('/api/admin/settings/danger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: dangerAction, password })
      });
      const data = await res.json();
      
      if (res.ok) {
        setDangerMessage(`SUCCESS: ${data.message}`);
        setPassword('');
      } else {
        setDangerMessage(`ERROR: ${data.error}`);
      }
    } catch (err) {
      setDangerMessage('ERROR: Network failure.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Master Settings</h1>
        <p className="text-slate-500 mt-1">Configure global application parameters and security.</p>
      </div>

      {/* Global Branding Settings */}
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
        <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
          <Settings className="text-blue-500" /> System Configurations
        </h2>
        
        {message && <div className="mb-4 p-3 bg-blue-50 text-blue-600 rounded-lg">{message}</div>}

        <form onSubmit={handleSaveSettings} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Bank Name</label>
              <input type="text" value={settings.site_name} onChange={e => setSettings({...settings, site_name: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Support Email</label>
              <input type="email" value={settings.contact_email} onChange={e => setSettings({...settings, contact_email: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Max Transfer Limit ($)</label>
              <input type="number" value={settings.max_transfer_limit} onChange={e => setSettings({...settings, max_transfer_limit: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Logo URL</label>
              <input type="text" value={settings.site_logo} onChange={e => setSettings({...settings, site_logo: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" placeholder="https://..." />
            </div>
          </div>
          <div className="pt-4 flex justify-end">
            <button type="submit" disabled={loading} className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg flex items-center gap-2">
              <Save size={18} /> {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>

      {/* DANGER ZONE */}
      <div className="bg-red-50 dark:bg-red-900/10 rounded-xl shadow-sm border border-red-200 dark:border-red-900/50 p-6">
        <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2 flex items-center gap-2">
          <ShieldAlert /> Danger Zone
        </h2>
        <p className="text-sm text-red-500 mb-6">These actions are destructive and cannot be undone. SuperAdmin password is required.</p>

        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4 items-center p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg">
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><ServerCrash size={18} className="text-red-500" /> Wipe All Transactions</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Deletes all transaction history and resets all account balances to $0.</p>
            </div>
            <button onClick={() => setDangerAction('wipe_transactions')} className="px-4 py-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 rounded-lg font-medium whitespace-nowrap">
              Select Action
            </button>
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-center p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg">
            <div className="flex-1">
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><Users size={18} className="text-red-500" /> Reset All KYC</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Changes all customer KYC statuses back to 'unverified'.</p>
            </div>
            <button onClick={() => setDangerAction('reset_kyc')} className="px-4 py-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 rounded-lg font-medium whitespace-nowrap">
              Select Action
            </button>
          </div>
        </div>

        {/* Password Verification Modal Area */}
        {dangerAction && (
          <div className="mt-6 p-4 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-900/50 rounded-lg">
            <label className="block text-sm font-bold text-red-700 dark:text-red-400 mb-2">
              Confirm Action: <span className="uppercase">{dangerAction.replace('_', ' ')}</span>
            </label>
            <div className="flex flex-col md:flex-row gap-3">
              <input 
                type="password" 
                placeholder="Enter SuperAdmin Password..." 
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="flex-1 px-4 py-2 bg-white dark:bg-slate-900 border border-red-300 dark:border-red-700 rounded-lg text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-red-500"
              />
              <button 
                onClick={handleDangerAction}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow-md"
              >
                Execute
              </button>
              <button 
                onClick={() => {setDangerAction(''); setDangerMessage(''); setPassword('');}}
                className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-white font-medium rounded-lg"
              >
                Cancel
              </button>
            </div>
            {dangerMessage && <p className="mt-3 font-medium text-red-600 dark:text-red-400">{dangerMessage}</p>}
          </div>
        )}
      </div>

    </div>
  );
}
"""
}

def fix_imports():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed lucide-react icon imports!")

if __name__ == "__main__":
    fix_imports()
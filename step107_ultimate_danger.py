import os

files = {
    # 1. THE ADVANCED DANGER API: Handles targeted deletions and granular resets safely
    "app/api/admin/settings/danger/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session || session.role !== 'SuperAdmin') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 403 });
    }

    const { action, password, userIds, resetType } = await request.json();

    // 1. Strict Password Verification for ALL Danger Actions
    const users: any = await query('SELECT password FROM users WHERE id = ?', [session.id]);
    if (users.length === 0) return NextResponse.json({ error: 'Session invalid' }, { status: 401 });

    const isMatch = await bcrypt.compare(password, users[0].password);
    if (!isMatch) return NextResponse.json({ error: 'Incorrect SuperAdmin password.' }, { status: 401 });

    // 2. ACTION: Fetch Users & Accounts for the Selection Modal
    if (action === 'fetch_users') {
        const customerList = await query('SELECT id, name, email FROM users WHERE role_id != 1 AND is_super_admin = 0');
        const accountList = await query('SELECT user_id, account_number, balance FROM accounts');
        return NextResponse.json({ users: customerList, accounts: accountList });
    }

    // 3. ACTION: Targeted User Deletion (Safely handling Foreign Keys)
    if (action === 'delete_users') {
        if (!userIds || userIds.length === 0) return NextResponse.json({ error: 'No users selected' }, { status: 400 });
        
        const placeholders = userIds.map(() => '?').join(',');
        
        // Delete dependent data first to prevent constraint crashes
        await query(`DELETE FROM accounts WHERE user_id IN (${placeholders})`, userIds);
        await query(`DELETE FROM users WHERE id IN (${placeholders})`, userIds);
        
        return NextResponse.json({ message: `Successfully deleted ${userIds.length} user(s).` });
    }

    // 4. ACTION: Granular System Reset
    if (action === 'factory_reset') {
        if (resetType === 'data' || resetType === 'both') {
            await query('UPDATE accounts SET balance = 0');
        }
        if (resetType === 'users' || resetType === 'both') {
            await query('DELETE FROM accounts WHERE user_id IN (SELECT id FROM users WHERE role_id != 1 AND is_super_admin = 0)');
            await query('DELETE FROM users WHERE role_id != 1 AND is_super_admin = 0');
        }
        return NextResponse.json({ message: `System reset (${resetType}) executed successfully.` });
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  } catch (error) {
    console.error('[DANGER API ERROR]:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
""",

    # 2. THE SETTINGS UI: Restores the Modals, Chevrons, and Password Gates
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { ShieldAlert, Save, ServerCrash, Settings, Users, ChevronDown, ChevronRight, UserX, AlertTriangle, X, CheckSquare, Square } from 'lucide-react';

export default function MasterSettings() {
  const [settings, setSettings] = useState({ site_name: '', contact_email: '', max_transfer_limit: '', site_logo: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // Advanced Danger Zone States
  const [modalType, setModalType] = useState<'users' | 'reset' | null>(null);
  const [password, setPassword] = useState('');
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [dangerLoading, setDangerLoading] = useState(false);
  const [dangerError, setDangerError] = useState('');
  const [dangerSuccess, setDangerSuccess] = useState('');

  // User Deletion States
  const [users, setUsers] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [expandedUsers, setExpandedUsers] = useState<Set<number>>(new Set());
  const [selectedUsers, setSelectedUsers] = useState<Set<number>>(new Set());

  // Reset States
  const [resetType, setResetType] = useState<'data' | 'users' | 'both'>('data');

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => setSettings(data));
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setMessage('');
    try {
      const res = await fetch('/api/admin/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings) });
      if (res.ok) {
        setMessage('Settings saved successfully!');
        setTimeout(() => window.location.reload(), 1200);
      } else setMessage('Failed to save settings.');
    } catch (err) { setMessage('Network error.'); }
    setLoading(false);
  };

  const closeDangerModal = () => {
    setModalType(null); setPassword(''); setIsUnlocked(false); setDangerError(''); setDangerSuccess('');
    setSelectedUsers(new Set()); setExpandedUsers(new Set());
  };

  const verifyPasswordAndUnlock = async () => {
    setDangerLoading(true); setDangerError('');
    try {
      const res = await fetch('/api/admin/settings/danger', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: modalType === 'users' ? 'fetch_users' : 'verify_only', password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      
      setIsUnlocked(true);
      if (modalType === 'users') {
        setUsers(data.users); setAccounts(data.accounts);
      }
    } catch (err: any) { setDangerError(err.message || 'Verification failed'); }
    setDangerLoading(false);
  };

  const executeUserDeletion = async () => {
    if (selectedUsers.size === 0) return setDangerError('No users selected.');
    if (!confirm(`Are you absolutely sure you want to delete ${selectedUsers.size} user(s)? This cannot be undone.`)) return;
    
    setDangerLoading(true);
    try {
      const res = await fetch('/api/admin/settings/danger', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete_users', password, userIds: Array.from(selectedUsers) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setDangerSuccess(data.message);
      setUsers(users.filter(u => !selectedUsers.has(u.id)));
      setSelectedUsers(new Set());
    } catch (err: any) { setDangerError(err.message); }
    setDangerLoading(false);
  };

  const executeSystemReset = async () => {
    if (!confirm(`WARNING: You are about to execute a ${resetType.toUpperCase()} reset. This is permanent. Continue?`)) return;
    
    setDangerLoading(true);
    try {
      const res = await fetch('/api/admin/settings/danger', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'factory_reset', password, resetType })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setDangerSuccess(data.message);
    } catch (err: any) { setDangerError(err.message); }
    setDangerLoading(false);
  };

  const toggleExpand = (id: number) => {
    const next = new Set(expandedUsers);
    next.has(id) ? next.delete(id) : next.add(id);
    setExpandedUsers(next);
  };

  const toggleSelect = (id: number) => {
    const next = new Set(selectedUsers);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelectedUsers(next);
  };

  const toggleSelectAll = () => {
    if (selectedUsers.size === users.length) setSelectedUsers(new Set());
    else setSelectedUsers(new Set(users.map(u => u.id)));
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
              <input type="text" value={settings.site_logo} onChange={e => setSettings({...settings, site_logo: e.target.value})} className="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg dark:text-white" />
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
        <p className="text-sm text-red-500 mb-6">These actions are destructive and cannot be undone.</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg flex flex-col justify-between h-full">
            <div>
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><UserX size={18} className="text-red-500" /> Wipe Specific Users</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">Target and delete specific user accounts and their associated banking data.</p>
            </div>
            <button onClick={() => setModalType('users')} className="w-full py-2 bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 rounded-lg font-bold transition-colors">
              Open User Wipe Utility
            </button>
          </div>

          <div className="p-4 bg-white dark:bg-slate-800 border border-red-100 dark:border-red-900/30 rounded-lg flex flex-col justify-between h-full">
            <div>
              <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><ServerCrash size={18} className="text-red-500" /> System Factory Reset</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">Perform a global wipe of financial data, user accounts, or the entire database.</p>
            </div>
            <button onClick={() => setModalType('reset')} className="w-full py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg font-bold shadow-lg transition-colors">
              Open Reset Utility
            </button>
          </div>
        </div>
      </div>

      {/* MODALS OVERLAY */}
      {modalType && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-2xl overflow-hidden border border-slate-700 shadow-2xl flex flex-col max-h-[90vh]">
            
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-900/50">
              <h2 className="text-lg font-bold flex items-center gap-2 text-slate-800 dark:text-white">
                <AlertTriangle className="text-red-500" /> 
                {modalType === 'users' ? 'User Wipe Utility' : 'System Factory Reset'}
              </h2>
              <button onClick={closeDangerModal} className="text-slate-400 hover:text-white"><X size={24} /></button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {dangerError && <div className="mb-4 p-3 bg-red-50 text-red-600 border border-red-200 rounded-lg text-sm">{dangerError}</div>}
              {dangerSuccess && <div className="mb-4 p-3 bg-green-50 text-green-600 border border-green-200 rounded-lg text-sm">{dangerSuccess}</div>}

              {/* STEP 1: PASSWORD GATE */}
              {!isUnlocked ? (
                <div className="space-y-4 py-8 text-center">
                  <ShieldAlert size={48} className="mx-auto text-red-500 opacity-80 mb-4" />
                  <h3 className="text-xl font-bold dark:text-white">SuperAdmin Authentication Required</h3>
                  <p className="text-slate-500 text-sm max-w-sm mx-auto">Please enter your master password to unlock this destructive utility.</p>
                  <div className="max-w-xs mx-auto flex gap-2 pt-4">
                    <input type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && verifyPasswordAndUnlock()} className="flex-1 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-lg dark:text-white outline-none focus:ring-2 focus:ring-red-500" placeholder="Password..." />
                    <button onClick={verifyPasswordAndUnlock} disabled={dangerLoading} className="px-4 py-2 bg-red-600 text-white rounded-lg font-bold hover:bg-red-700">{dangerLoading ? '...' : 'Unlock'}</button>
                  </div>
                </div>
              ) : (
                /* STEP 2: UNLOCKED CONTENT */
                <div className="space-y-6">
                  
                  {/* USER DELETION UI */}
                  {modalType === 'users' && (
                    <>
                      <div className="flex justify-between items-center bg-slate-100 dark:bg-slate-800 p-3 rounded-lg">
                        <span className="text-sm font-medium dark:text-slate-300">{selectedUsers.size} Users Selected</span>
                        <button onClick={toggleSelectAll} className="text-sm text-blue-600 dark:text-blue-400 font-bold">
                          {selectedUsers.size === users.length ? 'Deselect All' : 'Select All'}
                        </button>
                      </div>
                      
                      <div className="space-y-2 max-h-[40vh] overflow-y-auto pr-2">
                        {users.map(u => {
                          const userAccounts = accounts.filter(a => a.user_id === u.id);
                          const isExpanded = expandedUsers.has(u.id);
                          const isSelected = selectedUsers.has(u.id);
                          
                          return (
                            <div key={u.id} className={`border rounded-lg transition-colors ${isSelected ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800'}`}>
                              <div className="flex items-center p-3 gap-3">
                                <button onClick={() => toggleSelect(u.id)} className="text-slate-400 hover:text-red-500">
                                  {isSelected ? <CheckSquare className="text-red-500" /> : <Square />}
                                </button>
                                <div className="flex-1 cursor-pointer" onClick={() => toggleExpand(u.id)}>
                                  <div className="font-bold text-slate-800 dark:text-white text-sm">{u.name}</div>
                                  <div className="text-xs text-slate-500">{u.email}</div>
                                </div>
                                <button onClick={() => toggleExpand(u.id)} className="text-slate-400">
                                  {isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
                                </button>
                              </div>
                              
                              {/* Expanded Chevron Content */}
                              {isExpanded && (
                                <div className="p-3 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50">
                                  {userAccounts.length === 0 ? (
                                    <p className="text-xs text-slate-500 italic">No associated bank accounts.</p>
                                  ) : (
                                    <div className="space-y-2">
                                      {userAccounts.map(a => (
                                        <div key={a.account_number} className="flex justify-between text-xs dark:text-slate-300">
                                          <span className="font-mono">{a.account_number}</span>
                                          <span className="font-bold text-green-600 dark:text-green-400">${parseFloat(a.balance).toLocaleString()}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      <button onClick={executeUserDeletion} disabled={dangerLoading || selectedUsers.size === 0} className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow disabled:opacity-50">
                        {dangerLoading ? 'Processing...' : `Permanently Delete ${selectedUsers.size} User(s)`}
                      </button>
                    </>
                  )}

                  {/* SYSTEM RESET UI */}
                  {modalType === 'reset' && (
                    <div className="space-y-6">
                      <div className="space-y-3">
                        <label className={`flex p-4 border rounded-lg cursor-pointer transition-colors ${resetType === 'data' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : 'border-slate-200 dark:border-slate-700 dark:bg-slate-800'}`}>
                          <input type="radio" name="resetType" value="data" checked={resetType === 'data'} onChange={() => setResetType('data')} className="mt-1 mr-3" />
                          <div>
                            <div className="font-bold dark:text-white">Data Only (Soft Reset)</div>
                            <div className="text-sm text-slate-500">Wipes all transaction history and resets all balances to $0. Keeps user accounts intact.</div>
                          </div>
                        </label>

                        <label className={`flex p-4 border rounded-lg cursor-pointer transition-colors ${resetType === 'users' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : 'border-slate-200 dark:border-slate-700 dark:bg-slate-800'}`}>
                          <input type="radio" name="resetType" value="users" checked={resetType === 'users'} onChange={() => setResetType('users')} className="mt-1 mr-3" />
                          <div>
                            <div className="font-bold dark:text-white">Users Only</div>
                            <div className="text-sm text-slate-500">Deletes all customer accounts. System settings and staff accounts remain intact.</div>
                          </div>
                        </label>

                        <label className={`flex p-4 border rounded-lg cursor-pointer transition-colors ${resetType === 'both' ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : 'border-slate-200 dark:border-slate-700 dark:bg-slate-800'}`}>
                          <input type="radio" name="resetType" value="both" checked={resetType === 'both'} onChange={() => setResetType('both')} className="mt-1 mr-3" />
                          <div>
                            <div className="font-bold dark:text-white">Total Factory Reset (Hard Reset)</div>
                            <div className="text-sm text-slate-500">Wipes ALL user accounts, transactions, and balances. Leaves only the SuperAdmin account.</div>
                          </div>
                        </label>
                      </div>

                      <button onClick={executeSystemReset} disabled={dangerLoading} className="w-full py-3 bg-red-600 hover:bg-red-700 text-white font-bold rounded-lg shadow disabled:opacity-50">
                        {dangerLoading ? 'Executing Wipe...' : `Execute ${resetType.toUpperCase()} Reset`}
                      </button>
                    </div>
                  )}

                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"""
}

def apply_ultimate_danger_zone():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Ultimate Danger Zone Restored: Modals, Chevrons, and Password Gates are live!")

if __name__ == "__main__":
    apply_ultimate_danger_zone()
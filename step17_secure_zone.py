import os

files = {
    # --- 1. NEW API: VERIFY PASSWORD & CHECK ROLE ---
    "app/api/admin/verify-access/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/auth';
import bcrypt from 'bcryptjs';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { password } = await request.json();

  // 1. Fetch real user record
  const users: any = await query('SELECT * FROM users WHERE id = ?', [session.id]);
  if (users.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });
  const user = users[0];

  // 2. Verify Password
  const isMatch = await bcrypt.compare(password, user.password);
  if (!isMatch) {
    return NextResponse.json({ error: 'Incorrect password' }, { status: 401 });
  }

  // 3. Check Super Admin Status
  if (user.is_super_admin) {
    return NextResponse.json({ success: true });
  } else {
    // SECURITY INCIDENT! Regular Admin trying to access Danger Zone.
    
    // Find Super Admin ID (assuming the first one found)
    const superAdmins: any = await query('SELECT id FROM users WHERE is_super_admin = TRUE LIMIT 1');
    if (superAdmins.length > 0) {
        const superId = superAdmins[0].id;
        
        // Log Ticket
        await query(
            'INSERT INTO support_tickets (user_id, subject, message, status) VALUES (?, ?, ?, ?)',
            [session.id, 'SECURITY ALERT: Unauthorized Access Attempt', `User ${user.name} (${user.email}) tried to access the Danger Zone / Factory Reset.`, 'open']
        );

        // Send Notification
        await query(
            'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
            [superId, `SECURITY ALERT: ${user.name} tried to access Danger Zone!`, 'error']
        );
    }

    return NextResponse.json({ error: 'ACCESS DENIED. Incident reported to Super Admin.', incident: true }, { status: 403 });
  }
}
""",

    # --- 2. UPDATE SETTINGS PAGE (Hide Zone & Add Logic) ---
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Trash2, AlertTriangle, ChevronDown, ChevronUp, Save, Upload, Search, CheckSquare, Square, Lock, Unlock } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function MasterSettings() {
  // Settings State
  const [settings, setSettings] = useState({ site_name: '', site_logo: '', site_favicon: '' });
  const [loading, setLoading] = useState(false);

  // Security State
  const [showDangerZone, setShowDangerZone] = useState(false);
  
  // Manager State
  const [isCustomerModalOpen, setModalOpen] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [expandedUser, setExpandedUser] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => setSettings(data));
  }, []);

  const handleSave = async () => {
    const result = await Swal.fire({
        title: 'Save Changes?',
        text: 'Update site configuration?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#1E3A8A',
        confirmButtonText: 'Yes, Save'
    });

    if (!result.isConfirmed) return;
    setLoading(true);
    await fetch('/api/admin/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(settings)
    });
    setLoading(false);
    Swal.fire('Saved', 'Settings updated.', 'success');
    window.location.reload(); 
  };

  const handleFile = (e: any, key: string) => {
    const file = e.target.files[0];
    if (file) {
        if (file.size > 500 * 1024) return Swal.fire('Error', 'Max file size 500KB', 'error');
        const reader = new FileReader();
        reader.onloadend = () => setSettings({ ...settings, [key]: reader.result });
        reader.readAsDataURL(file);
    }
  };

  // --- SECURITY UNLOCK LOGIC ---
  const unlockDangerZone = async () => {
    const { value: password } = await Swal.fire({
        title: 'Security Verification',
        text: 'Enter your password to unlock Advanced Settings.',
        input: 'password',
        inputPlaceholder: 'Your Password',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Verify Access'
    });

    if (password) {
        const res = await fetch('/api/admin/verify-access', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ password })
        });

        const data = await res.json();

        if (res.ok) {
            setShowDangerZone(true);
            Swal.fire({
                toast: true, position: 'top-end', icon: 'success', 
                title: 'Access Granted', timer: 2000, showConfirmButton: false
            });
        } else {
            if (data.incident) {
                Swal.fire('ACCESS DENIED', 'This incident has been reported to the Super Admin.', 'error');
            } else {
                Swal.fire('Error', 'Incorrect Password', 'error');
            }
        }
    }
  };

  // --- DANGER ZONE ACTIONS ---
  const openCustomerManager = async () => {
    const res = await fetch('/api/admin/customers/details');
    setCustomers(await res.json());
    setModalOpen(true);
    setSelectedIds([]); 
  };

  const filteredCustomers = customers.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.account_number?.includes(searchQuery)
  );

  const toggleSelectAll = () => {
    setSelectedIds(selectedIds.length === filteredCustomers.length ? [] : filteredCustomers.map(c => c.id));
  };

  const toggleSelectOne = (id: number) => {
    setSelectedIds(selectedIds.includes(id) ? selectedIds.filter(sid => sid !== id) : [...selectedIds, id]);
  };

  const handleBulkDelete = async () => {
    const result = await Swal.fire({
        title: `Delete ${selectedIds.length} Users?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, Delete'
    });

    if (result.isConfirmed) {
        await fetch('/api/admin/users/bulk-delete', { method: 'POST', body: JSON.stringify({ ids: selectedIds }) });
        setCustomers(customers.filter(c => !selectedIds.includes(c.id)));
        setSelectedIds([]);
        Swal.fire('Deleted', 'Users removed.', 'success');
    }
  };

  const resetSystem = async () => {
    const res = await Swal.fire({
        title: '⚠️ FACTORY RESET?',
        text: 'WIPE ENTIRE DATABASE? Only Super Admin remains.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'NUKE EVERYTHING'
    });

    if (res.isConfirmed) {
        const finalCheck = await Swal.fire({ title: 'Final Warning', input: 'text', inputLabel: 'Type "CONFIRM"', showCancelButton: true });
        if (finalCheck.value === 'CONFIRM') {
            await fetch('/api/admin/danger/reset', { method: 'DELETE' });
            Swal.fire('System Reset', 'Database wiped.', 'success');
            window.location.href = '/login';
        }
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold dark:text-white">Master Settings</h2>

      {/* 1. General Settings */}
      <Card>
        <h3 className="text-lg font-bold mb-4 dark:text-slate-200">General Configuration</h3>
        <div className="space-y-4">
            <Input label="Site Name" value={settings.site_name} onChange={e => setSettings({...settings, site_name: e.target.value})} />
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium mb-2 dark:text-slate-300">Site Logo</label>
                    <div className="flex items-center gap-4">
                        {settings.site_logo && <img src={settings.site_logo} className="h-12 w-12 object-contain bg-slate-100 rounded" />}
                        <label className="cursor-pointer bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-200 transition text-sm flex items-center gap-2">
                            <Upload size={16}/> Upload
                            <input type="file" className="hidden" onChange={e => handleFile(e, 'site_logo')} />
                        </label>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium mb-2 dark:text-slate-300">Favicon</label>
                    <div className="flex items-center gap-4">
                        {settings.site_favicon && <img src={settings.site_favicon} className="h-8 w-8 object-contain bg-slate-100 rounded" />}
                        <label className="cursor-pointer bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded border border-slate-300 dark:border-slate-700 hover:bg-slate-200 transition text-sm flex items-center gap-2">
                            <Upload size={16}/> Upload
                            <input type="file" className="hidden" onChange={e => handleFile(e, 'site_favicon')} />
                        </label>
                    </div>
                </div>
            </div>
            
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button onClick={handleSave} disabled={loading} className="w-fit">
                    <Save size={18} className="mr-2"/> Save Settings
                </Button>

                {!showDangerZone && (
                    <button 
                        onClick={unlockDangerZone} 
                        className="text-red-500 hover:text-red-700 text-sm font-semibold flex items-center gap-2 px-4 py-2 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition"
                    >
                        <Lock size={16} /> Unlock Advanced Settings
                    </button>
                )}
            </div>
        </div>
      </Card>

      {/* 2. DANGER ZONE (Hidden by default) */}
      {showDangerZone && (
          <div className="border border-red-200 bg-red-50 dark:bg-red-900/10 rounded-xl p-6 animate-in slide-in-from-top-4 fade-in duration-500">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-red-700 flex items-center gap-2">
                    <AlertTriangle size={24}/> Danger Zone
                </h3>
                <button onClick={() => setShowDangerZone(false)} className="text-slate-400 hover:text-slate-600 flex items-center gap-1 text-sm">
                    <Unlock size={14} /> Lock Zone
                </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                    <h4 className="font-bold dark:text-white">Full System Reset</h4>
                    <p className="text-sm text-slate-500 mb-4">Wipes all customers, transactions, and messages. Keeps Super Admin.</p>
                    <Button variant="danger" onClick={resetSystem} className="w-full">Reset System</Button>
                </div>

                <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                    <h4 className="font-bold dark:text-white">Customer Data Manager</h4>
                    <p className="text-sm text-slate-500 mb-4">View detailed balances and bulk delete customers.</p>
                    <Button variant="secondary" onClick={openCustomerManager} className="w-full">Manage Customers</Button>
                </div>
            </div>
          </div>
      )}

      {/* Customer Manager Modal */}
      <Modal isOpen={isCustomerModalOpen} onClose={() => setModalOpen(false)} title="Customer Manager">
        <div className="flex flex-col h-[70vh]">
            <div className="flex justify-between items-center mb-4 gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input 
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border rounded-lg text-sm" 
                        placeholder="Search users..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
                {selectedIds.length > 0 && (
                    <Button variant="danger" size="sm" onClick={handleBulkDelete}>
                        Delete ({selectedIds.length})
                    </Button>
                )}
            </div>

            <div className="flex items-center gap-3 p-2 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-bold text-sm text-slate-600 dark:text-slate-300">
                 <button onClick={toggleSelectAll}>
                    {selectedIds.length === filteredCustomers.length && filteredCustomers.length > 0 ? (
                        <CheckSquare size={20} className="text-blue-600" />
                    ) : (
                        <Square size={20} className="text-slate-400" />
                    )}
                 </button>
                 <span>Select All ({filteredCustomers.length})</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-2 mt-2">
                {filteredCustomers.map((c: any) => (
                    <div key={c.id} className={`border rounded-lg overflow-hidden ${selectedIds.includes(c.id) ? 'border-blue-500 ring-1 ring-blue-500' : 'border-slate-200 dark:border-slate-700'}`}>
                        <div className="p-3 bg-white dark:bg-slate-900 flex items-center gap-3">
                            <button onClick={(e) => { e.stopPropagation(); toggleSelectOne(c.id); }} className="shrink-0">
                                {selectedIds.includes(c.id) ? <CheckSquare size={20} className="text-blue-600"/> : <Square size={20} className="text-slate-300"/>}
                            </button>
                            
                            <div 
                                className="flex-1 flex justify-between items-center cursor-pointer min-w-0"
                                onClick={() => setExpandedUser(expandedUser === c.id ? null : c.id)}
                            >
                                <div className="flex-1 min-w-0 mr-2">
                                    <div className="font-bold text-sm dark:text-slate-200 truncate">{c.name}</div>
                                    <div className="text-xs text-slate-500 truncate" title={c.email}>{c.email}</div>
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                     <span className="hidden sm:inline-block text-xs font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                        {c.account_number}
                                     </span>
                                     {expandedUser === c.id ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                                </div>
                            </div>
                        </div>
                        
                        {expandedUser === c.id && (
                            <div className="p-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 text-sm">
                                <div className="sm:hidden mb-3">
                                    <span className="block text-xs text-slate-500">Account Number</span>
                                    <span className="font-mono text-xs bg-white px-2 py-1 rounded border">{c.account_number}</span>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div><span className="block text-xs text-slate-500">Balance</span><span className="font-bold text-green-600">${Number(c.balance).toLocaleString()}</span></div>
                                    <div><span className="block text-xs text-slate-500">Transactions</span><span className="dark:text-slate-300">{c.tx_count}</span></div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
      </Modal>
    </div>
  );
}
"""
}

def secure_zone():
    print("🔒 Securing Danger Zone with Authentication...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    secure_zone()
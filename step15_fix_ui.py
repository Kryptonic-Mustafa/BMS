import os

files = {
    # --- 1. UPDATE MODAL (Make it wider on Desktop) ---
    "components/ui/Modal.tsx": """
'use client';
import { X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity" onClick={onClose} />
      {/* UPDATED: Changed max-w-md to md:max-w-2xl lg:max-w-3xl to give more space */}
      <div className="relative bg-white dark:bg-slate-900 w-full max-w-md md:max-w-2xl lg:max-w-3xl rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
        <div className="flex justify-between items-center p-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <X size={20} />
          </button>
        </div>
        <div className="p-6 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}
""",

    # --- 2. UPDATE SETTINGS PAGE (Fix List Item Overflow) ---
    "app/(dashboard)/admin/settings/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { Trash2, AlertTriangle, ChevronDown, ChevronUp, Save, Upload, Search, CheckSquare, Square } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function MasterSettings() {
  const [settings, setSettings] = useState({ site_name: '', site_logo: '', site_favicon: '' });
  const [loading, setLoading] = useState(false);
  const [isCustomerModalOpen, setModalOpen] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [expandedUser, setExpandedUser] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetch('/api/admin/settings').then(res => res.json()).then(data => setSettings(data));
  }, []);

  const handleSave = async () => {
    setLoading(true);
    await fetch('/api/admin/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(settings)
    });
    setLoading(false);
    Swal.fire('Saved', 'System settings updated.', 'success');
    window.location.reload(); 
  };

  const handleFile = (e: any, key: string) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onloadend = () => setSettings({ ...settings, [key]: reader.result });
        reader.readAsDataURL(file);
    }
  };

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
    if (selectedIds.length === filteredCustomers.length) {
        setSelectedIds([]);
    } else {
        setSelectedIds(filteredCustomers.map(c => c.id));
    }
  };

  const toggleSelectOne = (id: number) => {
    if (selectedIds.includes(id)) {
        setSelectedIds(selectedIds.filter(sid => sid !== id));
    } else {
        setSelectedIds([...selectedIds, id]);
    }
  };

  const handleBulkDelete = async () => {
    const result = await Swal.fire({
        title: `Delete ${selectedIds.length} Users?`,
        text: 'This cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Yes, Delete Selected'
    });

    if (result.isConfirmed) {
        await fetch('/api/admin/users/bulk-delete', {
            method: 'POST',
            body: JSON.stringify({ ids: selectedIds })
        });
        const remaining = customers.filter(c => !selectedIds.includes(c.id));
        setCustomers(remaining);
        setSelectedIds([]);
        Swal.fire('Deleted!', 'Users have been removed.', 'success');
    }
  };

  const resetSystem = async () => {
    const res = await Swal.fire({
        title: '⚠️ FACTORY RESET?',
        text: 'Delete ALL users & data? Only Super Admin remains.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'NUKE EVERYTHING'
    });

    if (res.isConfirmed) {
        const finalCheck = await Swal.fire({ title: 'Final Warning', input: 'text', inputLabel: 'Type "CONFIRM"', showCancelButton: true });
        if (finalCheck.value === 'CONFIRM') {
            await fetch('/api/admin/danger/reset', { method: 'DELETE' });
            Swal.fire('System Reset', 'The database has been wiped.', 'success');
            window.location.href = '/login';
        }
    }
  };

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold dark:text-white">Master Settings</h2>

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
            <Button onClick={handleSave} disabled={loading} className="w-fit">
                <Save size={18} className="mr-2"/> {loading ? 'Saving...' : 'Save Settings'}
            </Button>
        </div>
      </Card>

      <div className="border border-red-200 bg-red-50 dark:bg-red-900/10 rounded-xl p-6">
        <h3 className="text-lg font-bold text-red-700 flex items-center gap-2 mb-4">
            <AlertTriangle size={24}/> Danger Zone
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                <h4 className="font-bold dark:text-white">Full System Reset</h4>
                <p className="text-sm text-slate-500 mb-4">Wipes all data except Super Admin.</p>
                <Button variant="danger" onClick={resetSystem} className="w-full">Reset System</Button>
            </div>
            <div className="bg-white dark:bg-slate-900 p-4 rounded-lg border border-red-100 dark:border-red-900/30">
                <h4 className="font-bold dark:text-white">Customer Data Manager</h4>
                <p className="text-sm text-slate-500 mb-4">Bulk delete and manage customers.</p>
                <Button variant="secondary" onClick={openCustomerManager} className="w-full">Manage Customers</Button>
            </div>
        </div>
      </div>

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
                            {/* Checkbox */}
                            <button onClick={(e) => { e.stopPropagation(); toggleSelectOne(c.id); }} className="shrink-0">
                                {selectedIds.includes(c.id) ? <CheckSquare size={20} className="text-blue-600"/> : <Square size={20} className="text-slate-300"/>}
                            </button>
                            
                            {/* User Info Row - UPDATED FOR RESPONSIVENESS */}
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
                                {/* Mobile-only Account Number display */}
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

def fix_ui():
    print("🎨 Fixing Modal Width & Overflow Issues...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_ui()
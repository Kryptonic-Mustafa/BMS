import os

files = {
    # --- 1. UPDATE NOTIFICATION PAGE (Change AlertOctagon to Trash2) ---
    "app/(dashboard)/notifications/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
// FIXED: Removed AlertOctagon, ensuring Trash2 is used everywhere for delete
import { Check, Trash2, Bell, CheckCircle, AlertTriangle, Info, MailOpen, Mail, X } from 'lucide-react';
import Swal from 'sweetalert2';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [filter, setFilter] = useState('all'); // 'all', 'unread'
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const fetchNotifications = async () => {
    const res = await fetch('/api/notifications?limit=50');
    if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
    }
  };

  useEffect(() => { fetchNotifications(); }, []);

  // --- BULK ACTION LOGIC ---
  const toggleSelect = (id: number) => {
    setSelectedIds(prev => 
        prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === filtered.length && filtered.length > 0) {
        setSelectedIds([]);
    } else {
        setSelectedIds(filtered.map(n => n.id));
    }
  };

  const handleBulkAction = async (action: 'read' | 'unread' | 'delete') => {
    if (selectedIds.length === 0) return;

    if (action === 'delete') {
        const result = await Swal.fire({
            title: `Delete ${selectedIds.length} items?`,
            text: "This action cannot be undone.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#EF4444',
            confirmButtonText: 'Yes, Delete'
        });
        if (!result.isConfirmed) return;
    }

    for (const id of selectedIds) {
        if (action === 'delete') {
            await fetch('/api/notifications', { method: 'DELETE', body: JSON.stringify({ id }) });
        } else {
             await fetch('/api/notifications', { 
                method: 'PUT', 
                body: JSON.stringify({ id, status: action === 'read' })
            });
        }
    }

    // Optimistic UI Update
    if (action === 'delete') {
        setNotifications(prev => prev.filter(n => !selectedIds.includes(n.id)));
    } else {
        const isRead = action === 'read';
        setNotifications(prev => prev.map(n => selectedIds.includes(n.id) ? { ...n, is_read: isRead } : n));
    }
    
    setSelectedIds([]); // Clear selection
    
    const Toast = Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000 });
    Toast.fire({ icon: 'success', title: `Marked ${selectedIds.length} items as ${action}` });
  };

  // --- RENDER HELPERS ---
  const getIcon = (type: string) => {
    switch(type) {
        case 'success': return <CheckCircle size={20} className="text-green-500" />;
        case 'error': return <AlertTriangle size={20} className="text-red-500" />;
        default: return <Info size={20} className="text-blue-500" />;
    }
  };

  const filtered = filter === 'unread' ? notifications.filter(n => !n.is_read) : notifications;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
            <Bell className="text-blue-600"/> Notification Center
        </h2>
        
        <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-lg flex gap-1">
            <button 
                onClick={() => setFilter('all')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition ${filter === 'all' ? 'bg-white dark:bg-slate-700 shadow text-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-700'}`}
            >
                All
            </button>
            <button 
                onClick={() => setFilter('unread')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition ${filter === 'unread' ? 'bg-white dark:bg-slate-700 shadow text-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-700'}`}
            >
                Unread
            </button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden min-h-[500px] flex flex-col">
        {/* TOOLBAR */}
        <div className="p-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center h-14">
            <div className="flex items-center gap-4 pl-2">
                <label className="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 cursor-pointer select-none">
                    <input 
                        type="checkbox" 
                        className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-gray-300"
                        checked={selectedIds.length > 0 && selectedIds.length === filtered.length}
                        onChange={toggleSelectAll}
                    />
                    <span>Select All</span>
                </label>
                
                {selectedIds.length > 0 && (
                    <div className="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-200">
                        <div className="h-4 w-[1px] bg-slate-300 mx-2"></div>
                        <span className="text-xs font-semibold bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                            {selectedIds.length} selected
                        </span>
                        
                        <button onClick={() => handleBulkAction('read')} className="p-1.5 text-slate-500 hover:text-green-600 hover:bg-green-50 rounded transition" title="Mark as Read">
                            <MailOpen size={18}/>
                        </button>
                        
                        <button onClick={() => handleBulkAction('unread')} className="p-1.5 text-slate-500 hover:text-orange-600 hover:bg-orange-50 rounded transition" title="Mark as Unread">
                            <Mail size={18}/>
                        </button>

                        {/* FIXED: Dustbin Icon for Delete */}
                        <button onClick={() => handleBulkAction('delete')} className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition" title="Delete Selected">
                            <Trash2 size={18}/>
                        </button>

                        <button onClick={() => setSelectedIds([])} className="p-1.5 text-slate-400 hover:text-slate-600 rounded transition" title="Cancel Selection">
                            <X size={18}/>
                        </button>
                    </div>
                )}
            </div>
        </div>

        {/* LIST */}
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.map((n: any) => (
                <div 
                    key={n.id} 
                    className={`group p-4 flex gap-4 transition items-start hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                        selectedIds.includes(n.id) ? 'bg-blue-50 dark:bg-blue-900/20' : 
                        n.is_read ? 'bg-white dark:bg-slate-900 opacity-70' : 'bg-white dark:bg-slate-900'
                    }`}
                >
                    <div className="pt-1">
                        <input 
                            type="checkbox" 
                            className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500 border-gray-300 cursor-pointer"
                            checked={selectedIds.includes(n.id)}
                            onChange={() => toggleSelect(n.id)}
                        />
                    </div>

                    <div className="mt-0.5 shrink-0">{getIcon(n.type)}</div>
                    
                    <div className="flex-1 cursor-pointer" onClick={() => toggleSelect(n.id)}>
                        <div className="flex justify-between items-start">
                            <p className={`text-sm ${n.is_read ? 'text-slate-600 dark:text-slate-400 font-normal' : 'text-slate-900 dark:text-white font-bold'}`}>
                                {n.message}
                            </p>
                            <span className="text-xs text-slate-400 whitespace-nowrap ml-4">
                                {new Date(n.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                             {new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </p>
                    </div>

                    {/* HOVER ACTIONS */}
                    <div className="opacity-0 group-hover:opacity-100 transition flex items-center gap-2">
                        {n.is_read ? (
                             <button onClick={() => { setSelectedIds([n.id]); handleBulkAction('unread'); }} className="text-slate-400 hover:text-blue-600" title="Mark Unread"><Mail size={16}/></button>
                        ) : (
                             <button onClick={() => { setSelectedIds([n.id]); handleBulkAction('read'); }} className="text-slate-400 hover:text-green-600" title="Mark Read"><MailOpen size={16}/></button>
                        )}
                        <button onClick={() => { setSelectedIds([n.id]); handleBulkAction('delete'); }} className="text-slate-400 hover:text-red-600" title="Delete"><Trash2 size={16}/></button>
                    </div>
                </div>
            ))}
            
            {filtered.length === 0 && (
                <div className="p-12 text-center text-slate-400 flex flex-col items-center justify-center h-64">
                    <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-full mb-3">
                        <Bell size={32} className="opacity-20"/>
                    </div>
                    <p>No notifications found.</p>
                </div>
            )}
        </div>
      </Card>
    </div>
  );
}
""",

    # --- 2. UPDATE NOTIFICATION BELL (Water Droplet Animation) ---
    "components/layout/NotificationBell.tsx": """
'use client';
import { useState, useEffect, useRef } from 'react';
import { Bell, Check, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<any[]>([]);
  const dropdownRef = useRef<any>(null);
  const router = useRouter();

  const fetchNotifications = async () => {
    const res = await fetch('/api/notifications');
    if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.unreadCount || 0);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: any) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAsRead = async (id?: number) => {
    await fetch('/api/notifications', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, markAll: !id, status: true })
    });
    if (id) {
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
        setUnreadCount(prev => Math.max(0, prev - 1));
    } else {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
    }
  };

  const getIcon = (type: string) => {
    switch(type) {
        case 'success': return <CheckCircle size={16} className="text-green-600" />;
        case 'error': return <AlertTriangle size={16} className="text-red-500" />;
        default: return <Info size={16} className="text-blue-500" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition relative"
      >
        <Bell size={20} className="text-slate-600 dark:text-slate-300" />
        
        {/* WATER DROPLET RIPPLE ANIMATION */}
        {unreadCount > 0 && (
            <span className="absolute top-1 right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500 ring-2 ring-white dark:ring-slate-900"></span>
            </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center bg-slate-50 dark:bg-slate-800/50">
                <h3 className="font-bold text-sm text-slate-800 dark:text-white">Notifications</h3>
                {unreadCount > 0 && (
                    <button onClick={() => markAsRead()} className="text-xs text-blue-600 hover:text-blue-500 flex items-center gap-1 font-medium">
                        <Check size={12}/> Mark all read
                    </button>
                )}
            </div>

            <div className="max-h-[350px] overflow-y-auto">
                {notifications.length > 0 ? (
                    notifications.map((n) => (
                        <div 
                            key={n.id} 
                            onClick={() => !n.is_read && markAsRead(n.id)}
                            className={`p-4 border-b border-slate-50 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer flex gap-3 ${
                                n.is_read ? 'bg-white dark:bg-slate-900' : 'bg-blue-50/50 dark:bg-blue-900/10'
                            }`}
                        >
                            <div className="mt-1 shrink-0">{getIcon(n.type)}</div>
                            <div>
                                <p className={`text-sm ${n.is_read ? 'text-slate-700 dark:text-slate-300' : 'text-slate-900 dark:text-white font-bold'}`}>
                                    {n.message}
                                </p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </p>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="p-8 text-center text-slate-500">
                        <Bell size={32} className="mx-auto mb-2 opacity-20"/>
                        <p className="text-sm">No notifications yet.</p>
                    </div>
                )}
            </div>
            
            <div className="p-2 bg-slate-50 dark:bg-slate-800 text-center border-t border-slate-100 dark:border-slate-800">
                <button 
                    onClick={() => { setIsOpen(false); router.push('/notifications'); }} 
                    className="text-xs font-bold text-blue-600 hover:text-blue-800 uppercase tracking-wide"
                >
                    View Full History
                </button>
            </div>
        </div>
      )}
    </div>
  );
}
"""
}

def polish_ui():
    print("✨ Polishing UI: Setting Dustbin Icon & Water Droplet Animation...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    polish_ui()
import os

files = {
    # --- 1. UPDATED NOTIFICATION PAGE (Bulk Actions + Checkboxes) ---
    "app/(dashboard)/notifications/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, Trash2, Bell, CheckCircle, AlertTriangle, Info, MailOpen, Mail, X, AlertOctagon } from 'lucide-react';
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
    if (selectedIds.length === filtered.length) {
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

    // Call API (We loop for now, in production use a bulk API endpoint)
    // For this demo, we assume the API handles single ID updates, so we loop perfectly fine for small batches
    for (const id of selectedIds) {
        if (action === 'delete') {
            await fetch('/api/notifications', { method: 'DELETE', body: JSON.stringify({ id }) });
        } else {
            // We use a small hack: If action is 'unread', we assume the API supports toggling or we update client side
            // Ideally, update API to support 'is_read: false'. 
            // For now, let's assume 'read' marks TRUE. 'unread' logic below handles UI state.
             await fetch('/api/notifications', { 
                method: 'PUT', 
                body: JSON.stringify({ id, status: action === 'read' }) // API update needed to support explicit status
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
    
    // Quick Toast
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
        
        {/* IMPROVED TABS */}
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
                        
                        {/* MARK READ */}
                        <button onClick={() => handleBulkAction('read')} className="p-1.5 text-slate-500 hover:text-green-600 hover:bg-green-50 rounded transition" title="Mark as Read">
                            <MailOpen size={18}/>
                        </button>
                        
                        {/* MARK UNREAD */}
                        <button onClick={() => handleBulkAction('unread')} className="p-1.5 text-slate-500 hover:text-orange-600 hover:bg-orange-50 rounded transition" title="Mark as Unread">
                            <Mail size={18}/>
                        </button>

                        {/* DELETE DANGER */}
                        <button onClick={() => handleBulkAction('delete')} className="p-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded transition" title="Delete Selected">
                            <AlertOctagon size={18}/>
                        </button>

                        {/* CLEAR SELECTION */}
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
                    {/* CHECKBOX */}
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

    # --- 2. UPDATE NOTIFICATION API (To Support Explicit Read/Unread Status) ---
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  // Fetch notifications
  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
    [session.id]
  );
  
  // Fetch count
  const count: any = await query(
    'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE',
    [session.id]
  );

  return NextResponse.json({ 
    notifications, 
    unreadCount: count[0].count 
  });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id, markAll, status } = await request.json();

  // If status is provided explicitly (true=read, false=unread)
  // If not provided, default to true (read)
  const isRead = status !== undefined ? status : true;

  if (markAll) {
    await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  } else if (id) {
    await query('UPDATE notifications SET is_read = ? WHERE id = ? AND user_id = ?', [isRead, id, session.id]);
  }

  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  const { id } = await request.json();
  if (id) {
      await query('DELETE FROM notifications WHERE id = ? AND user_id = ?', [id, session.id]);
  }
  return NextResponse.json({ success: true });
}
"""
}

def upgrade_notifications():
    print("🔔 Upgrading Notification Center (Bulk Actions, Checkboxes)...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    upgrade_notifications()
import os

files = {
    # --- 1. NEW PAGE: ALL NOTIFICATIONS ---
    "app/(dashboard)/notifications/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, Trash2, Bell, CheckCircle, AlertTriangle, Info, Filter } from 'lucide-react';
import Swal from 'sweetalert2';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all', 'unread'

  const fetchNotifications = async () => {
    // We reuse the API but fetch ALL history
    const res = await fetch('/api/notifications?limit=50');
    if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
    }
  };

  useEffect(() => { fetchNotifications(); }, []);

  const handleAction = async (id: number | null, action: 'read' | 'delete') => {
    // This calls the API to update status
    await fetch('/api/notifications', {
        method: action === 'read' ? 'PUT' : 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id, markAll: !id })
    });
    
    // Optimistic Update
    if (action === 'read') {
        if (!id) setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        else setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } else {
        if (!id) setNotifications([]);
        else setNotifications(prev => prev.filter(n => n.id !== id));
    }
  };

  const getIcon = (type: string) => {
    switch(type) {
        case 'success': return <CheckCircle size={20} className="text-green-500" />;
        case 'error': return <AlertTriangle size={20} className="text-red-500" />;
        default: return <Info size={20} className="text-blue-500" />;
    }
  };

  const filtered = filter === 'unread' ? notifications.filter((n: any) => !n.is_read) : notifications;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <h2 className="text-2xl font-bold dark:text-white flex items-center gap-2">
            <Bell className="text-blue-600"/> Notification Center
        </h2>
        <div className="flex gap-2">
            <Button variant={filter === 'all' ? 'primary' : 'secondary'} onClick={() => setFilter('all')}>All</Button>
            <Button variant={filter === 'unread' ? 'primary' : 'secondary'} onClick={() => setFilter('unread')}>Unread</Button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
            <span className="text-sm font-bold text-slate-700 dark:text-slate-300">
                {filtered.length} Notifications
            </span>
            <div className="flex gap-2">
                <button onClick={() => handleAction(null, 'read')} className="text-xs flex items-center gap-1 text-blue-600 hover:text-blue-700 px-2 py-1 hover:bg-blue-50 rounded transition">
                    <Check size={14}/> Mark All Read
                </button>
                <button onClick={() => handleAction(null, 'delete')} className="text-xs flex items-center gap-1 text-red-600 hover:text-red-700 px-2 py-1 hover:bg-red-50 rounded transition">
                    <Trash2 size={14}/> Clear All
                </button>
            </div>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.map((n: any) => (
                <div key={n.id} className={`p-4 flex gap-4 transition hover:bg-slate-50 dark:hover:bg-slate-800/50 ${n.is_read ? 'bg-white dark:bg-slate-900' : 'bg-blue-50/30 dark:bg-blue-900/10'}`}>
                    <div className="mt-1 shrink-0">{getIcon(n.type)}</div>
                    <div className="flex-1">
                        <div className="flex justify-between items-start">
                            <p className={`text-sm ${n.is_read ? 'text-slate-700 dark:text-slate-300' : 'text-slate-900 dark:text-white font-bold'}`}>
                                {n.message}
                            </p>
                            <span className="text-xs text-slate-400 whitespace-nowrap ml-4">
                                {new Date(n.created_at).toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-end gap-3 mt-2">
                            {!n.is_read && (
                                <button onClick={() => handleAction(n.id, 'read')} className="text-xs text-blue-600 hover:underline">Mark Read</button>
                            )}
                            <button onClick={() => handleAction(n.id, 'delete')} className="text-xs text-slate-400 hover:text-red-500">Delete</button>
                        </div>
                    </div>
                </div>
            ))}
            {filtered.length === 0 && (
                <div className="p-12 text-center text-slate-400">
                    <Bell size={48} className="mx-auto mb-3 opacity-20"/>
                    <p>No notifications found.</p>
                </div>
            )}
        </div>
      </Card>
    </div>
  );
}
""",

    # --- 2. UPDATE BELL DROPDOWN (Fix Text Color & Link) ---
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
        body: JSON.stringify({ id, markAll: !id })
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
        {unreadCount > 0 && (
            <span className="absolute top-1 right-1 h-2.5 w-2.5 bg-red-500 rounded-full ring-2 ring-white dark:ring-slate-900 animate-pulse"></span>
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
                                    {!n.is_read && <span className="ml-2 inline-block w-2 h-2 bg-blue-500 rounded-full"></span>}
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
""",

    # --- 3. RESTORE 3-BUTTON THEME TOGGLE (In Navbar) ---
    "components/layout/Navbar.tsx": """
'use client';
import { Sun, Moon, Monitor, Search } from 'lucide-react';
import { useTheme } from 'next-themes';
import NotificationBell from './NotificationBell';
import { useEffect, useState } from 'react';

export function Navbar({ user }: { user: any }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => { setMounted(true); }, []);

  if (!mounted) return null;

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-8 z-20 relative">
      <div className="flex items-center w-full max-w-md bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2">
        <Search size={18} className="text-slate-400 mr-2" />
        <input 
          type="text" 
          placeholder="Search..." 
          className="bg-transparent border-none outline-none text-sm w-full dark:text-white placeholder:text-slate-500" 
        />
      </div>

      <div className="flex items-center gap-4">
        {/* 3-BUTTON THEME TOGGLE */}
        <div className="hidden md:flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button 
                onClick={() => setTheme('light')}
                className={`p-1.5 rounded-md transition ${theme === 'light' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
                <Sun size={16} />
            </button>
            <button 
                onClick={() => setTheme('system')}
                className={`p-1.5 rounded-md transition ${theme === 'system' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
                <Monitor size={16} />
            </button>
            <button 
                onClick={() => setTheme('dark')}
                className={`p-1.5 rounded-md transition ${theme === 'dark' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
            >
                <Moon size={16} />
            </button>
        </div>

        {/* NOTIFICATION CENTER */}
        <NotificationBell />

        <div className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-700">
          <div className="text-right hidden md:block">
            <p className="text-sm font-bold text-slate-800 dark:text-white leading-none">{user.name}</p>
            <p className="text-xs text-slate-500 mt-1 capitalize">{user.role}</p>
          </div>
          <div className="h-9 w-9 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
            {user.name ? user.name.substring(0, 2).toUpperCase() : 'U'}
          </div>
        </div>
      </div>
    </header>
  );
}
"""
}

def fix_notifications_and_theme():
    print("🔔 Installing Notifications Page & Restoring Theme Buttons...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_notifications_and_theme()
import os

files = {
    # --- 1. ROBUST NOTIFICATION API ---
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  // Fetch last 15 notifications
  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 15',
    [session.id]
  );
  
  // Fetch count of unread
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

  const { id, markAll } = await request.json();

  if (markAll) {
    await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  } else if (id) {
    await query('UPDATE notifications SET is_read = TRUE WHERE id = ? AND user_id = ?', [id, session.id]);
  }

  return NextResponse.json({ success: true });
}
""",

    # --- 2. NEW COMPONENT: NOTIFICATION BELL ---
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
    // Poll every 30 seconds for new alerts
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event: any) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
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
    
    // Update local state instantly for snappiness
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
        case 'success': return <CheckCircle size={16} className="text-green-500" />;
        case 'error': return <AlertTriangle size={16} className="text-red-500" />;
        default: return <Info size={16} className="text-blue-500" />;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* BELL ICON */}
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition relative"
      >
        <Bell size={20} className="text-slate-600 dark:text-slate-300" />
        {unreadCount > 0 && (
            <span className="absolute top-1 right-1 h-2.5 w-2.5 bg-red-500 rounded-full ring-2 ring-white dark:ring-slate-900 animate-pulse"></span>
        )}
      </button>

      {/* DROPDOWN */}
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
                                n.is_read ? 'opacity-60' : 'bg-blue-50/50 dark:bg-blue-900/10'
                            }`}
                        >
                            <div className="mt-1 shrink-0">{getIcon(n.type)}</div>
                            <div>
                                <p className={`text-sm ${n.is_read ? 'text-slate-600 dark:text-slate-400' : 'text-slate-900 dark:text-white font-semibold'}`}>
                                    {n.message}
                                </p>
                                <p className="text-xs text-slate-400 mt-1">
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
                <button onClick={() => router.push('/messages')} className="text-xs text-slate-500 hover:text-slate-700">View All History</button>
            </div>
        </div>
      )}
    </div>
  );
}
""",

    # --- 3. INJECT INTO NAVBAR ---
    "components/layout/Navbar.tsx": """
'use client';
import { Sun, Moon, Search } from 'lucide-react';
import { useTheme } from '@/components/theme-provider';
import NotificationBell from './NotificationBell';

export function Navbar({ user }: { user: any }) {
  const { theme, setTheme } = useTheme();

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
        <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
        >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

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

def install_notifications():
    print("🔔 Installing Notification Center...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    install_notifications()
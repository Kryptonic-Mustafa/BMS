import os

files = {
    # --- 1. CREATE DEDICATED TOAST LISTENER HOOK ---
    "components/layout/GlobalToastListener.tsx": """
'use client';
import { useEffect, useRef } from 'react';
import Swal from 'sweetalert2';

export function GlobalToastListener() {
  const lastNotifIdRef = useRef<number>(0);
  const isFirstLoad = useRef(true);

  useEffect(() => {
    const checkNotifications = async () => {
      try {
        const res = await fetch('/api/notifications');
        if (!res.ok) return;
        
        const data = await res.json();
        const list = data.notifications || [];

        if (list.length > 0) {
            const latest = list[0];
            
            // If this is the very first load, just sync the ID (don't spam toasts for old stuff)
            if (isFirstLoad.current) {
                lastNotifIdRef.current = latest.id;
                isFirstLoad.current = false;
                return;
            }

            // If we found a NEW notification (ID > last seen)
            if (latest.id > lastNotifIdRef.current) {
                // Play Sound (Optional, for emphasis)
                // const audio = new Audio('/notification.mp3'); audio.play().catch(() => {});

                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: latest.type === 'success' ? 'success' : latest.type === 'error' ? 'error' : 'info',
                    title: latest.type === 'success' ? 'Success!' : latest.type === 'error' ? 'Alert!' : 'New Notification',
                    text: latest.message,
                    showConfirmButton: false,
                    timer: 6000,
                    timerProgressBar: true,
                    background: document.documentElement.classList.contains('dark') ? '#1e293b' : '#fff',
                    color: document.documentElement.classList.contains('dark') ? '#fff' : '#0f172a',
                    didOpen: (toast) => {
                        toast.addEventListener('mouseenter', Swal.stopTimer);
                        toast.addEventListener('mouseleave', Swal.resumeTimer);
                    }
                });

                // Update ref so we don't show it again
                lastNotifIdRef.current = latest.id;
            }
        }
      } catch (e) { console.error("Toast Check Failed", e); }
    };

    // Check immediately, then every 3 seconds
    checkNotifications();
    const interval = setInterval(checkNotifications, 3000);
    return () => clearInterval(interval);
  }, []);

  return null; // This component renders nothing visually
}
""",

    # --- 2. MOUNT IT IN ROOT LAYOUT (So it works everywhere) ---
    "app/layout.tsx": """
import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { GlobalToastListener } from '@/components/layout/GlobalToastListener'; // NEW IMPORT

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Bank App',
  description: 'Next Gen Banking Management System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
            <GlobalToastListener /> {/* MOUNTED HERE: WATCHES EVERYTHING */}
            {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
""",

    # --- 3. CLEANUP NOTIFICATION BELL (Remove duplicate logic) ---
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

  // We kept fetch logic here just for the list, but removed the Swal/Toast logic
  // to prevent double toasts (since GlobalToastListener now handles popups).
  const fetchNotifications = async () => {
    try {
        const res = await fetch('/api/notifications');
        if (res.ok) {
            const data = await res.json();
            setNotifications(data.notifications || []);
            setUnreadCount(data.unreadCount || 0);
        }
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 5000);
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
  
  const handleRedirect = (msg: string) => {
    setIsOpen(false);
    const lower = msg.toLowerCase();
    if (lower.includes('loan request')) router.push('/admin/loans');
    else if (lower.includes('loan approved') || lower.includes('loan rejected')) router.push('/customer/loans');
    else if (lower.includes('kyc')) router.push(lower.includes('request') ? '/admin/kyc' : '/customer/kyc');
    else if (lower.includes('message')) router.push('/messages');
    else if (lower.includes('danger zone') || lower.includes('security')) router.push('/admin');
    else router.push('/notifications');
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
                            onClick={() => handleRedirect(n.message)}
                            className={`group p-4 border-b border-slate-50 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition cursor-pointer flex gap-3 relative ${
                                n.is_read ? 'bg-white dark:bg-slate-900 opacity-60' : 'bg-blue-50/50 dark:bg-blue-900/10'
                            }`}
                        >
                            <div className="mt-1 shrink-0">{getIcon(n.type)}</div>
                            <div className="flex-1 pr-6">
                                <p className={`text-sm ${n.is_read ? 'text-slate-700 dark:text-slate-300' : 'text-slate-900 dark:text-white font-bold'}`}>
                                    {n.message}
                                </p>
                                <p className="text-xs text-slate-500 mt-1">
                                    {new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                                </p>
                            </div>
                            {!n.is_read && (
                                <button 
                                    onClick={(e) => { e.stopPropagation(); markAsRead(n.id); }}
                                    className="absolute right-3 top-4 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-full p-1 transition"
                                    title="Mark as Read"
                                >
                                    <div className="h-2 w-2 bg-blue-500 rounded-full group-hover:scale-150 transition-all"></div>
                                </button>
                            )}
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

def fix_global_toasts():
    print("🌍 Installing System-Wide Global Toast Listener...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created/Updated: {path}")

if __name__ == "__main__":
    fix_global_toasts()
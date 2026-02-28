'use client';
import { Sun, Moon, Monitor, Search, LogOut, User, Settings } from 'lucide-react';
import { useTheme } from 'next-themes';
import NotificationBell from './NotificationBell';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Swal from 'sweetalert2';

export function Navbar({ user }: { user: any }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<any>(null);
  const router = useRouter();

  useEffect(() => { setMounted(true); }, []);

  // Close menu on click outside
  useEffect(() => {
    const handleClick = (e: any) => {
        if(menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  };

  if (!mounted) return null;

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-8 z-20 relative">
      <div className="flex items-center w-full max-w-md bg-slate-100 dark:bg-slate-800 rounded-lg px-3 py-2">
        <Search size={18} className="text-slate-400 mr-2" />
        <input type="text" placeholder="Search..." className="bg-transparent border-none outline-none text-sm w-full dark:text-white" />
      </div>

      <div className="flex items-center gap-4">
        {/* THEME TOGGLE */}
        <div className="hidden md:flex bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
            <button onClick={() => setTheme('light')} className={`p-1.5 rounded-md ${theme === 'light' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500'}`}><Sun size={16}/></button>
            <button onClick={() => setTheme('system')} className={`p-1.5 rounded-md ${theme === 'system' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500'}`}><Monitor size={16}/></button>
            <button onClick={() => setTheme('dark')} className={`p-1.5 rounded-md ${theme === 'dark' ? 'bg-white dark:bg-slate-700 shadow text-blue-600' : 'text-slate-500'}`}><Moon size={16}/></button>
        </div>

        <NotificationBell />

        {/* PROFILE DROPDOWN */}
        <div className="relative" ref={menuRef}>
            <button onClick={() => setMenuOpen(!menuOpen)} className="flex items-center gap-3 pl-4 border-l border-slate-200 dark:border-slate-700 hover:opacity-80 transition">
                <div className="text-right hidden md:block">
                    <p className="text-sm font-bold text-slate-800 dark:text-white leading-none">{user.name}</p>
                    <p className="text-xs text-slate-500 mt-1 capitalize">{user.role}</p>
                </div>
                <div className="h-9 w-9 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-bold text-sm">
                    {user.name ? user.name.substring(0, 2).toUpperCase() : 'U'}
                </div>
            </button>

            {menuOpen && (
                <div className="absolute right-0 mt-3 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in fade-in zoom-in-95 duration-200 z-50">
                    <button onClick={() => router.push('/profile')} className="flex items-center w-full px-4 py-3 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 transition text-slate-700 dark:text-slate-300">
                        <User size={16} className="mr-2"/> My Profile
                    </button>
                    {user.role === 'admin' && (
                        <button onClick={() => router.push('/admin/settings')} className="flex items-center w-full px-4 py-3 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 transition text-slate-700 dark:text-slate-300">
                            <Settings size={16} className="mr-2"/> Settings
                        </button>
                    )}
                    <div className="h-[1px] bg-slate-100 dark:bg-slate-800 my-0"></div>
                    <button onClick={handleLogout} className="flex items-center w-full px-4 py-3 text-sm hover:bg-red-50 hover:text-red-600 transition text-slate-500">
                        <LogOut size={16} className="mr-2"/> Sign Out
                    </button>
                </div>
            )}
        </div>
      </div>
    </header>
  );
}
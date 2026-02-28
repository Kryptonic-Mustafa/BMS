'use client';

import * as React from 'react';
import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from 'next-themes';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // Prevent hydration mismatch
  React.useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
      <button
        onClick={() => setTheme('light')}
        className={`p-1.5 rounded-md transition-all ${theme === 'light' ? 'bg-white dark:bg-slate-600 shadow-sm text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
      >
        <Sun size={16} />
      </button>
      <button
        onClick={() => setTheme('system')}
        className={`p-1.5 rounded-md transition-all ${theme === 'system' ? 'bg-white dark:bg-slate-600 shadow-sm text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
      >
        <Monitor size={16} />
      </button>
      <button
        onClick={() => setTheme('dark')}
        className={`p-1.5 rounded-md transition-all ${theme === 'dark' ? 'bg-white dark:bg-slate-600 shadow-sm text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
      >
        <Moon size={16} />
      </button>
    </div>
  );
}
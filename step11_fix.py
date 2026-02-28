import os

files = {
    # --- 1. DARK MODE PROVIDER ---
    "components/providers/ThemeProvider.tsx": """
'use client';

import * as React from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';

export function ThemeProvider({ children, ...props }: React.ComponentProps<typeof NextThemesProvider>) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
""",

    # --- 2. UPDATE LAYOUT (Wrap in Provider) ---
    "app/layout.tsx": """
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Modern Banking System",
  description: "Production grade banking application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
""",

    # --- 3. THEME TOGGLE COMPONENT ---
    "components/layout/ThemeToggle.tsx": """
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
""",

    # --- 4. UPDATE NAVBAR (Add Toggle) ---
    "components/layout/Navbar.tsx": """
'use client';
import { Bell, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { MobileMenu } from './MobileMenu';
import { ThemeToggle } from './ThemeToggle';

interface NavbarProps {
  user: { name: string; role: string; };
}

export function Navbar({ user }: NavbarProps) {
  const [hasUnread, setHasUnread] = useState(false);
  const initials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2);

  useEffect(() => {
    const check = async () => {
        try {
            const res = await fetch('/api/notifications');
            const data = await res.json();
            if(Array.isArray(data)) setHasUnread(data.some((n: any) => !n.is_read));
        } catch(e) {}
    };
    const interval = setInterval(check, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-6 sticky top-0 z-20 shadow-sm transition-colors">
      <div className="flex items-center gap-4">
        <MobileMenu userRole={user.role} />
        
        <div className="hidden md:block relative w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Search..." 
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-900/10 dark:text-slate-200 transition-all" 
          />
        </div>
      </div>

      <div className="flex items-center gap-3 md:gap-4">
        <ThemeToggle />
        
        <button className="relative p-2 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
          <Bell size={20} />
          {hasUnread && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border border-white dark:border-slate-900 animate-pulse"></span>
          )}
        </button>
        
        <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700 hidden md:block"></div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden md:block">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{user.name}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">{user.role}</p>
          </div>
          <div className="w-9 h-9 md:w-10 md:h-10 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded-full flex items-center justify-center font-bold border border-blue-200 dark:border-blue-800 text-sm md:text-base">
            {initials}
          </div>
        </div>
      </div>
    </header>
  );
}
""",

    # --- 5. FIX TABLE (No Hydration Error + Dark Mode) ---
    "components/ui/Table.tsx": """
import React from 'react';

// Strict Table Structure to prevent Hydration Errors
export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm bg-white dark:bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left text-slate-600 dark:text-slate-300 whitespace-nowrap">
          {children}
        </table>
      </div>
    </div>
  );
}

export function TableHead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="bg-slate-50 dark:bg-slate-800 text-xs uppercase text-slate-500 dark:text-slate-400 font-semibold">
      <tr>{children}</tr>
    </thead>
  );
}

export function TableRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <tr className={`border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors ${className}`}>
      {children}
    </tr>
  );
}

export function TableHeader({ children }: { children: React.ReactNode }) {
  return <th className="px-6 py-4 font-medium">{children}</th>;
}

export function TableCell({ children, className }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-6 py-4 ${className}`}>{children}</td>;
}
""",

    # --- 6. GENERIC MODAL COMPONENT (For Admin Deposit) ---
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
      <div className="relative bg-white dark:bg-slate-900 w-full max-w-md rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 animate-in zoom-in-95 duration-200">
        <div className="flex justify-between items-center p-4 border-b border-slate-100 dark:border-slate-800">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}
""",

    # --- 7. NEW PAGINATION COMPONENT ---
    "components/ui/Pagination.tsx": """
'use client';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';

export function Pagination({ totalPages }: { totalPages: number }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentPage = Number(searchParams.get('page')) || 1;

  const changePage = (page: number) => {
    if (page < 1 || page > totalPages) return;
    const params = new URLSearchParams(searchParams);
    params.set('page', page.toString());
    router.replace(`?${params.toString()}`);
  };

  return (
    <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 px-4 py-3 sm:px-6 mt-4">
      <div className="flex flex-1 justify-between sm:hidden">
        <button
          onClick={() => changePage(currentPage - 1)}
          disabled={currentPage <= 1}
          className="relative inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
        >
          Previous
        </button>
        <button
          onClick={() => changePage(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="relative ml-3 inline-flex items-center rounded-md border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50"
        >
          Next
        </button>
      </div>
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-700 dark:text-slate-400">
            Showing page <span className="font-medium">{currentPage}</span> of <span className="font-medium">{totalPages}</span>
          </p>
        </div>
        <div>
          <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
            <button
              onClick={() => changePage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="relative inline-flex items-center rounded-l-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 dark:ring-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
            >
              <ChevronLeft className="h-5 w-5" aria-hidden="true" />
            </button>
            <button
              onClick={() => changePage(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="relative inline-flex items-center rounded-r-md px-2 py-2 text-slate-400 ring-1 ring-inset ring-slate-300 dark:ring-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
            >
              <ChevronRight className="h-5 w-5" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
}
""",

    # --- 8. UPDATED DEPOSIT BUTTON (Uses New Modal) ---
    "app/(dashboard)/admin/customers/DepositButton.tsx": """
'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useRouter } from 'next/navigation';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import Swal from 'sweetalert2';

export default function DepositButton({ accountId }: { accountId: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await fetch('/api/admin/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accountId, amount: parseFloat(amount) }),
      });
      
      if (res.ok) {
        setIsOpen(false);
        setAmount('');
        Swal.fire({
          toast: true, position: 'top-end', icon: 'success', 
          title: 'Deposit Successful', timer: 3000, showConfirmButton: false
        });
        router.refresh(); 
      } else {
        Swal.fire('Error', 'Deposit failed', 'error');
      }
    } catch (e) {
      Swal.fire('Error', 'Network error', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button size="sm" variant="secondary" onClick={() => setIsOpen(true)}>
        + Deposit
      </Button>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Add Funds">
        <form onSubmit={handleDeposit} className="space-y-4">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Enter the amount to deposit into the customer's account.
          </p>
          <Input 
            label="Amount ($)" 
            type="number" 
            min="1" 
            placeholder="1000.00" 
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button type="button" variant="ghost" onClick={() => setIsOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Processing...' : 'Confirm Deposit'}
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
""",

    # --- 9. UPDATED ADMIN CUSTOMER PAGE (Mobile Cards & Pagination) ---
    "app/(dashboard)/admin/customers/page.tsx": """
import { query } from '@/lib/db';
import { Table, TableHead, TableHeader, TableRow, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import DepositButton from './DepositButton'; 
import UserActions from './UserActions';
import { Pagination } from '@/components/ui/Pagination';

async function getCustomers(page = 1, limit = 10) {
  const offset = (page - 1) * limit;
  
  const customers: any = await query(`
    SELECT u.id, u.name, u.email, u.created_at, a.account_number, a.balance, a.id as account_id
    FROM users u
    JOIN accounts a ON u.id = a.user_id
    WHERE u.role = 'customer'
    ORDER BY u.created_at DESC
    LIMIT ? OFFSET ?
  `, [limit, offset]);
  
  const count: any = await query('SELECT COUNT(*) as total FROM users WHERE role = "customer"');
  
  return { 
    data: customers, 
    totalPages: Math.ceil(count[0].total / limit) 
  };
}

export default async function CustomersPage({ searchParams }: { searchParams: { page?: string } }) {
  const page = Number(searchParams.page) || 1;
  const { data: customers, totalPages } = await getCustomers(page);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Customer Management</h2>
      </div>

      {/* DESKTOP TABLE VIEW */}
      <div className="hidden md:block bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <Table>
          <TableHead>
            <TableHeader>Customer</TableHeader>
            <TableHeader>Account Info</TableHeader>
            <TableHeader>Balance</TableHeader>
            <TableHeader>Actions</TableHeader>
          </TableHead>
          <tbody>
            {customers.map((user: any) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="font-medium text-slate-900 dark:text-white">{user.name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{user.email}</div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                    {user.account_number}
                  </span>
                </TableCell>
                <TableCell className="font-bold text-slate-700 dark:text-slate-200">
                  ${Number(user.balance).toLocaleString()}
                </TableCell>
                <TableCell>
                   <div className="flex items-center gap-3">
                     <DepositButton accountId={user.account_id} />
                     <div className="h-4 w-[1px] bg-slate-300 dark:bg-slate-700"></div>
                     <UserActions user={user} />
                   </div>
                </TableCell>
              </TableRow>
            ))}
          </tbody>
        </Table>
      </div>

      {/* MOBILE CARD VIEW (Label Left, Data Right) */}
      <div className="md:hidden space-y-4">
        {customers.map((user: any) => (
          <div key={user.id} className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm space-y-3">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-2">
              <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Customer</span>
              <div className="text-right">
                <div className="font-medium text-slate-900 dark:text-white">{user.name}</div>
                <div className="text-xs text-slate-500">{user.email}</div>
              </div>
            </div>
            
            <div className="flex justify-between items-center">
               <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Account</span>
               <span className="font-mono text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm">
                 {user.account_number}
               </span>
            </div>

            <div className="flex justify-between items-center">
               <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">Balance</span>
               <span className="font-bold text-slate-900 dark:text-white">
                 ${Number(user.balance).toLocaleString()}
               </span>
            </div>

            <div className="pt-3 flex gap-3 justify-end">
               <DepositButton accountId={user.account_id} />
               <UserActions user={user} />
            </div>
          </div>
        ))}
      </div>

      <Pagination totalPages={totalPages} />
    </div>
  );
}
""",

    # --- 10. UPDATE TAILWIND CONFIG (Dark Mode Strategy) ---
    "tailwind.config.ts": """
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1E3A8A", // Blue 900
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#0D9488", // Teal 600
          foreground: "#FFFFFF",
        },
        background: "var(--background)",
        neutral: "#334155",
        danger: "#EF4444",
        success: "#10B981",
      },
      borderRadius: {
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
};
export default config;
"""
}

def apply_ultimate_ui():
    print("🌙 Installing Dark Mode, Pagination & Mobile Cards...")
    for path, content in files.items():
        # --- FIX: Only create directory if path contains one ---
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")
    
    print("\n✨ UI Overhaul Complete! Restart server to see the magic.")

if __name__ == "__main__":
    apply_ultimate_ui()
import os

files = {
    # --- 1. UPDATE REGISTER API (Generate PIN + Welcome Mail) ---
    "app/api/auth/register/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';

export async function POST(request: Request) {
  try {
    const { name, email, password } = await request.json();

    // 1. Check existing
    const existing: any = await query('SELECT id FROM users WHERE email = ?', [email]);
    if (existing.length > 0) return NextResponse.json({ error: 'Email already exists' }, { status: 400 });

    // 2. Generate Credentials
    const hashedPassword = await bcrypt.hash(password, 10);
    const pin = Math.floor(1000 + Math.random() * 9000).toString(); // Random 4-digit PIN
    const accountNumber = 'ACC' + Math.floor(1000000000 + Math.random() * 9000000000).toString();

    // 3. Create User
    const res: any = await query(
      'INSERT INTO users (name, email, password, role_id, pin) VALUES (?, ?, ?, 3, ?)',
      [name, email, hashedPassword, pin]
    );
    const userId = res.insertId;

    // 4. Create Account
    await query(
      'INSERT INTO accounts (user_id, account_number, balance, type, status) VALUES (?, ?, 0.00, "savings", "active")',
      [userId, accountNumber]
    );

    // 5. SEND WELCOME BANKMAIL
    const welcomeMsg = `
      Welcome to Dev Bank, ${name}!
      
      Here are your confidential account details:
      -----------------------------------------
      Account Number: ${accountNumber}
      Security PIN:   ${pin}
      -----------------------------------------
      
      Please keep your PIN safe. You will need it for all transfers.
      You can view this PIN anytime in your Profile.
    `;

    await query(
      'INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (0, ?, ?, ?)',
      [userId, 'Welcome to Dev Bank - Important Details', welcomeMsg]
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: 'Registration failed' }, { status: 500 });
  }
}
""",

    # --- 2. PROFILE API (Get Details, Edit, Reveal PIN) ---
    "app/api/profile/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import bcrypt from 'bcryptjs';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({});

  const user: any = await query(`
    SELECT u.id, u.name, u.email, u.role, u.pin, a.account_number, a.balance 
    FROM users u
    LEFT JOIN accounts a ON u.id = a.user_id
    WHERE u.id = ?
  `, [session.id]);

  if (user.length === 0) return NextResponse.json({ error: 'User not found' });
  
  // Return everything EXCEPT password. PIN is returned but handled carefully in UI.
  return NextResponse.json(user[0]);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json();

  // A. REVEAL PIN REQUEST
  if (body.action === 'reveal_pin') {
      const { password } = body;
      // Fetch real password hash
      const u: any = await query('SELECT password, pin FROM users WHERE id = ?', [session.id]);
      
      const isMatch = await bcrypt.compare(password, u[0].password);
      if (!isMatch) return NextResponse.json({ error: 'Incorrect Password' }, { status: 401 });
      
      return NextResponse.json({ success: true, pin: u[0].pin });
  }

  // B. UPDATE PROFILE REQUEST
  if (body.action === 'update_info') {
      const { name, email } = body;
      await query('UPDATE users SET name = ?, email = ? WHERE id = ?', [name, email, session.id]);
      return NextResponse.json({ success: true });
  }

  // C. CHANGE PASSWORD REQUEST
  if (body.action === 'change_password') {
      const { currentPassword, newPassword } = body;
      const u: any = await query('SELECT password FROM users WHERE id = ?', [session.id]);
      
      const isMatch = await bcrypt.compare(currentPassword, u[0].password);
      if (!isMatch) return NextResponse.json({ error: 'Current password incorrect' }, { status: 401 });

      const hashed = await bcrypt.hash(newPassword, 10);
      await query('UPDATE users SET password = ? WHERE id = ?', [hashed, session.id]);
      
      return NextResponse.json({ success: true });
  }

  return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
}
""",

    # --- 3. FIX TRANSFER API (Verify PIN) ---
    "app/api/customer/transfer/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const session = await getSession();
    if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { amount, accountNumber, pin } = await request.json();

    // 1. Verify Sender & PIN
    const users: any = await query('SELECT * FROM users WHERE id = ?', [session.id]);
    const user = users[0];

    // Simple string comparison for PIN (since we generated it as 4 digits)
    if (user.pin !== pin) {
        return NextResponse.json({ error: 'Invalid Security PIN' }, { status: 400 });
    }

    const senderAcc: any = await query('SELECT * FROM accounts WHERE user_id = ?', [session.id]);
    if (senderAcc.length === 0 || Number(senderAcc[0].balance) < Number(amount)) {
        return NextResponse.json({ error: 'Insufficient funds' }, { status: 400 });
    }

    // 2. Find Receiver
    const receiverAcc: any = await query('SELECT * FROM accounts WHERE account_number = ?', [accountNumber]);
    if (receiverAcc.length === 0) return NextResponse.json({ error: 'Receiver account not found' }, { status: 404 });

    // 3. Execute Transfer
    await query('UPDATE accounts SET balance = balance - ? WHERE id = ?', [amount, senderAcc[0].id]);
    await query('UPDATE accounts SET balance = balance + ? WHERE id = ?', [amount, receiverAcc[0].id]);

    // 4. Log Transactions
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "debit", ?, "completed", ?)', 
        [senderAcc[0].id, amount, `Transfer to ${accountNumber}`]);
    await query('INSERT INTO transactions (account_id, type, amount, status, description) VALUES (?, "credit", ?, "completed", ?)', 
        [receiverAcc[0].id, amount, `Received from ${user.name}`]);

    return NextResponse.json({ success: true });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: 'Transfer failed' }, { status: 500 });
  }
}
""",

    # --- 4. PROFILE PAGE UI (The Big Feature) ---
    "app/(dashboard)/profile/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { User, Lock, Mail, CreditCard, Eye, EyeOff, Shield, Edit2, Save, X } from 'lucide-react';
import Swal from 'sweetalert2';

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState({ name: '', email: '' });
  
  // PIN Reveal State
  const [showPin, setShowPin] = useState(false);
  const [revealedPin, setRevealedPin] = useState('****');
  
  // Password Change State
  const [passForm, setPassForm] = useState({ current: '', new: '', confirm: '' });

  useEffect(() => {
    fetch('/api/profile').then(res => res.json()).then(data => {
        setUser(data);
        setForm({ name: data.name, email: data.email });
    });
  }, []);

  const handleUpdateInfo = async () => {
    const res = await fetch('/api/profile', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: 'update_info', ...form })
    });
    if (res.ok) {
        Swal.fire('Updated', 'Profile details saved.', 'success');
        setIsEditing(false);
        setUser({ ...user, ...form });
    }
  };

  const handleRevealPin = async () => {
    if (showPin) {
        setShowPin(false);
        setRevealedPin('****');
        return;
    }

    const { value: password } = await Swal.fire({
        title: 'Enter Password',
        text: 'Verify your identity to view Security PIN',
        input: 'password',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Reveal PIN'
    });

    if (password) {
        const res = await fetch('/api/profile', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ action: 'reveal_pin', password })
        });
        const data = await res.json();
        
        if (res.ok) {
            setRevealedPin(data.pin);
            setShowPin(true);
            // Auto-hide after 10 seconds
            setTimeout(() => { setShowPin(false); setRevealedPin('****'); }, 10000);
        } else {
            Swal.fire('Error', 'Incorrect Password', 'error');
        }
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passForm.new !== passForm.confirm) return Swal.fire('Error', 'New passwords do not match', 'error');
    
    const res = await fetch('/api/profile', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
            action: 'change_password', 
            currentPassword: passForm.current, 
            newPassword: passForm.new 
        })
    });
    
    if (res.ok) {
        Swal.fire('Success', 'Password changed successfully', 'success');
        setPassForm({ current: '', new: '', confirm: '' });
    } else {
        const data = await res.json();
        Swal.fire('Error', data.error, 'error');
    }
  };

  if (!user) return <div className="p-8 text-center">Loading Profile...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold dark:text-white mb-6">My Profile</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LEFT: INFO CARD */}
        <Card className="relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-r from-blue-600 to-blue-400"></div>
            <div className="relative pt-8 px-4 text-center">
                <div className="h-20 w-20 mx-auto bg-white rounded-full p-1 shadow-lg">
                    <div className="h-full w-full bg-blue-100 rounded-full flex items-center justify-center text-2xl font-bold text-blue-600">
                        {user.name.charAt(0).toUpperCase()}
                    </div>
                </div>
                
                {isEditing ? (
                    <div className="mt-4 space-y-3">
                        <Input value={form.name} onChange={e => setForm({...form, name: e.target.value})} label="Full Name" />
                        <Input value={form.email} onChange={e => setForm({...form, email: e.target.value})} label="Email Address" />
                        <div className="flex gap-2 justify-center mt-4">
                            <Button variant="danger" onClick={() => setIsEditing(false)} size="sm"><X size={16}/></Button>
                            <Button onClick={handleUpdateInfo} size="sm"><Save size={16}/> Save</Button>
                        </div>
                    </div>
                ) : (
                    <div className="mt-4">
                        <h3 className="text-xl font-bold dark:text-white">{user.name}</h3>
                        <p className="text-slate-500">{user.email}</p>
                        <button onClick={() => setIsEditing(true)} className="absolute top-28 right-4 text-slate-400 hover:text-blue-600">
                            <Edit2 size={18}/>
                        </button>
                    </div>
                )}
            </div>

            <div className="mt-8 border-t border-slate-100 dark:border-slate-800 pt-6 space-y-4">
                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <CreditCard className="text-slate-400"/>
                        <span className="text-sm font-medium">Account Number</span>
                    </div>
                    <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{user.account_number}</span>
                </div>

                <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                        <Shield className="text-slate-400"/>
                        <span className="text-sm font-medium">Security PIN</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xl tracking-widest text-slate-800 dark:text-white">
                            {revealedPin}
                        </span>
                        <button onClick={handleRevealPin} className="text-blue-600 hover:text-blue-500 text-sm font-medium ml-2">
                            {showPin ? 'Hide' : 'Reveal'}
                        </button>
                    </div>
                </div>
            </div>
        </Card>

        {/* RIGHT: SECURITY CARD */}
        <Card>
            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                <Lock className="text-slate-400"/> Security Settings
            </h3>
            
            <form onSubmit={handleChangePassword} className="space-y-4">
                <Input 
                    type="password" label="Current Password" required
                    value={passForm.current} onChange={e => setPassForm({...passForm, current: e.target.value})}
                />
                <Input 
                    type="password" label="New Password" required
                    value={passForm.new} onChange={e => setPassForm({...passForm, new: e.target.value})}
                />
                <Input 
                    type="password" label="Confirm Password" required
                    value={passForm.confirm} onChange={e => setPassForm({...passForm, confirm: e.target.value})}
                />
                <Button type="submit" variant="secondary" className="w-full">Update Password</Button>
            </form>
        </Card>
      </div>
    </div>
  );
}
""",

    # --- 5. UPDATED NAVBAR (With Profile Dropdown) ---
    "components/layout/Navbar.tsx": """
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
"""
}

def install_profile_and_security():
    print("🔐 Installing Profile Page, Security PIN, and fixing Transfer...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    install_profile_and_security()
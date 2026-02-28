import os

files = {
    # --- 1. UPDATE LOGIN API (Log the Login) ---
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';
import { decryptData } from '@/lib/crypto';
import { logActivity } from '@/lib/audit';

export async function POST(request: Request) {
  try {
    const rawBody = await request.json();
    const body = rawBody.data ? decryptData(rawBody.data) : rawBody;
    const { email, password } = body;

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    // --- LOG LOGIN ATTEMPT ---
    const userAgent = request.headers.get('user-agent') || 'Unknown Device';
    const ip = request.headers.get('x-forwarded-for') || '127.0.0.1';
    
    await query(
        'INSERT INTO login_logs (user_id, ip_address, user_agent, location) VALUES (?, ?, ?, ?)',
        [user.id, ip, userAgent, 'Pune, India'] // Simulating location
    );

    // Notify user of login
    await query(
        'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
        [user.id, `New login detected from ${userAgent.substring(0, 30)}...`, 'info']
    );

    const sessionData = { id: user.id, name: user.name, email: user.email, role: user.role };
    const cookieStore = await cookies();
    const token = await encrypt(sessionData);
    cookieStore.set('session', token, { httpOnly: true, secure: true, maxAge: 86400, path: '/' });

    return NextResponse.json({ message: 'Login successful', user: sessionData });
  } catch (error) {
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
""",

    # --- 2. SECURITY CENTER PAGE ---
    "app/(dashboard)/customer/security/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Shield, Smartphone, Globe, Clock, AlertTriangle } from 'lucide-react';

export default function SecurityPage() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch('/api/customer/security').then(res => res.json()).then(setLogs);
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-600 rounded-lg text-white"><Shield size={24}/></div>
        <h2 className="text-2xl font-bold dark:text-white">Security Center</h2>
      </div>

      <Card className="p-0 overflow-hidden border-slate-200 dark:border-slate-800">
        <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800">
            <h3 className="font-bold text-sm">Recent Login Activity</h3>
            <p className="text-xs text-slate-500">Check this list for any recognized devices or locations.</p>
        </div>
        
        <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {logs.map((log: any) => (
                <div key={log.id} className="p-4 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                    <div className="flex items-center gap-4">
                        <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-500">
                            {log.user_agent.includes('Mobi') ? <Smartphone size={20}/> : <Globe size={20}/>}
                        </div>
                        <div>
                            <p className="text-sm font-bold dark:text-white truncate max-w-[200px] md:max-w-md">
                                {log.user_agent}
                            </p>
                            <div className="flex gap-3 text-xs text-slate-500 mt-1">
                                <span className="flex items-center gap-1"><Clock size={12}/> {new Date(log.created_at).toLocaleString()}</span>
                                <span className="font-mono">IP: {log.ip_address}</span>
                            </div>
                        </div>
                    </div>
                    <span className="text-xs font-bold text-green-600 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded">
                        {log.location}
                    </span>
                </div>
            ))}
            {logs.length === 0 && <p className="p-8 text-center text-slate-400">No logs found.</p>}
        </div>
      </Card>
      
      <div className="bg-orange-50 dark:bg-orange-900/10 border border-orange-200 dark:border-orange-800 p-4 rounded-xl flex gap-3">
        <AlertTriangle className="text-orange-600 shrink-0"/>
        <p className="text-sm text-orange-800 dark:text-orange-200">
            <strong>Security Tip:</strong> If you see a login you don't recognize, change your password immediately in your <strong>Profile</strong>.
        </p>
      </div>
    </div>
  );
}
""",

    # --- 3. SECURITY API ---
    "app/api/customer/security/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export const dynamic = 'force-dynamic';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const logs = await query(
    'SELECT * FROM login_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
    [session.id]
  );
  return NextResponse.json(logs);
}
"""
}

def install_security_center():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Security Center installed! Syncing login logs...")

if __name__ == "__main__":
    install_security_center()
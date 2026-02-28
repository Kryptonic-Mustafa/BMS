import os

files = {
    # 1. THE FIX: Vercel-Safe Cookie Attachment
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/session';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    
    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });

    const isStaff = user.role_id === 1 || user.role_id === 2 || user.is_super_admin === 1 || user.role === 'admin';
    const roleName = isStaff ? (user.role_id === 1 ? 'SuperAdmin' : 'Manager') : 'Customer';
    const targetRoute = isStaff ? '/admin' : '/customer';

    let permissionNames: string[] = [];
    if (isStaff) {
        try {
            const perms: any = await query('SELECT p.name FROM permissions p JOIN role_permissions rp ON p.id = rp.permission_id WHERE rp.role_id = ?', [user.role_id]);
            permissionNames = perms.map((p: any) => p.name);
        } catch (e) {}
    }

    const sessionData = { id: user.id, name: user.name, email: user.email, role: roleName, permissions: permissionNames };
    const token = await encrypt(sessionData);
    
    // THE FIX: Create the response first, then attach cookies directly to it
    const response = NextResponse.json({ message: 'Success', redirectUrl: targetRoute });
    
    response.cookies.set('session', token, { 
        httpOnly: true, 
        secure: true, 
        maxAge: 86400, 
        path: '/' 
    });
    
    response.cookies.set('client_policy', JSON.stringify({ role: roleName, permissions: permissionNames }), { 
        httpOnly: false, 
        secure: false, 
        maxAge: 86400, 
        path: '/' 
    });

    return response;
  } catch (error) {
    console.error('LOGIN ERROR:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
""",

    # 2. THE FIX: Hardcoded Secret to prevent environment decryption failures
    "lib/session.ts": """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

// Hardcoded to guarantee the encrypt and decrypt functions are using the EXACT same key
const secretKey = "bms_super_secret_key_production_2026"; 
const key = new TextEncoder().encode(secretKey);

export async function encrypt(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(key);
}

export async function decrypt(input: string): Promise<any> {
  try {
    const { payload } = await jwtVerify(input, key, { algorithms: ['HS256'] });
    return payload;
  } catch (error) {
    console.error("[SESSION ERROR] Failed to decrypt token:", error);
    return null;
  }
}

export async function getSession() {
  const sessionCookie = (await cookies()).get('session')?.value;
  if (!sessionCookie) {
      console.warn("[SESSION ERROR] No session cookie found in request.");
      return null;
  }
  return await decrypt(sessionCookie);
}
""",

    # 3. THE FIX: Add Bouncer Logs
    "app/(dashboard)/layout.tsx": """
import Sidebar from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();
  
  // THE FIX: Log what the server sees to the Vercel Console
  console.log("[LAYOUT BOUNCER] Session Check:", session ? `Valid User: ${session.email}` : "NULL - Redirecting to /login");

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden pl-64">
        <Navbar user={session} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-50 dark:bg-slate-900 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
"""
}

def apply_cookie_bounce_fix():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Vercel-Safe Cookie Attachment and Bouncer Logs Applied!")

if __name__ == "__main__":
    apply_cookie_bounce_fix()
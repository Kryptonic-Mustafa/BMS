import os

files = {
    # --- 1. ENVIRONMENT VARIABLES (Template) ---
    ".env.local": """
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=bank_app
JWT_SECRET=supersecretkey12345
""",

    # --- 2. DATABASE CONNECTION ---
    "lib/db.ts": """
import mysql from 'mysql2/promise';

// Create a connection pool
export const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

export async function query(sql: string, params: any[] = []) {
  try {
    const [results] = await pool.execute(sql, params);
    return results;
  } catch (error) {
    console.error('Database Error:', error);
    throw new Error('Database query failed');
  }
}
""",

    # --- 3. AUTHENTICATION UTILS ---
    "lib/auth.ts": """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

const secretKey = process.env.JWT_SECRET || 'secret';
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
    const { payload } = await jwtVerify(input, key, {
      algorithms: ['HS256'],
    });
    return payload;
  } catch (error) {
    return null;
  }
}

export async function getSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get('session')?.value;
  if (!session) return null;
  return await decrypt(session);
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
}
""",

    # --- 4. API: REGISTER ---
    "app/api/auth/register/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';

export async function POST(request: Request) {
  try {
    const { name, email, password } = await request.json();

    // 1. Check if user exists
    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length > 0) {
      return NextResponse.json({ error: 'User already exists' }, { status: 400 });
    }

    // 2. Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // 3. Insert user
    const result: any = await query(
      'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
      [name, email, hashedPassword, 'customer']
    );

    // 4. Create default account for customer
    const userId = result.insertId;
    const accountNumber = 'ACC' + Math.floor(1000000000 + Math.random() * 9000000000);
    
    await query(
      'INSERT INTO accounts (user_id, account_number, balance, type) VALUES (?, ?, ?, ?)',
      [userId, accountNumber, 0.00, 'savings']
    );

    return NextResponse.json({ message: 'User created successfully' });
  } catch (error) {
    return NextResponse.json({ error: 'Registration failed' }, { status: 500 });
  }
}
""",

    # --- 5. API: LOGIN ---
    "app/api/auth/login/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import bcrypt from 'bcryptjs';
import { encrypt } from '@/lib/auth';
import { cookies } from 'next/headers';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

    // 1. Find user
    const users: any = await query('SELECT * FROM users WHERE email = ?', [email]);
    if (users.length === 0) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }
    
    const user = users[0];

    // 2. Check password
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    // 3. Create Session
    const sessionData = {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role
    };
    
    const token = await encrypt(sessionData);

    // 4. Set Cookie
    const cookieStore = await cookies();
    cookieStore.set('session', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      maxAge: 60 * 60 * 24, // 1 day
      path: '/',
    });

    return NextResponse.json({ 
      message: 'Login successful', 
      user: sessionData 
    });

  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Login failed' }, { status: 500 });
  }
}
""",

    # --- 6. API: LOGOUT ---
    "app/api/auth/logout/route.ts": """
import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';

export async function POST() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
  return NextResponse.json({ message: 'Logged out' });
}
""",

    # --- 7. MIDDLEWARE (PROTECTED ROUTES) ---
    "middleware.ts": """
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { decrypt } from '@/lib/auth';

export async function middleware(request: NextRequest) {
  const session = request.cookies.get('session')?.value;
  const path = request.nextUrl.pathname;

  // 1. Decrypt session
  const payload = session ? await decrypt(session) : null;

  // 2. Define protected routes
  const isDashboard = path.startsWith('/admin') || path.startsWith('/customer');
  const isAuthPage = path.startsWith('/login') || path.startsWith('/register');

  // 3. Redirect logic
  if (isDashboard && !payload) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  if (isAuthPage && payload) {
    // Redirect based on role
    if (payload.role === 'admin') {
      return NextResponse.redirect(new URL('/admin', request.url));
    } else {
      return NextResponse.redirect(new URL('/customer', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/customer/:path*', '/login', '/register'],
};
"""
}

def create_backend():
    print("🔐 Generating Auth & Database Layer...")
    for path, content in files.items():
        # --- FIX: Only create directory if path contains one ---
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n⚠️ IMPORTANT: Edit '.env.local' with your actual MySQL password!")

if __name__ == "__main__":
    create_backend()
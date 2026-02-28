import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { decrypt } from '@/lib/auth';

export async function middleware(request: NextRequest) {
  const session = request.cookies.get('session')?.value;
  const path = request.nextUrl.pathname;

  const payload = session ? await decrypt(session) : null;

  const isDashboard = path.startsWith('/admin') || path.startsWith('/customer');
  const isAuthPage = path.startsWith('/login') || path.startsWith('/register');

  if (isDashboard && !payload) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  if (isAuthPage && payload) {
    // Redirect based on role
    if (['admin', 'manager'].includes(payload.role)) {
      return NextResponse.redirect(new URL('/admin', request.url));
    } else {
      return NextResponse.redirect(new URL('/customer', request.url));
    }
  }

  // Protect Admin Routes from Customers
  if (path.startsWith('/admin') && payload && !['admin', 'manager'].includes(payload.role)) {
     return NextResponse.redirect(new URL('/customer', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/customer/:path*', '/login', '/register'],
};
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
import Sidebar from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  if (!session) {
    redirect('/login');
  }

  return (
    // THE FIX: suppressHydrationWarning stops React from panicking when browser extensions alter the DOM
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900" suppressHydrationWarning>
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
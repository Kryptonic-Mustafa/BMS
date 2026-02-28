import { Sidebar } from '@/components/layout/Sidebar';
import { Navbar } from '@/components/layout/Navbar';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';
import { NotificationListener } from '@/components/layout/NotificationListener';
import { RouteGuard } from '@/components/auth/RouteGuard';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession();
  if (!session) redirect('/login');

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar userRole={session.role} /> 
      
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar user={{ name: session.name, role: session.role }} />
        <NotificationListener /> 
        
        <main className="flex-1 overflow-auto p-4 md:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {/* WRAP CONTENT IN GUARD */}
            <RouteGuard>
                {children}
            </RouteGuard>
          </div>
        </main>
      </div>
    </div>
  );
}
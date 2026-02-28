import os

files = {
    # FIX: Passing the session user to the Navbar to satisfy TypeScript and restore identity
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

  if (!session) {
    redirect('/login');
  }

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden pl-64">
        {/* THE FIX: Passing session as the user prop */}
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

def apply_final_handshake():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Finalized Layout Handshake!")

if __name__ == "__main__":
    apply_final_handshake()
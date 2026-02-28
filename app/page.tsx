
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-background">
      <div className="text-center space-y-6">
        <h1 className="text-5xl font-bold text-primary">Bank Management System</h1>
        <p className="text-xl text-neutral/80">Secure. Modern. Reliable.</p>
        <div className="flex gap-4 justify-center mt-8">
          <Link href="/login" className="btn-primary">Login</Link>
          <Link href="/register" className="px-4 py-2 rounded-lg border border-primary text-primary hover:bg-primary/5 transition-all">Register</Link>
        </div>
      </div>
    </main>
  );
}

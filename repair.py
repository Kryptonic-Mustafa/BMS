import os

# Define the valid React code for each file
files_to_fix = {
    # 1. Auth Layout (Fixes the current error)
    "app/(auth)/layout.tsx": """
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  );
}
""",

    # 2. Login Page
    "app/(auth)/login/page.tsx": """
import Link from 'next/link';

export default function LoginPage() {
  return (
    <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
      <h2 className="text-2xl font-bold text-blue-900 mb-6 text-center">Login</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input type="email" className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:outline-none" placeholder="admin@bank.com" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input type="password" className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:outline-none" placeholder="••••••••" />
        </div>
        <button className="w-full bg-blue-900 text-white py-2 rounded-lg hover:bg-blue-800 transition">Sign In</button>
      </div>
      <p className="mt-4 text-center text-sm text-slate-600">
        Don't have an account? <Link href="/register" className="text-blue-900 font-semibold hover:underline">Register</Link>
      </p>
    </div>
  );
}
""",

    # 3. Register Page
    "app/(auth)/register/page.tsx": """
import Link from 'next/link';

export default function RegisterPage() {
  return (
    <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-200">
      <h2 className="text-2xl font-bold text-blue-900 mb-6 text-center">Register</h2>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
          <input type="text" className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:outline-none" placeholder="John Doe" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
          <input type="email" className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:outline-none" placeholder="john@example.com" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
          <input type="password" className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:outline-none" placeholder="••••••••" />
        </div>
        <button className="w-full bg-teal-600 text-white py-2 rounded-lg hover:bg-teal-700 transition">Create Account</button>
      </div>
      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account? <Link href="/login" className="text-blue-900 font-semibold hover:underline">Login</Link>
      </p>
    </div>
  );
}
""",

    # 4. Dashboard Layout (Prevents future errors when you log in)
    "app/(dashboard)/layout.tsx": """
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar Placeholder */}
      <aside className="w-64 bg-blue-900 text-white hidden md:block">
        <div className="p-6 text-2xl font-bold">BankApp</div>
        <nav className="mt-6 px-4 space-y-2">
          <div className="px-4 py-2 hover:bg-blue-800 rounded cursor-pointer">Dashboard</div>
          <div className="px-4 py-2 hover:bg-blue-800 rounded cursor-pointer">Transactions</div>
          <div className="px-4 py-2 hover:bg-blue-800 rounded cursor-pointer">Settings</div>
        </nav>
      </aside>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white shadow-sm flex items-center px-6 border-b border-slate-200">
          <h1 className="text-xl font-semibold text-slate-800">Dashboard</h1>
        </header>
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
""",

    # 5. Admin Dashboard Home
    "app/(dashboard)/admin/page.tsx": """
export default function AdminDashboard() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Admin Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 className="text-slate-500 text-sm">Total Customers</h3>
            <p className="text-3xl font-bold text-blue-900">1,240</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 className="text-slate-500 text-sm">Total Transactions</h3>
            <p className="text-3xl font-bold text-teal-600">$4.2M</p>
        </div>
      </div>
    </div>
  );
}
""",

    # 6. Customer Dashboard Home
    "app/(dashboard)/customer/page.tsx": """
export default function CustomerDashboard() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-4">Welcome Back, User</h2>
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-8 rounded-2xl text-white shadow-lg mb-8">
        <p className="opacity-80 mb-1">Total Balance</p>
        <h3 className="text-4xl font-bold">$12,450.00</h3>
      </div>
    </div>
  );
}
"""
}

def repair_project():
    print("🛠️ Repairing project files...")
    for path, content in files_to_fix.items():
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Write file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Fixed: {path}")
    
    print("\n🎉 Repair complete! Run 'npm run dev' and refresh your browser.")

if __name__ == "__main__":
    repair_project()
import os

files = {
    # --- 1. KYC API (Upload & Status) ---
    "app/api/customer/kyc/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { type, number, file } = await request.json();

  if (!file) return NextResponse.json({ error: 'Document image required' }, { status: 400 });

  // 1. Save Document
  await query(
    'INSERT INTO kyc_documents (user_id, document_type, document_number, file_data) VALUES (?, ?, ?, ?)',
    [session.id, type, number, file]
  );

  // 2. Update User Status
  await query("UPDATE users SET kyc_status = 'pending' WHERE id = ?", [session.id]);

  return NextResponse.json({ success: true });
}

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json({});

  const res: any = await query('SELECT kyc_status FROM users WHERE id = ?', [session.id]);
  return NextResponse.json({ status: res[0]?.kyc_status || 'unverified' });
}
""",

    # --- 2. ADMIN KYC API (Approve/Reject) ---
    "app/api/admin/kyc/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session || !session.permissions?.includes('KYCManage') && session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  // Fetch pending requests with user details
  const requests = await query(`
    SELECT k.id, k.document_type, k.document_number, k.file_data, k.submitted_at, 
           u.id as user_id, u.name, u.email 
    FROM kyc_documents k
    JOIN users u ON k.user_id = u.id
    WHERE u.kyc_status = 'pending'
    ORDER BY k.submitted_at DESC
  `);

  return NextResponse.json(requests);
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session || !session.permissions?.includes('KYCManage') && session.role !== 'admin') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
  }

  const { userId, action, notes } = await request.json();
  const status = action === 'approve' ? 'verified' : 'rejected';

  // Update User Status
  await query('UPDATE users SET kyc_status = ? WHERE id = ?', [status, userId]);
  
  // Optional: Add notes to doc (if rejected)
  if (notes) {
      await query('UPDATE kyc_documents SET admin_notes = ? WHERE user_id = ? ORDER BY id DESC LIMIT 1', [notes, userId]);
  }
  
  // Notify User
  await query('INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)', [
      userId, 
      `Your KYC Verification has been ${status.toUpperCase()}.`, 
      status === 'verified' ? 'success' : 'error'
  ]);

  return NextResponse.json({ success: true });
}
""",

    # --- 3. CUSTOMER KYC PAGE ---
    "app/(dashboard)/customer/kyc/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Upload, CheckCircle, Clock, XCircle, FileText } from 'lucide-react';
import Swal from 'sweetalert2';

export default function KYCPage() {
  const [status, setStatus] = useState('loading');
  const [form, setForm] = useState({ type: 'national_id', number: '', file: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/customer/kyc').then(res => res.json()).then(data => setStatus(data.status));
  }, []);

  const handleFile = (e: any) => {
    const file = e.target.files[0];
    if (file) {
        if(file.size > 2 * 1024 * 1024) return Swal.fire('Error', 'File too large (Max 2MB)', 'error');
        const reader = new FileReader();
        reader.onloadend = () => setForm({ ...form, file: reader.result as string });
        reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    const res = await fetch('/api/customer/kyc', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(form)
    });

    if (res.ok) {
        setStatus('pending');
        Swal.fire('Submitted', 'Your documents are under review.', 'success');
    } else {
        Swal.fire('Error', 'Upload failed.', 'error');
    }
    setLoading(false);
  };

  if (status === 'verified') return (
    <Card className="text-center p-12">
        <CheckCircle size={64} className="text-green-500 mx-auto mb-4"/>
        <h2 className="text-2xl font-bold text-green-700">KYC Verified</h2>
        <p className="text-slate-500 mt-2">Your account is fully active. You can now access all features.</p>
    </Card>
  );

  if (status === 'pending') return (
    <Card className="text-center p-12">
        <Clock size={64} className="text-orange-500 mx-auto mb-4"/>
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white">Verification Pending</h2>
        <p className="text-slate-500 mt-2">Our team is reviewing your documents. This usually takes 24 hours.</p>
    </Card>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6 text-slate-800 dark:text-white">Identity Verification</h2>
      
      {status === 'rejected' && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6 flex items-center gap-3">
            <XCircle size={24}/>
            <div>
                <span className="font-bold">Verification Rejected.</span> Please check your documents and try again.
            </div>
        </div>
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
            <div>
                <label className="block text-sm font-medium mb-2 dark:text-slate-300">Document Type</label>
                <select 
                    className="w-full p-2 border rounded-lg bg-white dark:bg-slate-800 dark:border-slate-700"
                    value={form.type}
                    onChange={e => setForm({...form, type: e.target.value})}
                >
                    <option value="national_id">National ID Card</option>
                    <option value="passport">Passport</option>
                    <option value="drivers_license">Driver's License</option>
                </select>
            </div>

            <Input 
                label="Document Number" 
                placeholder="e.g. A12345678" 
                value={form.number}
                onChange={e => setForm({...form, number: e.target.value})}
                required
            />

            <div>
                <label className="block text-sm font-medium mb-2 dark:text-slate-300">Upload Document Image</label>
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-8 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition relative">
                    {form.file ? (
                        <div className="flex flex-col items-center">
                            <img src={form.file} className="h-32 object-contain mb-2 rounded shadow-sm" />
                            <button type="button" onClick={() => setForm({...form, file: ''})} className="text-red-500 text-sm">Remove</button>
                        </div>
                    ) : (
                        <label className="cursor-pointer block">
                            <Upload size={32} className="mx-auto text-slate-400 mb-2"/>
                            <span className="text-blue-600 font-medium">Click to Upload</span>
                            <span className="text-slate-500 text-sm block mt-1">JPG, PNG up to 2MB</span>
                            <input type="file" className="hidden" accept="image/*" onChange={handleFile} required />
                        </label>
                    )}
                </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
                {loading ? 'Uploading...' : 'Submit for Verification'}
            </Button>
        </form>
      </Card>
    </div>
  );
}
""",

    # --- 4. ADMIN KYC PAGE (Review Queue) ---
    "app/(dashboard)/admin/kyc/page.tsx": """
'use client';
import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Check, X, FileText } from 'lucide-react';
import Swal from 'sweetalert2';
import { Modal } from '@/components/ui/Modal';

export default function AdminKYCPage() {
  const [requests, setRequests] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  const fetchRequests = async () => {
    const res = await fetch('/api/admin/kyc');
    if (res.ok) setRequests(await res.json());
  };

  useEffect(() => { fetchRequests(); }, []);

  const handleAction = async (userId: number, action: 'approve' | 'reject') => {
    let notes = '';
    if (action === 'reject') {
        const { value } = await Swal.fire({
            title: 'Reject Reason',
            input: 'text',
            inputPlaceholder: 'Why was this rejected?',
            showCancelButton: true
        });
        if (!value) return; 
        notes = value;
    }

    await fetch('/api/admin/kyc', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ userId, action, notes })
    });

    Swal.fire(action === 'approve' ? 'Approved' : 'Rejected', 'User status updated.', 'success');
    fetchRequests();
    setSelectedDoc(null);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold dark:text-white">KYC Verification Requests</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {requests.map((req: any) => (
            <Card key={req.id} className="flex flex-col gap-4">
                <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
                    <div className="bg-blue-100 p-2 rounded-full text-blue-600">
                        <FileText size={20}/>
                    </div>
                    <div>
                        <div className="font-bold text-slate-900">{req.name}</div>
                        <div className="text-xs text-slate-500">{req.email}</div>
                    </div>
                </div>

                <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                        <span className="text-slate-500">Doc Type:</span>
                        <span className="font-medium capitalize">{req.document_type.replace('_', ' ')}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">Number:</span>
                        <span className="font-mono bg-slate-50 px-1 rounded">{req.document_number}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-500">Submitted:</span>
                        <span>{new Date(req.submitted_at).toLocaleDateString()}</span>
                    </div>
                </div>

                <div className="mt-auto pt-4 flex gap-2">
                    <Button variant="secondary" className="flex-1" onClick={() => setSelectedDoc(req)}>View Doc</Button>
                </div>
            </Card>
        ))}
        {requests.length === 0 && <p className="text-slate-500 col-span-3 text-center py-12">No pending verification requests.</p>}
      </div>

      {/* DOCUMENT PREVIEW MODAL */}
      <Modal isOpen={!!selectedDoc} onClose={() => setSelectedDoc(null)} title="Review Document">
        {selectedDoc && (
            <div className="space-y-6">
                <div className="bg-slate-100 p-4 rounded-lg flex justify-center">
                    <img src={selectedDoc.file_data} className="max-h-[60vh] object-contain shadow-lg rounded" />
                </div>
                
                <div className="flex justify-end gap-3">
                    <Button variant="danger" onClick={() => handleAction(selectedDoc.user_id, 'reject')}>
                        <X size={18} className="mr-2"/> Reject
                    </Button>
                    <Button onClick={() => handleAction(selectedDoc.user_id, 'approve')}>
                        <Check size={18} className="mr-2"/> Approve
                    </Button>
                </div>
            </div>
        )}
      </Modal>
    </div>
  );
}
""",

    # --- 5. UPDATE SIDEBAR (Add KYC Links) ---
    "components/layout/Sidebar.tsx": """
'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, Users, CreditCard, ArrowRightLeft, ShieldCheck, Mail, HelpCircle, LogOut, Settings, Lock, FileText, BadgeCheck } from 'lucide-react';
import Swal from 'sweetalert2';
import { useEffect, useState } from 'react';
import { getClientPolicy } from '@/lib/clientCookie';

export function Sidebar({ userRole }: { userRole: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [policy, setPolicy] = useState<{ role: string, permissions: string[] }>({ role: '', permissions: [] });
  const [siteSettings, setSiteSettings] = useState({ site_name: 'BankSystem', site_logo: '' });

  useEffect(() => {
    const data = getClientPolicy();
    setPolicy(data);
    fetch('/api/admin/settings').then(res => res.json()).then(data => { if(data.site_name) setSiteSettings(data); });
  }, []);

  const adminMenuItems = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard, requiredPerm: null },
    { name: 'Customers', href: '/admin/customers', icon: Users, requiredPerm: 'CustomersView' },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard, requiredPerm: 'AccountsView' },
    { name: 'Transactions', href: '/admin/transactions', icon: ArrowRightLeft, requiredPerm: 'TransactionsView' },
    { name: 'KYC Requests', href: '/admin/kyc', icon: BadgeCheck, requiredPerm: 'KYCManage' }, // NEW LINK
    { name: 'Support Tickets', href: '/admin/support', icon: HelpCircle, requiredPerm: 'SupportView' },
    { name: 'BankMail', href: '/messages', icon: Mail, requiredPerm: 'BankMailUse' },
    { name: 'Roles & Permissions', href: '/admin/roles', icon: Lock, requiredPerm: 'RolesManage' },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings, requiredPerm: 'SettingsView' },
  ];

  const customerMenuItems = [
    { name: 'Overview', href: '/customer', icon: LayoutDashboard },
    { name: 'Transfer', href: '/customer/transfer', icon: ArrowRightLeft },
    { name: 'Verify Identity (KYC)', href: '/customer/kyc', icon: FileText }, // NEW LINK
    { name: 'History', href: '/customer/history', icon: ShieldCheck },
    { name: 'BankMail', href: '/messages', icon: Mail },
    { name: 'Support', href: '/customer/support', icon: HelpCircle },
  ];

  const effectiveRole = policy.role || userRole;
  const effectivePerms = policy.permissions || [];

  const links = effectiveRole === 'customer' 
    ? customerMenuItems 
    : adminMenuItems.filter(item => {
        if (effectiveRole === 'admin') return true;
        if (!item.requiredPerm) return true;
        return effectivePerms.includes(item.requiredPerm);
      });

  const handleLogout = async () => {
    const result = await Swal.fire({
      title: 'Sign Out?',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#EF4444',
      confirmButtonText: 'Yes, Sign Out'
    });

    if (result.isConfirmed) {
      await fetch('/api/auth/logout', { method: 'POST' });
      router.push('/login');
      router.refresh();
    }
  };

  return (
    <aside className="hidden md:flex w-64 bg-slate-900 text-white flex-col h-full border-r border-slate-800 shadow-xl shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-800/50 gap-3">
        {siteSettings.site_logo ? (
            <img src={siteSettings.site_logo} className="w-8 h-8 rounded bg-white p-0.5" />
        ) : (
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="font-bold text-lg text-white">B</span>
            </div>
        )}
        <span className="font-bold text-xl tracking-tight text-slate-100 truncate">{siteSettings.site_name}</span>
      </div>

      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          {effectiveRole === 'customer' ? 'Customer Menu' : 'Staff Menu'}
        </p>
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <Icon size={18} className={`mr-3 ${isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-300'}`} />
              {link.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800/50">
        <button onClick={handleLogout} className="flex items-center w-full px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-400/10 rounded-lg transition-colors">
          <LogOut size={18} className="mr-3" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
"""
}

def kyc_module():
    print("🆔 Installing KYC Module (Customer Upload + Admin Review)...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created: {path}")
    
    print("\n✅ KYC Module Ready! Restart server.")

if __name__ == "__main__":
    kyc_module()
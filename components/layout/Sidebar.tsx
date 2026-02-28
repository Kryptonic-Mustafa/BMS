'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { LayoutDashboard, PieChart, Users, CreditCard, Landmark, ShieldCheck, Headset, Settings, LogOut, Menu, X } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();
  const [brandName, setBrandName] = useState('Loading...');
  const [brandLogo, setBrandLogo] = useState('');
  const [isOpen, setIsOpen] = useState(false); // Mobile state

  useEffect(() => {
    const fetchBrand = async () => {
      try {
        const res = await fetch('/api/admin/settings');
        const data = await res.json();
        if (data.site_name) setBrandName(data.site_name);
        if (data.site_logo) setBrandLogo(data.site_logo);
      } catch (e) {
        setBrandName('Bank System');
      }
    };
    fetchBrand();
  }, []);

  const links = [
    { name: 'Dashboard', href: '/admin', icon: LayoutDashboard },
    { name: 'Analytics', href: '/admin/analytics', icon: PieChart },
    { name: 'Customers', href: '/admin/customers', icon: Users },
    { name: 'Accounts', href: '/admin/accounts', icon: CreditCard },
    { name: 'Loans', href: '/admin/loans', icon: Landmark },
    { name: 'KYC', href: '/admin/kyc', icon: ShieldCheck },
    { name: 'Support', href: '/admin/support', icon: Headset },
    { name: 'Master Settings', href: '/admin/settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Hamburger Button */}
      <div className="md:hidden fixed top-0 left-0 w-full h-16 bg-[#0f172a] z-40 flex items-center px-4 border-b border-slate-800">
        <button onClick={() => setIsOpen(true)} className="text-white hover:text-blue-400 transition-colors">
          <Menu size={28} />
        </button>
        <span className="ml-4 text-white font-bold text-lg">{brandName}</span>
      </div>

      {/* Mobile Overlay Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm" onClick={() => setIsOpen(false)} />
      )}

      {/* Sidebar Core */}
      <div className={`w-64 bg-[#0f172a] text-white h-screen fixed left-0 top-0 border-r border-slate-800 flex flex-col z-50 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:translate-x-0`}>
        <div className="p-6 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {brandLogo ? (
              <img src={brandLogo} alt="Logo" className="w-8 h-8 rounded object-cover" />
            ) : (
              <Landmark className="text-blue-500" size={28} />
            )}
            <span className="text-xl font-bold tracking-tight truncate">{brandName}</span>
          </div>
          {/* Mobile Close Button */}
          <button onClick={() => setIsOpen(false)} className="md:hidden text-slate-400 hover:text-white">
            <X size={24} />
          </button>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4 overflow-y-auto">
          {links.map((link) => {
            const isActive = pathname === link.href || pathname?.startsWith(link.href + '/');
            const Icon = link.icon;
            return (
              <Link 
                key={link.name} 
                href={link.href} 
                onClick={() => setIsOpen(false)} // Close on click for mobile
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive ? 'bg-blue-600/10 text-blue-500 font-semibold' : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{link.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <Link href="/api/auth/logout" className="flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
            <LogOut size={20} />
            <span className="font-medium">Sign Out</span>
          </Link>
        </div>
      </div>
    </>
  );
}
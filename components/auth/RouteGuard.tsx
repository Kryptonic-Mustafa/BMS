'use client';
import { useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Swal from 'sweetalert2';
import { getClientPolicy } from '@/lib/clientCookie';

const REQUIRED_PERMISSIONS: Record<string, string> = {
  '/admin/customers': 'CustomersView',
  '/admin/accounts': 'AccountsView',
  '/admin/transactions': 'TransactionsView',
  '/admin/settings': 'SettingsView', 
  '/admin/roles': 'RolesManage',
  '/admin/danger': 'DangerZoneAccess'
};

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const checkedRef = useRef('');

  useEffect(() => {
    // 1. Read Policy from Cookie
    const { role, permissions } = getClientPolicy();
    
    if (role === 'admin') return; // Bypass for SuperAdmin

    // 2. Check Permission
    const protectKey = Object.keys(REQUIRED_PERMISSIONS).find(key => pathname.startsWith(key));
    
    if (protectKey) {
      const requiredPerm = REQUIRED_PERMISSIONS[protectKey];
      
      // If permission is missing in the array
      if (!permissions.includes(requiredPerm)) {
        if (checkedRef.current === pathname) return;
        checkedRef.current = pathname;

        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'error',
            title: 'ACCESS DENIED',
            text: 'You do not have permission to view this page.',
            showConfirmButton: false,
            timer: 3000
        });

        router.replace('/admin');
      }
    }
  }, [pathname, router]);

  return <>{children}</>;
}
'use client';
import { useState, useEffect } from 'react';

export function usePermissions() {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [role, setRole] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch fresh data on mount
    fetch('/api/auth/profile')
      .then(res => res.json())
      .then(data => {
        if (data.permissions) {
            setPermissions(data.permissions);
            setRole(data.role);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const can = (permissionName: string) => {
    if (role === 'admin') return true; // Super Admin bypass
    return permissions.includes(permissionName);
  };

  return { permissions, role, can, loading };
}
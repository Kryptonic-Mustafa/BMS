'use client';
import { useEffect, useRef } from 'react';
import Swal from 'sweetalert2';
import { useRouter } from 'next/navigation';

export function NotificationListener() {
  const router = useRouter();
  const lastIdRef = useRef<number>(0);

  useEffect(() => {
    const checkNotifications = async () => {
      try {
        const res = await fetch('/api/notifications');
        const data = await res.json();
        
        // Filter for unread
        const unread = data.filter((n: any) => !n.is_read);

        if (unread.length > 0) {
          const latest = unread[0];
          
          // Only show toast if it's a NEW notification we haven't seen in this session
          if (latest.id > lastIdRef.current) {
            lastIdRef.current = latest.id;
            
            const isMail = latest.message.includes('New Message');

            const Toast = Swal.mixin({
              toast: true,
              position: 'top-end',
              showConfirmButton: false,
              timer: 5000,
              timerProgressBar: true,
              didOpen: (toast) => {
                toast.addEventListener('click', () => {
                   if (isMail) router.push('/messages'); // Click to go to mail
                });
              }
            });

            Toast.fire({
              icon: isMail ? 'info' : latest.type,
              title: isMail ? '📧 New Email Received' : latest.message,
              text: isMail ? latest.message : ''
            });

            // Mark as read immediately
            await fetch('/api/notifications', { method: 'PUT' });
          }
        }
      } catch (error) {
        // silent fail
      }
    };

    // Poll frequently (every 3 seconds) for that "Instant" feel
    const interval = setInterval(checkNotifications, 3000);
    return () => clearInterval(interval);
  }, [router]);

  return null;
}
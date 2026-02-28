'use client';
import { useEffect, useRef } from 'react';
import Swal from 'sweetalert2';

export function GlobalToastListener() {
  const lastNotifIdRef = useRef<number>(0);
  const isFirstLoad = useRef(true);

  // Simple Notification Sound
  const playSound = () => {
    try {
        const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
        audio.volume = 0.5;
        audio.play().catch(() => {}); // Catch error if user hasn't interacted yet
    } catch (e) {}
  };

  useEffect(() => {
    const checkNotifications = async () => {
      try {
        // Add timestamp to prevent browser caching
        const res = await fetch(`/api/notifications?t=${Date.now()}`);
        if (!res.ok) return;
        
        const data = await res.json();
        const list = data.notifications || [];

        if (list.length > 0) {
            const latest = list[0];
            
            // Sync on first load without popup
            if (isFirstLoad.current) {
                lastNotifIdRef.current = latest.id;
                isFirstLoad.current = false;
                return;
            }

            // NEW NOTIFICATION DETECTED
            if (latest.id > lastNotifIdRef.current) {
                playSound(); // Play "Pop" sound

                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: latest.type === 'success' ? 'success' : latest.type === 'error' ? 'error' : 'info',
                    title: latest.type === 'success' ? 'Success' : latest.type === 'error' ? 'Alert' : 'Update',
                    text: latest.message,
                    showConfirmButton: false,
                    timer: 5000,
                    timerProgressBar: true,
                    background: document.documentElement.classList.contains('dark') ? '#1e293b' : '#fff',
                    color: document.documentElement.classList.contains('dark') ? '#fff' : '#0f172a',
                    didOpen: (toast) => {
                        toast.addEventListener('mouseenter', Swal.stopTimer);
                        toast.addEventListener('mouseleave', Swal.resumeTimer);
                        // Add click to view
                        toast.addEventListener('click', () => {
                            window.location.href = '/notifications';
                        });
                    }
                });

                lastNotifIdRef.current = latest.id;
            }
        }
      } catch (e) { console.error("Toast Error:", e); }
    };

    // Poll every 2 seconds (Faster updates)
    checkNotifications();
    const interval = setInterval(checkNotifications, 2000);
    return () => clearInterval(interval);
  }, []);

  return null;
}
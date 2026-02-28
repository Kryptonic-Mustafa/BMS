import os

files = {
    # --- 1. FORCE DYNAMIC API (CRITICAL FIX) ---
    # Adding 'export const dynamic = "force-dynamic"' fixes the caching issue.
    "app/api/notifications/route.ts": """
import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

// CRITICAL: This line stops Next.js from caching the response!
export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  // Fetch notifications (limit 50)
  const notifications = await query(
    'SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50',
    [session.id]
  );
  
  // Fetch unread count
  const count: any = await query(
    'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = FALSE',
    [session.id]
  );

  return NextResponse.json({ 
    notifications, 
    unreadCount: count[0].count 
  });
}

export async function PUT(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { id, markAll, status } = await request.json();
  const isRead = status !== undefined ? status : true;

  if (markAll) {
    await query('UPDATE notifications SET is_read = TRUE WHERE user_id = ?', [session.id]);
  } else if (id) {
    await query('UPDATE notifications SET is_read = ? WHERE id = ? AND user_id = ?', [isRead, id, session.id]);
  }

  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  
  const { id } = await request.json();
  if (id) {
      await query('DELETE FROM notifications WHERE id = ? AND user_id = ?', [id, session.id]);
  }
  return NextResponse.json({ success: true });
}
""",

    # --- 2. ENHANCED GLOBAL LISTENER (With Sound & Faster Polling) ---
    "components/layout/GlobalToastListener.tsx": """
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
"""
}

def fix_alerts():
    print("🚑 Fixing Notification Caching & Enhancing Toasts...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Updated: {path}")

if __name__ == "__main__":
    fix_alerts()
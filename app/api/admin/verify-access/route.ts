import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';
import bcrypt from 'bcryptjs';

export async function POST(request: Request) {
  const session = await getSession();
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { password } = await request.json();

  // 1. Fetch real user record
  const users: any = await query('SELECT * FROM users WHERE id = ?', [session.id]);
  if (users.length === 0) return NextResponse.json({ error: 'User not found' }, { status: 404 });
  const user = users[0];

  // 2. Verify Password
  const isMatch = await bcrypt.compare(password, user.password);
  if (!isMatch) {
    return NextResponse.json({ error: 'Incorrect password' }, { status: 401 });
  }

  // 3. Check Super Admin Status
  if (user.is_super_admin) {
    return NextResponse.json({ success: true });
  } else {
    // SECURITY INCIDENT! Regular Admin trying to access Danger Zone.
    
    // Find Super Admin ID (assuming the first one found)
    const superAdmins: any = await query('SELECT id FROM users WHERE is_super_admin = TRUE LIMIT 1');
    if (superAdmins.length > 0) {
        const superId = superAdmins[0].id;
        
        // Log Ticket
        await query(
            'INSERT INTO support_tickets (user_id, subject, message, status) VALUES (?, ?, ?, ?)',
            [session.id, 'SECURITY ALERT: Unauthorized Access Attempt', `User ${user.name} (${user.email}) tried to access the Danger Zone / Factory Reset.`, 'open']
        );

        // Send Notification
        await query(
            'INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)',
            [superId, `SECURITY ALERT: ${user.name} tried to access Danger Zone!`, 'error']
        );
    }

    return NextResponse.json({ error: 'ACCESS DENIED. Incident reported to Super Admin.', incident: true }, { status: 403 });
  }
}
import { query } from '@/lib/db';

interface AuditParams {
  actorId: number;
  actorName: string;
  targetId?: number;
  targetName?: string;
  action: string;
  details: string;
  status?: 'SUCCESS' | 'FAILED' | 'PENDING';
}

export async function logActivity({ actorId, actorName, targetId, targetName, action, details, status = 'SUCCESS' }: AuditParams) {
  try {
    await query(
      `INSERT INTO audit_logs (actor_id, actor_name, target_id, target_name, action_type, details, status) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [actorId, actorName, targetId || null, targetName || 'System', action, details, status]
    );
  } catch (e) {
    console.error('Failed to write audit log:', e);
  }
}
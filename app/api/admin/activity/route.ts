import { NextResponse } from 'next/server';
import { query } from '@/lib/db';
import { getSession } from '@/lib/session';

export async function GET() {
  const session = await getSession();
  if (!session) return NextResponse.json([]);

  const logs = await query(`
    SELECT * FROM audit_logs 
    ORDER BY created_at DESC 
    LIMIT 20
  `);
  
  return NextResponse.json(logs);
}
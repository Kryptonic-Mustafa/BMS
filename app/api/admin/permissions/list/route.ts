import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  const perms = await query('SELECT * FROM permissions ORDER BY name ASC');
  return NextResponse.json(perms);
}
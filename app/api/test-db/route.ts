import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export async function GET() {
  try {
    const result: any = await query('SELECT 1 + 1 AS result');
    return NextResponse.json({ status: 'Connected', data: result });
  } catch (error: any) {
    return NextResponse.json({ status: 'Error', message: error.message }, { status: 500 });
  }
}
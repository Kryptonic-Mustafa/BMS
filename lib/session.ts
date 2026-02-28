import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

// Hardcoded to guarantee the encrypt and decrypt functions are using the EXACT same key
const secretKey = "bms_super_secret_key_production_2026"; 
const key = new TextEncoder().encode(secretKey);

export async function encrypt(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(key);
}

export async function decrypt(input: string): Promise<any> {
  try {
    const { payload } = await jwtVerify(input, key, { algorithms: ['HS256'] });
    return payload;
  } catch (error) {
    console.error("[SESSION ERROR] Failed to decrypt token:", error);
    return null;
  }
}

export async function getSession() {
  const sessionCookie = (await cookies()).get('session')?.value;
  if (!sessionCookie) {
      console.warn("[SESSION ERROR] No session cookie found in request.");
      return null;
  }
  return await decrypt(sessionCookie);
}
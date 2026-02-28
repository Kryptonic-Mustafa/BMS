import os

# 1. Revert lib/auth.ts to be Edge-Safe (No DB imports)
auth_content = """
import { SignJWT, jwtVerify } from 'jose';
import { cookies } from 'next/headers';

const secretKey = process.env.JWT_SECRET || 'secret';
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
    return null;
  }
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete('session');
}
"""

# 2. Create lib/session.ts (Node.js only - Handles DB)
session_content = """
import { cookies } from 'next/headers';
import { decrypt } from '@/lib/auth';
import { query } from '@/lib/db';

export async function getSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get('session')?.value;
  if (!session) return null;
  
  const payload: any = await decrypt(session);
  if(!payload) return null;

  try {
    // Fetch fresh permissions from DB
    // We check if role_id exists to handle migration, otherwise fallback
    if (payload.role_id) {
        const perms: any = await query(`
            SELECT p.name 
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = ?
        `, [payload.role_id]);

        const permissionList = perms.map((p: any) => p.name);
        return { ...payload, permissions: permissionList };
    }
    return payload; 
  } catch (e) {
    // Fallback if DB fails or during strict edge cases
    return payload;
  }
}
"""

# List of files that likely use getSession and need updating
files_to_update = [
    "app/api/admin/roles/route.ts",
    "app/api/admin/permissions/route.ts",
    "app/api/admin/users/route.ts",
    "app/api/admin/users/bulk-delete/route.ts",
    "app/api/admin/settings/route.ts",
    "app/api/admin/customers/details/route.ts",
    "app/api/admin/deposit/route.ts",
    "app/api/tickets/route.ts",
    "app/api/messages/route.ts",
    "app/api/auth/profile/route.ts",
    "app/api/admin/danger/reset/route.ts",
    "app/api/admin/verify-access/route.ts",
    "app/api/customer/transfer/route.ts",
    "app/(dashboard)/layout.tsx",
    "app/(dashboard)/admin/customers/page.tsx",
    "app/(dashboard)/customer/page.tsx", 
    "app/(dashboard)/customer/history/page.tsx" 
]

def fix_edge_issue():
    print("🔧 Fixing Edge Runtime Crash...")

    # 1. Write clean auth.ts
    with open("lib/auth.ts", "w", encoding="utf-8") as f:
        f.write(auth_content.strip())
    print("✅ Restored lib/auth.ts (Edge Safe)")

    # 2. Create session.ts
    with open("lib/session.ts", "w", encoding="utf-8") as f:
        f.write(session_content.strip())
    print("✅ Created lib/session.ts (DB Connected)")

    # 3. Update imports in other files
    count = 0
    for file_path in files_to_update:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace import { getSession } from '@/lib/auth' 
            # with import { getSession } from '@/lib/session'
            if "from '@/lib/auth'" in content and "getSession" in content:
                new_content = content.replace(
                    "import { getSession } from '@/lib/auth';", 
                    "import { getSession } from '@/lib/session';"
                )
                # Handle cases where multiple imports existed like { getSession, encrypt }
                # This simple replace covers the most common pattern we generated. 
                # If complex, we just append the new import.
                if new_content == content: 
                     # Regex fallback or simple string manipulation for mixed imports
                     new_content = content.replace("getSession,", "").replace(", getSession", "")
                     new_content = "import { getSession } from '@/lib/session';\n" + new_content

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"   -> Updated imports in {file_path}")
                count += 1
    
    print(f"🎉 Fixed {count} files. Restart server with 'npm run dev'.")

if __name__ == "__main__":
    fix_edge_issue()
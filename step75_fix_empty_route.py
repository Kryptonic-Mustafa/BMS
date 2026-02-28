import os

files = {
    # Provide a valid export so TypeScript stops complaining
    "app/api/auth/route.ts": """
import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ message: 'Auth API Base Route is Active' });
}
"""
}

def fix_empty_route():
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
    print("✅ Fixed Empty Route Error! The file is now a valid TypeScript module.")

if __name__ == "__main__":
    fix_empty_route()
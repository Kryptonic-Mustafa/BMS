import os

files = {
    # --- 1. CREATE THEME PROVIDER ---
    "components/theme-provider.tsx": """
'use client';

import * as React from 'react';
import { ThemeProvider as NextThemesProvider, useTheme } from 'next-themes';

export function ThemeProvider({ children, ...props }: any) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}

export { useTheme };
""",

    # --- 2. WRAP ROOT LAYOUT (To Enable Themes Globally) ---
    "app/layout.tsx": """
import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Bank App',
  description: 'Next Gen Banking Management System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
            {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
"""
}

def fix_theme_error():
    print("🎨 Creating Theme Provider & Wrapping App...")
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"✅ Created/Updated: {path}")
    
    print("\n✅ Fix Complete! Restart server with 'npm run dev'.")

if __name__ == "__main__":
    fix_theme_error()
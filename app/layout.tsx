import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ThemeProvider } from '@/components/theme-provider';
import { GlobalToastListener } from '@/components/layout/GlobalToastListener';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'DevOs Bank - Next Gen Banking',
  description: 'Secure, Fast, and Reliable Banking System',
  icons: {
    icon: 'https://cdn-icons-png.flaticon.com/512/2830/2830284.png', // Generic Bank Icon
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-300`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
            <GlobalToastListener />
            {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
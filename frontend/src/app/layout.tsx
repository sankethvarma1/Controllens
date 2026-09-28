import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import AppShell from '@/components/AppShell';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'CONTROLLENS | Regulatory & Control Intelligence Platform',
  description: 'Connect regulations to controls with full traceability and evidence-based reasoning.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} font-sans`}>
      <body className="min-h-screen bg-secondary-50">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
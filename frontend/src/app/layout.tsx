import './globals.css';

import type { Metadata } from 'next';

import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Polyphony Ledger',
  description: 'Real-time crypto payments ledger demo'
};

export default function RootLayout({ children }: { children: React.ReactNode }): React.JSX.Element {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}

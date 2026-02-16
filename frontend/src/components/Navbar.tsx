'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const links = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/transactions', label: 'Transactions' },
  { href: '/ledger', label: 'Ledger' },
  { href: '/analytics', label: 'Analytics' },
  { href: '/replay', label: 'Replay' },
  { href: '/traces', label: 'Traces' }
];

export default function Navbar(): React.JSX.Element {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/dashboard" className="text-xl font-bold tracking-tight text-ink">
          Polyphony Ledger
        </Link>
        <nav className="flex flex-wrap gap-2">
          {links.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-3 py-1 text-sm font-medium transition-all ${
                  active
                    ? 'bg-ink text-white shadow-lg shadow-slate-300'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

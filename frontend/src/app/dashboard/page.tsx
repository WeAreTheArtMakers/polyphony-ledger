'use client';

import { useEffect, useMemo, useState } from 'react';

import BalanceTable from '@/components/BalanceTable';
import KpiCards from '@/components/KpiCards';
import LedgerTable from '@/components/LedgerTable';
import { api } from '@/lib/api';
import { BalanceRow, LedgerKpis, LedgerRow, WsSnapshot } from '@/lib/types';
import { useStream } from '@/lib/ws';

export default function DashboardPage(): React.JSX.Element {
  const [kpis, setKpis] = useState<LedgerKpis | null>(null);
  const [balances, setBalances] = useState<BalanceRow[]>([]);
  const [ledgerRows, setLedgerRows] = useState<LedgerRow[]>([]);
  const [generatorRunning, setGeneratorRunning] = useState(false);

  const refresh = async () => {
    const [kpiRes, balRes, ledRes, genRes] = await Promise.all([
      api.ledgerKpis(),
      api.balances('default', 20),
      api.ledgerRecent(20),
      api.generatorStatus()
    ]);
    setKpis(kpiRes);
    setBalances(balRes);
    setLedgerRows(ledRes);
    setGeneratorRunning(genRes.running);
  };

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => {
      void refresh();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useStream((snapshot: WsSnapshot) => {
    if (snapshot.type === 'snapshot') {
      setBalances(snapshot.balances || []);
      setLedgerRows(snapshot.ledger || []);
    }
  });

  const throughputPerMin = useMemo(() => {
    if (!kpis || kpis.tx_count === 0) {
      return 0;
    }
    return Math.max(0, Math.min(99999, kpis.entry_count));
  }, [kpis]);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Real-Time Ledger Dashboard</h1>
      <KpiCards kpis={kpis} throughputPerMin={throughputPerMin} generatorRunning={generatorRunning} />
      <div className="grid gap-4 xl:grid-cols-2">
        <LedgerTable rows={ledgerRows} />
        <BalanceTable rows={balances} />
      </div>
    </div>
  );
}

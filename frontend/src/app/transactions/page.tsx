'use client';

import { useEffect, useState } from 'react';

import TxIngestForm from '@/components/TxIngestForm';
import TxTables from '@/components/TxTables';
import { api } from '@/lib/api';

export default function TransactionsPage(): React.JSX.Element {
  const [rawRows, setRawRows] = useState<any[]>([]);
  const [validatedRows, setValidatedRows] = useState<any[]>([]);
  const [generatorRunning, setGeneratorRunning] = useState(false);

  const refresh = async () => {
    const [raw, validated, generatorStatus] = await Promise.all([
      api.recentRaw(40),
      api.recentValidated(40),
      api.generatorStatus()
    ]);
    setRawRows(raw);
    setValidatedRows(validated);
    setGeneratorRunning(generatorStatus.running);
  };

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => {
      void refresh();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const toggleGenerator = async () => {
    if (generatorRunning) {
      await api.generatorStop();
    } else {
      await api.generatorStart(8);
    }
    await refresh();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Transactions</h1>
        <button
          onClick={toggleGenerator}
          className={`rounded-lg px-3 py-2 font-medium text-white ${generatorRunning ? 'bg-coral' : 'bg-mint'}`}
        >
          {generatorRunning ? 'Stop Seed Generator' : 'Start Seed Generator'}
        </button>
      </div>
      <TxIngestForm />
      <TxTables rawRows={rawRows} validatedRows={validatedRows} />
    </div>
  );
}

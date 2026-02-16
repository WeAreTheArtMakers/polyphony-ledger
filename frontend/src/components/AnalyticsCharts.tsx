'use client';

import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { AnalyticsPoint, TopAccountPoint } from '@/lib/types';

type Props = {
  volumeRows: AnalyticsPoint[];
  netflowRows: AnalyticsPoint[];
  topRows: TopAccountPoint[];
};

export default function AnalyticsCharts({ volumeRows, netflowRows, topRows }: Props): React.JSX.Element {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold">Volume per Asset (1m MV)</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={volumeRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" hide />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="volume" stroke="#2a9d8f" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <h3 className="mb-3 text-lg font-semibold">Netflow (1m MV)</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={netflowRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="netflow" stroke="#e76f51" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-2">
        <h3 className="mb-3 text-lg font-semibold">Top Accounts (5m MV)</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="account_id" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="netflow" fill="#1b263b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

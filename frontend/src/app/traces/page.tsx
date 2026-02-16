'use client';

import TraceEmbed from '@/components/TraceEmbed';

export default function TracesPage(): React.JSX.Element {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Distributed Tracing</h1>
      <TraceEmbed />
    </div>
  );
}

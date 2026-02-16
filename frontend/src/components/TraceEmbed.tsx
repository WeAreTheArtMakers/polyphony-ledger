'use client';

export default function TraceEmbed(): React.JSX.Element {
  const jaegerUrl = process.env.NEXT_PUBLIC_JAEGER_URL || 'http://localhost:16686';

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Jaeger Traces</h3>
        <a href={jaegerUrl} target="_blank" rel="noreferrer" className="text-sm underline">
          Open Jaeger in new tab
        </a>
      </div>
      <iframe
        title="Jaeger"
        src={jaegerUrl}
        className="h-[720px] w-full rounded-lg border border-slate-200"
        referrerPolicy="no-referrer"
      />
      <p className="text-sm text-slate-600">
        Tip: filter by tag <code>correlation_id</code> or <code>event_id</code> to inspect end-to-end pipeline traces.
      </p>
    </div>
  );
}

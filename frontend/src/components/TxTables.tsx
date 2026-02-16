'use client';

type Props = {
  rawRows: any[];
  validatedRows: any[];
};

function Table({ title, rows }: { title: string; rows: any[] }): JSX.Element {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-lg font-semibold">{title}</h3>
      <div className="max-h-[360px] overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-100">
            <tr>
              {rows[0]
                ? Object.keys(rows[0]).map((key) => (
                    <th key={key} className="px-2 py-2 font-medium text-slate-600">
                      {key}
                    </th>
                  ))
                : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className="border-b border-slate-100 align-top">
                {Object.values(row).map((value, i) => (
                  <td key={i} className="px-2 py-2 text-slate-700">
                    <span className="inline-block max-w-[260px] truncate">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TxTables({ rawRows, validatedRows }: Props): JSX.Element {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Table title="Recent Raw Events" rows={rawRows} />
      <Table title="Recent Validated Transactions" rows={validatedRows} />
    </div>
  );
}

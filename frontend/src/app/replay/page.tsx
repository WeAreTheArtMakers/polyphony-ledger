'use client';

import ReplayControls from '@/components/ReplayControls';

export default function ReplayPage(): React.JSX.Element {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Replay</h1>
      <ReplayControls />
    </div>
  );
}

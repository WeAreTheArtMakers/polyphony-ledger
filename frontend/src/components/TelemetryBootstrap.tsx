'use client';

import { useEffect, useRef } from 'react';

import { usePathname } from 'next/navigation';
import { useReportWebVitals } from 'next/web-vitals';

import { emitClientError, emitWebVital, TelemetryRating } from '@/lib/telemetry';

type MetricWithRating = {
  id: string;
  name: string;
  value: number;
  delta: number;
  rating?: TelemetryRating;
};

function serializeReason(reason: unknown): { message: string; stack?: string } {
  if (reason instanceof Error) {
    return {
      message: reason.message || 'Unhandled promise rejection',
      stack: reason.stack
    };
  }
  if (typeof reason === 'string') {
    return { message: reason };
  }
  try {
    return { message: JSON.stringify(reason) };
  } catch {
    return { message: String(reason) };
  }
}

export default function TelemetryBootstrap(): null {
  const pathname = usePathname() || '/';
  const pathRef = useRef<string>(pathname);

  useEffect(() => {
    pathRef.current = pathname || '/';
  }, [pathname]);

  useReportWebVitals((metric) => {
    const value = metric as unknown as MetricWithRating;
    emitWebVital(pathRef.current, {
      id: value.id,
      name: value.name,
      value: value.value,
      delta: value.delta,
      rating: value.rating
    });
  });

  useEffect(() => {
    const onError = (event: ErrorEvent): void => {
      emitClientError(pathRef.current, {
        kind: 'error',
        message: event.message || 'Window error',
        stack: event.error instanceof Error ? event.error.stack : undefined
      });
    };

    const onUnhandledRejection = (event: PromiseRejectionEvent): void => {
      const reason = serializeReason(event.reason);
      emitClientError(pathRef.current, {
        kind: 'unhandledrejection',
        message: reason.message,
        stack: reason.stack
      });
    };

    window.addEventListener('error', onError);
    window.addEventListener('unhandledrejection', onUnhandledRejection);

    return () => {
      window.removeEventListener('error', onError);
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
    };
  }, []);

  return null;
}

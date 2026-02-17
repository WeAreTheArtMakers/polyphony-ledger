import { API_BASE } from '@/lib/api';

export type TelemetryRating = 'good' | 'needs-improvement' | 'poor' | 'unknown';
type ErrorKind = 'error' | 'unhandledrejection';

type FrontendTelemetryEvent = {
  type: 'web_vital' | 'client_error';
  path: string;
  href: string;
  workspace_id: string;
  session_id: string;
  user_agent: string;
  ts: string;
  name?: string;
  value?: number;
  rating?: TelemetryRating;
  id?: string;
  delta?: number;
  kind?: ErrorKind;
  message?: string;
  stack?: string;
};

const TELEMETRY_ENDPOINT = `${API_BASE}/telemetry/frontend`;
const SESSION_STORAGE_KEY = 'polyphony_telemetry_session_id';
const MAX_TEXT_LENGTH = 1024;

function sanitizeText(value: string | undefined): string | undefined {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const clipped = trimmed.slice(0, MAX_TEXT_LENGTH);
  return clipped
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[redacted-email]')
    .replace(/\b\d{12,19}\b/g, '[redacted-number]');
}

function telemetryEnabled(): boolean {
  const raw = process.env.NEXT_PUBLIC_FE_TELEMETRY_ENABLED ?? 'true';
  return raw.toLowerCase() !== 'false';
}

function sampleEnabled(): boolean {
  const raw = process.env.NEXT_PUBLIC_FE_TELEMETRY_SAMPLE_RATE ?? '1';
  const parsed = Number(raw);
  const rate = Number.isFinite(parsed) ? Math.max(0, Math.min(1, parsed)) : 1;
  if (rate <= 0) {
    return false;
  }
  if (rate >= 1) {
    return true;
  }
  return Math.random() < rate;
}

const TELEMETRY_ALLOWED = telemetryEnabled() && sampleEnabled();

function getSessionId(): string {
  if (typeof window === 'undefined') {
    return 'server';
  }
  try {
    const existing = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (existing) {
      return existing;
    }
  } catch {
    return `session-${Date.now()}`;
  }
  const generated =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, generated);
  } catch {
    return generated;
  }
  return generated;
}

function inferRating(name: string, value: number): TelemetryRating {
  const metric = name.toUpperCase();
  if (metric === 'LCP') {
    if (value <= 2.5) {
      return 'good';
    }
    if (value <= 4) {
      return 'needs-improvement';
    }
    return 'poor';
  }
  if (metric === 'INP') {
    if (value <= 200) {
      return 'good';
    }
    if (value <= 500) {
      return 'needs-improvement';
    }
    return 'poor';
  }
  if (metric === 'CLS') {
    if (value <= 0.1) {
      return 'good';
    }
    if (value <= 0.25) {
      return 'needs-improvement';
    }
    return 'poor';
  }
  return 'unknown';
}

function postEvent(payload: FrontendTelemetryEvent): void {
  if (!TELEMETRY_ALLOWED || typeof window === 'undefined') {
    return;
  }

  const body = JSON.stringify(payload);
  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    const ok = navigator.sendBeacon(TELEMETRY_ENDPOINT, new Blob([body], { type: 'application/json' }));
    if (ok) {
      return;
    }
  }

  void fetch(TELEMETRY_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true
  }).catch(() => undefined);
}

function telemetryContext(path: string): Omit<FrontendTelemetryEvent, 'type'> {
  const href = typeof window !== 'undefined' ? window.location.href : '';
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : '';
  return {
    path: path || '/',
    href,
    workspace_id: 'default',
    session_id: getSessionId(),
    user_agent: userAgent.slice(0, 256),
    ts: new Date().toISOString()
  };
}

type WebVitalInput = {
  id: string;
  name: string;
  value: number;
  delta: number;
  rating?: TelemetryRating;
};

export function emitWebVital(path: string, metric: WebVitalInput): void {
  const normalizedName = metric.name.toUpperCase();
  const rating = metric.rating ?? inferRating(normalizedName, metric.value);
  postEvent({
    type: 'web_vital',
    ...telemetryContext(path),
    id: metric.id,
    name: normalizedName,
    value: metric.value,
    delta: metric.delta,
    rating
  });
}

type ClientErrorInput = {
  kind: ErrorKind;
  message: string;
  stack?: string;
};

export function emitClientError(path: string, input: ClientErrorInput): void {
  postEvent({
    type: 'client_error',
    ...telemetryContext(path),
    kind: input.kind,
    message: sanitizeText(input.message),
    stack: sanitizeText(input.stack)
  });
}

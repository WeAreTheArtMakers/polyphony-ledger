'use client';

import Link from 'next/link';
import Script from 'next/script';
import { useMemo, useState } from 'react';

declare global {
  interface Window {
    LanguageManager?: {
      getLanguage: () => string;
      setLanguage: (lang: string) => string;
      t: (key: string, lang?: string) => string;
      getSupportedLanguages: () => string[];
    };
  }
}

const FALLBACK: Record<string, string> = {
  'site.badge': 'Enterprise Real-Time Crypto Payments Infrastructure',
  'site.title': 'Polyphony Ledger',
  'site.subtitle': 'Immutable ledger accuracy + streaming analytics speed, in one production-ready platform.',
  'site.cta_demo': 'Open Live Demo',
  'site.cta_docs': 'View Documentation',
  'site.lang': 'Language',
  'outcomes.title': 'Sell Outcomes, Not Features',
  'outcomes.subtitle': 'Illustrative benchmark targets for pilot discussions.',
  'outcomes.reconciliation.label': 'Reconciliation Cycle',
  'outcomes.reconciliation.value': '4h -> 15m',
  'outcomes.reconciliation.delta': 'up to 93% faster',
  'outcomes.incident.label': 'Incident MTTR',
  'outcomes.incident.value': '120m -> 25m',
  'outcomes.incident.delta': 'up to 79% faster',
  'outcomes.audit.label': 'Audit Preparation Time',
  'outcomes.audit.value': '2 days -> 30m',
  'outcomes.audit.delta': 'up to 98% faster',
  'pillars.title': 'Why Teams Choose Polyphony Ledger',
  'pillars.p1.title': 'Financial Correctness by Design',
  'pillars.p1.desc': 'Immutable double-entry ledger with replayable projections and deterministic recovery.',
  'pillars.p2.title': 'Streaming Native Backbone',
  'pillars.p2.desc': 'Redpanda + Schema Registry + Protobuf evolution for durable event contracts.',
  'pillars.p3.title': 'Audit-Ready Observability',
  'pillars.p3.desc': 'End-to-end traces, DLQ isolation, structured logs, metrics and alerting out of the box.',
  'pillars.p4.title': 'Enterprise Controls',
  'pillars.p4.desc': 'OIDC SSO, RBAC guards, tenant quota controls and usage metering API.',
  'roi.title': 'ROI Readiness Checklist',
  'roi.c1': 'Do we know our current reconciliation lead time?',
  'roi.c2': 'Do we have measured MTTR for payment incidents?',
  'roi.c3': 'How many FTE-hours are spent preparing audit evidence?',
  'roi.c4': 'Can we prove schema changes do not break consumers?',
  'roi.c5': 'Can we trace one transaction end-to-end in under 2 minutes?',
  'delivery.title': 'Risk Reduction Delivery Plan',
  'delivery.d30': '0-30 Days: Discovery, baseline KPIs, pilot architecture, SLA and security scope.',
  'delivery.d60': '31-60 Days: Controlled pilot traffic, alerts/runbooks, governance policy tuning.',
  'delivery.d90': '61-90 Days: Production cutover, SSO/RBAC hardening, cost optimization and handover.',
  'pricing.title': 'Commercial Packaging',
  'pricing.poc': 'PoC',
  'pricing.poc_desc': 'Fast proof of value with measurable KPI delta.',
  'pricing.pilot': 'Pilot',
  'pricing.pilot_desc': 'Controlled real traffic with governance and observability.',
  'pricing.enterprise': 'Enterprise',
  'pricing.enterprise_desc': 'SLA-backed production with security and compliance controls.',
  'footer.note': 'Made with love by WeAreTheArtMakers'
};

function trans(key: string, lang: string): string {
  if (typeof window === 'undefined') {
    return FALLBACK[key] ?? key;
  }
  return window.LanguageManager?.t(key, lang) ?? FALLBACK[key] ?? key;
}

export default function SalesPage(): React.JSX.Element {
  const [lang, setLang] = useState<'en' | 'tr'>('en');

  const metrics = useMemo(
    () => [
      {
        label: trans('outcomes.reconciliation.label', lang),
        value: trans('outcomes.reconciliation.value', lang),
        delta: trans('outcomes.reconciliation.delta', lang)
      },
      {
        label: trans('outcomes.incident.label', lang),
        value: trans('outcomes.incident.value', lang),
        delta: trans('outcomes.incident.delta', lang)
      },
      {
        label: trans('outcomes.audit.label', lang),
        value: trans('outcomes.audit.value', lang),
        delta: trans('outcomes.audit.delta', lang)
      }
    ],
    [lang]
  );

  const roiChecklist = useMemo(
    () => [trans('roi.c1', lang), trans('roi.c2', lang), trans('roi.c3', lang), trans('roi.c4', lang), trans('roi.c5', lang)],
    [lang]
  );

  const deliveryPlan = useMemo(
    () => [trans('delivery.d30', lang), trans('delivery.d60', lang), trans('delivery.d90', lang)],
    [lang]
  );

  const pillars = useMemo(
    () => [
      { title: trans('pillars.p1.title', lang), desc: trans('pillars.p1.desc', lang) },
      { title: trans('pillars.p2.title', lang), desc: trans('pillars.p2.desc', lang) },
      { title: trans('pillars.p3.title', lang), desc: trans('pillars.p3.desc', lang) },
      { title: trans('pillars.p4.title', lang), desc: trans('pillars.p4.desc', lang) }
    ],
    [lang]
  );

  const pricing = useMemo(
    () => [
      { title: trans('pricing.poc', lang), desc: trans('pricing.poc_desc', lang) },
      { title: trans('pricing.pilot', lang), desc: trans('pricing.pilot_desc', lang) },
      { title: trans('pricing.enterprise', lang), desc: trans('pricing.enterprise_desc', lang) }
    ],
    [lang]
  );

  const switchLanguage = (next: 'en' | 'tr') => {
    if (typeof window !== 'undefined') {
      const normalized = (window.LanguageManager?.setLanguage(next) ?? next) as 'en' | 'tr';
      setLang(normalized);
      return;
    }
    setLang(next);
  };

  return (
    <div className="space-y-10 pb-12">
      <Script
        src="/language-manager.js"
        strategy="afterInteractive"
        onLoad={() => {
          const active = (window.LanguageManager?.getLanguage() ?? 'en') as 'en' | 'tr';
          setLang(active);
        }}
      />

      <section className="rounded-2xl border border-slate-200 bg-gradient-to-r from-ink to-sea p-8 text-white shadow-xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold tracking-wide">{trans('site.badge', lang)}</span>
          <div className="flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm">
            <span>{trans('site.lang', lang)}:</span>
            <button
              onClick={() => switchLanguage('en')}
              className={`rounded-full px-2 py-1 ${lang === 'en' ? 'bg-white text-ink' : 'bg-transparent text-white'}`}
            >
              EN
            </button>
            <button
              onClick={() => switchLanguage('tr')}
              className={`rounded-full px-2 py-1 ${lang === 'tr' ? 'bg-white text-ink' : 'bg-transparent text-white'}`}
            >
              TR
            </button>
          </div>
        </div>

        <h1 className="text-4xl font-black tracking-tight">{trans('site.title', lang)}</h1>
        <p className="mt-3 max-w-3xl text-lg text-slate-100">{trans('site.subtitle', lang)}</p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/dashboard" className="rounded-xl bg-white px-4 py-2 font-semibold text-ink">
            {trans('site.cta_demo', lang)}
          </Link>
          <a href="https://github.com/WeAreTheArtMakers/polyphony-ledger/tree/main/docs" className="rounded-xl border border-white/60 px-4 py-2 font-semibold text-white">
            {trans('site.cta_docs', lang)}
          </a>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-bold">{trans('outcomes.title', lang)}</h2>
        <p className="text-slate-600">{trans('outcomes.subtitle', lang)}</p>
        <div className="grid gap-4 md:grid-cols-3">
          {metrics.map((item) => (
            <article key={item.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
              <p className="mt-2 text-2xl font-bold text-ink">{item.value}</p>
              <p className="mt-1 text-sm font-semibold text-mint">{item.delta}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-bold">{trans('pillars.title', lang)}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {pillars.map((item) => (
            <article key={item.title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-ink">{item.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{item.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xl font-bold">{trans('roi.title', lang)}</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {roiChecklist.map((item) => (
              <li key={item} className="flex items-start gap-2">
                <input type="checkbox" className="mt-1" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xl font-bold">{trans('delivery.title', lang)}</h2>
          <ul className="mt-3 space-y-3 text-sm text-slate-700">
            {deliveryPlan.map((item) => (
              <li key={item} className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                {item}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-bold">{trans('pricing.title', lang)}</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {pricing.map((item) => (
            <article key={item.title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-bold text-ink">{item.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{item.desc}</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="rounded-xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-600 shadow-sm">
        {trans('footer.note', lang)}
      </footer>
    </div>
  );
}

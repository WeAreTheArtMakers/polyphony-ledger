(function (global) {
  var STORAGE_KEY = 'polyphony_language';
  var DEFAULT_LANG = 'en';
  var supported = ['en', 'tr'];

  var translations = {
    en: {
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
    },
    tr: {
      'site.badge': 'Kurumsal Gercek Zamanli Kripto Odeme Altyapisi',
      'site.title': 'Polyphony Ledger',
      'site.subtitle': 'Immutable ledger dogrulugu + streaming analitik hizi, tek bir production-ready platformda.',
      'site.cta_demo': 'Canli Demoyu Ac',
      'site.cta_docs': 'Dokumantasyonu Gor',
      'site.lang': 'Dil',

      'outcomes.title': 'Ozellik Degil Sonuc Satin',
      'outcomes.subtitle': 'Pilot gorusmeleri icin ornek hedef KPI seti.',
      'outcomes.reconciliation.label': 'Mutabakat Dongusu',
      'outcomes.reconciliation.value': '4 saat -> 15 dk',
      'outcomes.reconciliation.delta': 'yaklasik %93 daha hizli',
      'outcomes.incident.label': 'Incident MTTR',
      'outcomes.incident.value': '120 dk -> 25 dk',
      'outcomes.incident.delta': 'yaklasik %79 daha hizli',
      'outcomes.audit.label': 'Denetim Hazirlik Suresi',
      'outcomes.audit.value': '2 gun -> 30 dk',
      'outcomes.audit.delta': 'yaklasik %98 daha hizli',

      'pillars.title': 'Neden Polyphony Ledger?',
      'pillars.p1.title': 'Tasarımla Finansal Dogruluk',
      'pillars.p1.desc': 'Immutable double-entry ledger, replay edilebilir projection ve deterministik toparlanma.',
      'pillars.p2.title': 'Streaming Native Omurga',
      'pillars.p2.desc': 'Redpanda + Schema Registry + Protobuf evrimi ile saglam event sozlesmeleri.',
      'pillars.p3.title': 'Denetime Hazir Gozlemlenebilirlik',
      'pillars.p3.desc': 'Uctan uca trace, DLQ izolasyonu, structured log, metrik ve alert paket olarak gelir.',
      'pillars.p4.title': 'Kurumsal Kontroller',
      'pillars.p4.desc': 'OIDC tabanli SSO, RBAC guardlari, tenant quota ve usage metering API.',

      'roi.title': 'ROI Hazirlik Checklist',
      'roi.c1': 'Mevcut mutabakat suremizi net olcuyor muyuz?',
      'roi.c2': 'Odeme incidentlari icin olculmus MTTR var mi?',
      'roi.c3': 'Audit kaniti icin kac FTE-saat harcaniyor?',
      'roi.c4': 'Schema degisikliklerinin consumer kirmadigini kanitlayabiliyor muyuz?',
      'roi.c5': 'Tek transactioni 2 dakikadan kisa surede uctan uca izleyebiliyor muyuz?',

      'delivery.title': 'Riski Dusuren Delivery Plani',
      'delivery.d30': '0-30 Gun: Kesif, baseline KPI, pilot mimari, SLA ve guvenlik kapsami.',
      'delivery.d60': '31-60 Gun: Kontrollu pilot trafik, alert/runbook, governance politika ayari.',
      'delivery.d90': '61-90 Gun: Canliya gecis, SSO/RBAC sertlestirme, maliyet optimizasyonu ve devir.',

      'pricing.title': 'Ticari Paketleme',
      'pricing.poc': 'PoC',
      'pricing.poc_desc': 'Olculen KPI farki ile hizli deger kaniti.',
      'pricing.pilot': 'Pilot',
      'pricing.pilot_desc': 'Governance ve observability ile kontrollu gercek trafik.',
      'pricing.enterprise': 'Enterprise',
      'pricing.enterprise_desc': 'Guvenlik ve uyumluluk kontrolleriyle SLA destekli canli ortam.',

      'footer.note': 'WeAreTheArtMakers tarafindan gelistirildi'
    }
  };

  function clampLanguage(lang) {
    if (supported.indexOf(lang) >= 0) {
      return lang;
    }
    return DEFAULT_LANG;
  }

  function getLanguage() {
    try {
      var saved = global.localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return clampLanguage(saved);
      }
    } catch (err) {
      // ignore
    }
    return DEFAULT_LANG;
  }

  function setLanguage(lang) {
    var normalized = clampLanguage(lang);
    try {
      global.localStorage.setItem(STORAGE_KEY, normalized);
    } catch (err) {
      // ignore
    }
    return normalized;
  }

  function t(key, lang) {
    var active = clampLanguage(lang || getLanguage());
    var table = translations[active] || translations[DEFAULT_LANG];
    return table[key] || translations[DEFAULT_LANG][key] || key;
  }

  global.LanguageManager = {
    getLanguage: getLanguage,
    setLanguage: setLanguage,
    t: t,
    getSupportedLanguages: function () {
      return supported.slice();
    },
    translations: translations
  };
})(window);

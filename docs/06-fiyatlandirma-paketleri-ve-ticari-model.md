# 06 - Fiyatlandırma Paketleri ve Ticari Model

> Aşağıdaki model satış görüşmelerine başlangıç çerçevesi sunar. Nihai fiyatlar müşteri ölçeği ve SLA’ya göre netleşir.

## Paket 1: Starter (PoC)

- Hedef: 2-6 hafta teknik doğrulama
- Kapsam: tek tenant, temel dashboard, temel alerting
- Model: kurulum + aylık destek

## Paket 2: Growth (Pilot)

- Hedef: sınırlı canlı trafik
- Kapsam: çok tenant, gelişmiş alerting, replay runbook, e2e test gate
- Model: aylık lisans + kullanım bazlı (işlem hacmi)

## Paket 3: Enterprise

- Hedef: regülasyon odaklı yüksek hacimli kullanım
- Kapsam: SSO/RBAC, DR, gelişmiş güvenlik ve uyumluluk katmanı, özel SLA
- Model: yıllık sözleşme + opsiyonel managed service

## Gelir Modeli Seçenekleri

- Platform lisansı (SaaS/managed)
- On-prem kurulum + yıllık bakım
- İşlem hacmi bazlı katmanlı ücret
- Ek modül gelirleri (fraud, compliance, settlement orchestration)

## Satışta KPI Odaklı Fiyatlandırma

Müşteriye teknik özellik değil, etki sat:

- Mutabakat süresi düşüşü
- Incident çözüm süresi düşüşü
- Finans raporlama gecikmesi azalması
- Operasyonel hata maliyeti düşüşü

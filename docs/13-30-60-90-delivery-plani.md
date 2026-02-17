# 13 - 30-60-90 Gunluk Delivery Plani

## 0-30 Gun: Kesif ve Mimari Sabitleme

Hedef:

- mevcut sistemi anlamak
- baseline KPI toplamak
- risk haritasi cikarmak

Ciktilar:

- mimari karar kaydi (ADR)
- veri akis haritasi
- baslangic dashboard + alert seti
- pilot kapsam dokumani

## 31-60 Gun: Pilot Trafik ve Kontroller

Hedef:

- kontrollu canli trafik altinda platform davranisini olcmek

Ciktilar:

- pipeline e2e gecerlilik raporu
- runbook seti (incident/replay/dlq)
- quota/usage/governance aktif kullanimi
- KPI ara raporu

## 61-90 Gun: Production Cutover

Hedef:

- canliya gecis ve risk dusurme

Ciktilar:

- production deployment checklist
- rollback plani
- SSO/RBAC sertlestirme adimlari
- maliyet optimizasyonu + kapasite raporu

## Basari Kriterleri

- kritik akislarda SLO hedefleri tutuyor
- musteri KPI hedefleri olculur sekilde iyilesiyor
- audit ve incident akislari runbook ile standartlasiyor

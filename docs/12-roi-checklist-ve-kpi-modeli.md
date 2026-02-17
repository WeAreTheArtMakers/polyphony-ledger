# 12 - ROI Checklist ve KPI Modeli

## Amac

Her musteri gorusmesini teknik ozelliklerden cikartip finansal etki odagina tasimak.

## 1) Baseline KPI Toplama (Musteriden)

- Mevcut mutabakat dongusu: saat/gun
- Incident MTTR: dakika/saat
- Audit hazirlik suresi: FTE-saat
- Hata/geri donus oranlari
- Manuel operasyon adim sayisi

## 2) Hedef KPI Seti (Pilot Sonu)

- Mutabakat suresi: %50+ iyilesme hedefi
- MTTR: %40+ iyilesme hedefi
- Audit hazirlik: %60+ iyilesme hedefi
- Kritik hata adedi: azalma trendi

## 3) ROI Checklist (Toplanti Formu)

1. Mevcut mutabakat surecimiz olculuyor mu?
2. Incident root-cause bulma suremiz nedir?
3. Audit kaniti icin kac kisi/saat harcaniyor?
4. Yeni event alanlari eklendiginde kirilma yasaniyor mu?
5. Tek transaction'i API'den OLAP'a kadar izleyebiliyor muyuz?
6. Replay ile projection bozulmalarini guvenli toparlayabiliyor muyuz?
7. DLQ'daki kayip/failure olaylarini aksiyona ceviriyor muyuz?
8. Tenant bazli quota ve rol yonetimi gerekiyor mu?

## 4) KPI Sunum Sablonu (Oncesi / Sonrasi)

- Reconciliation: 4 saat -> 15 dk
- MTTR: 120 dk -> 25 dk
- Audit prep: 2 gun -> 30 dk

Not: Bu degerler demo benchmark'idir; musteri ortaminda baseline'a gore olculur.

## 5) Ticari Ceviri

KPI farki -> ticari kazanima cevrilir:

- daha az operasyon maliyeti
- daha az kesinti riski
- daha hizli denetim hazirligi
- daha iyi musteri guveni

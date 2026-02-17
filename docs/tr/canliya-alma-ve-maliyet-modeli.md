# Canliya Alma ve Maliyet Modeli

## Onerilen Kurulum Modlari

## 1) Demo / Portfoy Ortami

- tek VPS node
- Docker Compose ile tam stack
- reverse proxy + TLS + subdomain yonlendirme

## 2) Kontrollu Pilot

- uygulama ve veritabani sorumluluklarini ayrisma
- belirgin backup ve retention stratejisi
- daha guclu monitoring ve alert yonlendirme

## 3) Production

- cok node topoloji
- SLO/SLA odakli operasyon
- erisim ve secret yonetiminde sertlestirme

## Maliyet Planlama (Referans Bant)

Bu dokumanda altyapi ham maliyetleri yerine ticari teklif modeli kullanilir.

## Ticari Teklif Modeli (Public)

Toplam teklif 2 ana bolumden olusur:

1. Kurulum Bedeli (tek sefer)
2. Aylik Platform Bedeli (operasyon + sureklilik)

## Fiyatlandirma Parametreleri

Nihai teklif su parametrelere gore olusturulur:

- trafik hacmi (aylik tx ve pik TPS)
- retention suresi (log/metric/trace saklama penceresi)
- availability hedefi (hedef uptime ve failover seviyesi)
- entegrasyon kapsam seviyesi (SSO, RBAC, governance, raporlama)

## Referans Paket Yapisi

- Foundation: tek node canli demo + temel gozlemlenebilirlik
- Growth: ayrisik pilot mimari + gelismis alerting + governance aktif kullanim
- Enterprise: cok node topoloji + yuksek erisilebilirlik + guvenlik sertlestirme

Not: Ham altyapi maliyet detaylari public teklif dokumaninda yer almaz; teknik kesif sonrasinda proje kapsaminda ic teklif modeliyle hesaplanir.

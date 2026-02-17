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

- Demo: ~80 - 220 USD/ay
- Pilot: ~250 - 700 USD/ay
- Enterprise baslangic: ~800 - 2500+ USD/ay

Nihai maliyet; trafik hacmi, retention suresi ve availability hedeflerine gore degisir.

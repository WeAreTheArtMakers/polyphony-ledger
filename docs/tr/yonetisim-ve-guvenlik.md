# Yonetisim ve Guvenlik

## Mevcut Yonetisim Kabiliyetleri

- rol tabanli erisim guardlari (`viewer`, `operator`, `admin`, `owner`)
- ingest islemlerinde tenant quota kontrolu
- workspace bazli usage metering endpointleri
- Auth0/Keycloak uyumlu OIDC token dogrulama modu ve geriye donuk header modu

## Guvenlik ve Operasyon Temeli

- immutable finansal kayit yapisi
- structured log ve trace baglantili hata inceleme
- redacted payload ile DLQ izolasyonu
- health/readiness endpointleri

## Enterprise Sertlestirme Yolu

- OIDC/SAML entegrasyonu
- rol/tenant bazli daha ince yetki politikasi
- secret manager ve anahtar donusum politikasi
- disaster recovery ve backup dogrulama tatbikatlari

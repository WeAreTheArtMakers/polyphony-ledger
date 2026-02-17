# 15 - SSO/RBAC + Tenant Quota + Usage Metering Stratejisi

Bu dokuman, projede eklenen governance temelini ve enterprise'a gecis yolunu anlatir.

## 1) Mevcut Temel (Bu repoda)

- Header tabanli auth mode (`AUTH_MODE=header`) opsiyonu
- Role guard (`viewer`, `operator`, `admin`, `owner`)
- Admin endpoint korumalari (`replay`, `generator`, quota update)
- Workspace quota tablolari ve ingest sirasinda kota tuketimi
- Usage metering API (`/governance/usage`, `/governance/quota`, `/governance/me`)

## 2) SSO Ready Yaklasimi

Bugun:

- reverse proxy veya API gateway'den gelen kimlik basliklari (`x-auth-subject`, `x-workspace-role`, `x-workspace-id`)

Yarin:

- OIDC/SAML provider entegrasyonu
- header setini gateway tarafinda signed/jwt claim'den uretme

## 3) RBAC Kademesi

- viewer: read-only
- operator: ingest + operasyonel islemler
- admin: governance update + operasyon
- owner: tam yetki

## 4) Quota ve Metering

- Aylik tenant kotasi (`workspace_quotas`)
- Aylik kullanim sayaci (`workspace_usage`)
- ingest aninda kota kontrolu (429 ile geri donus)

## 5) Fiyatlandirmaya Etkisi

- paket bazli quota limiti
- asimda usage bazli fiyat
- tenant bazli SLA katmanlamasi

## 6) Bir Sonraki Adimlar

1. OIDC token dogrulamasi (JWKS)
2. rol mapleme politikasi
3. billing export endpoint
4. tenant bazli aylik rapor/limit bildirimleri

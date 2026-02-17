# 10 - Altyapıyı Satmak İçin Pratik Öneriler

## Satışta Kullanılacak Ana Hikaye

"Biz ödeme event’ini sadece taşıyan bir sistem değiliz; her işlemi finansal olarak ispatlanabilir, geriye dönük izlenebilir ve anlık analiz edilebilir hale getiren bir platformuz."

## Müşteri Görüşmesinde 5 Kritik Soru

1. Bugün işlem hatasını kaç saatte kök nedenine indiriyorsunuz?
2. Ledger doğruluğunu nasıl kanıtlıyorsunuz?
3. Analitik raporlarınız gerçek zamanlı mı, batch mi?
4. Şema değişikliği olduğunda üretimde kırılma yaşıyor musunuz?
5. Denetim/audit talebine kaç günde cevap veriyorsunuz?

## Cevabı Bizim Çözümle Eşleştirme

- Root cause hızı -> tracing + correlation_id
- Ledger kanıtı -> immutable double-entry
- Anlık rapor -> ClickHouse materialized view
- Evrim güvenliği -> Schema Registry + protobuf compatibility
- Audit yanıtı -> append-only event/ledger geçmişi

## Teklif Kurgusu

- Aşama 1: 2 haftalık teknik keşif + başarı kriteri seti
- Aşama 2: 4-6 haftalık pilot (gerçek trafik alt kümesi)
- Aşama 3: kademeli production rollout

## Satış Materyali Önerileri

- 1 sayfa yönetici özeti
- 10 slaytlık demo deck
- 30 dakikalık canlı demo scripti
- Teknik due diligence cevap seti
- Sık sorulan sorular (SSS) dokümanı

## Upsell Fikirleri

- Fraud/risk skor katmanı
- Settlement orchestration
- Regülasyon raporlama otomasyonu
- Multi-region DR paketi

## Kapanış Cümlesi Önerisi

"Bu platform, finansal doğruluk ve gerçek zamanlı karar hızını aynı anda sağlayarak yalnızca teknik bir altyapı değil, operasyonel bir rekabet avantajı sunar."

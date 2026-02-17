# 04 - Rekabet Analizi ve Konumlandırma

## Pazar Gerçeği

Çoğu ekip iki uç arasında bölünüyor:

- Sadece ödeme akışını çözen çözümler
- Sadece muhasebe/raporlama tarafını çözen çözümler

## Bizim Konumumuz

"Streaming-native ledger + real-time analytics" birlikte sunan platform.

## Karşılaştırma Çerçevesi

## 1) Genel Ödeme Altyapıları

- Güçlü tarafları: hızlı entegrasyon, geniş ekosistem
- Zayıf tarafları: kripto-spesifik double-entry ve replay senaryolarında sınırlı derinlik

## 2) Sadece Muhasebe/Ledger Odaklı Ürünler

- Güçlü tarafları: kayıt doğruluğu
- Zayıf tarafları: gerçek zamanlı OLAP ve event-stream entegrasyonu genelde ek iş ister

## 3) Custom In-house Çözümler

- Güçlü tarafları: tam özelleştirme
- Zayıf tarafları: bakım maliyeti, observability ve şema yönetiminde kırılganlık

## Polyphony Ledger Farkı

- Tek akıştan operasyon + analitik katmanı birlikte üretir.
- Tracing ve metrikleri satış demosunda gösterilebilecek olgunlukta sunar.
- Outbox/idempotency ile üretim koşullarına yakın dayanıklılık sağlar.
- PoC’den production’a geçişte mimariyi baştan yazma ihtiyacını azaltır.

## Satışta Kullanılacak Ana Mesaj

"Sadece ödeme geçirmek değil, geçen ödemenin finansal olarak ispatlanabilir ve anlık analiz edilebilir olmasını sağlıyoruz."

# 01 - Yönetici Özeti

## 1) Ürün Nedir?

`polyphony-ledger`, gerçek zamanlı kripto ödeme hareketlerini güvenilir biçimde işleyen ve iki farklı kullanım amacına aynı anda hizmet eden bir platformdur:

- Operasyonel doğruluk: immutable (değiştirilemez), çift kayıt (double-entry) ledger
- Analitik hız: ClickHouse üzerinde gerçek zamanlı OLAP katmanı

## 2) Hangi Problemi Çözer?

Kripto ödeme sistemlerinde kurumların temel sorunu şudur:

- Event akışı hızlıdır ama muhasebe doğruluğu kırılgandır.
- Doğruluk sağlanırsa analitik gecikir.
- Analitik hızlanırsa denetlenebilirlik zayıflar.

Bu platform, outbox + idempotency + immutable ledger yaklaşımıyla doğruluğu korurken, ClickHouse ile analitiği gerçek zamanlı hale getirir.

## 3) Neden Şimdi?

- Regülasyon baskısı: işlem izi ve audit trail zorunlulukları artıyor.
- Çok kaynaklı ödeme akışı: farklı wallet/provider/exchange kaynaklarını tek modelde toplama ihtiyacı büyüyor.
- CFO ve risk ekipleri artık "gün sonu" değil "anlık" görünürlük istiyor.

## 4) İş Değeri (Business Value)

- Mutabakat ve hata maliyetini düşürür.
- Finans/operasyon ekiplerinin karar hızını artırır.
- Incident çözüm süresini (MTTR) tracing + metriklerle kısaltır.
- Teknik borç yaratmadan event şema evrimini yönetir.

## 5) Kimler İçin?

- Kripto ödeme geçidi kuran fintech ekipleri
- B2B cüzdan altyapısı geliştiren şirketler
- Exchange/treasury/muhasebe entegrasyonu yapan ekipler
- Kurumsal müşterilerine audit-ready hareket geçmişi sunmak isteyen ürünler

## 6) Öne Çıkan Fark

Piyasadaki çoğu çözüm tek katmanda güçlüdür (ya ledger ya analytics). Bu çözümde:

- Aynı event akışından hem immutable ledger hem OLAP çıkar.
- Replay ile projection katmanı deterministik olarak yeniden üretilir.
- Uçtan uca trace (API -> Kafka -> DB -> OLAP) tek transaction seviyesinde izlenebilir.

## 7) Kısa Sonuç

`polyphony-ledger`, teknik olarak kurumsal-ready bir iskelet, ticari olarak da hızlı PoC -> pilot -> production geçişine uygun bir ürünleşme tabanıdır.

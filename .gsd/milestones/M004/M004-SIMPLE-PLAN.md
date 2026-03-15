# M004 Basit Plan (Adım Adım)

Bu planın amacı: model kalitesini güvenli şekilde artırmak ve artışı kanıtlamak.

## Adım 0 — Mevcut başarı ölçütünü test et (Tamamlandı)

- [x] Testleri çalıştır (`57 passed`)
- [x] Güncel baseline metriklerini kaydet
- [x] Readiness durumunu doğrula (`ready`)

Detay: `M004-BASELINE-STATUS.md`

---

## Adım 1 — HPO değerlendirmesini güçlendir (Tamamlandı)

- [x] Val tek split yerine daha sağlam bir değerlendirme düzeni kur
- [x] Parametre seçimini daha stabil hale getir
- [x] Güncel `hpo_report` ile adayları tekrar değerlendir

Çıktı: daha güvenilir HPO seçim kararı

---

## Adım 2 — Ensemble kararını sıkılaştır (Tamamlandı)

- [x] Baseline / HPO / blend karşılaştırmasını net kural ile seç
- [x] Gereksiz aday terfisini engelle (eşik altı iyileşmede baseline)

Çıktı: daha stabil `ensemble_report`

---

## Adım 3 — Performans doğrulaması (önce/sonra) (Tamamlandı)

- [x] Referans metriklere karşı yeni metrikleri kıyasla
- [x] Men/Women için iyileşme ya da kötüleşmeyi açık raporla

Çıktı: tek tabloda net karşılaştırma

---

## Adım 4 — Readiness ve submission tekrar kontrol (Tamamlandı)

- [x] Gate + submission ile son smoke koşusu
- [x] `submission_readiness_report` doğrulaması

Çıktı: final release adayının teknik uygunluk kanıtı

---

## Adım 5 — Son inceleme adımı (Tamamlandı)

- [x] Önce/sonra metrik özeti
- [x] HPO + ensemble karar özeti
- [x] Commit listesi
- [x] Burada durup senin onayını bekleme

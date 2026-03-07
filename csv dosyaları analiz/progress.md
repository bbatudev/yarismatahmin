# March Machine Learning Mania 2026 - Proje Takibi

## Kaggle Linkleri

- **Yarışma Genel Bakış**: https://www.kaggle.com/competitions/march-machine-learning-mania-2026/overview
- **Başlangıç Notebook**: https://www.kaggle.com/code/martynaplomecka/march-machine-learning-mania-2026-starter

---

## Proje Özeti

**Amaç**: NCAA basketbol turnuva maçlarının sonucunu olasılık (0-1) olarak tahmin etmek
**Değerlendirme Metriği**: Brier Score (düşük daha iyi)
**Veri Seti**: March Machine Learning Mania 2026

---

## Versiyon / Değişiklik Log'u

| Tarih | Saat | Oturum | Versiyon | Değişiklik |
|-------|------|--------|----------|------------|
| 26-02-2026 | 16:45 | 1 | v0.1 | Proje başlangıcı, brainstorm raporu, CSV analizi, oturum sistemi |
| 01-03-2026 | - | 2 | v0.2 | Tüm değişkenler tek tek analiz edildi (19 dosya, 40+ değişken grubu) |
| 01-03-2026 | - | 2 | v0.3 | Feature engineering script'i yazıldı (02_feature_engineering.py) |
| 02-03-2026 | - | 3 | v0.4 | Değişken korelasyon metodolojisi ve 3'lü AI denetim sistemi kuruldu |
| 07-03-2026 | - | 4 | v0.5 | Tüm korelasyon analizleri (8/8) ve değişken klasörleri (11/11) tamamlandı, KORELASYON_KULLANIM_RAPORU.md güncellendi, baseline model için hazır |
| 07-03-2026 | 14:50 | 5 | v0.6 | İleri seviye feature engineering: bağlamsal dinlenme, FTr context, konferans turnuvası momentumu, tur bağlamı, Bayesian smoothing, kod temizliği |
| 07-03-2026 | 18:20 | 6 | v0.7 | Korelasyon raporundan sadece uygulanan kararlar progress'e işlendi; konferans turnuvası + tur bağlamı aktif doğrulandı, zayıf değişken temizliği tamamlandı |

**Format:** GG-AA-YYYY | HH:MM | Oturum No | vX.X | Kısa açıklama

---

## Korelasyon Raporundan Islenenler (Sadece Uygulananlar)

Bu bolumde sadece kodda aktif olan ve veri uretiminde dogrulanan kararlar tutulur.

### Aktif ve Uygulanan Cekirdekler

| Alan | Durum | Not |
|------|-------|-----|
| Home court normalizasyonu | Uygulandi | TrueMargin hesaplamasinda 5.73 sabiti kullaniliyor |
| Four Factors guvenli calisma | Uygulandi | Eksik kolon varsa Four Factors kapanip compact akisa geciliyor |
| Baglamsal FTr | Uygulandi | `FTr_vs_OppAllowed_diff` aktif, Women tarafinda klasik `FTr_diff` devre disi |
| Rest/Fatigue baglami | Uygulandi | `DaysSinceLastGame`, `GamesLast7Days`, `GamesLast14Days`, `B2B_Last14Days` aktif |
| Konferans gucu | Uygulandi | `ConfStrength`, `ConfWinPct`, `ConfBidCount`, `ConfTeamCount` aktif |
| Konferans turnuvasi context | Uygulandi | `ConfTourneyGamesPlayed`, `ConfTourneyWinPct`, `ConfTourneyChampion`, `DaysSinceConfFinal` aktif |
| Tur baglami (round context) | Uygulandi | `Round_Num`, `Is_FirstWeekend`, `Is_SecondWeekend`, `Is_FinalWeekend` aktif |
| Close game smoothing | Uygulandi | `CloseWinPct` Bayesian smoothing ile hesaplaniyor, `CloseGamesCount_diff` aktif |

### Bilerek Cikarilan/Zayif Bulunanlar

| Degisken | Karar | Gerekce |
|----------|-------|---------|
| `EloScore` | Cikarildi | Bu pipeline icinde tutarli ek veri kaynagi yoktu |
| `Upset_Zone` | Cikarildi | Simetrik veri yapisinda lineer sinyal vermedi |
| `Rank_Agreement` | Cikarildi | Ek bilgi katmadi, gürültü urettigi goruldu |
| `CoachChangedThisSeason` | Cikarildi | Nadir ve zayif sinyal |

### Son Uretim Durumu (Dogrulandi)

| Cikti | Durum |
|------|-------|
| `processed_features_men.csv` | Guncel ve uretildi (62 sutun) |
| `processed_features_women.csv` | Guncel ve uretildi (57 sutun) |
| Eksik deger kontrolu | Geciyor (kritik merge boslugu yok) |
| Target dengesi | 0.5 / 0.5 korunuyor |

---

## CSV Dosyaları Analizi

### Erkekler Turnuva Verileri (M öneki)

| Dosya | Amacı | Önemli Sütunlar |
|-------|-------|-----------------|
| **MTeams.csv** | Takım bilgileri | TeamID, TeamName, FirstD1Season, LastD1Season |
| **MSeasons.csv** | Sezon metadatası | Season, DayZero, RegionW/X/Y/Z |
| **MRegularSeasonDetailedResults.csv** | Normal sezon maç sonuçları | W/L TeamID, Score, WLoc, detaylı istatistikler |
| **MNCAATourneyDetailedResults.csv** | Turnuva maç sonuçları | Normal sezon ile aynı yapı |
| **MNCAATourneySeeds.csv** | Turnuva sıralamaları | Season, Seed (W01-X16), TeamID |
| **MMasseyOrdinals.csv** | Sıralama sistemleri | Season, RankingDayNum, SystemName, TeamID, OrdinalRank |
| **MTeamConferences.csv** | Takım-konferans eşleştirme | Season, TeamID, ConfAbbrev |
| **Conferences.csv** | Konferans isimleri | ConfAbbrev, Description |
| **MNCAATourneySlots.csv** | Turnuva braket slotları | Slot, StrongSeed, WeakSeed |
| **MRegularSeasonCompactResults.csv** | Basit normal sezon sonuçları | Season, DayNum, W/L TeamID, Score, WLoc, NumOT |
| **MNCAATourneyCompactResults.csv** | Basit turnuva sonuçları | Compact normal sezon ile aynı |

### Ek Erkek Verileri

| Dosya | Amacı |
|-------|-------|
| **MGameCities.csv** | Maç yapılan şehirler |
| **Cities.csv** | Şehir bilgileri |
| **MTeamCoaches.csv** | Takımların koç geçmişi |
| **MTeamSpellings.csv** | Alternatif takım isimleri |
| **MSecondaryTourneyTeams.csv** | İkincil turnuva takımları |
| **MSecondaryTourneyCompactResults.csv** | İkincil turnuva sonuçları |
| **MConferenceTourneyGames.csv** | Konferans turnuva maçları |
| **MNCAATourneySeedRoundSlots.csv** | Seed-tur slot eşleştirmeleri |

### Kadınlar Turnuva Verileri (W öneki)

Erkek verileri ile aynı yapıda:
- WTeams.csv, WSeasons.csv, WRegularSeasonDetailedResults.csv
- WNCAATourneyDetailedResults.csv, WNCAATourneySeeds.csv
- WTeamConferences.csv, WRegularSeasonCompactResults.csv
- WNCAATourneyCompactResults.csv, WNCAATourneySlots.csv
- WSecondaryTourneyTeams.csv, WSecondaryTourneyCompactResults.csv
- WConferenceTourneyGames.csv, WGameCities.csv

### Submission Dosyaları

| Dosya | Amacı | Format |
|-------|-------|--------|
| **SampleSubmissionStage1.csv** | Stage 1 submission formatı | ID (Season_TeamA_TeamB), Pred (0-1) |
| **SampleSubmissionStage2.csv** | Stage 2 submission formatı | Aynı format |

---

## Terminoloji Sözlüğü

| Terim | Açıklama |
|-------|----------|
| **Brier Score** | Olasılık tahminlerinin kalitesini ölçen metrik. 0=mükemmel, 1=en kötü. Formül: 1/N * Σ(forecast - outcome)² |
| **Massey Ordinals** | Kenneth Massey tarafından geliştirilen, 196 farklı sıralama sisteminin birleşimi. **Düşük rank = daha iyi takım** (TERS!) |
| **Seed** | Turnuvadaki takımların sıralaması (1-16 arası). W01 = West bölgesi 1. sıra |
| **WLoc** | Maç yeri: H=Home (ev), A=Away (deplasman), N=Neutral (nötr) |
| **DayNum** | Sezon içindeki gün numarası (0=Season başı, 132=Turnuva başı) |
| **Regular Season** | Normal sezon - turnuva öncesi maçlar |
| **NCAA Tournament** | March Madness - eleme turnuvası |
| **Conference** | Üniversite ligleri (ACC, Big Ten, SEC vb.) |
| **OrdinalRank** | Takımın sıralaması (düşük = iyi) |
| **Probability Calibration** | Model olasılıklarını gerçek olasılıklara yakın hale getirme |
| **Data Leakage** | Gelecek bilginin geçmişe sızması - overfitting sebebi |
| **Time-Series Split** | Zaman sırasına göre train-test ayrımı (geleceği geçmişle test etme) |

---

## Model Performans Tablosu

| Model | Brier Score | CV Skor | Test Skor | Notlar | Tarih |
|-------|-------------|---------|-----------|--------|-------|
| Baseline | - | - | - | Logistic Regression | |
| | | | | | |
| | | | | | |

---

## Proje Anayasası ve Altın Kurallar

Bu kurallar analiz ve modelleme sürecinde **KESİNLİKLE** uyulması gereken temel prensiplerdir:

1. **Test Verisi Sadakati:** Modelin nihai hedefi turnuva maçlarını tahmin etmektir. Bu yüzden, değişkenlerin modeldeki gücünü (korelasyonunu) ölçerken **ASLA** 196.000 maçlık Regular Season verisi kullanılmaz. Upsetlerin ve denk güçlerin olduğu **2.585 maçlık Turnuva verisi (1985-2025)** kullanılır.
2. **Kusursuz Matematik (Yaklaşıklık Yasağı):** Hiçbir oran, korelasyon veya sayı tahmin usulü, yuvarlama veya göz kararı ile yazılamaz. "Yaklaşık %20" gibi ifadeler yasaktır. Her şey Python üzerinden sıfırdan hesaplanıp, virgülüne kadar doğrulanmak zorundadır.
3. **Üçlü AI Denetimi:** Her bir değişken analiz dosyası, yazıldıktan sonra **3 farklı AI (Veri Bilimcisi, Veritabanı Uzmanı, Basketbol Analisti)** tarafından ayrı ayrı Python betikleriyle test edilip matematiksel olarak teyit edilir. Sadece üçünün de onayladığı veriler "DOĞRULANMIŞ" kabul edilir.
4. **Zorunlu Özetleme:** Her değişkenin kendi `.txt` analizi bittikten sonra, ondan elde edilen kritik yüzdeler ve model çıkarma kararları (Feature kararları) derhal `08_yuzdesel_analizler.txt` adlı özet dosyasına kopyalanır. Bu dosya modelin beyni olacaktır.
5. **Data Leakage (Sızıntı) Önlemi:** Geçmişi gelecekle test etmek yasaktır. Train/Test split yapılırken kesinlikle zaman ekseni (Time-Series Split) korunacaktır.

---

## Yapılacaklar ve Yapılmayanlar

### ✅ Yapılanlar

| Görev | Durum | Notlar |
|-------|--------|--------|
| **Brainstorm raporu** | ✅ Tamamlandı | Feature fikirleri, model yaklaşımları, CV stratejisi belirlendi |
| **CSV dosyaları analizi** | ✅ Tamamlandı | Tüm veri dosyaları incelendi ve belgelendi |
| **Proje yapısı oluşturma** | ✅ Tamamlandı | Klasörler, progress, oturum sistemleri oluşturuldu |
| **MCP sunucuları kurulumu** | ✅ Tamamlandı | GitHub MCP eklendi (restart gerekli) |
| **Environment kurulumu** | ✅ Tamamlandı | Virtual environment mevcut |
| **Oturum rapor sistemi** | ✅ Tamamlandı | session_start.md, session_end.md, günlük klasörler |
| **Değişkenlerin tek tek analizi** | ✅ Tamamlandı | 11 klasör, 40+ değişken grubu detaylı analiz edildi |
| **Feature engineering script'i** | ✅ Tamamlandı | 02_feature_engineering.py ile SeedDiff, MasseyRankDiff, WinPctDiff, PointDiffDiff feature'ları üretildi |
| **Korelasyon analizleri (8/8)** | ✅ Tamamlandı | Tüm korelasyon dosyaları incelendi, kararlar alındı |
| **KORELASYON_KULLANIM_RAPORU.md** | ✅ Tamamlandı | Tüm kararlar ve test planları belgelendi |
| **İleri seviye feature engineering (v0.6)** | ✅ Tamamlandı | Aşağıda detaylar |

**v0.6 – İleri Seviye Feature Engineering Detayları:**

| Yeni Feature / Değişiklik | Açıklama |
|---------------------------|----------|
| `FTr_vs_OppAllowed_diff` | Bağlamsal serbest atış oranı: Kendi FTr – Rakibin izin verdiği FTr |
| `DaysSinceLastGame` | Kontekst bazlı dinlenme süresi (eski RestDays'in yerini aldı) |
| `GamesLast7Days / GamesLast14Days` | Son 7/14 gündeki maç yükü (yorgunluk birikimi) |
| `B2B_Last14Days` | Son 14 gündeki arka arkaya (B2B) maç sayısı |
| `ConfTourneyGamesPlayed` | Konferans turnuvasında kaç maç oynandı (Champ Week yorgunluğu) |
| `ConfTourneyWinPct` | Konf. turnuvası kazanma oranı (son form göstergesi) |
| `ConfTourneyChampion` | Konferans şampiyonu bayrak (Auto-Bid alan takımlar) |
| `DaysSinceConfFinal` | Konf. finalinden NCAA Turnuvasına kaç gün (dinlenme süresi) |
| `Round_Num` | Turnuva tur numarası (1-6 arası, bracket bağlamı) |
| `Is_FirstWeekend / Is_SecondWeekend / Is_FinalWeekend` | Tur bayrakları – hangi hafta sonu |
| `CloseWinPct` → Bayesian Smoothing | Az örnekli takımlar için Beta prior (α=2, β=2) eklendi |
| `CloseGamesCount_diff` | Yakın maç sayısı farkı (sinyal güvenilirliği) |
| **Kaldırılan:** `CoachChangedThisSeason` | Zayıf sinyal, gürültü kaynağıydı |
| **Kaldırılan:** `Upset_Zone` | Simetrik veri setinde Pearson=0, modele katkı yok |
| **Kaldırılan:** `Rank_Agreement` | Seed ve Massey zaten ayrı sinyal veriyor, fazlalıktı |
| **Women özel:** `FTr_diff` kaldırıldı | Kadınlarda zayıf sinyal; bağlamsal `FTr_vs_OppAllowed_diff` korundu |

**Değişken Analizi Detayları:**
- `değişkenlerin tek tek analizi/` klasöründe 19 analiz dosyası
- Core: Season, DayNum, TeamID (3 dosya)
- Game Results: Results, WLoc/NumOT (2 dosya)
- Tournament: Seed, Massey Ordinals (2 dosya)
- Conference: Konferans (1 dosya)
- Stats: Shooting, Rebounding, Ball Control, Defensive, Fouls (5 dosya)
- Metadata: Team Info, Tournament Structure, Locations, Coaches, Other Tournaments, Submission Format (6 dosya)

### ⏳ Yapılacaklar

| Görev | Öncelik | Notlar |
|-------|---------|--------|
| **Korelasyon dosyaları analizi (4. dosyadan devam)** | 🔴 Yüksek | 04_wloc_analizi.txt'den başlayacak (5,6,7,8 kaldı) |
| **Baseline model oluştur** | 🔴 Yüksek | LightGBM ile başlangıç modeli (03_lgbm_train.py) |
| **Model eğitimi ve değerlendirme** | 🔴 Yüksek | Brier Score ile performans ölçümü |
| **StdOrdinalRank testi** | 🟡 Orta | Baseline sonrası ekle, Brier Score > 0.001 improvement kontrol et |
| **Hyperparameter tuning** | 🟡 Orta | Optuna ile optimizasyon |
| **Probability calibration** | 🟡 Orta | Brier Score için olasılık kalibrasyonu |
| **Final submission** | 🟢 Düşük | Kaggle'a dosya yükle |

### ❌ Yapılmayanlar

| Görev | Sebep |
|-------|-------|
| Model Eğitimi | Analiz fazı tamamlandı, eğitim aşamasına geçiliyor. |

---

## Tespit Edilen Problemler ve Riskler

### 🟡 Orta Öncelikli Problemler

| Problem | Çözüm Önerisi | Durum |
|---------|---------------|-------|
| **2020 sezonu yok** (COVID-19) | Veride boşluk var, continuity sorun olabilir | Açık |
| **Erkek ve Kadın verileri ayrı** | Ayrı model mi yoksa ortak mı kullanılacak karar verilmeli | Açık |
| **Çok fazla sıralama sistemi** (Massey) | Hangi sistemler daha güvenilir, aggregate etme gerekli | Açık |
| **Submission ID formatı** | `Season_TeamA_TeamB` formatında, hangi takımın evde olduğu belli değil | Açık |

### 🔴 Yüksek Öncelikli Problemler

| Problem | Çözüm Önerisi | Durum |
|---------|---------------|-------|
| **Brier Score için kalibrasyon gerekliliği** | Model olasılıkları 0-1 arası iyi dağıtılmalı, aşırı güvenli tahminlerden kaçınılmalı | Açık |
| **Data leakage riski** | Gelecek bilgileri (gelecek sezon maçları) geçmişe sızdırma riski var | Açık |
| **Cross-validation stratejisi** | Aynı sezonun train ve test setinde olmaması gerekli | Açık |
| **Turnuva verisi azlığı** | Sadece turnuva maçları ile model eğitmek yetersiz olabilir | Açık |

### 🟢 Düşük Öncelikli Riskler

| Risk | Not |
|------|-----|
| **Home court advantage** | Turnuva maçları neutral court'ta, WLoc=N olabilir |
| **Yeni takımlar** | İlk kez turnuvaya katılan takımlar için geçmiş veri yok |
| **Koç değişiklikleri** | MTeamCoaches.csv var ama etkisi ölçmek zor |

---

## Özellik Mühendisliği – Doğrulanmış Korelasyonlar (v0.6)

### 🔴 1. Sınıf Sinyaller (|corr| ≥ 0.40)

| Feature | Men Corr | Women Corr | Kaynak |
|---------|----------|------------|--------|
| `SeedNum_diff` | -0.482 | -0.624 | Seed parse + diff |
| `NetRtg_diff` | 0.401 | 0.473 | Four Factors / efficiency |
| `TrueMarginAvg_diff` | 0.375 | 0.472 | Nötrleştirilmiş sayı farkı |
| `AvgScore_diff` | 0.232 | 0.437 | Ort. atılan sayı |
| `Heavy_Favorite` | 0.341 | 0.411 | SeedNum_diff ≤ -8 bayrak |
| `ConfBidCount_diff` | — | 0.425 | Konferans NCAA bid sayısı |
| `ConfStrength_diff` | — | 0.405 | Konferans gücü |

### 🟡 2. Sınıf Sinyaller (0.25 ≤ |corr| < 0.40)

| Feature | Men Corr | Women Corr |
|---------|----------|------------|
| `WinPct_diff` | 0.326 | 0.369 |
| `eFG_diff` | 0.170 | 0.355 |
| `Margin_last21_diff` | 0.245 | 0.350 |
| `BlkPct_diff` | 0.203 | 0.330 |
| `ORBpct_diff` | 0.209 | 0.323 |
| `MasseyPct_diff` | 0.449 | — (yok) |

### Four Factors (Dean Oliver)
- **eFG%Diff** (Shooting) – En güçlü Four Factor 🔴
- **TOVpct_diff** (Turnovers) – Ters korelasyonlu 🔴
- **ORBpct_diff** (Rebounding) – Orta seviye sinyal 🟡
- **FTr_vs_OppAllowed_diff** (Bağlamsal FTr) – Women için özellikle güçlendirilmiş 🟢

### Bağlamsal Feature'lar (v0.6 – YENİ)

| Kategori | Özellikler |
|----------|------------|
| **Konf. Turnuvası** | ConfTourneyGamesPlayed, ConfTourneyWinPct, ConfTourneyChampion, DaysSinceConfFinal |
| **Tur Bağlamı** | Round_Num, Is_FirstWeekend, Is_SecondWeekend, Is_FinalWeekend |
| **Dinlenme** | DaysSinceLastGame, GamesLast7Days, GamesLast14Days, B2B_Last14Days |

### Data Leakage Önlemleri

**KRİTİK KURAL:** `Season < Target_Season VE DayNum < Target_DayNum`

- Sadece maç öncesindeki bilgileri kullan
- Sezon kronolojik sırasını koru
- Aynı fold içinde gelecekteki maçlardan feature üretme
- ❌ Yanlış: Gelecek sezon veya gün sonuçlarını kullanma
- ❌ Yanlış: Turnuva maçlarını regular season'da kullanma
- ✅ Doğru: Geçmiş sezonlar + mevcut sezon (maçtan öncesi)

### Train/Test Split Stratejisi

```
Train: 2016, 2017, 2018, 2019, 2021, 2022
Val:   2023
Test:  2024, 2025
```

**❌ ASLA rastgele split yapma!**
**❌ Aynı sezonu train ve test'e koşma!**

---

## Kullanışlı Komutlar

### Python / Jupyter
```bash
# Virtual environment aktif et
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Jupyter notebook başlat
jupyter notebook

# Kütüphane kur
pip install pandas numpy scikit-learn xgboost lightgbm
```

### Git / GitHub
```bash
# Durum kontrol
git status

# Son 10 COMMIT'I GOR (ONEMLI!)
git log --oneline -10

# Commit detaylari (her bir commit icin)
git show --stat <commit-hash>

# MEVCUT SON 10 COMMIT (Guncel):
# 7672dd8 - feat: korelasyon analizleri, veri toplama ve dogrulama scriptleri
# 36c6ada - chore: Kiro ve Claude icin oturum baslangic hook'lari guncellendi
# 084d3e5 - Update analiz.txt
# ff35228 - degisken analizi, analiz txt devam
# c713101 - chore: setup empty data and competition directories
# 280bdd9 - Giris
# 93dce3a - feat: 26-02-2026 16:45 oturum yonetim sistemi ve saat takibi
# 329b340 - Initial commit

# Degisiklikleri ekle
git add .

# Commit (standart format)
git commit -m "feat: 26-02-2026 ozet

- detay 1
- detay 2"

# Push
git push origin main
```

### Veri İşleme
```python
# Tüm CSV'leri oku
import pandas as pd
import glob

csv_files = glob.glob("march-machine-leraning-mania-2026/*.csv")
for file in csv_files:
    print(file)
```

---

## Standart Commit Mesaj Formatı

```
<tür>: <kısa-özet>

- <değişiklik 1> (eklendi/güncellendi/silindi)
- <değişiklik 2>
- <değişiklik 3>

Çözülen sorunlar: X, Y, Z
```

**Türler:**
- `feat`: Yeni özellik
- `fix`: Bug düzeltmesi
- `docs`: Dokümantasyon
- `refactor`: Kod yeniden düzenleme
- `test`: Test ekleme
- `chore`: Diğer değişiklikler

**Örnek:**
```
feat: 26-02-2026 veri yükleme sistemi

- CSV okuma fonksiyonları eklendi
- Progress.md güncellendi
- Günlük rapor sistemi kuruldu

Çözülen sorunlar: Veri yapısı belirsizliği
```

---

## Proje Klasör Yapısı

```
yarismatahmin/
├── csv dosyaları analiz/
│   └── progress.md               # Ana progress takibi
├── korelasyonlar/                 # Ham korelasyon analiz dosyaları
├── mania_pipeline/
│   ├── scripts/
│   │   ├── 02_feature_engineering.py   # Ana feature pipeline
│   │   ├── 03_lgbm_train.py            # Model eğitim scripti (taslak)
│   │   └── analyze_weak_features.py    # Zayıf feature analiz aracı
│   ├── artifacts/data/
│   │   ├── processed_features_men.csv   # Erkek feature matrisi
│   │   └── processed_features_women.csv # Kadın feature matrisi
│   └── KORELASYON_KULLANIM_RAPORU.md
├── march-machine-leraning-mania-2026/  # Ham CSV veri seti
├── venv/                         # Virtual environment
└── .gitignore
```

---

## Sonraki Adımlar

1. **✅ DEĞİŞKEN ANALİZİ (TAMAMLANDI)** - Tüm 40+ değişken grubu ve 8 korelasyon dosyası analiz edildi.
2. **✅ KUSURSUZ DOĞRULAMA (TAMAMLANDI)** - Tüm korelasyon ve değişken analizleri Turnuva verisi üzerinden doğrulandı.
3. **✅ İLERİ SEVİYE FEATURE ENGINEERING (v0.6)** - Bağlamsal dinlenme, FTr context, konf. turnuvası, tur bağlamı, Bayesian smoothing.
4. **⏳ BASELINE MODEL KURULUMU** - LightGBM ile ilk model eğitimi (03_lgbm_train.py).
5. **Model Optimizasyonu** - Hyperparameter tuning ve probability calibration.
6. **Kaggle Submission** - Stage 1 için submission dosyası üretme.

---

*Son Güncelleme: 07-03-2026*

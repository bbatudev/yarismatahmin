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
| | | | | |

**Format:** GG-AA-YYYY | HH:MM | Oturum No | vX.X | Kısa açıklama

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
| **Değişkenlerin tek tek analizi** | ✅ Tamamlandı | 19 dosya, 40+ değişken grubu detaylı analiz edildi |
| **Feature engineering script'i** | ✅ Tamamlandı | 02_feature_engineering.py ile SeedDiff, MasseyRankDiff, WinPctDiff, PointDiffDiff feature'ları üretildi |

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
| **Korelasyon analizi (Tüm Değişkenler Tablosu)** | 🔴 Yüksek | `tüm degiskenler tablo` adlı dosyada listelenen 60-70 adet değişkenin, yeni 3'lü AI doğrulama ve turnuva verisi kurallarına göre tek tek hesaplanması. |
| **Kalan Değişkenlerin Onayı** | 🔴 Yüksek | 04, 05, 06 ve 07 numaralı dosyalar şu an sadece prototip olarak kuruldu. 1, 2 ve 3 numaralı dosyalarda yapılan "Kesin Matematiksel Doğrulama" işlemi henüz bunlara uygulanmadı. Sırayla teyit edilecekler. |
| **Yüzdesel Analizlerin Güncellenmesi** | 🔴 Yüksek | Her biten değişken dosyasının özetinin `08_yuzdesel_analizler.txt` dosyasına eklenmesi işlemine devam edilecek. |
| **Baseline model oluştur** | 🟡 Orta | Logistic Regression ile başlangıç modeli |
| **Model eğitimi ve değerlendirme** | 🟡 Orta | Brier Score ile performans ölçümü |
| **Model geliştirme (XGBoost/LightGBM)** | 🟡 Orta | Gelişmiş modelleri dene |
| **Hyperparameter tuning** | 🟡 Orta | GridSearch / Optuna ile optimizasyon |
| **Cross-validation stratejisi** | 🟡 Orta | Time-series split ile sezon bazlı CV |
| **Probability calibration** | 🟡 Orta | Brier Score için olasılık kalibrasyonu |
| **Final submission** | 🟢 Düşük | Kaggle'a dosya yükle |

### ❌ Yapılmayanlar

| Görev | Sebep |
|-------|-------|
| 04, 05, 06 ve 07 Dosyaları Teyidi | Henüz prototip halindeler, sıradaki adım olarak 3'lü AI denetiminden geçecekler. |
| Tüm Değişkenlerin Analizi | Şu an sadece ilk 3 dosya bitti. Tablodaki 60-70 değişken için bu süreç devam edecek. |
| Model Eğitimi | Değişken testleri ve Feature Engineering süreci kusursuzlaşmadan model kurmak hatalı olur. |

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

## Özellik Mühendisliği Planı

### 🔴 En Önemli Feature'lar (Analiz Sonucu)

| Feature | Kaynak | Formül | Korelasyon |
|---------|--------|--------|------------|
| **SeedDiff** | Seed | Seed_A - Seed_B | +0.85 |
| **MasseyRankDiff** | Massey | Rank_B - Rank_A (TERS!) | +0.78 |
| **WinPctDiff** | Results | Win%_A - Win%_B | +0.70 |
| **PointDiffDiff** | Results | AvgPtDiff_A - AvgPtDiff_B | +0.72 |

**Four Factors (Dean Oliver):**
- **eFG%Diff** (Shooting) - %40 ağırlık 🔴
- **TO%Diff** (Turnovers) - %25 ağırlık 🔴
- **ORB%Diff** (Rebounding) - %20 ağırlık 🟡
- **FTRateDiff** (Fouling) - %15 ağırlık 🟢

### Temel Özellikler

| Kategori | Özellikler |
|----------|------------|
| **Takım Gücü** | Massey Ordinals ortalaması, sıralama farkı, trend |
| **Regular Season** | Win-Loss record, point differential, Son 10 maç |
| **İstatistikler** | Offensive/Defensive efficiency, 3P%, FT%, rebound rate |
| **Turnuva** | Seed numarası, geçmiş turnuva performansı |
| **Konferans** | Konferans gücü, konferans içi performans |
| **Diğer** | Rest days, travel distance (veri varsa) |

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
├── session_start.md              # Oturum başı şablonu
├── session_end.md                # Oturum sonu şablonu
├── brainstorm_report.md          # Beyin fırtınası raporu
├── kaggle_akis_plani.md          # Kaggle yarışması akış planı
├── .env                          # Environment variables
├── .mcp.json                     # MCP sunucu ayarları
├── .claude/
│   └── settings.local.json       # Claude ayarları
├── csv dosyaları analiz/
│   └── progress.md               # Ana progress takibi
├── değişkenlerin tek tek analizi/  # Değişken analizleri (YENİ!)
│   ├── season/                   # Season analizi
│   ├── daynum/                   # DayNum analizi
│   ├── teamid/                   # TeamID analizi
│   ├── results/                  # Results, WLoc, NumOT
│   ├── seed/                     # Seed analizi
│   ├── massey/                   # Massey Ordinals analizi
│   ├── konferans/                # Konferans analizi
│   ├── stats/                    # Shooting, Rebounding, etc.
│   ├── metadata/                 # Team info, locations, coaches
│   └── FINAL_OZET.md             # Tüm değişkenler özeti
├── 26-02-2026/                   # Günlük klasör (GG-AA-YYYY)
│   └── gunluk_rapor.md           # Günlük rapor
├── src/                          # Kaynak kodlar
├── notebooks/                    # Jupyter notebook'lar
├── venv/                         # Virtual environment
└── march-machine-leraning-mania-2026/  # Veri seti
```

---

## Sonraki Adımlar

1. **✅ DEĞİŞKEN ANALİZİ PROTOTİPLERİ** - Tüm 40+ değişken grubu yüzeysel olarak analiz edildi.
2. **✅ KUSURSUZ DOĞRULAMA (Faz 1)** - İlk 3 Değişken dosyası (RestDays, RestDaysDiff, WScore/LScore) 3'lü AI sistemi ile Turnuva verisi üzerinden kusursuzlaştırıldı ve özet dosyasına aktarıldı.
3. **Kalan Dosyaların Teyidi** - Prototip halindeki 04, 05, 06 ve 07 numaralı dosyaların testten geçirilmesi.
4. **Yeni Feature Taraması** - `tüm degiskenler tablo` dosyasındaki 60-70 değişkenin sırayla bu sisteme sokulması.
5. **Model ve Optimizasyon** - Tüm özellikler (feature) elendikten ve onaylandıktan sonra XGBoost vb. ile Brier skor hedefine yöneliş.

---

*Son Güncelleme: 02-03-2026*

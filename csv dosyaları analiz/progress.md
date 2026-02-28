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
| | | | | |
| | | | | |
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
| **Massey Ordinals** | Kenneth Massey tarafından geliştirilen, 100+ farklı sıralama sisteminin birleşimi. Düşük rank = daha iyi takım |
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

### ⏳ Yapılacaklar

| Görev | Öncelik | Notlar |
|-------|---------|--------|
| **Veri yükleme ve keşif** | 🔴 Yüksek | Python ile verileri yükleyip istatistiksel inceleme |
| **Baseline model oluştur** | 🔴 Yüksek | Logistic Regression ile başlangıç modeli |
| **Feature engineering** | 🔴 Yüksek | Massey Ordinals, win-loss, SOS vb. özellikler |
| **EDA (Exploratory Data Analysis)** | 🟡 Orta | Veri dağılımları, korelasyonlar, outlier analizi |
| **Model geliştirme (XGBoost/LightGBM)** | 🟡 Orta | Gelişmiş modelleri dene |
| **Hyperparameter tuning** | 🟡 Orta | GridSearch / Optuna ile optimizasyon |
| **Cross-validation stratejisi** | 🟡 Orta | Time-series split ile sezon bazlı CV |
| **Probability calibration** | 🟡 Orta | Brier Score için olasılık kalibrasyonu |
| **Ensemble modeller** | 🟢 Düşük | Birden fazla modeli birleştir |
| **Error analysis** | 🟢 Düşük | Hatalı tahminleri analiz et |
| **Final submission** | 🟢 Düşük | Kaggle'a dosya yükle |

### ❌ Yapılmayanlar

| Görev | Sebep |
|-------|-------|
| Python kodları yazılması | Henüz başlanmadı |
| Model eğitimi | Veri işleme aşamasında |
| Kaggle submission | Model hazır değil |

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

- Sadece maç öncesindeki bilgileri kullan
- Sezon kronolojik sırasını koru
- Aynı fold içinde gelecekteki maçlardan feature üretme

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

# Değişiklikleri ekle
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
├── .env                          # Environment variables
├── .mcp.json                     # MCP sunucu ayarları
├── .claude/
│   └── settings.local.json       # Claude ayarları
├── csv dosyaları analiz/
│   └── progress.md               # Ana progress takibi
├── 26-02-2026/                   # Günlük klasör (GG-AA-YYYY)
│   └── gunluk_rapor.md           # Günlük rapor
├── src/                          # Kaynak kodlar
├── notebooks/                    # Jupyter notebook'lar
├── venv/                         # Virtual environment
└── march-machine-leraning-mania-2026/  # Veri seti
```

---

## Sonraki Adımlar

1. **Veri yükleme script'i yaz** - Tüm CSV'leri bir araya getir
2. **Keşifsel veri analizi (EDA)** - Python ile verileri incele
3. **Baseline model oluştur** - Logistic Regression ile başla
4. **Feature engineering** - Brainstorm raporundaki fikirleri uygula
5. **Model geliştirme** - XGBoost/LightGBM dene

---

*Son Güncelleme: 26-02-2026*

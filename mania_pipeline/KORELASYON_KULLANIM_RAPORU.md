# 📊 KORELASYON ANALİZLERİ KULLANIM RAPORU

**Tarih:** 06-03-2026  
**Analiz Edilen Kod:** `mania_pipeline/scripts/02_feature_engineering.py`

---

## ✅ KULLANILAN KORELASYON ANALİZLERİ

### 1. **04_wloc_analizi.txt** → HOME_COURT_ADVANTAGE

**📍 Code Konumu:** Satır 25-26
```python
# Ev Sahibi Normalizasyon Sabiti (04_wloc_analizi.txt'den)
HOME_COURT_ADVANTAGE = 5.73
```

**🎯 Ne İçin Kullanıldı:**
- **Analiz Bulgusu:** Regular Season'da ev sahibi ortalama +5.73 sayı avantaja sahip
- **Uygulama:** TrueMargin (gerçek güç farkı) hesaplarken bu avantaj çıkarılıyor
- **Kullanım Yerleri:**
  - Satır 85-87: Kazanan takımın margin'ini düzelt
  - Satır 96-98: Kaybeden takımın margin'ini düzelt

### 2. **01_season_daynum_restdays.txt** → FATIGUE FLAGS

**📍 Code Konumu:** Satır 203-217
```python
def build_rest_days(gl):
    """
    01_season_daynum_restdays.txt kural setinden çekilmiştir.
    """
    # ...
    gl["Is_Rusty"] = (gl["RestDays"] >= 7).astype(int) 
    gl["Is_Back_To_Back"] = (gl["RestDays"] <= 2).astype(int)
```

**🎯 Ne İçin Kullanıldı:**
- **Analiz Bulgusu:** Ortalama dinlenme 3.96 gün
- **Uygulama:** 
  - **Is_Rusty (≥7 gün):** Paslanma/ritim kaybı riski
  - **Is_Back_To_Back (≤2 gün):** Yorgunluk riski




## ❌ KULLANILMAYAN KORELASYON ANALİZLERİ

Bu dosyalar **araştırma aşamasında** yazılmış ama henüz **koda eklenmemiş**:

### 1. **02_restdaysdiff_target.txt**
**İçerik:** RestDays farkı ile kazanma olasılığı arasındaki korelasyon  
**Durum:** ⚠️ DOLAYLI KULLANILDI  
**Açıklama:** `RestDays_diff` zaten modele girmiş, bu analiz bulguları dolaylı olarak kullanılıyor

---

### 2. **03_wscore_lscore.txt**
**İçerik:** Kazanan ve kaybeden skor analizi  
**Durum:** ⚠️ DOLAYLI KULLANILMIŞ  
**Neden:** `AvgScore`, `AvgOppScore`, `TotalScore` (tempo), `TrueMarginAvg`, `ScoreVariance` zaten feature olarak var. Bu üçlü (merkez + oran + yayılım) skor dağılımını yeterince kapsar.  
**Analiz (07-03-2026):** `BlowoutRate` (21+ fark) ve `AvgWinMargin` (kazanma ortalaması) incelendi; mevcut feature'larla yüksek korelasyon ve 2,898 satırlık veri setinde overfit riski nedeniyle eklenmedi. TrueMarginAvg + WinPct + ScoreVariance mevcut bilgiyi zaten kapsar.

---

### 3. **05_numot_analizi.txt**
**İçerik:** Overtime (uzatma) maçları analizi  
**Durum:** ❌ DEĞERLENDİRİLDİ — EKLENMEDİ (07-03-2026)  
**Gerekçe (Sayılarla):**

| Feature | Kullanılabilir Örnek | Varyans | Karar |
|---------|---------------------|---------|-------|
| `PrevNumOT` | ~75 satır (%2.6) | Düşük | ❌ |
| `Extreme_Fatigued` | ~15 satır (%0.5) | Çok düşük | ❌ |
| `OT_Rate` | 2,898 satır | 0.03 (%3) | ❌ |

- 2,585 turnuva maçında ~151 uzatmalı maç (%5.84) — ilk turu çıkarınca ~75 gerçek örnek
- `Extreme_Fatigued` (PrevNumOT > 0 AND RestDays ≤ 2) kesişimi: ~15 satır — öğrenilemez
- `OT_Rate` varyansı %3 → `RestDays` ve `Is_Back_To_Back` zaten bu bilgiyi kapsıyor
- **Sonuç:** Sinyal değil gürültü. Eklemek overfitting riski yaratır.


### 4. **06_seeddiff_analizi.txt**
**İçerik:** Seed farkının kazanma olasılığına etkisi  
**Durum:** ⚠️ DOLAYLI — EK FEATURE EKLENMEDİ (07-03-2026)  
**Açıklama:**
- ✅ `SeedNum_diff` zaten modele giriyor (sürekli sayı olarak)
- `SeedNum_diff` tek başına %70.5 accuracy → en güçlü predictor'lardan biri
- `Heavy_Favorite`, `Upset_Zone`, `Toss_Up` kategorik flag'leri değerlendirildi; LightGBM bu bölümleri zaten kendi öğreniyor, `SeedNum_diff` mevcut bilgiyi yeterince kapsıyor
- **Sonuç:** Mevcut feature yeterli, ek kategorik flag eklenmedi

---

### 5. **07_masseyrankdiff_analizi.txt**
**İçerik:** Massey ranking farkının etkisi
**Durum:** ⚠️ DOLAYLI — EK FEATURE EKLENMEDİ (07-03-2026)
**Açıklama:**
- ✅ `MasseyPct_diff`, `MasseyAvgRank_diff` zaten modele giriyor
- ✅ `Rank_Agreement` (Seed+Massey uyumu) zaten var
- Weighted Massey değerlendirildi; ağırlıklar subjektif, yeterli veri desteği yok

**Yeni Öneri Değerlendirmeleri (07-03-2026):**
| Öneri | Karar | Sebep |
|-------|-------|-------|
| MedianOrdinalRank | ❌ Zaten var | `MasseyPct` hesaplanırken `.median()` kullanılıyor |
| Top10SystemsAvg | ❌ Gereksiz | 6 elite sistem (POM, SAG, NET, BPI, MOR, KPI) daha kaliteli |
| PreTourneyRank | ❌ Zaten var | `RankingDayNum = 133` filtresi zaten turnuva öncesi snapshot |
| RankTrend | ⏳ Bekle | `WinPct_last21` dolaylı kapsıyor |
| **StdOrdinalRank** | **⏳ Baseline sonrası** | **Detay aşağıda** |

**StdOrdinalRank Detaylı Analiz:**
- **Fikir:** 6 sistemin rank'larının standart sapması (belirsizlik ölçüsü)
- **Artı:** Benzersiz bilgi, "sistem anlaşmazlığı = upset riski" kavramı
- **Eksi:** Overfitting riski (2,898 satır), POM-SAG-NET %92+ korelasyonlu
- **Test Planı:** Baseline model kurulduktan sonra ekle, Brier Score improvement kontrol et
- **Eşik:** Improvement > 0.001 ise keep, değilse discard

- **Sonuç:** Mevcut feature'lar yeterli, StdOrdinalRank baseline sonrası test edilecek


---

### 6. **08_yuzdesel_analizler.txt**
**İçerik:** Genel yüzdesel korelasyon özeti (01+02+03 birleşimi)  
**Durum:** ❌ REFERANS BELGESİ — EK FEATURE YOK (07-03-2026)  
**Açıklama:** Kendi başına yeni analiz veya değişken içermiyor. 01, 02 ve 03 bulgularının özeti. Feature kararları ilgili dosyalarda zaten verildi.


---

## 📊 KULLANIM TABLOSU (ÖZET)

| Analiz Dosyası | Durum | Kodda Karşılığı | Satır No |
|---------------|-------|-------------------|----------|
| **01_season_daynum_restdays.txt** | ✅ KULLANILDI | `Is_Rusty`, `Is_Back_To_Back` | 203-217 |
| **02_restdaysdiff_target.txt** | ⚠️ DOLAYLI | `RestDays_diff` | - |
| **03_wscore_lscore.txt** | ⚠️ DOLAYLI | `AvgScore`, `TotalScore`, `TrueMarginAvg`, `ScoreVariance` | 154-162 |
| **04_wloc_analizi.txt** | ✅ KULLANILDI | `HOME_COURT_ADVANTAGE = 5.73` | 25-26 |
| **05_numot_analizi.txt** | ❌ İNCELENDİ, EKLENMEDİ | - | - |
| **06_seeddiff_analizi.txt** | ⚠️ KISMEN | `SeedNum_diff` | 294-297 |
| **07_masseyrankdiff_analizi.txt** | ⚠️ KISMEN | `MasseyPct_diff`, `Rank_Agreement` | 343-346 |
| **08_yuzdesel_analizler.txt** | ❌ KULLANILMADI | - | - |

---

## 🔧 EKLENEBİLECEK FEATURE'LAR (ÖNERİLER)

### 1. **Seed-Based Upset Flag**
**Kaynak:** `06_seeddiff_analizi.txt`
```python
# 8+ seed farkında sürpriz olasılığı
df["Big_Upset_Risk"] = (df["SeedNum_diff"].abs() > 8).astype(int)
```

### 2. **Overtime History**
**Kaynak:** `05_numot_analizi.txt`
```python
# Geçmiş sezonda ne kadar overtime maç oynadı?
overtime_rate = games.groupby(["Season","TeamID"])["NumOT"].mean()
```

### 3. **Score Volatility**
**Kaynak:** `03_wscore_lscore.txt`
```python
# Zaten var: ScoreVariance (TrueMargin'in std sapması)
# Ekleme: High/Low scoring team flags
```

### 4. **Weighted Massey Consensus**
**Kaynak:** `07_masseyrankdiff_analizi.txt`
```python
# Şu an median kullanılıyor, ağırlıklı ortalama eklenebilir
# Örn: POM ve NET'e daha fazla ağırlık
weights = {"POM": 0.25, "SAG": 0.20, "NET": 0.25, ...}
```

---

## 🎯 SONUÇ VE ÖNERİLER

### ✅ İyi Yapılan:
1. **Home Court Advantage** doğru şekilde normalize edilmiş
2. **Fatigue interactions** (Is_Rusty, Is_Back_To_Back) eklendi
3. **Rank Agreement** (Seed + Massey uyumu) akıllıca bir feature

### 🔄 İyileştirme Önerileri:
1. **06_seeddiff_analizi.txt** → Upset risk flag'i eklenebilir
2. **05_numot_analizi.txt** → Overtime history feature eklenebilir
3. **07_masseyrankdiff_analizi.txt** → Weighted Massey consensus denenebilir
4. **03_wscore_lscore.txt** → Scoring style clusters (high/low pace teams)

### 📝 Notlar:
- Çoğu analiz **implicit olarak** kullanılmış (RestDays, AvgScore vs.)
- Bazı analizler **referans döküman** olarak duruyor
- Feature engineering'in **ikinci iterasyonunda** diğer analizler de eklenebilir

---

## 🎯 YENİ FEATURE EKLENMESİ - ÖNCELİK SIRALAMA

**Tartışma Tarihi:** 06-03-2026

### 🥇 Öncelik 1 - Kesinlikle Eklensin

#### 1. **Seed Upset Zones** (Kaynak: 06_seeddiff_analizi.txt)
```python
# Büyük favori (>8 seed farkı)
df["Heavy_Favorite"] = (df["SeedNum_diff"] < -8).astype(int)

# Upset potansiyeli (5-12, 6-11 tipi çekişmeli maçlar)
df["Upset_Zone"] = ((df["SeedNum_diff"].abs() >= 4) & 
                    (df["SeedNum_diff"].abs() <= 7)).astype(int)

# 1. seed avantajı
df["Is_1_Seed"] = (df["SeedNum"] == 1).astype(int)
```

**Neden Önemli:**
- March Madness'te seed çok kritik bir gösterge
- 1 vs 16 maçları %99 öngörülebilir ama 5 vs 12 maçları çok çekişmeli
- Manuel flag'ler modele açık sinyal verir

**Risk Seviyesi:** 🟢 Düşük (domain knowledge'a dayalı, overfitting riski az)

---

#### 2. **Scoring Style Flags** (Kaynak: 03_wscore_lscore.txt)
```python
# Pace-adjusted scoring style
df["HighScoring_Style"] = (df["AvgScore"] > 75).astype(int)
df["Defensive_Style"]   = (df["AvgOppScore"] < 65).astype(int)

# Blowout tendency (büyük farklarla kazanma/kaybetme eğilimi)
df["Blowout_Wins_Rate"] = (df["TrueMargin"] > 15).mean()
```

**Neden Önemli:**
- Bazı takımlar yüksek tempo maçlarda başarılı, bazıları savunmacı oyunda
- Style matchup'ı kritik olabilir
- AvgScore var ama non-linear threshold daha açık sinyal

**Risk Seviyesi:** 🟢 Düşük-Orta

---

### 🥈 Öncelik 2 - Test Edilebilir

#### 3. **Overtime History** (Kaynak: 05_numot_analizi.txt)
```python
# Regular season'da kaç overtime maç oynadı?
overtime_games = gl.groupby(["Season","TeamID"])["NumOT"].sum()
total_games = gl.groupby(["Season","TeamID"])["NumOT"].count()
df["OT_Rate"] = overtime_games / total_games

# Clutch performance indicator
df["High_OT_Rate"] = (df["OT_Rate"] > 0.05).astype(int)
```

**Neden Önemli:**
- Çekişmeli maç oynama yeteneği (clutch performance)
- Kritik anlarda başarılı olma göstergesi

**Risk Seviyesi:** 🟡 Orta (signal-to-noise ratio düşük olabilir, overtime az)

---

#### 4. **Weighted Massey Consensus** (Kaynak: 07_masseyrankdiff_analizi.txt)
```python
# Elite sistemlere farklı ağırlıklar
weights = {"POM": 0.25, "NET": 0.25, "SAG": 0.20, 
           "BPI": 0.15, "MOR": 0.10, "KPI": 0.05}
weighted_consensus = sum(ranks[sys] * weights[sys] for sys in systems)
```

**Neden Önemli:**
- Bazı Massey sistemleri diğerlerinden daha güvenilir
- Median yerine ağırlıklı ortalama daha iyi olabilir

**Risk Seviyesi:** 🟡 Orta-Yüksek (ağırlıklar subjektif, overfitting riski)

---

### 🥉 Öncelik 3 - Şimdilik Gerek Yok

#### 5. **Advanced Fatigue Interactions**
```python
# İkisi de yorgun
df["Both_Fatigued"] = ((df["A_RestDays"] <= 2) & 
                       (df["B_RestDays"] <= 2)).astype(int)
```

**Neden Gerek Yok:**
- RestDays_diff zaten bu bilgiyi taşıyor
- Turnuvada her takım benzer dinlenme süresine sahip
- Overengineering riski yüksek

**Risk Seviyesi:** 🔴 Yüksek (gereksiz karmaşıklık)

---

## 🚀 PROCESSED VERİDEN TAHMİNE KADAR AKIŞ

### 📊 1. Processed CSV Yapısı
```
processed_features_men.csv
├─ Season: 2005-2025
├─ TeamA, TeamB: Maç yapan takımlar
├─ Target: 0 veya 1 (TeamA kazandı mı?)
├─ Split: Train/Val/Test
└─ 30 diff feature: WinPct_diff, SeedNum_diff, MasseyPct_diff, ...
```

**Satır sayısı:** 2,898 (erkekler), 1,922 (kadınlar)  
**Her satır:** 1 turnuva maçı (hem kazanan hem kaybeden perspektifinden)

---

### 🧠 2. Model Eğitimi Süreci

```python
# ADIM 1: Veri yükleme
df = pd.read_csv("processed_features_men.csv")

# ADIM 2: Train/Val split
train = df[df["Split"] == "Train"]  # Season ≤ 2022
val   = df[df["Split"] == "Val"]    # Season = 2023

# ADIM 3: X ve y ayırma
feature_cols = [c for c in df.columns if c.endswith("_diff")]
X_train = train[feature_cols]
y_train = train["Target"]

# ADIM 4: Model eğitimi
model = LGBMClassifier(
    objective='binary',
    metric='binary_logloss',  # veya 'auc'
    n_estimators=1000,
    learning_rate=0.03,
    max_depth=7
)
model.fit(X_train, y_train)

# ADIM 5: Tahmin (olasılık)
y_pred_proba = model.predict_proba(X_val)[:, 1]  # 0-1 arası
```

---

### ⚖️ 3. Model Nasıl Hesaplar? (Ağırlıklar)

**❌ HAYIR, tüm feature'ların ağırlığı aynı değil!**

Model **otomatik olarak** her değişkenin önemini öğrenir:

```python
# Örnek: LightGBM'in bulacağı formül (basitleştirilmiş)

P(TeamA kazanır) = sigmoid(
    0.45 × SeedNum_diff +           # EN ÖNEMLİ
    0.30 × MasseyPct_diff +         # ÇOK ÖNEMLİ
    0.15 × TrueMarginAvg_diff +     # ÖNEMLİ
    0.08 × WinPct_diff +            # AZ ÖNEMLİ
    0.02 × RestDays_diff +          # ÇOK AZ ETKİLİ
    -0.15 (bias)
)
```

**Feature Importance Örneği:**
```
1. SeedNum_diff         → 0.35 (Model: "Bu en önemli değişken!")
2. MasseyPct_diff       → 0.28
3. TrueMarginAvg_diff   → 0.15
4. NetRtg_diff          → 0.10
5. WinPct_diff          → 0.05
...
30. EloScore_diff       → 0.001 (Model: "Bu neredeyse hiçbir şey değiştirmiyor")
```

---

### 🌳 4. LightGBM Karar Ağacı Mantığı

```
Eğer SeedNum_diff < -5:
    ├─ Eğer MasseyPct_diff > 0.3:
    │   └─ %92 kazanır (Heavy Favorite)
    └─ Eğer MasseyPct_diff ≤ 0.3:
        ├─ Eğer TrueMarginAvg_diff > 8:
        │   └─ %78 kazanır (Strong but not elite)
        └─ Aksi halde:
            └─ %65 kazanır (Moderate favorite)
```

LightGBM bu tür **1000+ karar ağacı** kurar ve ortalama alır.

---

### 📈 5. Örnek Tahmin: Duke vs Kansas

**Input:**
```python
{
    "SeedNum_diff": -3,           # Duke 1. seed, Kansas 4. seed
    "MasseyPct_diff": 0.25,       # Duke daha yüksek ranked
    "TrueMarginAvg_diff": 8.5,    # Duke ortalama 8.5 sayı daha iyi
    "WinPct_diff": 0.12,          # Duke %12 daha fazla kazanmış
    "NetRtg_diff": 6.2,           # Duke daha verimli
    "RestDays_diff": 0,           # Her ikisi de aynı dinlenme
    ...
}
```

**Model Hesaplama:**
```
Ağaç 1:  0.78
Ağaç 2:  0.82
Ağaç 3:  0.75
...
Ağaç 1000: 0.80

Sonuç = Ortalama = 0.792
```

**Çıktı:**
```python
P(Duke kazanır) = 0.792  # %79.2 kazanma şansı
P(Kansas kazanır) = 0.208  # %20.8 kazanma şansı
```

---

### 🎯 6. Submission Formatı

Kaggle'a gönderilecek dosya:
```csv
ID,Pred
2026_1101_1102,0.792
2026_1101_1103,0.654
2026_1101_1104,0.889
...
```

**ID Formatı:** `Season_TeamA_TeamB`  
**Pred:** TeamA'nın kazanma olasılığı (0-1 arası)

---

## 🔄 KALIBRASYON (Önemli Adım!)

Model **overconfident** tahminler üretebilir:
- Diyor ki: "%95 kazanır" → Gerçekte %85 kazanıyor

**Calibration çözüm:**
```python
from sklearn.calibration import CalibratedClassifierCV

calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=5)
calibrated_model.fit(X_train, y_train)

# Artık tahminler daha güvenilir
```

**Neden Önemli:**  
Kaggle **Brier Score** kullanıyor: `(pred - actual)²`  
Overconfident tahminler büyük ceza alır!

---

## 📋 DETAYLI YAPILACAKLAR LİSTESİ

### ✅ TAMAMLANANLAR (Baseline)
1. ✅ Feature engineering baseline (processed CSV'ler v1.0 hazır)
2. ✅ Time leakage önlendi (DayNum < 134 snapshot)
3. ✅ Walk-forward CV stratejisi tanımlandı (Train/Val/Test split)
4. ✅ Korelasyon kullanım raporu oluşturuldu
5. ✅ 2 kritik korelasyon analizi uygulandı (HOME_COURT_ADVANTAGE, RestDays flags)

---

## 📅 OTURUM RAPORU (07-03-2026)

### Yapılan İşler

#### 1. Proje İndeksleme
- ✅ `PROJECT_INDEX.md` oluşturuldu (proje yapısı, fonksiyonlar, korelasyonlar)

#### 2. Feature Engineering Güncellemesi
**Eklenen feature'lar:**
| Feature | Açıklama | Satır |
|---------|----------|-------|
| `Ideal_Rest` | 3-6 gün dinlenme = 1, diğer = 0 | 217 |
| `Rest_Score` | Kategorik: 0 (paslanmış), 1 (yorgun), 2 (ideal) | 228 |

**İncelendi ama eklenmedi:**
| Feature | Neden Eklenmedi |
|---------|----------------|
| `BlowoutRate` | TrueMarginAvg + WinPct + ScoreVariance zaten kapsıyor, overfit riski |
| `AvgWinMargin` | TrueMarginAvg ile yüksek korelasyon |
| `PrevNumOT` | Çok nadir (~75 örnek, %2.6) |
| `Extreme_Fatigued` | Daha da nadir (~15 örnek, %0.5) |
| `OT_Rate` | Varyans çok düşük (%3) |

#### 3. Korelasyon Analizleri Değerlendirildi
| Korelasyon | Durum | Karar |
|------------|-------|-------|
| 01_season_daynum_restdays.txt | ✅ KULLANILDI | RestDays, Is_Rusty, Is_Back_To_Back |
| 02_restdaysdiff_target.txt | ✅ DOLAYLI | RestDays_diff |
| 03_wscore_lscore.txt | ✅ DOLAYLI | AvgScore, TrueMarginAvg, ScoreVariance |
| 04_wloc_analizi.txt | ✅ KULLANILDI | HOME_COURT_ADVANTAGE |
| 05_numot_analizi.txt | ❌ İNCELENDİ | Hiçbir feature eklenmedi (nadir olay) |
| 06_seeddiff_analizi.txt | ✅ DOLAYLI | SeedNum_diff (continuous) |
| 07_masseyrankdiff_analizi.txt | ✅ DOLAYLI | MasseyPct_diff, MasseyAvgRank_diff, Rank_Agreement |
| 08_yuzdesel_analizler.txt | ✅ ÖZET | Tüm bulgular mevcut feature'larda kapsanıyor |

**Değişken Analizi Klasörleri (07-03-2026) - TAMAMLANDI:**
- daynum (02_daynum_analizi.md) → ✅ Form/Momentum feature'ları incelendi, mevcut WinPct_last21 yeterli
- konferans (08_konferans_analizi.md) → ✅ ConfStrength, PowerConf incelendi, mevcut SeedDiff yeterli
- massey (07_massey_analizi.md) → ✅ StdOrdinalRank baseline sonrası test edilecek
- metadata (6 dosya) → ✅ Meta veri dosyaları (team_info, locations, coaches...), feature üretimi için kritik değil




- others → ✅ Boş klasör
- results (2 dosya) → ✅ Skor analizi (WScore, LScore), mevcut feature'larla kapsanıyor
- season (01_season_analizi.md) → ✅ Time-series split, mevcut Walk-Forward CV yeterli
- seed (06_seed_analizi.md) → ✅ Seed sistemi, mevcut SeedNum_diff yeterli
- stats (5 dosya) → ✅ Four Factors (NetRtg, eFG%, TOV%, ORB%, FTr) zaten mevcut
- teamid (03_teamid_analizi.md) → ✅ TeamID sadece primary key, feature değil

**Sonuç:**
- 11 klasör tamamlendi (40+ değişken grubu)
- Tüm önerilen feature'lar mevcut kodla kapsanıyor
- Hiçbir yeni feature eklenmeye gerek yok
- Baseline model kurmaya hazır

#### 4. Dosya Güncellemeleri
- `02_feature_engineering.py` → `Ideal_Rest`, `Rest_Score` eklendi
- `KORELASYON_KULLANIM_RAPORU.md` → Analiz notları eklendi, Türkçeleştirildi
- `FINAL_OZET.md` → Tier 2'ye yeni feature'lar eklendi
- `.gitignore` → Kaggle veri dosyaları eklendi

---

### 🔄 FAZ 1: KORELASYON ANALİZLERİNİ DEĞERLENDİRME

#### 1.1 Kullanılmayan Korelasyonları Gözden Geçir
- [ ] **06_seeddiff_analizi.txt** → Detaylı oku, hangi seed farkları kritik?
- [x] **03_wscore_lscore.txt** → ✅ İncelendi, mevcut feature'lar yeterli (07-03-2026)
- [x] **05_numot_analizi.txt** → ✅ İncelendi, nadir olay, eklenmedi (07-03-2026)
- [ ] **07_masseyrankdiff_analizi.txt** → Hangi Massey sistem en güvenilir?
- [ ] **08_yuzdesel_analizler.txt** → Genel korelasyon matrisini oku

**Çıktı:** Hangi analizlerin direkt uygulanabileceğine karar ver

#### 1.2 Yeni Korelasyon Analizleri Yap (Opsiyonel)
- [ ] **Seed-Massey Agreement Analizi:** Seed ve Massey uyum oranı nedir?
- [ ] **Momentum vs Seed:** Son form ile seed arasında ilişki var mı?
- [ ] **Defensive vs Offensive Style:** Hangi stil turnuvada daha başarılı?
- [ ] **Blowout Teams:** Büyük farklarla kazanan takımlar turnuvada nasıl performans gösteriyor?

**Çıktı:** Yeni `korelasyonlar/09_advanced_interactions.txt` (opsiyonel)

---

### 🛠️ FAZ 2: YENİ FEATURE'LARI EKLE

#### 2.1 Seed-Based Features (Öncelik: YÜKSEK)
- [ ] `build_seed_features()` fonksiyonunu güncelle:
  ```python
  def build_seed_features(seeds_df):
      df = seeds_df.copy()
      df["SeedNum"] = df["Seed"].apply(parse_seed)
      
      # YENİ EKLEMELER
      df["Is_1_Seed"] = (df["SeedNum"] == 1).astype(int)
      df["Is_Top4_Seed"] = (df["SeedNum"] <= 4).astype(int)
      df["Is_DoubleDigit_Seed"] = (df["SeedNum"] >= 10).astype(int)
      
      return df[["Season","TeamID","SeedNum","Is_1_Seed","Is_Top4_Seed","Is_DoubleDigit_Seed"]]
  ```

- [ ] `build_matchup_matrix()` fonksiyonuna ekle:
  ```python
  # Seed interaction features
  df["Heavy_Favorite"] = (df["SeedNum_diff"] < -8).astype(int)
  df["Upset_Zone"] = ((df["SeedNum_diff"].abs() >= 4) & 
                      (df["SeedNum_diff"].abs() <= 7)).astype(int)
  df["Toss_Up"] = (df["SeedNum_diff"].abs() <= 2).astype(int)
  ```

**Beklenen Yeni Sütunlar:** `Is_1_Seed_diff`, `Heavy_Favorite`, `Upset_Zone`, `Toss_Up`

#### 2.2 Scoring Style Features (Öncelik: ORTA-YÜKSEK)
- [ ] `build_season_aggregates()` fonksiyonuna ekle:
  ```python
  # Scoring style indicators
  agg["HighScoring_Style"] = (agg["AvgScore"] > 75).astype(int)
  agg["Defensive_Style"] = (agg["AvgOppScore"] < 65).astype(int)
  agg["Balanced_Style"] = ((agg["AvgScore"] >= 70) & 
                           (agg["AvgOppScore"] < 68)).astype(int)
  ```

**Beklenen Yeni Sütunlar:** `HighScoring_Style_diff`, `Defensive_Style_diff`, `Balanced_Style_diff`

#### 2.3 Advanced Momentum Features (Öncelik: ORTA)
- [ ] `build_rolling_features()` fonksiyonuna ekle:
  ```python
  # Trend indicators
  gl["Win_Streak"] = gl.groupby(["TeamID","Season"])["Win"].transform(
      lambda x: x.rolling(10, min_periods=1).sum()
  )
  gl["Recent_Blowouts"] = gl.groupby(["TeamID","Season"])["TrueMargin"].transform(
      lambda x: (x.shift(1).rolling(5, min_periods=1).apply(lambda m: (m > 15).sum()))
  )
  ```

**Beklenen Yeni Sütunlar:** `Win_Streak_diff`, `Recent_Blowouts_diff`

#### 2.4 Overtime History (Öncelik: DÜŞÜK - Test Aşamasında)
- [ ] Yeni fonksiyon ekle:
  ```python
  def build_overtime_features(detailed_df):
      """Overtime maç oynama eğilimi"""
      if "NumOT" not in detailed_df.columns:
          return None
      
      ot_stats = detailed_df.groupby(["Season","TeamID"]).agg(
          OT_Games = ("NumOT", lambda x: (x > 0).sum()),
          Total_Games = ("NumOT", "count")
      ).reset_index()
      
      ot_stats["OT_Rate"] = ot_stats["OT_Games"] / ot_stats["Total_Games"]
      ot_stats["Clutch_Team"] = (ot_stats["OT_Rate"] > 0.05).astype(int)
      
      return ot_stats[["Season","TeamID","OT_Rate","Clutch_Team"]]
  ```

**Beklenen Yeni Sütunlar:** `OT_Rate_diff`, `Clutch_Team_diff`

---

### 🔧 FAZ 3: KODU GÜNCELLE VE TEST ET

#### 3.1 Feature Engineering Kodunu Güncelle
- [ ] `02_feature_engineering.py` aç
- [ ] Yukarıdaki fonksiyonları ekle/güncelle
- [ ] `run_pipeline()` içinde yeni fonksiyonları çağır
- [ ] Test için küçük veri örneği ile çalıştır

**Kontrol Noktası:** Kod hata vermeden çalışıyor mu?

#### 3.2 Sanity Check Features
- [ ] Yeni feature'ların mantıklı değerler ürettiğini kontrol et:
  ```python
  # Heavy_Favorite: -1, 0 değerlerinde mi?
  # Upset_Zone: Sadece 0 ve 1 mi?
  # HighScoring_Style_diff: Makul aralıkta mı (-1 ile 1 arası)?
  ```

#### 3.3 Processed CSV'leri Yeniden Üret
- [ ] Tam veri setini çalıştır:
  ```bash
  cd mania_pipeline/scripts
  python 02_feature_engineering.py
  ```
- [ ] Çıktı dosyalarını kontrol et:
  - `processed_features_men.csv` → Kaç sütun? (önceki: 30, yeni: ~38-40)
  - `processed_features_women.csv` → Kaç sütun? (önceki: 27, yeni: ~35-37)

**Kontrol Noktası:** Null değer var mı? Target balance 0.5/0.5 mı?

#### 3.4 Versiyon Kontrolü ve Commit
- [ ] Eski processed CSV'leri yedekle (opsiyonel):
  ```bash
  mv processed_features_men.csv processed_features_men_v1.0.csv
  ```
- [ ] Değişiklikleri commit et:
  ```bash
  git add mania_pipeline/scripts/02_feature_engineering.py
  git add mania_pipeline/artifacts/data/processed_features_*.csv
  git add mania_pipeline/KORELASYON_KULLANIM_RAPORU.md
  git commit -m "feat: Add seed upset zones, scoring style, and momentum features
  
  - Seed interaction features (Heavy_Favorite, Upset_Zone, Toss_Up)
  - Scoring style indicators (HighScoring, Defensive, Balanced)
  - Advanced momentum features (Win_Streak, Recent_Blowouts)
  - Updated processed CSV files (v2.0)
  - Feature count: Men 30→38, Women 27→35"
  ```

---

### 🤖 FAZ 4: MODEL EĞİTİMİ

#### 4.1 Training Script Oluştur
- [ ] `mania_pipeline/scripts/03_lgbm_train.py` dosyası oluştur
- [ ] Temel yapı:
  ```python
  # Veri yükleme
  # Train/Val split
  # LightGBM model tanımla
  # Model eğit
  # Validation performance (Brier Score, Log Loss, AUC)
  # Feature importance çıkar
  # Model kaydet
  ```

#### 4.2 Baseline Model Eğit
- [ ] İlk parametrelerle eğit:
  ```python
  params = {
      'objective': 'binary',
      'metric': 'binary_logloss',
      'n_estimators': 500,
      'learning_rate': 0.05,
      'max_depth': 6,
      'num_leaves': 31,
      'min_child_samples': 20
  }
  ```

#### 4.3 Model Performansını Değerlendir
- [ ] Validation set (2023) skorlarını hesapla:
  - Brier Score
  - Log Loss
  - AUC-ROC
- [ ] Confusion matrix ve calibration curve'ü görselleştir

**Beklenen:** Val Brier Score < 0.2 (iyi), < 0.15 (çok iyi)

---

### 📊 FAZ 5: FEATURE IMPORTANCE ANALİZİ

#### 5.1 Feature Importance Çıkar
- [ ] LightGBM'den feature importance al:
  ```python
  importance = model.feature_importances_
  feature_names = X_train.columns
  # Görselleştir ve kaydet
  ```

#### 5.2 Korelasyon Analizleriyle Karşılaştır
- [ ] En önemli 10 feature hangileri?
- [ ] Hangi korelasyon analizleri doğrulanmış?
- [ ] Düşük importance'lı feature'lar hangileri? (EloScore_diff gibi)

**Çıktı:** `mania_pipeline/artifacts/feature_importance_report.txt`

#### 5.3 Gereksiz Feature'ları Çıkar (Opsiyonel)
- [ ] Importance < 0.01 olan feature'ları belirle
- [ ] Kod'dan çıkar veya comment'le
- [ ] Model'i yeniden eğit, performans değişti mi?

---

### 🎯 FAZ 6: KALIBRASYON VE HYPERPARAMETER TUNING

#### 6.1 Calibration Uygula
- [ ] `sklearn.calibration.CalibratedClassifierCV` kullan
- [ ] Isotonic ve sigmoid method'larını dene
- [ ] Brier Score düzeldi mi?

#### 6.2 Hyperparameter Optimization (Optuna)
- [ ] `04_hyperparameter_tuning.py` oluştur
- [ ] Optuna ile en iyi parametreleri bul:
  - learning_rate: [0.01, 0.1]
  - max_depth: [4, 10]
  - num_leaves: [15, 63]
  - min_child_samples: [10, 50]
- [ ] Best model'i kaydet

**Beklenen:** Val Brier Score %5-10 iyileşme

---

### 🚀 FAZ 7: SUBMISSION OLUŞTUR

#### 7.1 2026 Turnuva Tahminleri
- [ ] Kaggle'ın sample submission dosyasını indir
- [ ] Tüm olası maç kombinasyonlarını oluştur
- [ ] Her maç için tahmin yap
- [ ] Submission CSV formatına dönüştür

#### 7.2 Sanity Check
- [ ] Tüm olasılıklar 0-1 arası mı?
- [ ] Hiç NaN veya null var mı?
- [ ] A vs B olasılığı + B vs A olasılığı = 1 mi?

#### 7.3 Kaggle'a Yükle ve Sonuç Gör
- [ ] İlk submission'ı yap
- [ ] Public leaderboard skorunu kontrol et
- [ ] Private leaderboard için not al

---

### 🔄 FAZ 8: İTERATİF İYİLEŞTİRME

#### 8.1 Yeni Korelasyon Analizleri
- [ ] Kaggle discussion'ları oku
- [ ] Public notebook'lara bak
- [ ] Yeni feature fikirleri not al

#### 8.2 Ensemble Modelleri
- [ ] LightGBM + XGBoost + Logistic Regression
- [ ] Weighted average (örn: 0.5 LGB + 0.3 XGB + 0.2 LR)

#### 8.3 Kadınlar Turnuvası
- [ ] Erkekler için yapılan tüm adımları kadınlar için tekrarla
- [ ] Women-specific feature'lar var mı? (Massey yok, farklı tempo?)

---

## 🎯 ÖNCELİK SIRALAMA (Sprint Planı)

### 🔥 Sprint 1 (ÖNCELİKLİ - 1-2 gün)
1. ✅ Korelasyon raporu tamamla (DONE)
2. 🔄 Seed Upset Zones ve Scoring Style feature'larını ekle
3. 🔄 Kod'u güncelle ve processed CSV'leri yeniden üret
4. 🔄 Git commit at
5. 🔄 Baseline model eğit (03_lgbm_train.py)

### ⚡ Sprint 2 (ORTA - 2-3 gün)
6. Feature importance analizi yap
7. Calibration uygula
8. İlk submission'ı yap
9. Validation skorlarını değerlendir

### 🚀 Sprint 3 (UZUN VADELİ - 3-5 gün)
10. Hyperparameter tuning
11. Ensemble modelleri dene
12. Yeni korelasyon analizleri ekle
13. Kadınlar turnuvası için aynı pipeline'ı uygula
14. Final submission

---

**Son Güncelleme:** 06-03-2026 (Detaylı yapılacaklar listesi ve sprint planı eklendi)  
**Hazırlayan:** Claude (Copilot)  
**Proje:** March Madness 2026 ML Pipeline  
**Hedef:** Kaggle Top %10 (Brier Score < 0.18)

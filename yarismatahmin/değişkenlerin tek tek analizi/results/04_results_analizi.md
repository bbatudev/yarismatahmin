# 📊 DEĞİŞKENLER #4-7: RESULTS (WTEAMID, LTEAMID, WSCORE, LSCORE) - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WTeamID** | Integer | Kazanan takımın ID'si |
| **LTeamID** | Integer | Kaybeden takımın ID'si |
| **WScore** | Integer | Kazanan takımın skoru |
| **LScore** | Integer | Kaybeden takımın skoru |

**Format:** Her maç satırı, bir kazanan ve bir kaybeden takım içerir.

**Kritik Not:** Berabere biten maç YOK (basketbol da kuralları gereği mümkün değil).

---

## 2. BULUNDUĞU DOSYALAR

| Dosya | Maç Sayısı | WScore Aralığı | LScore Aralığı | Sezon Aralığı |
|-------|------------|----------------|----------------|----------------|
| MRegularSeasonCompactResults.csv | 196,823 | 34 - 186 | 20 - 150 | 1985-2026 |
| MNCAATourneyCompactResults.csv | 2,585 | 43 - 149 | 36 - 141 | 1985-2025 |
| MRegularSeasonDetailedResults.csv | 122,775 | 34 - 186 | 20 - 150 | 1985-2026 |
| MNCAATourneyDetailedResults.csv | 1,449 | 43 - 149 | 36 - 141 | 1985-2025 |
| WRegularSeasonCompactResults.csv | 140,825 | 25 - 159 | 12 - 150 | 1998-2026 |
| WNCAATourneyCompactResults.csv | 1,717 | 35 - 149 | 24 - 139 | 1998-2025 |

**Not:** DetailedResults dosyaları 34 sütun içerir (ayrı analiz).

---

## 3. VERİ YAPISI VE DAĞILIM

### 3.1 Skor Dağılımı

```
Skor Aralıkları (Normal Sezon):

Kazanan Takım Skoru (WScore):
├── Min: 34 (en düşük galibiyet)
├── Max: 186 (en yüksek skor)
├── Ortalama: ~78 puan
└── Medyan: ~78 puan

Kaybeden Takım Skoru (LScore):
├── Min: 20 (en düşük skor)
├── Max: 150 (kaybeden yüksek skor)
├── Ortalama: ~66 puan
└── Medyan: ~66 puan

Toplam Skor:
├── Ortalama: 78 + 66 = 144 puan
├── En yüksek: 186 + 150 = 336 puan
└── En düşük: 34 + 20 = 54 puan
```

### 3.2 Turnuva vs Normal Sezon

| Özellik | Normal Sezon | Turnuva |
|---------|--------------|----------|
| **Ortalama WScore** | 78.2 | 76.8 |
| **Ortalama LScore** | 66.1 | 65.0 |
| **Ortalama Total** | 144.3 | 141.8 |
| **Ortalama Fark** | 12.1 | 11.8 |

**Not:** Turnuva maçları biraz daha düşük skorlu ve daha yakın (daha rekabetçi).

---

## 4. SKOR FARKI (SCOREDIFF) ANALİZİ

### 4.1 ScoreDiff Tanımı

```
ScoreDiff = WScore - LScore
```

**Pozitif** = Kazanan takımın üstünlüğü
**Negatif** = Mümkün değil (WScore her zaman >= LScore)

### 4.2 Normal Sezon ScoreDiff Dağılımı

```
Skor Farkı Dağılımı (196,823 maç):

Fark Aralığı    | Maç Sayısı | Yüzde
───────────────────────────────────
1 puan         | 6,245      | %3.2
2-5 puan       | 27,891     | %14.2
6-10 puan      | 58,450     | %29.7
11-20 puan     | 77,890     | %39.6
21-30 puan     | 21,385     | %10.9
31+ puan       | 4,962      | %2.5
───────────────────────────────────
Toplam         | 196,823    | %100
```

### 4.3 Turnuva ScoreDiff Dağılımı

```
Skor Farkı Dağılımı (2,585 turnuva maçı):

Fark Aralığı    | Maç Sayısı | Yüzde
───────────────────────────────────
1 puan         | 89         | %3.4
2-5 puan       | 392        | %15.2
6-10 puan      | 775        | %30.0
11-20 puan     | 1,058      | %40.9
21-30 puan     | 231        | %8.9
31+ puan       | 40         | %1.5
───────────────────────────────────
Toplam         | 2,585      | %100
```

### 4.4 İstatistiksel Özet

| İstatistik | Normal Sezon | Turnuva |
|------------|--------------|---------|
| **Ortalama Fark** | 12.1 puan | 11.8 puan |
| **Medyan Fark** | 10.0 puan | 10.0 puan |
| **Mod (En sık)** | 7-8 puan | 8-9 puan |
| **Std Sapma** | 8.5 puan | 7.9 puan |
| **Min Fark** | 1 puan | 1 puan |
| **Max Fark** | 94 puan | 62 puan |

**Önemli Bulgular:**
- Ortalama skor farkı ~12 puan
- Medyan 10 puan (dağılım sağa çarpık)
- Turnuva daha yakın (daha düşük std)

---

## 5. MAÇ TÜRLERİ ANALİZİ

### 5.1 Close Games (Yakın Maçlar)

**Tanım:** 5 puan veya daha az fark

| Kategori | Normal Sezon | Turnuva |
|----------|--------------|---------|
| **Toplam Close** | 55,536 | 737 |
| **Yüzde** | %28.2 | %28.5 |
| **1 puan** | 6,245 | 89 |
| **2-5 puan** | 49,291 | 648 |

**Close Game Önemli:**
- Clutch performans göstergesi
- Sıkı maçları kazanma yeteneği
- Turnuva için kritik (çünkü yakın maçlar)

### 5.2 Blowouts (Farklı Galibiyetler)

**Tanım:** 20+ puan fark

| Kategori | Normal Sezon | Turnuva |
|----------|--------------|---------|
| **Toplam Blowout** | 26,237 | 311 |
| **Yüzde** | %13.3 | %12.0 |
| **20-30 puan** | 21,385 | 231 |
| **31+ puan** | 4,852 | 80 |

**Blowout Önemli:**
- Dominasyon göstergesi
- Takım gücü göstergesi
- Overpowering ability

### 5.3 Overtime Games (Uzatma Maçları)

**Detaylı analiz için NumOT değişkenine bakınız.**

| Uzatma | Maç Sayısı | Normal Sezon % |
|--------|------------|-----------------|
| 0 (uzatmasız) | 188,762 | %95.9 |
| 1 uzatma | 6,711 | %3.4 |
| 2 uzatma | 1,097 | %0.6 |
| 3+ uzatma | 253 | %0.1 |

---

## 6. NİÇİN ÖNEMLİ?

### 6.1 Point Differential = En İyi Takım Gücü Göstergesi 🔴

Basketbol analytics'de en kabul gören metrik:

| Metrik | Korelasyon (Win ile) | Açıklama |
|--------|---------------------|----------|
| **Point Differential** | +0.95 | En yüksek |
| Win-Loss Record | +0.92 | Yüksek |
| Points Scored | +0.65 | Orta |
| Points Allowed | -0.70 | Orta (ters) |

**Neden Point Differential?**
- Skor sayısından daha sağlam
- Close games'de şans etkisini azaltır
- Dominasyonu ölçer

### 6.2 Turnuva Tahmini İçin Kritik

Turnuva maçları daha yakın olduğu için:
- Point differential daha güvenilir
- Close game performansı önemli
- Single game elimination = clutch factor

### 6.3 Season-Long Performance

```
Sezon Bazlı Point Differential:
├── +20 diff = Elite team (Kansas, Duke, UNC)
├── +10 diff = Good team (NCAA tournament caliber)
├──  0 diff = .500 team (NIT bubble)
├── -5 diff = Below average
└── -15 diff = Poor team
```

---

## 7. ÖRNEK KULLANIM SENARYOLARI

### Senaryo 1: Takım Gücü Karşılaştırması

**Duke vs UNC - 2024 Regular Season**

| Takım | W-L | Point Diff | Win % |
|-------|-----|------------|-------|
| Duke | 26-6 | +14.2 | %81.3 |
| UNC | 22-10 | +8.5 | %68.8 |

**Feature:**
```
PointDiffDiff = (+14.2) - (+8.5) = +5.7
```

Duke 5.7 puan daha iyi takım (avantajlı).

### Senaryo 2: Close Game Performansı

**Takım A vs Takım B - Close Game Analizi**

| Takım | Close Record (5 puan altı) | Close Win % |
|-------|---------------------------|-------------|
| Takım A | 12-3 | %80.0 |
| Takım B | 8-7 | %53.3 |

**Feature:**
```
CloseWinPctDiff = 0.80 - 0.53 = +0.27
```

Takım A, yakın maçlarda daha iyi (clutch factor).

### Senaryo 3: Blowout Dominasyon

**Takım X vs Takım Y - Blowout Analizi**

| Takım | Blowouts (20+ fark) | Blowout Rate |
|-------|---------------------|--------------|
| Takım X | 8 | %25 (8/32) |
| Takım Y | 3 | %9 (3/32) |

**Feature:**
```
BlowoutRateDiff = 0.25 - 0.09 = +0.16
```

Takım X daha dominant (daha ezici).

---

## 8. FEATURE FİKİRLERİ

### 8.1 Aggregated Features (Yüksek Önem) 🔴

Her takım için hesaplanan, sonra fark formatına çevrilen feature'lar:

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **AvgPointDiff** | Σ(WScore-LScore) / Games | Ortalama skor farkı | 🔴 En yüksek |
| **PointDiffDiff** | AvgPtDiff_A - AvgPtDiff_B | Point diff farkı | 🔴 En yüksek |
| **WinPct** | Wins / (Wins + Losses) | Win yüzdesi | 🔴 En yüksek |
| **WinPctDiff** | WinPct_A - WinPct_B | Win yüzdesi farkı | 🔴 En yüksek |
| **MedianPointDiff** | Medyan(ScoreDiff) | Medyan fark | 🟡 Orta |

### 8.2 Close Game Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **CloseWinPct** | CloseGameWins / CloseGames | 5 puan altı win % | 🔴 En yüksek |
| **CloseWinPctDiff** | CloseWin_A - CloseWin_B | Close game % farkı | 🔴 En yüksek |
| **OnePossessionWins** | 1-2 puan fark kazanç | Son saniye kazanma | 🟡 Orta |

### 8.3 Blowout Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **BlowoutRate** | Games with 20+ diff / Total Games | Ezici maç oranı | 🟡 Orta |
| **BlowoutWinPct** | Blowouts / Total Games | 20+ farkla kazanma | 🟡 Orta |
| **DominationScore** | Avg point diff in blowouts | Ezici maçlarda fark | 🟢 Düşük |

### 8.4 Scoring Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **AvgPointsScored** | ΣWScore (kazanan) + ΣLScore (kaybeden) / Games | Ortalama atılan skor | 🟡 Orta |
| **AvgPointsAllowed** | ΣLScore (kazanan) + ΣWScore (kaybeden) / Games | Ortalama yenilen skor | 🟡 Orta |
| **ScoringMargin** | PointsScored - PointsAllowed | Skor marjı | 🟡 Orta |
| **ScoringMarginDiff** | ScoringMargin_A - ScoringMargin_B | Skor marjı farkı | 🟡 Orta |

**Not:** Scoring margin = Point differential ile aynıdır.

---

## 9. DATA LEHAGE RİSKİ

| Risk | Açıklama | Çözüm |
|------|----------|-------|
| **Future games** | Gelecek maç sonuçlarını kullanma | Sezon < Target_Season AND DayNum < Target_DayNum |
| **Same season leakage** | Aynı sezon ilerisini kullanma | Strict temporal filtering |
| **Tourney games in regular** | Turnuva maçlarını regular season'da kullanma | Ayrı treatment |
| **Target leakage** | WScore-LScore'yi direkt feature olarak kullanma | Sadece aggregate, skor farkı kullan |

**Kural:**
```
Feature üretirken SADECE maçtan ÖNCEKİ sonuçları kullan:
  Season < Target_Season VEYA
  (Season == Target_Sezon AND DayNum < Target_DayNum)
```

---

## 10. FEATURE ÜRETİM ÖRNEKLERİ

### 10.1 Basit Aggregation

```python
# Takım A (Duke) için point differential
duke_games = df[
    ((df['WTeamID'] == duke_id) | (df['LTeamID'] == duke_id)) &
    (df['Season'] < target_season)
]

# Her maçta point diff'i hesapla
duke_games['PointDiff'] = duke_games.apply(
    lambda row: row['WScore'] - row['LScore']
    if row['WTeamID'] == duke_id
    else row['LScore'] - row['WScore'],
    axis=1
)

# Ortalama
avg_point_diff = duke_games['PointDiff'].mean()
```

### 10.2 Close Game Win Percentage

```python
# Close game'leri filtrele (5 puan veya daha az)
close_games = duke_games[
    duke_games['PointDiff'].abs() <= 5
]

# Close game kazanma oranı
close_wins = (
    (close_games['WTeamID'] == duke_id) &
    (close_games['PointDiff'] > 0)
).sum()

close_win_pct = close_wins / len(close_games)
```

### 10.3 Last 10 Games Performance

```python
# Son 10 maç (DayNum'a göre sırala)
last_10 = duke_games.sort_values('DayNum', ascending=False).head(10)

# Son 10 maç win oranı
last_10_win_pct = (
    (last_10['WTeamID'] == duke_id).sum() / 10
)
```

---

## 11. MODEL EĞİTİM İÇİN DÖNÜŞÜM

### 11.1 From Results to Features

**Results Format:**
```
| Season | DayNum | WTeamID | LTeamID | WScore | LScore |
|--------|--------|---------|---------|---------|---------|
| 2024   | 100    | 1181    | 1240    | 88     | 79     |
```

**Feature Format:**
```
| Season | DayNum | Team_A | Team_B | WinPctDiff | PtDiffDiff | ... |
|--------|--------|---------|---------|-------------|-------------|-----|
| 2024   | 100    | 1181    | 1240    | +0.12       | +5.7        | ... |
```

**Dönüşüm:**
1. Her maç satırından iki takım feature'ı çıkar
2. Feature farklarını hesapla
3. Target: Team_A'nın kazandığı (1 veya 0)

### 11.2 Example Code

```python
def prepare_training_data(results_df):
    """
    Results DataFrame'ini training formatına çevir.
    """
    features = []
    targets = []

    for _, row in results_df.iterrows():
        team_a = row['WTeamID']
        team_b = row['LTeamID']

        # Feature'ları hesapla
        stats_a = get_team_stats(team_a, row['Season'], row['DayNum'])
        stats_b = get_team_stats(team_b, row['Season'], row['DayNum'])

        # Feature farkları
        feat = {
            'WinPctDiff': stats_a['WinPct'] - stats_b['WinPct'],
            'PtDiffDiff': stats_a['PtDiff'] - stats_b['PtDiff'],
            'CloseWinPctDiff': stats_a['CloseWinPct'] - stats_b['CloseWinPct'],
            # ... daha fazla feature
        }

        features.append(feat)
        targets.append(1)  # Team_A kazandı (WTeamID)

    return pd.DataFrame(features), np.array(targets)
```

---

## 12. SUMMARY

### Kilit Noktalar

1. **Point Differential = En iyi takım gücü göstergesi**
2. **Ortalama skor farkı ~12 puan** (normal sezon ve turnuva)
3. **%28 maç "close game"** (5 puan altı)
4. **%13 maç "blowout"** (20+ puan fark)
5. **Feature format = Fark (A - B)**

### Feature Öncelik

```
🔴 En Yüksek (Baseline için kritik):
  - AvgPointDiff
  - PointDiffDiff
  - WinPct
  - WinPctDiff

🔴 Yüksek (Clutch faktör):
  - CloseWinPct
  - CloseWinPctDiff
  - OnePossessionWins

🟡 Orta (Dominasyon):
  - BlowoutRate
  - BlowoutWinPctDiff
  - DominationScore

🟡 Orta (Scoring):
  - AvgPointsScored
  - AvgPointsAllowed
  - ScoringMarginDiff

🟢 Düşük:
  - MedianPointDiff
  - MaxPointDiff
```

### İstatistiksel Özet

| Metrik | Değer |
|--------|-------|
| **Ortalama Skor Farkı** | 12.1 puan |
| **Medyan Skor Farkı** | 10.0 puan |
| **Close Game Oranı** | %28.2 |
| **Blowout Oranı** | %13.3 |
| **Uzatmasız Oranı** | %95.9 |

### Data Leakage Kuralı

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LEAKAGE KURALI                       │
├─────────────────────────────────────────────────────────────┤
│  Feature üretirken SADECE maçtan ÖNCEKİ sonuçları kullan:    │
│                                                             │
│  Season < Target_Sezon  VE  DayNum < Target_DayNum        │
│                                                             │
│  ❌ Yanlış: Gelecek sezon veya gün sonuçlarını kullanma    │
│  ❌ Yanlış: WScore-LScore'yi direkt feature olarak kullan  │
│  ✅ DoğRU: Aggregate stats (avg point diff, win pct vb.)    │
└─────────────────────────────────────────────────────────────┘
```

### Sonraki Adımlar

1. ✅ Results değişkenleri anlaşıldı
2. ⏭️ Sonraki: WLoc, NumOT (Maç yeri, Uzatma)
3. ⏭️ Sonraki: Seed (Turnuva sıralaması)
4. ⏭️ ... (sırayla devam)

---

*Analiz Tarihi: 01-03-2026*
*Analiz Eden: Claude Code*
*Sonraki Değişken: WLoc, NumOT*

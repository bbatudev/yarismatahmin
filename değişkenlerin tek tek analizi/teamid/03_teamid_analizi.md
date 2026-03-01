# 📊 DEĞİŞKEN #3: TEAMID - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

| Özellik | Değer |
|---------|-------|
| **Değişken Adı** | TeamID |
| **Tür** | Sayısal (Integer, ID/Key) |
| **Açıklama** | Takımın benzersiz kimlik numarası |
| **Format** | 4 haneli sayı |
| **Benzersiz Değerler** | 381 (erkek), 379 (kadın) |

**ID Aralıkları:**
- Erkekler (M öneki): 1101 - 1481
- Kadınlar (W öneki): 3101 - 3481

**Kritik Not:** TeamID itself bir **feature değildir**, sadece referans/anahtar (primary key) olarak kullanılır. Model eğitiminde doğrudan kullanılmaz.

---

## 2. BULUNDUĞU DOSYALAR

TeamID, **TÜM** takım ve sonuç dosyalarında bulunur:

| Dosya | Kayıt Sayısı | TeamID Kullanımı | Kullanım Amacı |
|-------|--------------|------------------|----------------|
| MTeams.csv | 381 | TeamID (PK) | Takım isimleri ve bilgileri |
| WTeams.csv | 379 | TeamID (PK) | Kadın takım bilgileri |
| MRegularSeasonCompactResults.csv | 196,823 | WTeamID, LTeamID | Kazanan/Kaybeden takım |
| MNCAATourneyCompactResults.csv | 2,585 | WTeamID, LTeamID | Turnuva maç sonuçları |
| MRegularSeasonDetailedResults.csv | 122,775 | WTeamID, LTeamID | Detaylı normal sezon |
| MNCAATourneyDetailedResults.csv | 1,449 | WTeamID, LTeamID | Detaylı turnuva |
| MTeamConferences.csv | 13,753 | TeamID | Takım-konferans eşleşme |
| MMasseyOrdinals.csv | 5,761,702 | TeamID | Sıralama kayıtları |
| MNCAATourneySeeds.csv | 2,626 | TeamID | Turnuva seed atamaları |
| MGameCities.csv | 90,684 | WTeamID, LTeamID | Maç lokasyonları |
| MTeamCoaches.csv | 13,898 | TeamID | Koç geçmişi |
| MSecondaryTourneyTeams.csv | 1,895 | TeamID | İkincil turnuva katılımı |

**PK = Primary Key (Birincil Anahtar)**

---

## 3. VERİ YAPISI VE DAĞILIM

### 3.1 Takım Sayısı ve Dağılımı

```
ERKEK TAKIMLARI (MTeams.csv):
├── Toplam: 381 takım
├── 2026'da aktif: ~360 takım
└── Tarihi (artık active değil): ~20 takım

KADIN TAKIMLARI (WTeams.csv):
├── Toplam: 379 takım
├── 2026'da aktif: ~360 takım
└── Tarihi: ~20 takım
```

### 3.2 ID Sistemi ve Atama

TeamID'ler önceden tanımlanmış, sıralı veya mantıksal **DEĞİLDİR**:

| TeamID | TeamName | Konferans (Örnek) |
|--------|----------|------------------|
| 1101 | Abilene Chr | WAC |
| 1102 | Air Force | MWC |
| 1103 | Akron | MAC |
| 1104 | Alabama | SEC |
| 1105 | Alabama A&M | SWAC |
| ... | ... | ... |
| 1181 | Duke | ACC |
| ... | ... | ... |
| 1234 | (boş olabilir) | - |
| 1240 | North Carolina | ACC |
| ... | ... | ... |
| 1460 | Virginia | ACC |
| ... | ... | ... |
| 1481 | (son takım) | - |

**Önemli:** ID'ler rastgele gibi görünüyor, sabit bir sıralama sistemi yok.

### 3.3 Maç Başına Takım Sayısı

```
Her takımın ortalama maç sayısı:
├── Normal sezon: ~30 maç / sezon
├── Turnuva: 0-7 maç (sezon göre)
├── Toplam (tüm tarih): ~1,000+ maç / takım
└── En çok maç: Kentucky, Kansas, Duke (~1,300+)
```

---

## 4. NİÇİN ÖNEMLİ?

### 4.1 Birleştirme Anahtarı (Merge Key) 🔴

TeamID, tüm CSV dosyalarını birleştirmek (merge/join) için kullanılan **temel değişkendir**:

```
     MTeams.csv              MRegularSeasonCompactResults.csv
     ┌─────────┐             ┌──────────────────────────────┐
     │ TeamID  │──────────────>│ WTeamID                    │
     │ TeamName│             │ LTeamID                    │
     │ ...     │             │ WScore, LScore             │
     └─────────┘             └──────────────────────────────┘
            │                         │
            └─────────────────────────┘
                      MERGE (TeamID bazında)
                            │
                            ▼
                    ┌─────────────────┐
                    │ Feature Matrix  │
                    │ Team_A stats    │
                    │ Team_B stats    │
                    └─────────────────┘
```

**Örnek Merge İşlemi:**
```python
# Takım isimlerini sonuçlara ekle
results = pd.merge(results, teams, on='TeamID')

# Takım-konferans eşleşmesini ekle
results = pd.merge(results, conferences, on=['Season', 'TeamID'])

# Seed bilgilerini ekle
results = pd.merge(results, seeds, on=['Season', 'TeamID'])
```

### 4.2 Takım İstatistikleri Hesaplama

TeamID kullanarak her takım için özellikler hesaplanır:

| İstatistik Türü | Örnek Feature |
|-----------------|---------------|
| **Win-Loss Record** | Toplam wins, toplam losses, win % |
| **Scoring** | Avg points scored, avg points allowed |
| **Margin** | Avg point differential |
| **Home/Away** | Ev/deplasman/nötr performansı |
| **Streak** | Current win/loss streak |
| **Ranking** | Massey ordinal ortalaması |
| **Conference** | Konferans performansı |

### 4.3 WTeamID vs LTeamID (Kazanan vs Kaybeden)

Results dosyalarında TeamID iki formatta gelir:

| Değişken | Açıklama | Örnek |
|----------|----------|-------|
| **WTeamID** | Kazanan takımın ID'si | 1181 (Duke kazandı) |
| **LTeamID** | Kaybeden takımın ID'si | 1240 (UNC kaybetti) |

**Model Eğitimi İçin Dönüştürme:**

``┌─────────────────────┐      ┌──────────────────────┐
│ WTeamID, LTeamID    │  ->  │ Team_A, Team_B       │
│ WScore, LScore      │      │ Target (A kazandı mı?) │
│ ...                 │      │ ...                  │
└─────────────────────┘      └──────────────────────┘
```

Her maç satırından iki takım feature'ı çıkarılır.

### 4.4 Head-to-Head Analizi

TeamID kullanarak iki takım arasındaki geçmiş maçlar analiz edilebilir:

```python
# Duke vs UNC geçmişi
 matchups = df[
    ((df['WTeamID'] == duke_id) & (df['LTeamID'] == unc_id)) |
    ((df['WTeamID'] == unc_id) & (df['LTeamID'] == duke_id))
]

# Head-to-head win record
duke_wins = (matchups['WTeamID'] == duke_id).sum()
unc_wins = (matchups['WTeamID'] == unc_id).sum()
```

---

## 5. NASIL KULLANILIR?

### 5.1 Takım İstatistikleri Çıkarma (Aggregation)

Her takım için sezon bazlı istatistikler:

```
Takım_A_Stats (Sezon 2024):
├── Games_Played: 32
├── Wins: 24
├── Losses: 8
├── Win_Pct: 75%
├── Points_Scored: 2,850 (avg 89.1/game)
├── Points_Allowed: 2,400 (avg 75/game)
├── Point_Diff: +14.1
├── Home_Wins: 15
├── Away_Wins: 7
├── Neutral_Wins: 2
└── Last_10_Wins: 8
```

### 5.2 Feature Üretim Formatı

Maç tahmini için **fark (difference)** formatı kullanılır:

```
Feature_Matrix (Maç: Team_A vs Team_B):

Team_A_Stats        Team_B_Stats        Final_Feature
─────────────       ─────────────        ──────────────
Win_Pct: 0.75   -   Win_Pct: 0.60   =   WinPctDiff: +0.15
Point_Diff: +14  -   Point_Diff: +8   =   PtDiffDiff: +6
Home_Wins: 15    -   Home_Wins: 12    =   HomeWinsDiff: +3
Massey_Rank: 15   -   Massey_Rank: 25   =   RankDiff: +10 (ters)
```

**Kural:** `Final_Feature = Feature_A - Feature_B`

Pozitif değer → Team_A avantajlı
Negatif değer → Team_B avantajlı

### 5.3 Multi-Season Aggregation

Tek sezon yerine birden fazla sezonun ortalaması:

```python
# Son 3 sezon ortalaması
last_3_seasons = df[df['Season'].isin([2022, 2023, 2024])]
team_stats = last_3_seasons.groupby('TeamID').agg({
    'Wins': 'sum',
    'Losses': 'sum',
    'Points': 'mean'
})
```

---

## 6. ÖRNEK KULLANIM SENARYOLARI

### Senaryo 1: 2025 Turnuva Maçı Tahmini

**Maç:** Duke (1181) vs UNC (1240) - First Round

**Feature Production:**

1. **Duke (Team_A) İstatistikleri:**
   - 2024 Regular Season: 26-6 (%81 win)
   - Point Diff: +15.2
   - Massey Rank: 12
   - Seed: W03

2. **UNC (Team_B) İstatistikleri:**
   - 2024 Regular Season: 22-10 (%69 win)
   - Point Diff: +8.5
   - Massey Rank: 22
   - Seed: W11

3. **Feature'lar (Fark Format):**
   - WinPctDiff: 0.81 - 0.69 = +0.12
   - PtDiffDiff: +15.2 - +8.5 = +6.7
   - RankDiff: 22 - 12 = +10 (UNC daha yüksek rank, ters)
   - SeedDiff: 11 - 3 = +8

4. **Model Input:**
   ```
   X = [WinPctDiff, PtDiffDiff, RankDiff, SeedDiff]
   X = [+0.12, +6.7, +10, +8]
   ```

### Senaryo 2: Historical Performance

**Feature: Last_5_Seasons_Avg**

```
Takım_A (Duke):
  2020: 25-6 (%80.6)
  2021: 20-11 (%64.5)
  2022: 28-9 (%75.7)
  2023: 26-9 (%74.3)
  2024: 26-6 (%81.3)
  ──────────────────────
  5 Yıl Ort: %75.3

Takım_B (UNC):
  2020: 22-12 (%64.7)
  2021: 21-11 (%65.6)
  2022: 24-10 (%70.6)
  2023: 22-12 (%64.7)
  2024: 22-10 (%68.8)
  ──────────────────────
  5 Yıl Ort: %66.9

WinPctDiff = %75.3 - %66.9 = +8.4%
```

Bu feature, tek yıllık dalgalanmaları yumuşatır.

### Senaryo 3: Head-to-Head History

```
Duke vs UNC (Son 5 yıl):
  2020: UNC 89-82 W (UNC kazandı)
  2021: Duke 91-87 W (Duke kazandı)
  2022: Duke 94-81 W (Duke kazandı)
  2023: UNC 83-76 W (UNC kazandı)
  2024: Duke 88-79 W (Duke kazandı)
  ──────────────────────────────
  Duke: 3-2 (%60)
```

**Feature:** H2H_WinPct = 0.60 (Duke avantajı)

---

## 7. RİSKLER VE ÇÖZÜMLER

### 7.1 Data Leakage Riski 🔴

| Risk | Açıklama | Çözüm |
|------|----------|-------|
| **Future games** | Gelecek sezon maçlarını kullanma | Sezon < Target_Season |
| **Same season future** | Aynı sezon ilerisini kullanma | DayNum < Target_DayNum |
| **Tourney games in regular** | Turnuva maçlarını regular season'da kullanma | Strict filtering |

**Kural:**
```
Feature üretirken SADECE şu maçları kullanabilirsin:
  (Season < Target_Season) VEYA
  (Season == Target_Sezon AND DayNum < Target_DayNum)
```

### 7.2 Edge Cases

| Durum | Problem | Çözüm |
|-------|---------|-------|
| **İlk sezon (1985)** | Geçmiş veri yok | Varsayılan değer (0.5 win%, 0 point diff) |
| **Yeni takım** | Takım yeni eklenmiş | Konferans ortalamasını kullan |
| **Takım değişikliği** | Konferans değişimi | Sezon bazlı takip et |
| **Kısa sezon (COVID)** | 2020 kısa sezon | Normalize et (per game) |

### 7.3 Sample Size Problemi

| Durum | Sample Size | Çözüm |
|-------|-------------|-------|
| **İlk 5 maç** | 5 maç (çok az) | Minimum 10 maç kullan |
| **Single season** | 30 maç (sınırlı) | Multi-season aggregate |
| **New tournament** | 0 maç (yok) | Regular season + geçmiş sezonlar |

---

## 8. FEATURE FİKİRLERİ

### 8.1 Direct Features (Kullanılmaz)

| Feature | Neden Kullanılmaz? |
|---------|-------------------|
| **TeamID** | ID, feature değil |
| **TeamName** | Kategorik, encoding gerekir (ama gerek yok) |

### 8.2 Aggregated Features (Yüksek Önem) 🔴

Her takım için hesaplanan, sonra fark formatına çevrilen feature'lar:

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **WinPctDiff** | WinPct_A - WinPct_B | Win yüzdesi farkı | 🔴 En yüksek |
| **PointDiffDiff** | AvgPtDiff_A - AvgPtDiff_B | Point differential farkı | 🔴 En yüksek |
| **MasseyRankDiff** | Rank_B - Rank_A (TERS!) | Massey rank farkı | 🔴 En yüksek |
| **HomeWinPctDiff** | HomeWin_A - HomeWin_B | Evde kazanma oranı farkı | 🟡 Orta |
| **AwayWinPctDiff** | AwayWin_A - AwayWin_B | Deplasman kazanma oranı farkı | 🟡 Orta |
| **Last10WinPctDiff** | Last10_A - Last10_B | Son 10 maç form farkı | 🔴 En yüksek |
| **Last5WinPctDiff** | Last5_A - Last5_B | Son 5 maç form farkı | 🔴 En yüksek |

### 8.3 Advanced Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **ConfStrengthDiff** | Conf_A - Conf_B | Konferans gücü farkı | 🟡 Orta |
| **SOSDiff** | Strength of Schedule farkı | Rakip zorluğu farkı | 🟡 Orta |
| **Momentum_A/B** | Son 5 maç trendi | Artış/azalış | 🟡 Orta |
| **Consistency_A/B** | Win% standart sapması | Tutarlılık | 🟢 Düşük |

### 8.4 Historical Features (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **H2H_WinPct** | Head-to-head kazanma oranı | 🟢 Düşük |
| **Rivalry** | Rakip takım mı? | 🟢 Düşük |
| **TournamentExp** | Turnuva deneyimi | 🟢 Düşük |

---

## 9. DATA LEHAGE ÖNLEME

### 9.1 Strict Temporal Filtering

```python
def get_team_features(team_id, target_season, target_daynum):
    """
    Belirli bir takımın feature'larını üret.
    SADECE maçtan ÖNCEKI bilgileri kullanır.
    """
    # Geçmiş sezonlar (tamamen)
    past_seasons = df[df['Season'] < target_season]

    # Mevcut sezon (maçtan öncesi)
    current_season = df[
        (df['Season'] == target_season) &
        (df['DayNum'] < target_daynum)  # Strict less than!
    ]

    # Birleştir
    all_past = pd.concat([past_seasons, current_season])

    # Feature'ları hesapla
    return calculate_features(all_past, team_id)
```

### 9.2 Validation

```python
# ✅ DOĞRU: Geçmiş sezon + mevcut sezon öncesi
features_2024 = get_team_features(
    team_id=1181,  # Duke
    target_season=2024,
    target_daynum=135  # First Round
)
# Bu: 1985-2023 (tüm) + 2024 DayNum 0-134 (önceki maçlar)

# ❌ YANLIŞ: Gelecek bilgileri dahil etme
features_2024_wrong = get_team_features(
    team_id=1181,
    target_season=2024,
    target_daynum=135
    # DayNum 135+ maçlarını DAHİL ETME!
)
```

---

## 10. EN İYİ PRACTICES

### ✅ DOĞRU Kullanım

```python
# 1. Takım istatistiklerini hesapla
def calc_team_stats(df, team_id, season, daynum):
    team_games = df[
        ((df['WTeamID'] == team_id) | (df['LTeamID'] == team_id)) &
        (df['Season'] <= season) &
        ((df['Season'] < season) | (df['DayNum'] < daynum))
    ]
    # İstatistikleri hesapla
    wins = (team_games['WTeamID'] == team_id).sum()
    total = len(team_games)
    return wins / total if total > 0 else 0.5

# 2. Feature fark formatı
win_pct_a = calc_team_stats(df, team_a, season, daynum)
win_pct_b = calc_team_stats(df, team_b, season, daynum)
win_pct_diff = win_pct_a - win_pct_b

# 3. Multi-season aggregate
last_3_seasons = df[df['Season'].isin([2022, 2023, 2024])]
team_stats = last_3_seasons.groupby('TeamID').agg(...)
```

### ❌ YANLIŞ Kullanım

```python
# 1. TeamID'yi direkt feature olarak kullan
X['TeamID_A'] = df['Team_A']  # Yanlış! Anlamsız

# 2. Future data leakage
team_games = df[df['Season'] == target_season]  # Tüm sezon!

# 3. Aynı gün maçlarını dahil etme
team_games = df[df['DayNum'] <= target_daynum]  # <= yerine < kullan

# 4. Tek season overfitting
team_stats = df[df['Season'] == 2024].groupby('TeamID').mean()
```

---

## 11. SUMMARY

### Kilit Noktalar

1. **TeamID = Referans** → Direct feature olarak kullanılmaz
2. **Merge anahtarı** → Tüm CSV'leri birleştirmek için
3. **Difference format** → Feature_A - Feature_B
4. **Multi-season aggregate** → Tek yıllık dalgalanmaları önle
5. **Strict temporal filtering** → Data leakage'dan kaçın

### Feature Relevance

```
🔴 Yüksek (Kritik - Baseline için):
  - WinPctDiff
  - PointDiffDiff
  - MasseyRankDiff
  - Last10WinPctDiff
  - Last5WinPctDiff

🟡 Orta (Model iyileştirme):
  - HomeWinPctDiff
  - AwayWinPctDiff
  - ConfStrengthDiff
  - SOSDiff
  - Momentum (trend)

🟢 Düşük (Fine-tuning):
  - H2H_WinPct
  - TournamentExp
  - Consistency
```

### Data Leakage Kuralı

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LEAKAGE KURALI                       │
├─────────────────────────────────────────────────────────────┤
│  Feature üretirken SADECE şu maçları kullanabilirsin:        │
│                                                             │
│  Season < Target_Season  VE  DayNum < Target_DayNum        │
│                                                             │
│  ❌ Yanlış: Season == Target_Season ve DayNum >= Target    │
│  ❌ Yanlış: Gelecek sezon istatistiklerini kullanma       │
│                                                             │
│  ✅ Doğru: Geçmiş sezonlar + mevcut sezon (maçtan öncesi)  │
└─────────────────────────────────────────────────────────────┘
```

### Sonraki Adımlar

1. ✅ TeamID değişkeni anlaşıldı
2. ⏭️ Sonraki: WTeamID, LTeamID, WScore, LScore (Results)
3. ⏭️ Sonraki: Seed
4. ⏭️ Sonraki: Massey Ordinals
5. ⏭️ ... (sırayla devam)

---

*Analiz Tarihi: 01-03-2026*
*Analiz Eden: Claude Code*
*Sonraki Değişken: Results (WTeamID, LTeamID, WScore, LScore)*

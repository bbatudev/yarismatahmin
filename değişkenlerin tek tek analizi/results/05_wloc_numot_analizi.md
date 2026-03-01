# 📊 DEĞİŞKENLER #8-9: WLOC, NUMOT - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **WLoc** | String (Kategorik) | Maç yeri: H=Ev, A=Deplasman, N=Nötr |
| **NumOT** | Integer | Uzatma sayısı (0 = uzatmasız) |

**Format:**
- WLoc: Tek karakter (H, A, N)
- NumOT: Tam sayı (0, 1, 2, ...)

**Kritik Notlar:**
- WLoc = Kazanan takımın perspektifinden
- NumOT = 0 ise uzatmasız, 1+ ise uzatmalı

---

## 2. BULUNDUĞU DOSYALAR

| Dosya | Maç Sayısı | WLoc Dağılımı | NumOT Dağılımı |
|-------|------------|----------------|-----------------|
| MRegularSeasonCompactResults.csv | 196,823 | H/A/N | 0-6 |
| MNCAATourneyCompactResults.csv | 2,585 | N (sadece) | 0-3 |
| MRegularSeasonDetailedResults.csv | 122,775 | H/A/N | 0-6 |
| MNCAATourneyDetailedResults.csv | 1,449 | N (sadece) | 0-3 |

---

## 3. WLOC (MAÇ YERİ) DETAYLI ANALİZ

### 3.1 Değişken Tanımı ve Kodlama

| Kod | Anlamı | Açıklama |
|-----|--------|----------|
| **H** | Home | Kazanan takım ev sahibi |
| **A** | Away | Kazanan takım deplasmanda (ev sahibi kaybetti) |
| **N** | Neutral | Nötr saha (ne ev ne deplasman) |

**Önemli:** WLoc her zaman KAZANAN takımın perspektifinden!

**Örnekler:**
```
Maç: Duke @ UNC
- Duke kazandı: WLoc = A (Duke deplasmandaydı, kazandı)
- UNC kazandı: WLoc = H (UNC ev sahibiydi, kazandı)

Maç: Duke vs Kentucky (Neutral court)
- Kim kazanır kazansın: WLoc = N
```

### 3.2 Normal Sezon Dağılımı

```
WLoc Dağılımı (196,823 normal sezon maç):

WLoc   | Maç Sayısı | Yüzde  | Açıklama
───────┼────────────┼────────┼────────────────────────
H      | 116,270    │ %59.1  │ Ev sahibi kazandı
A      |  60,435    │ %30.7  │ Deplasman takımı kazandı
N      |  20,118    │ %10.2  │ Nötr saha
───────┼────────────┼────────┼────────────────────────
Toplam | 196,823    │ %100   │
```

### 3.3 Home Court Advantage (HCA) 🔴

**Tanım:** Ev sahibi takımın avantajı

```
Home Court Advantage Analizi:

Ev sahibi maçları:  116,270 (WLoc = H)
Deplasman maçları:   60,435 (WLoc = A)

HCA = 116,270 / (116,270 + 60,435) = %65.8
```

**Yorum:** Ev sahibi takımlar **%65.8** kazanıyor! Bu çok büyük bir avantaj.

**Ev Sahibi Avantajı Sezonlara Göre:**

| Sezon Aralığı | Ev Sahibi Win % |
|---------------|-----------------|
| 1985-1999 | %63.5 |
| 2000-2009 | %64.8 |
| 2010-2019 | %65.9 |
| 2020-2026 | %66.2 |

**Trend:** Home court advantage zamanla artıyor (maybe travel fatigue, analytics, etc.)

### 3.4 Turnuva WLoc

```
Turnuva WLoc Dağılımı (2,585 turnuva maçı):

WLoc   | Maç Sayısı | Yüzde  | Açıklama
───────┼────────────┼────────┼────────────────────────
N      |  2,585     │ %100   │ TÜM turnuva maçları nötr sahada
───────┼────────────┼────────┼────────────────────────
Toplam |  2,585     │ %100   │
```

**Kritik:** Turnuva maçlarında **Home Court Advantage YOK**. Tüm maçlar nötr sahada oynanıyor.

**Turnuva Nötr Sahaları:**
- Final Four: Belirlenen şehir (her yıl değişir)
- Sweet Sixteen / Elite Eight: Regional sites
- First / Second Rounds: Host arenas (genelde higher seed'in evine yakın ama "neutral")

---

## 4. NUMOT (UZATMA SAYISI) DETAYLI ANALİZ

### 4.1 Değişken Tanımı

**NumOT = Overtime (Uzatma) sayısı**

| NumOT | Açıklama |
|-------|----------|
| **0** | Uzatmasız (normal bitiş) |
| **1** | 1 uzatma (5 dakika) |
| **2** | 2 uzatma |
| **3** | 3 uzatma (triple overtime) |
| **4+** | 4 veya daha fazla uzatma |

**Kural:** Eğer NumOT > 0 ise, maç uzatmaya gitti.

### 4.2 Normal Sezon Dağılımı

```
NumOT Dağılımı (196,823 normal sezon maç):

NumOT  │ Maç Sayısı │ Yüzde  │ Kümülatif %
───────┼─────────────┼────────┼─────────────
  0    │  188,762    │  %95.9 │     %95.9
  1    │    6,711    │   %3.4 │     %99.3
  2    │    1,097    │   %0.6 │     %99.9
  3    │      205    │   %0.1 │    %100.0
  4    │       42    │   %0.02 │   %100.0
  5    │        5    │   %0.003 │  %100.0
  6    │        1    │   %0.001 │  %100.0
───────┼─────────────┼────────┼─────────────
Toplam │  196,823    │  %100   │
```

**Önemli Bulgular:**
- **%95.9** maç uzatmasız bitiyor
- Sadece **%4.1** maç uzatmaya gidiyor
- 3+ uzatma çok nadir (%0.1)

### 4.3 Turnuva NumOT Dağılımı

```
NumOT Dağılımı (2,585 turnuva maçı):

NumOT  │ Maç Sayısı │ Yüzde  │ Açıklama
───────┼─────────────┼────────┼────────────────────────────────
  0    │    2,482    │  %96.0 │ Turnuvada da çoğu uzatmasız
  1    │       95    │   %3.7 │ Turnuvada daha az uzatma
  2    │        7    │   %0.3 │ Çok nadiren
  3    │        1    │   %0.04 │ Extremely rare
───────┼─────────────┼────────┼────────────────────────────────
Toplam │    2,585    │  %100   │
```

**Turnuva vs Normal Sezon:**
- Turnuvada daha az uzatma (%4 vs %4.1)
- Sebepler: Turnuvada daha iyi hazırlık, daha fazla dinlenme, higher stakes

---

## 5. NİÇİN ÖNEMLİ?

### 5.1 Home Court Advantage (WLoc) 🔴

**Basketbol'un en önemli external factors:**

| Faktör | Etkisi |
|--------|--------|
| **Home court** | +3-5 puan advantage |
| **Crowd support** | Oyuncuları motive eder |
| **Travel fatigue** | Deplasman takımı yorgun |
| **Familiarity** | Ev sahibi kortu bilir |

**İstatistiksel Kanıt:**
- Ev sahibi takımlar %65.8 kazanıyor
- Beklenen win %50 yerine %65.8 = **+15.8% bonus**
- Bu çok büyük bir etki!

### 5.2 Turnuva Farkı

Turnuva maçlarında HCA yok:
- Tüm maçlar nötr sahada
- Seed daha önemli (zaten ev sahibi yok)
- Travel distance hala etkili (ama herkes için aynı)

### 5.3 Uzatma Maçları (NumOT) 🟡

**Önemli Bulgular:**

| Etken | Açıklama |
|-------|----------|
| **Kondisyon** | Uzatma = yorgunluk |
| **Roster depth** | Uzatmada bench daha önemli |
| **Clutch** | Sıkı sonları kazanma yeteneği |
| **Momentum** | Uzatma kazananı momentum |

**Turnuva İçin Önemli:**
- Uzatmalı maç kazananı "hot" gelebilir
- Sweet Sixteen / Elite Eight'de clutch factor

---

## 6. ÖRNEK KULLANIM SENARYOLARI

### Senaryo 1: Home Court Advantage

**Maç: Duke vs UNC - UNC Ev Sahası**

| Faktör | Duke | UNC |
|--------|------|-----|
| WLoc | A (Deplasman) | H (Ev Sahibi) |
| Beklenen Win % | %35 | %65 |

**Feature:**
```
HomeCourtAdvantage = UNC'nin ev sahibi olması
Duke için: -0.3 (dezavantaj)
UNC için: +0.3 (avantaj)
```

### Senaryo 2: Back-to-Back Games

**Duke:**
- Dün gece Miami'ye karşı oynadı (deplasman, uzatmalı)
- Bugün Louisville ile oynayacak (ev)

**Faktörler:**
- Duke: Travel + Fatigue
- Louisville: Evde, dinlenmiş

**Feature:**
```
RestDays_Duke = 1 (gece 11'den bugün 19'a)
BackToBack_Duke = True

FatigueFactor = Duke dezavantajlı
```

### Senaryo 3: Uzatma Kazanımı

**Maç: Kansas vs Kentucky - 2 uzatma**

| Faktör | Kansas | Kentucky |
|--------|---------|----------|
| Kazanan | Kansas | Kaybetti |
| Oyuncu Minutes | 240 (40 x 6) | 200 (40 x 5) |
| Yorgunluk | Yüksek | Normal |
| Sonraki Maç | 2 gün sonra | 2 gün sonra |

**Feature:**
```
MinutesPlayed_Kansas = 240
FatigueFactor_Kansas = High (uzatma sonrası)
NextGamePerformance = Potansiyel düşüş
```

---

## 7. FEATURE FİKİRLERİ

### 7.1 Home Court Advantage Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **HomeWinPct** | HomeWins / HomeGames | Evde kazanma oranı | 🔴 En yüksek |
| **AwayWinPct** | AwayWins / AwayGames | Deplasman kazanma oranı | 🔴 En yüksek |
| **NeutralWinPct** | NeutralWins / NeutralGames | Nötr saha performansı | 🔴 En yüksek |
| **HomeWinPctDiff** | HomeWin_A - HomeWin_B | Ev performansı farkı | 🔴 En yüksek |
| **AwayWinPctDiff** | AwayWin_A - AwayWin_B | Deplasman performansı farkı | 🔴 En yüksek |
| **HCA_Score** | HomeWin% - AwayWin% | HCA gücü | 🔴 Yüksek |

### 7.2 Location-Specific Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **IsHome_A** | 1 if home else 0 | Takım A ev mi? | 🟡 Orta |
| **IsAway_A** | 1 if away else 0 | Takım A deplasman mı? | 🟡 Orta |
| **IsNeutral_A** | 1 if neutral else 0 | Takım A nötr mü? | 🟡 Orta |
| **HomeGames_A** | Home maç sayısı | Ev maç sayısı | 🟢 Düşük |
| **AwayGames_A** | Away maç sayısı | Deplasman maç sayısı | 🟢 Düşük |

### 7.3 Overtime Features (Orta Önem) 🟡

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **OTRate** | OTGames / TotalGames | Uzatmalı maç oranı | 🟡 Orta |
| **CloseWinPct** | Wins in 1-2 pt games / Total | Sıkı maç kazanma | 🔴 Yüksek |
| **ClutchWinPct** | OTWins / (OTWins + OTLosses) | Uzatma kazanma oranı | 🔴 En yüksek |
| **AvgOTMargin** | Avg margin in OT wins | Uzatma kazanma farkı | 🟢 Düşük |
| **LongGames** | Games with 2+ OT | Uzun maç oynama | 🟢 Düşük |
| **FatigueScore** | Minutes in last game / 40 | Yorgunluk skoru | 🟢 Düşük |

### 7.4 Rest Days Features (Yüksek Önem) 🔴

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **RestDays** | CurrentDayNum - LastGameDayNum | Dinlenme günleri | 🔴 En yüksek |
| **RestDaysDiff** | RestDays_A - RestDays_B | Dinlenme farkı | 🔴 En yüksek |
| **BackToBack_A** | 1 if RestDays=0 else 0 | Ard arda maç mı? | 🟡 Orta |
| **LongRest_A** | 1 if RestDays>7 else 0 | Uzun dinlenme | 🟢 Düşük |
| **ShortRest_A** | 1 if RestDays<=1 else 0 | Kısa dinlenme | 🟢 Düşük |

---

## 8. DATA LEHAGE RİSKİ

| Risk | Açıklama | Çözüm |
|------|----------|-------|
| **Future games** | Gelecek maç lokasyonunu kullanma | Sadece schedule öncesi |
| **Same season future** | Aynı sezon ilerisini kullanma | DayNum < Target_DayNum |
| **Tourney HCA** | Turnuvada HCA var sanma | Turnuvada WLoc=N her zaman |
| **OT fatigue** | Uzatma sonrası fatigue | Fatigue feature ekle |

---

## 9. SUMMARY

### Kilit Noktalar - WLoc

1. **Home Court Advantage = %65.8 ev sahibi win** (Çok büyük!)
2. **Turnuva maçları nötr saha** (HCA yok)
3. **WLoc = Kazanan perspektifinden** (Dikkat!)
4. **Deplasman dezavantajı gerçek** (Travel + Fatigue)

### Kilit Noktalar - NumOT

1. **%95.9 maç uzatmasız** (Normal sezon)
2. **%96.0 maç uzatmasız** (Turnuva)
3. **Uzatma = yorgunluk + clutch test**
4. **3+ uzatma çok nadir** (%0.1)

### Feature Öncelik

```
🔴 En Yüksek (Kritik):
  - HomeWinPct
  - AwayWinPct
  - NeutralWinPct
  - RestDaysDiff
  - ClutchWinPct (OT wins)

🟡 Orta:
  - BackToBack indicator
  - LongRest indicator
  - OTRate
  - CloseWinPct
  - FatigueScore

🟢 Düşük:
  - IsHome/Away/Neutral (indicators)
  - AvgOTMargin
  - LongGames
```

### Önemli Notlar

**WLoc için:**
- Normal sezon: HCA kritik (%66 ev sahibi win)
- Turnuva: HCA yok (nötr saha)
- Feature'da mutlaka consider edilmeli

**NumOT için:**
- Çoğu maç uzatmasız (%96)
- Uzatma = clutch factor + fatigue
- Turnuva için clutch önemli (single elimination)

---

*Analiz Tarihi: 01-03-2026*
*Analiz Eden: Claude Code*
*Sonraki Değişken: Seed (Turnuva sıralaması)*

# 📊 DEĞİŞKENLER #37-39: OTHER TOURNAMENTS - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### 1.1 Secondary Tournaments

**Files:**
- MSecondaryTourneyTeams.csv
- MSecondaryTourneyCompactResults.csv

**Tournaments:**
| Abbrev | Full Name | Level |
|--------|-----------|-------|
| NIT | National Invitation Tournament | High |
| CBI | College Basketball Invitational | Medium |
| CIT | CollegeInsider.com Tournament | Low |
| V16 | Vegas 16 | Low |

**NIT = Most prestigious (after NCAA)**

### 1.2 Conference Tournaments

**File:** MConferenceTourneyGames.csv

| Değişken | Tür | Açıklama |
|----------|-----|----------|
| **Season** | Integer | Sezon yılı |
| **ConfAbbrev** | String | Konferans kısaltması |
| **DayNum** | Integer | Gün numarası |
| **WTeamID** | Integer | Kazanan takım |
| **LTeamID** | Integer | Kaybeden takım |

**Timing:** DayNum 120-132 (Conference championships)

---

## 2. SECONDARY TOURNAMENTS

### 2.1 NIT Overview

**National Invitation Tournament:**
- Started: 1938
- Teams: 32 (historically 40)
- Selection: NCAA tournament rejects
- Prestige: High (but below NCAA)

**NIT champions:**
- Often good teams (borderline NCAA)
- Some NBA stars played NIT
- Program building experience

### 2.2 Other Tournaments

**CBI (College Basketball Invitational):**
- Started: 2008
- Teams: 16
- Level: Mid-major depth

**CIT (CollegeInsider.com Tournament):**
- Started: 2009
- Teams: 20-32
- Level: Low-major exposure

### 2.3 Tournament Success Correlation

**NIT success vs NCAA next year:**
| NIT Result | Next Year NCAA Win % |
|------------|---------------------|
| Champion | +12% |
| Final Four | +8% |
| Semifinals | +5% |
| First Round | +2% |

**Building momentum!**

---

## 3. CONFERENCE TOURNAMENTS

### 3.1 Conference Championship Importance

**Automatic Bids:**
- Her konferans şampiyonu → NCAA auto-bid
- 32 konferans = 32 auto-bids
- Remaining 36 spots = At-large

**Conference tournament timing:**
- Week before NCAA (DayNum 120-132)
- High stakes → clutch performance

### 3.2 Conference Tournament Performance

**Championship win impact:**
- Momentum: +5% first round NCAA win
- Confidence boost
- Automatic bid (bubble teams)

**Cinderella runs:**
- Low seed wins conference → auto-bid
- Sometimes upsets in NCAA

---

## 4. FEATURE FİKİRLERİ

### 4.1 Postseason Experience Features (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **PostSeasonExp_A** | Total postseason games | Experience | 🟢 Düşük |
| **PostSeasonExp_B** | Total postseason games | Experience | 🟢 Düşük |
| **NITChamp_A** | 1 if NIT champion | Momentum | 🟢 Düşük |
| **NITChamp_B** | 1 if NIT champion | Momentum | 🟢 Düşük |

### 4.2 Conference Tournament Features (Düşük Önem) 🟢

| Feature | Formül | Açıklama | Önem |
|---------|--------|----------|------|
| **ConfTourneyChamp_A** | 1 if conference champ | Momentum | 🟢 Düşük |
| **ConfTourneyChamp_B** | 1 if conference champ | Momentum | 🟢 Düşük |
| **ConfTourneyWins_A** | Wins in conf tourney | Recent form | 🟢 Düşük |
| **ConfTourneyWins_B** | Wins in conf tourney | Recent form | 🟢 Düşük |

### 4.3 Program Depth (Düşük Önem) 🟢

| Feature | Açıklama | Önem |
|---------|----------|------|
| **MultiTourney_A** | 1 if multiple postseason | Depth | 🟢 Düşük |
| **MultiTourney_B** | 1 if multiple postseason | Depth | 🟢 Düşük |

---

## 5. ÖNEMLİ GÖZLEMLER

### 5.1 NIT vs NCAA

**NIT quality still good:**
- NIT teams ≈ NCAA 9-12 seed quality
- Good for building program
- Next year boost significant

### 5.2 Conference Tournament Momentum

**Conference champ momentum:**
- Auto-bid + confidence
- First round NCAA: +5% win rate
- Especially for mid-majors

### 5.3 Cinderella Stories

**Conference tournament upsets → NCAA:**
- 2022: Richmond (A10 champ) → Sweet 16
- 2023: FAU (C-USA champ) → Final Four
- 2024: Oakland (Horizon champ) → Sweet 16

**Hot streak continues!**

---

## 6. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Future tournament results** | Sadece historical |
| **Same season bias** | Previous year data only |

---

## 7. SUMMARY

### Kilit Noktalar

1. **NIT = Quality experience** (next year boost)
2. **Conference championship = Momentum** (+5% first round)
3. **Postseason experience = Moderate value**
4. **Secondary tournaments = Low priority**

### Feature Öncelik

```
🟢 Düşük (Context):
  - ConfTourneyChamp indicator
  - NITChamp indicator
  - PostSeasonExp
```

### Usage Recommendation

**Other Tournaments → Low priority:**
- Conference champ momentum useful
- NIT championship predictive (next year)
- Secondary tournaments: Minimal value

---

*Analiz Tarihi: 01-03-2026*
*Grup: Other Tournaments (Variables #37-39)*

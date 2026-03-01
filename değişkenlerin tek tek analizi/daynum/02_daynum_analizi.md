# 📊 DEĞİŞKEN #2: DAYNUM

---

## 1. DEĞİŞKEN TANIMI

| Özellik | Değer |
|---------|-------|
| **Değişken Adı** | DayNum |
| **Tür** | Sayısal (Integer) |
| **Açıklama** | Sezon içindeki gün numarası (0 = sezon başı) |
| **Aralık** | 0 - 154 |
| **Benzersiz Değerler** | 133 (normal sezon), 15 (turnuva) |

**Not:** DayNum, gerçek takvim tarihinden ziyade sezon içindeki sıralı gün numarasını temsil eder.

---

## 2. KRİTİK DAYNUM DEĞERLERİ

| DayNum | Olay | Açıklama |
|--------|------|----------|
| **0-131** | Normal Sezon | Conference tournament öncesi |
| **132-133** | Conference Tournaments | Konferans turnuvaları |
| **134** | First Four | Turnuva öncesi 4 maç |
| **135-138** | First Round | 64 → 32 takım |
| **139-142** | Second Round | 32 → 16 takım |
| **145-146** | Sweet Sixteen | 16 → 8 takım |
| **151-152** | Elite Eight | 8 → 4 takım |
| **154** | Final Four | Yarı final |
| **155-156** | Championship | Şampiyonluk maçı |

```
0 ─────────────────────────────────────> 132 (Normal Sezon: 133 gün)
134 ──────────────────────────────────────> 154 (Turnuva: 15 gün)
```

---

## 3. NİÇİN ÖNEMLİ?

### 🔴 Data Leakage Önleme (Kritik)
Feature üretirken sadece **maçtan ÖNCEKİ** DayNum'ları kullan!
- Kural: `DayNum < Target_DayNum` (strict less than!)

### Rest Days (Dinlenme Günü)
```
RestDays = CurrentGameDayNum - LastGameDayNum

Etkisi:
- RestDays = 0: Back-to-back (yorgun)
- RestDays = 3-7: Optimal
- RestDays = 14+: Paslanma (rust)
```

### Momentum (Son Form)
Takımın son maçlardaki performansı sonucu etkiler.

### Sezon Dönemleri
- **Sezon başı** (0-30): Takımlar oluşuyor
- **Mid-season** (31-90): Ana rotasyon
- **Late-season** (91-132): Postseason push
- **Tournament** (134+): Do-or-die

---

## 4. FEATURE FİKİRLERİ

### Rest-Based Features (Yüksek Önem)

| Feature | Açıklama | Önem |
|---------|----------|------|
| **RestDaysDiff** | RestDays_A - RestDays_B | 🔴 Yüksek |
| **BackToBack_A/B** | Ard arda 2. maç mı? | 🟡 Orta |
| **LongRest_A/B** | RestDays > 7? | 🟢 Düşük |

### Form-Based Features (Yüksek Önem)

| Feature | Açıklama | Önem |
|---------|----------|------|
| **Last10WinPctDiff** | Son 10 maç form farkı | 🔴 Yüksek |
| **Last5WinPctDiff** | Son 5 maç form farkı | 🔴 Yüksek |
| **Momentum_A/B** | Son 5 maç trendi | 🟡 Orta |

### Fatigue-Based Features (Orta Önem)

| Feature | Açıklama | Önem |
|---------|----------|------|
| **GamesLast30DaysDiff** | Son 30 gün maç sayısı farkı | 🟡 Orta |
| **GamesLast7DaysDiff** | Son 7 gün maç sayısı farkı | 🟡 Orta |
| **FatigueScore_A/B** | GamesLast30 / 30 yoğunluk | 🟢 Düşük |

---

## 5. RİSKLER VE ÇÖZÜMLER

| Risk | Çözüm |
|------|-------|
| **Future Games** | DayNum < CurrentDayNum (strict) |
| **Same Day Leakage** | Aynı gün maçlarını hariç tut |
| **Tourney Data in Regular** | Sezon+DayNum check |
| **İlk maç (no history)** | Varsayılan değer kullan |
| **Long gap (20+ gün)** | Max cap uygula |

---

## 6. DATA LEAKAGE KURALI

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA LEAKAGE KURALI                       │
├─────────────────────────────────────────────────────────────┤
│  Feature üretirken SADECE şu maçları kullanabilirsin:        │
│                                                             │
│  Season < Target_Season  VE  DayNum < Target_DayNum        │
│                                                             │
│  ❌ Yanlış: DayNum <= Target_DayNum                         │
│  ❌ Yanlış: Season <= Target_Season                         │
│                                                             │
│  ✅ Doğru: Season < Target_Season                           │
│           OR                                                 │
│           Season == Target_Season AND DayNum < Target_DayNum│
└─────────────────────────────────────────────────────────────┘
```

---

## 7. SUMMARY

### Kilit Noktalar
1. **DayNum = Zaman içinde zaman** → Strict filtering şart
2. **DayNum < Target_DayNum** (strict!) → Aynı gün dahil değil
3. **Rest days önemli** → Yorgunluk ve performans etkisi var
4. **Momentum ölçülebilir** → Son 5-10 maç formu
5. **Turnuva farklı** → DayNum 134+ nötr saha

### Feature Öncelik

```
🔴 Yüksek:
  - RestDaysDiff
  - Last10WinPctDiff
  - Last5WinPctDiff

🟡 Orta:
  - GamesLast30DaysDiff
  - BackToBack indicator
  - Momentum (trend)

🟢 Düşük:
  - DayNum (direct)
  - IsTournament indicator
```

---

*Analiz Tarihi: 01-03-2026*
*Sonraki Değişken: TeamID*

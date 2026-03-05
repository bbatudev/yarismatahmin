# 📊 DEĞİŞKEN #40: SUBMISSION FORMAT - DETAYLI ANALİZ

---

## 1. DEĞİŞKEN TANIMI

### Sample Submission Files

**Files:**
- SampleSubmissionStage1.csv
- SampleSubmissionStage2.csv

**Format:**

| Column | Tür | Açıklama |
|--------|-----|----------|
| **ID** | String | Maç kimliği (Season_TeamA_TeamB) |
| **Pred** | Float | Tahmin (0-1 arası) |

**ID Format:** `Season_TeamA_TeamB`
- **Season:** Sezon yılı (örn: 2026)
- **TeamA, TeamB:** Takım ID'leri

**Pred Format:** Float [0, 1]
- 0.0 = Team A kesin kazanır
- 0.5 = Berabere (muhtemelen yok)
- 1.0 = Team B kesin kazanır

---

## 2. STAGE SYSTEM

### 2.1 Stage 1 vs Stage 2

**Stage 1:**
- Timing: Before tournament
- Games: All possible first round matchups
- Purpose: Public leaderboard
- Data: No tournament game results

**Stage 2:**
- Timing: During tournament
- Games: Actual tournament matchups
- Purpose: Final scoring
- Data: Includes tournament results up to current

### 2.2 Submission Timeline

```
Stage 1:
├── Opens: March 2026 (pre-tournament)
├── Closes: Tournament start
└── Games: All possible 1st round matchups

Stage 2:
├── Opens: Round 1 completed
├── Updates: Every round
└── Games: Actual remaining matchups
```

---

## 3. ID FORMAT

### 3.1 Structure

**Example ID:** `2026_1234_5678`

| Component | Value | Açıklama |
|-----------|-------|----------|
| Season | 2026 | Sezon yılı |
| TeamA | 1234 | İlk takım ID |
| TeamB | 5678 | İkinci takım ID |

**Important:**
- TeamA < TeamB (always!)
- Predict: Probability that TeamA wins

### 3.2 ID Generation

```python
# Correct order
ID = f"{Season}_{min(TeamA, TeamB)}_{max(TeamA, TeamB)}"

# Example
# Actual matchup: Duke (1231) vs UNC (1181)
# ID: "2026_1181_1231" (UNC first because 1181 < 1231)
# Pred: Probability that UNC (1181) wins
```

---

## 4. PRED FORMAT

### 4.1 Probability Range

**Pred must be [0, 1]:**
- 0.0 = 0% chance TeamA wins (100% TeamB)
- 0.5 = 50% chance each
- 1.0 = 100% chance TeamA wins

**Common mistakes:**
- ❌ Predicting 1.15 (invalid)
- ❌ Predicting -0.1 (invalid)
- ❌ Predicting outside [0, 1]

### 4.2 Calibration

**Well-calibrated predictions:**
- Pred 0.7 → TeamA wins %70 of the time
- Pred 0.3 → TeamA wins %30 of the time

**Brier Score penalty for poor calibration:**
- Overconfident wrong: High penalty
- Underconfident right: Small penalty

---

## 5. EVALUATION METRIC

### 5.1 Brier Score

**Formula:**
```
Brier Score = (1/N) × Σ(Pred - Actual)²
```

**Where:**
- Pred = Your prediction [0, 1]
- Actual = 1 if TeamA won, 0 if TeamB won
- N = Number of games

**Example:**
```
Game 1: Pred = 0.7, Actual = 1 (TeamA won)
  Contribution: (0.7 - 1)² = 0.09

Game 2: Pred = 0.3, Actual = 0 (TeamB won)
  Contribution: (0.3 - 0)² = 0.09

Brier Score = (0.09 + 0.09) / 2 = 0.09
```

**Lower is better:**
- Perfect: 0.0
- Random: 0.25
- Terrible: >0.5

### 5.2 Brier Score Components

**Two components:**
1. **Calibration:** Are predictions accurate?
2. **Refinement:** Do predictions vary?

**Good model:**
- Well-calibrated (pred ≈ actual frequency)
- High refinement (confident when correct)

---

## 6. FEATURE-TO-PREDICTION PIPELINE

### 6.1 Feature Extraction

```python
# For each matchup (Season, TeamA, TeamB):
features = {
    'SeedDiff': Seed_A - Seed_B,
    'MasseyRankDiff': Rank_B - Rank_A,  # TERS!
    'WinPctDiff': WinPct_A - WinPct_B,
    # ... more features
}

# Note: Feature_A - Feature_B format
```

### 6.2 Model Prediction

```python
# Model takes features → probability
pred = model.predict_proba(features)  # [0, 1]

# Ensure valid range
pred = np.clip(pred, 0.01, 0.99)  # Avoid extremes
```

### 6.3 Submission Generation

```python
# Create submission DataFrame
submission = pd.DataFrame({
    'ID': [f"{s}_{t1}_{t2}" for s, t1, t2 in matchups],
    'Pred': predictions
})

# Save
submission.to_csv('submission.csv', index=False)
```

---

## 7. ÖNEMLİ GÖZLEMLER

### 7.1 Probability Calibration

**Critical for Brier Score:**

| Issue | Symptom | Fix |
|-------|---------|-----|
| Overconfident | Preds near 0/1 | Calibration (Platt/Isotonic) |
| Underconfident | Preds near 0.5 | Boost confidence |
| Poor calibration | Brier high | Calibrate on CV |

### 7.2 Team Ordering

**Always TeamID_A < TeamID_B:**
- ID: `2026_1181_1231` (UNC vs Duke)
- Feature UNC first: `Seed_UNC - Seed_Duke`
- Pred: Probability UNC wins

**Common mistake:**
- ❌ Wrong order → Wrong target
- ❌ Confusing which team is "A"

### 7.3 Stage Differences

**Stage 1 = All possibilities:**
- Every team vs every other team
- Many impossible matchups

**Stage 2 = Actual matchups:**
- Only real tournament games
- Known after each round

---

## 8. DATA LEAKAGE RİSKİ

| Risk | Çözüm |
|------|-------|
| **Using tournament results** | Stage 1: No tourney data |
| **Future game stats** | Only pre-game features |
| **Seed information** | OK to use (known before) |

---

## 9. SUMMARY

### Kilit Noktalar

1. **ID format:** `Season_TeamA_TeamB` (TeamA < TeamB)
2. **Pred range:** [0, 1] probability
3. **Brier Score:** Lower is better (calibration critical)
4. **Stage 1 vs 2:** Public vs final leaderboard

### Submission Checklist

```
✓ ID format correct (TeamA < TeamB)
✓ Pred in [0, 1]
✓ Predictions calibrated
✓ No future data used
✓ Correct feature differences
```

---

*Analiz Tarihi: 01-03-2026*
*Grup: Submission Format (Variable #40)*

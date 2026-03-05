# Project: March Machine Learning Mania 2026 (Kaggle)

## Objective

Predict win probabilities for NCAA basketball games (Men and Women).
The primary evaluation metric is **Brier Score**.

The goal is to produce well-calibrated probabilities rather than raw classification accuracy.

---

# Core Modeling Philosophy

The modeling pipeline should follow this structure:

RAW DATA
→ canonical game dataset
→ team-level features
→ matchup features
→ model training
→ probability calibration
→ submission generation

Game predictions should always be **probability estimates**.

---

# Hard Constraints (Must Always Hold)

These rules prevent common Kaggle mistakes.

### 1. No Time Leakage

Features must only use information available **before the game date**.

Never use:

- tournament results for the same season
- rankings published after the game
- season aggregates that include future games

### 2. Pre-Game Feature Construction

Rolling or aggregated statistics must exclude the current game.

Example:

rolling_mean(points) must only use games before the current game.

### 3. Ranking Data Rules

For Massey Ordinals (Men's dataset):
RankingDayNum < GameDayNum must always hold (e.g., DayNum=133 snapshot).
**Filtering Rule:** Never average all 196 Massey systems. You MUST filter exclusively for Elite Predictive Systems: `["POM", "SAG", "NET", "BPI", "MOR", "KPI"]`.
Future rankings must never be used.

### 4. Minimum Season Boundaries (Preventing NaNs)
Historical Kaggle data dates back to 1985, but Detailed Box Scores and Massey Ordinals did not exist then.
If you attempt to merge 1980s data with the Four Factors, you will pollute the dataset with 44% NaNs. 
- **Men's Minimum Season:** `2003`
- **Women's Minimum Season:** `2010` (Also note: Women's Data has NO Massey system).
All raw dataset queries MUST drop rows prior to these bounds before generating the Matchup Matrix.

---

# Validation Strategy

Random KFold is forbidden.

Use **season-aware walk-forward validation**.

Example:

Train: seasons ≤ 2021  
Validate: season 2022  

Train: seasons ≤ 2022  
Validate: season 2023

Evaluation should primarily focus on **tournament games**.

---

# Modeling Strategy

Initial baseline models may include:

- LightGBM
- Logistic Regression
- Elo rating models

The exact modeling stack may evolve after feature engineering and analysis.

Models must output probabilities between (0,1).

Clipping or calibration may be applied if needed.

---

# Feature Engineering Principles

Prefer **team strength representations**.

Games should be transformed into matchup features:
`TeamA_feature − TeamB_feature`
(Always apply this symmetrically, where Win=1 and Loss=0 to maintain perfect Target balance).

Feature categories MUST include:
- **Four Factors:** Calculate Pace-Adjusted (Per 100 Possessions) efficiency: `NetRtg`, `eFG%`, `TOV%`, `ORB%`, `FTr`.
- **True Margin:** Point Differentials MUST be normalized for Home Court Advantage. Subtract `5.73` from Home Wins and add `5.73` to Away Wins before averaging.
- **Fatigue Flags:** Convert `RestDays` into interaction flags. E.g., `Is_Rusty` (Rest >= 7) and `Is_Back_To_Back` (Rest <= 2).
- **Rolling Form:** Track `WinPct` and `TrueMargin` over the last 14 and 21 days to capture late-season momentum.

---

# Repository Structure

The project follows a structured pipeline layout.

Raw datasets

data/raw/

Intermediate datasets

artifacts/data/

Saved models

artifacts/models/

Submission files

artifacts/submissions/

Source code

src/

Configuration

configs/

---

# Engineering Rules

Large datasets should be saved as **parquet** whenever possible.

Avoid committing large datasets to git.

All processing steps should be implemented as modular pipeline components.

Typical module layout:

src/data  
src/features  
src/models  
src/pipeline  

Add sanity checks wherever possible:

- row counts
- duplicate detection
- schema validation

---

# Tooling

SuperClaude workflow is encouraged:

sc:brainstorm  
sc:design  
sc:pm  
sc:implement  

---

# Development Philosophy

Prioritize:

correct data pipeline  
leakage-free features  
reproducible experiments  

Model complexity should only increase **after the data pipeline is stable**.


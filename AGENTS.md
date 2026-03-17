# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Kaggle March Machine Learning Mania 2026 — A machine learning competition to predict NCAA basketball tournament outcomes. The goal is to minimize **Brier Score** by producing well-calibrated win probabilities.

## Environment Setup

```bash
# Create and activate conda environment
conda env create -f mania_pipeline/environment.yml
conda activate march_mania

# Or use the existing venv in the project root
./venv/Scripts/python  # Windows
```

## Running the Pipeline

```bash
# Feature Engineering - generates processed_features_men.csv and processed_features_women.csv
python mania_pipeline/scripts/02_feature_engineering.py

# Model Training - trains LightGBM baseline models
python mania_pipeline/scripts/03_lgbm_train.py

# Analyze weak features
python mania_pipeline/scripts/analyze_weak_features.py
```

## Project Structure

- **[mania_pipeline/](mania_pipeline/)** — Core ML pipeline
  - `scripts/02_feature_engineering.py` — Feature engineering pipeline (Four Factors, Rolling Form, Massey, Seed, Conference features)
  - `scripts/03_lgbm_train.py` — LightGBM baseline model training
  - `artifacts/data/` — Processed features (CSV files)
  - `artifacts/models/` — Trained models (.pkl files)
- **[march-machine-leraning-mania-2026/](march-machine-leraning-mania-2026/)** — Raw Kaggle data (not in git)
- **Research folders** — Turkish language analysis folders (`değişkenlerin tek tek analizi/`, `feature_planlari/`, etc.)

## Critical Constraints

### No Time Leakage
- Features must only use information available **before** the game date
- Use `DayNum < 134` snapshot to capture pre-tournament state (prevents using tournament results)
- For Massey Ordinals (Men's): `RankingDayNum < GameDayNum` must hold

### Elite Massey Systems Only
When using Massey rankings, NEVER average all 196 systems. Filter exclusively for:
```python
ELITE_MASSEY_SYSTEMS = ["POM", "SAG", "NET", "BPI", "MOR", "KPI"]
```

### Minimum Season Boundaries
- **Men:** 2003+ (detailed box scores available from 2003)
- **Women:** 2010+ (box scores available from 2010, NO Massey system)
Using data before these years will cause 40%+ NaNs in Four Factors features.

### Validation Strategy
Random KFold is **forbidden**. Use season-aware walk-forward validation:
```
Train: seasons ≤ 2021, Validate: season 2022
Train: seasons ≤ 2022, Validate: season 2023
```

## Feature Architecture

The pipeline follows this flow:

1. **Long Format Games** — Convert compact/detailed results to long format with home court adjustment (5.73 point advantage)
2. **Four Factors** — eFG%, TOV%, ORB%, FTr (pace-adjusted per 100 possessions)
3. **Season Aggregates** — TrueMargin, NetRtg, paces
4. **Rolling Features** — WinPct, TrueMargin over last 7/14/21 days
5. **Rest Days & Fatigue** — Is_Rusty (≥7 days), Is_Back_To_Back (≤2 days)
6. **Matchup Matrix** — TeamA - TeamB differential features

### Key Feature Columns
- `SeedNum_diff` — Seed difference
- `Massey_EliteConsensus_diff` — Elite Massey systems average (Men only)
- `NetRtg_diff`, `eFG_diff`, `TOV_diff`, `ORB_diff`, `FTr_diff` — Four Factors
- `WinPct_Last14Days_diff`, `TrueMargin_Last21Days_diff` — Rolling form
- `Is_Rusty_diff`, `Is_Back_To_Back_diff` — Fatigue flags

## Model Outputs

Models output probabilities between (0, 1). The target is symmetric:
- Win = 1
- Loss = 0
- Each game is cloned twice (once from winner's perspective, once from loser's)

## File Formats

Use **parquet** for large intermediate datasets. Avoid committing large CSV files to git.

## Important Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `MIN_SEASON_MEN` | 2003 | Earliest season with full data (Men's) |
| `MIN_SEASON_WOMEN` | 2010 | Earliest season with full data (Women's) |
| `HOME_COURT_ADVANTAGE` | 5.73 | Points to subtract from home wins, add to away wins |
| `CLOSE_GAME_MARGIN` | 6 | Points defining a "close game" |
| `ROLLING_WINDOWS` | [7, 14, 21] | Days for rolling statistics |

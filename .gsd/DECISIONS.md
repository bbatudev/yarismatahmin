# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? |
|---|------|-------|----------|--------|-----------|------------|
| D001 | M001 | arch | Execution path authority | Script-first canonical path; notebook training disabled | “Tek gerçeklik” hedefi için iki eğitim yolu bırakmamak | No |
| D002 | M001 | data | Evaluation split | Train<=2022, Val=2023, Test=2024-2025 | Val/test illüzyonunu engellemek için sabit walk-forward standardı | No |
| D003 | M001 | pattern | Men/Women model handling | Separate training/eval artifacts for each | Cinsiyet bazlı davranış ayrışmasını görünür ve yönetilebilir tutmak | No |
| D004 | M001 | convention | Reproducibility gate tolerance | Same commit+seed requires |ΔBrier| <= 1e-4 | Run tekrar üretilebilirliğini ölçülebilir kontrata bağlamak | Yes — if numerical backend behavior changes |
| D005 | M001 | api | Regression gate policy | Brier mandatory, calibration degradation = fail, AUC informational | Tek metrik körlüğünü engelleyip kalite düşüşünü otomatik yakalamak | Yes — threshold tuning after baseline history |
| D006 | M001 | scope | External systems boundary | Local + git + Kaggle only (no MLflow/W&B/DB/scheduler now) | Önce canonical hattı stabilize etmek, erken MLOps entegrasyonundan kaçınmak | Yes — after M001 stabilization |
| D007 | M001/S01 | contract | Canonical run artifact layout | Each run writes `mania_pipeline/artifacts/runs/<run_id>/run_metadata.json` + `stage_events.jsonl` | S02+ gate and S06 reproducibility checks need a stable machine-readable run surface | Yes — if contract versioning is needed later |
| D008 | M001/S01/T01 | test-contract | Orchestrator test seam | `run_pipeline.py` must expose `build_run_context(seed=...)`, `main(argv=None)`, `CANONICAL_STAGES`, and `STAGE_HANDLERS` for contract-driven monkeypatch tests | T01 locks CLI lifecycle behavior before implementation; this seam keeps tests deterministic without running real feature/train workloads | Yes — if we later introduce explicit interface/versioned adapter |
| D009 | M001/S01/T02 | runtime-wiring | Canonical orchestrator stage integration | `run_pipeline.py` dynamically loads `02_feature_engineering.py` and `03_lgbm_train.py` via importlib and rebinds their data/artifact dirs to absolute repo paths before calling Python-level functions | Numeric-prefixed script names are not import-safe as regular modules; dynamic loading + absolute path rebinding keeps a single canonical command deterministic across caller cwd contexts | Yes — if scripts are later packaged as importable modules |

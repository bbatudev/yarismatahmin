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

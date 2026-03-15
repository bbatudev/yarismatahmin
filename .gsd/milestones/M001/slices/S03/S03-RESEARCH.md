# M001/S03 — Research

**Date:** 2026-03-14

## Summary

S03 owns **R003, R005, R006, R019** and depends on already-validated **R002** gate behavior from S02. Current canonical runtime is stable on gate enforcement (`stage_outputs.feature.gates.{men,women}` is present and pass/fail is machine-readable), but S03 deliverables are not yet implemented in runtime output shape: canonical `train` only persists `men_test_brier` / `women_test_brier`, and `eval_report.json` mirrors only those two values.

The main architectural gap is that richer Men/Women evaluation logic exists in `03_model_training.ipynb`, not in script-first runtime. Notebook logic includes its own split/training/eval path and already diverges from canonical contract (notably: notebook test split uses **2024 only**, while canonical contract is **2024+2025**). This is the exact drift vector S03 is supposed to close.

Primary recommendation: move all authoritative training/eval reporting into a unified script core (single codepath used by both genders), then demote notebook to reporting/EDA only (no model fitting/persistence). Add explicit tests for (a) Men/Women metrics table schema and side-by-side row, and (b) notebook training-path prohibition.

## Recommendation

Implement S03 in two coupled tracks:

1. **Unified Men/Women eval core in `03_lgbm_train.py` (script authority):**
   - Keep one training/eval function used for both genders.
   - Return structured per-split metrics (`Train`, `Val`, `Test`) with `brier`, `logloss`, `auc`.
   - Include feature snapshot per gender (`feature_columns`, `feature_count`) in returned payload for S05 handoff.
   - Ensure split sourcing is canonical (`Split` column produced by feature stage; `Test` includes 2024+2025).

2. **Single execution path enforcement (R003/R019):**
   - Disable notebook as an independent training path (no `model.fit`, no `joblib.dump` as executable authority).
   - Convert notebook role to read/visualize canonical artifacts only.
   - Add automated test guard that fails if notebook reintroduces training/persistence primitives.

Why this approach: it satisfies S03 directly, and also prepares S04/S05 boundaries (probability outputs + feature snapshot contract) without introducing a second authority.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Per-split probabilistic metrics (Brier/LogLoss/AUC) | `sklearn.metrics` (`brier_score_loss`, `log_loss`, `roc_auc_score`) | Already in project dependencies and notebook logic; avoids custom metric bugs. |
| Men/Women table + side-by-side export | `pandas.DataFrame` assembly + JSON/CSV write | Deterministic schema output, easy downstream consumption in S04/S06. |
| Notebook contract enforcement | Parse notebook JSON via stdlib (`json`) in pytest | Cheap, deterministic regression gate against notebook training drift. |

## Existing Code and Patterns

- `mania_pipeline/scripts/run_pipeline.py` — Canonical stage order is fixed (`feature -> train -> eval_report -> artifact`); S03 must preserve stage order while enriching `train`/`eval_report` payloads.
- `mania_pipeline/scripts/run_pipeline.py::stage_train` — Current seam expects `train_module.load_data(...)` and `train_module.train_baseline(...)`; today only test Brier is returned, so eval surface is too thin for R006.
- `mania_pipeline/scripts/03_lgbm_train.py` — Already computes Train/Val/Test Brier+LogLoss internally, but only returns `(model, test_brier)`; this is the lowest-friction place to expose unified structured metrics.
- `mania_pipeline/scripts/03_model_training.ipynb` — Contains a second full training/eval path (model fit, split logic, metric reporting, model persistence). This is the current R003/R019 violation surface.
- `mania_pipeline/scripts/split_leakage_contracts.py` — Leakage namespace is strict (`*_diff` + explicit allowlist); any new feature columns must respect this or runs will fail in `feature` stage.
- `mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py` — Existing contract tests prove fail-fast gating + metadata persistence; S03 can rely on this as precondition and should add new contract tests rather than changing stage topology.

## Constraints

- Canonical runtime stage order and lifecycle event contract are already tested; S03 must not break these (`mania_pipeline/tests/test_run_pipeline_cli.py`).
- S02 gate output is now part of run metadata contract (`stage_outputs.feature.gates.{men,women}`); S03 should consume this pass state, not bypass it.
- Men/Women feature spaces are intentionally different (current probe: men 57 features, women 52; men-only Massey/coaching/program signals). Unified core must be common logic over separate schemas, not forced column parity.
- `assign_split` contract is authoritative (`Train<=2022`, `Val=2023`, `Test=2024-2025`); notebook-style ad-hoc split code is not acceptable for canonical evaluation.
- Current artifact flow stores run docs in `artifacts/runs/<run_id>/...` and models in `artifacts/models/...`; S03 changes should keep paths explicit and machine-readable.

## Common Pitfalls

- **Notebook split drift** — Notebook currently evaluates `test = Season==2024` in one path, which silently violates canonical `2024-2025` test definition. Enforce split via canonical script data.
- **Thin metric payload** — Keeping only `men_test_brier/women_test_brier` blocks R006 and weakens S04/S05 handoff. Persist full Train/Val/Test table with Brier/LogLoss/AUC.
- **Hidden second authority** — Leaving executable notebook training cells in place reintroduces script/notebook dual truth even if canonical CLI works.
- **Namespace contract breakage** — Adding new non-diff feature columns without updating allowlist will fail S02 leakage gate before training.

## Open Risks

- `roc_auc_score` can raise on single-class slices; defensive handling policy must be defined (fail-fast vs `null` with explicit reason).
- Notebook enforcement via static checks can be bypassed manually unless validated in CI/pytest; add hard test coverage.
- Refactoring `train_baseline` return shape may break existing callers if not migrated atomically in `run_pipeline.py` and any direct script usage.

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| LightGBM | `tondevrel/scientific-agent-skills@xgboost-lightgbm` | available (not installed) — `npx skills add tondevrel/scientific-agent-skills@xgboost-lightgbm` |
| Jupyter Notebook | `openai/skills@jupyter-notebook` | available (not installed) — `npx skills add openai/skills@jupyter-notebook` |
| Pandas | `jeffallan/claude-skills@pandas-pro` | available (not installed) — `npx skills add jeffallan/claude-skills@pandas-pro` |
| Kaggle workflow | `shepsci/kaggle-skill@kaggle` | available (not installed) — `npx skills add shepsci/kaggle-skill@kaggle` |
| Python runtime profiling | `python-performance-optimization` | installed (project/user available skill list) |

## Sources

- Canonical runtime currently persists S02 gate payloads and only thin train metrics (source: [`mania_pipeline/artifacts/runs/20260314T151107Z_s03_research_probe/run_metadata.json`](mania_pipeline/artifacts/runs/20260314T151107Z_s03_research_probe/run_metadata.json))
- Eval report currently contains only test Brier pair + model paths, no Train/Val/Test table or side-by-side row (source: [`mania_pipeline/artifacts/runs/20260314T151107Z_s03_research_probe/eval_report.json`](mania_pipeline/artifacts/runs/20260314T151107Z_s03_research_probe/eval_report.json))
- Stage sequencing contract and CLI event schema are fixed by tests (source: [`mania_pipeline/tests/test_run_pipeline_cli.py`](mania_pipeline/tests/test_run_pipeline_cli.py))
- Split/leakage gate persistence and fail-fast behavior are contract-tested (source: [`mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py`](mania_pipeline/tests/test_run_pipeline_split_leakage_gate.py))
- Current script trainer computes multiple metrics but returns only `(model, test_brier)` to orchestrator (source: [`mania_pipeline/scripts/03_lgbm_train.py`](mania_pipeline/scripts/03_lgbm_train.py))
- Notebook contains independent training/eval/persistence path and split logic drift (`test=Season==2024`) discovered via notebook JSON inspection command (source: [`mania_pipeline/scripts/03_model_training.ipynb`](mania_pipeline/scripts/03_model_training.ipynb))
- Feature-stage split/leakage authority and namespace constraints that S03 must respect (source: [`mania_pipeline/scripts/split_leakage_contracts.py`](mania_pipeline/scripts/split_leakage_contracts.py))

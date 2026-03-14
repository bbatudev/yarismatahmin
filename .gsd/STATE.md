# GSD State

**Active Milestone:** M001 — Canonical Foundation
**Active Slice:** S01 — Canonical Run Orchestrator
**Active Task:** T00 — Slice planning bootstrap
**Phase:** Planning
**Slice Branch:** gsd/M001/S01
**Active Workspace:** main workspace
**Next Action:** Create `.gsd/milestones/M001/slices/S01/S01-PLAN.md` and decompose S01 into context-window-sized tasks.
**Last Updated:** 2026-03-14
**Requirements Status:** 14 active · 0 validated · 3 deferred · 2 out of scope

## Recent Decisions

- Script-first canonical execution path selected; notebook training path will be disabled.
- Walk-forward split fixed to Train<=2022, Val=2023, Test=2024-2025.
- Regression gate will use multi-rule policy (Brier required, calibration degradation fail, AUC informational).
- Reproducibility tolerance fixed at |ΔBrier| <= 1e-4 for same commit+seed runs.

## Blockers

- (none)

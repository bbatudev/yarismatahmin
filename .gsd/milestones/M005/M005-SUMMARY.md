---
id: M005
provides:
  - Weighted promotion gate, error decomposition, stacking-policy research seam, and feature-branch research evidence.
key_decisions:
  - Keep canonical pipeline topology unchanged.
  - Do not promote full M005-S04 feature package.
  - Treat `men + luck_only` as the only surviving follow-up candidate from the feature branch.
  - Preserve women-side `LGBM + HistGB` blend as the only concrete post-feature-branch improvement candidate.
  - Stop pushing the same blend-calibration refinement axis on men after the narrow follow-up failed to clear calibration.
  - Record men external-prior disagreement policy as promising on raw Brier/AUC but still blocked by calibration regression.
  - Record men multi-model combo follow-up as research-informative but not promotion-worthy after the real gate check failed.
  - Record men residual-correction follow-up as non-promotable; it did not improve the current raw reference without losing local gate safety.
  - Record men regime-routing follow-up as research-confirming only; it selected the same external-prior raw candidate across all seed-gap regimes and did not create a new route-to-promotion.
patterns_established:
  - Research-first feature branching before promotion.
  - Artifact-backed feature-family comparison on canonical splits.
observability_surfaces:
  - `multi_season_weighted_gate_report.json`
  - `error_decomposition_report.json`
  - `stacking_policy_report.json`
  - `feature_branch_report.json`
  - `men_external_prior_policy_report.json`
  - `men_combo_followup_report.json`
  - `men_residual_correction_report.json`
  - `men_regime_routing_report.json`
duration: 1d
verification_result: passed_with_research_hold
completed_at: 2026-03-16
---

# M005: Evaluation Discipline, Error Diagnostics, and Feature Branching

M005 moved the project from "add more pipeline pieces" to "measure whether any new idea deserves promotion."

## What Happened

- S01 added a multi-season weighted promotion gate without changing the canonical stage order.
- S02 added deeper error decomposition so close/medium seed-gap failures became easy to inspect.
- S03 tested stacking/policy-layer ideas live and showed the candidate pool was too correlated to create lift.
- S04 shifted to controlled feature branching:
  - `PythWR`, `Luck`, and men-only elite Massey spread/disagreement were added and tested.
  - a single style-clash feature was added and tested.
  - a seed-mispricing feature family was added and tested.

The main result is simple:

- Full feature packages did not beat the legacy baseline reliably.
- Women-side follow-ups did not produce a stable candidate.
- Men-side `luck_only` is the one small feature variant that improved both Val and Test Brier in the final follow-up probe.

## Authoritative Run Evidence

- `20260316T172000Z_m005_s04_smoke`
  - Full M005-S04 feature package.
  - Result: blocked by regression gate.
- `20260316T172927Z_m005_s04_feature_branch_smoke`
  - First package decomposition run.
  - Result: legacy baseline best for both genders.
- `20260316T173658Z_m005_s04_style_clash_smoke`
  - Added `style_clash_only` probe.
  - Result: not promising for both genders.
- `20260316T174122Z_m005_s04_seed_mispricing_smoke`
  - Added seed-mispricing family.
  - Result: men-side follow-up warranted, women still not promising.
- `20260316T174519Z_m005_s04_men_followup_smoke`
  - Men-focused narrow comparison.
  - Result: `luck_only` became the best men-side variant.

## Final Read

- Women should stay on baseline for this branch.
- Men has one surviving feature candidate:
  - `luck_only`
- Full M005-S04 package should not be promoted.
- Further broad feature digging inside this branch has diminishing returns.

## Men Follow-Up Numbers

From `20260316T174519Z_m005_s04_men_followup_smoke`:

- `legacy_baseline`
  - Val Brier: `0.20591347061475848`
  - Test Brier: `0.18623398593102922`
- `luck_only`
  - Val Brier: `0.20184204526834426`
  - Test Brier: `0.1821890782227556`
- `luck_seed_mispricing`
  - Val Brier: `0.20584153261130603`
  - Test Brier: `0.17975485077243838`

Interpretation:

- `luck_only` is the cleanest candidate because it improved both Val and Test relative to the legacy baseline.
- `luck_seed_mispricing` improved Test more, but it did not produce the same clean Val signal.

## Forward Intelligence

- If M005-S04 is resumed, the default starting point should be:
  - men-only `luck_only` follow-up
  - women baseline hold
- If the team wants faster progress, it is reasonable to stop feature excavation here and move attention to another hypothesis family or a deployment/policy decision based on men-only evidence.

## M005-S05 Follow-Up

After the feature branch was effectively closed, a narrow alternative-model blend follow-up was run on `2026-03-16`.

Authoritative runs:

- `20260316T182859Z_m005_s05_blend_gate_smoke_v3`
  - First live confirmation that the active blend policy removed the earlier men Brier block and women-side calibration block.
  - Remaining blocker: `men:calibration_degraded`
- `20260316T205334Z_m005_s05_blend_refine_smoke`
  - Narrow weight-refinement follow-up.
  - Result: women-side blend remained strong, men-side blocker still remained

Final read from the follow-up:

- Women now has a concrete non-baseline candidate:
  - `0.6 * LGBM + 0.4 * HistGB`
- Men still has a promising diversity signal on raw Brier:
  - `0.5 * LGBM + 0.5 * HistGB`
  - but it does not clear the canonical calibration gate
- Narrow weight refinement plus post-blend calibration checks did not close the men blocker

Women-side evidence from `20260316T205334Z_m005_s05_blend_refine_smoke`:

- baseline test Brier: `0.14223205049047852`
- blend test Brier: `0.1363404443967679`
- delta test Brier: `-0.005891606093710616`
- calibration gate: passed

Men-side evidence from `20260316T205334Z_m005_s05_blend_refine_smoke`:

- baseline test Brier: `0.18175050076078456`
- blend test Brier: `0.18112539714261014`
- delta test Brier: `-0.0006251036181744163`
- remaining blocker:
  - `delta_ece = +0.008896634902444037`
  - `delta_wmae = +0.008896634902444037`
  - `delta_high_prob_gap_abs = +0.0233571541548917`

Operational decision:

- Women should be stabilized on the blend candidate and not be the main research focus right now.
- Men needs a new research axis rather than more of the same blend-weight/calibration tweaking.

## M005-S06 Men Policy Follow-Up

After the blend-refinement path stalled, a men-only policy follow-up was run on `2026-03-16` to test whether a disagreement-aware external prior could improve the active blend candidate.

Authoritative runs:

- `20260316T210809Z_m005_s06_men_policy_smoke`
  - Men-only regime-aware blend policy probe over close/medium/wide seed-gap buckets.
  - Result: no meaningful edge over the uniform men blend.
- `20260316T212240Z_m005_s06_men_external_prior_smoke`
  - Research-only seed-prior disagreement seam.
  - Result: `committee_guardrail_medium_only` beat the men blend reference on Val/Test Brier and Test ECE.
- `20260316T213120Z_m005_s06_men_external_prior_gate_smoke_v2`
  - First live run where the external-prior policy was actually active in `prediction_policy`.
  - Result: men Brier and AUC improved materially, women blend stayed strong, but the canonical run still failed on `men:calibration_degraded`.

Men-side evidence from `20260316T213120Z_m005_s06_men_external_prior_gate_smoke_v2`:

- active men recipe:
  - reference blend: `0.5 * LGBM + 0.5 * HistGB`
  - external prior policy: `committee_guardrail_medium_only`
  - trigger regime: `medium`
  - disagreement threshold: `0.12`
  - seed prior weight: `0.4`
- canonical baseline test Brier: `0.18175050076078456`
- active policy test Brier: `0.1767538639967954`
- delta test Brier: `-0.0049966367639891485`
- canonical baseline test AUC: `0.8022388059701493`
- active policy test AUC: `0.8218979728224549`
- delta test AUC: `+0.01965916685230562`
- remaining blocker:
  - `delta_ece = +0.022080860244739063`
  - `delta_wmae = +0.022080860244739063`
  - `delta_high_prob_gap_abs = +0.027278791394369617`

Final read from the follow-up:

- Women remains in a good state on the existing `0.6 * LGBM + 0.4 * HistGB` candidate.
- Men now has a stronger raw-performance policy candidate than the plain blend.
- But that candidate still does not clear the canonical calibration gate.
- The men problem is now narrower and clearer:
  - not lack of raw signal
  - but inability to convert that signal into gate-safe calibrated probabilities.

## M005-S07 Men Multi-Model Follow-Up

After the men external-prior policy still failed the canonical gate, a broader model-family benchmark was run on `2026-03-16` to test whether `XGBoost`, `CatBoost`, and selected 2-model / 3-model combinations could create a cleaner men candidate.

Authoritative runs:

- `20260316T220058Z_m005_s07_xgboost_benchmark_smoke`
  - Added `xgboost` to the alternative-model benchmark.
  - Result: useful benchmark, but `LGBM + HistGB` remained the best disciplined candidate.
- `20260316T220848Z_m005_s07_multi_model_combo_smoke`
  - Added `catboost` plus pair/triple combo comparisons.
  - Result: several men combos improved raw Test Brier, but Val discipline still favored `baseline_histgb_blend`.
- `20260316T222202Z_m005_s07_men_combo_followup_smoke`
  - Men-only shortlist follow-up with calibration-aware comparison over five candidates.
  - Result: `baseline_histgb_xgboost_blend` became the best local-gate shortlist candidate.
- `20260316T222943Z_m005_s07_men_combo_gate_smoke`
  - First real gate check with `--prediction-policy men_combo_followup_v1`.
  - Result: failed canonical gate; men candidate degraded Brier after the selected calibration step and women fell back to baseline for this policy path.

Men-side shortlist evidence from `20260316T222202Z_m005_s07_men_combo_followup_smoke`:

- shortlist:
  - `baseline_histgb_blend`
  - `baseline_histgb_xgboost_blend`
  - `baseline_histgb_catboost_blend`
  - `baseline_xgboost_blend`
  - `xgboost_catboost_blend`
- local shortlist winner:
  - `baseline_histgb_xgboost_blend`
  - weights: `0.5 * LGBM + 0.25 * HistGB + 0.25 * XGBoost`
  - selected calibration: `isotonic`

Real-gate evidence from `20260316T222943Z_m005_s07_men_combo_gate_smoke`:

- active men candidate:
  - `baseline_histgb_xgboost_blend`
  - weights: `0.5 * LGBM + 0.25 * HistGB + 0.25 * XGBoost`
  - selected calibration: `isotonic`
- canonical baseline test Brier: `0.18175050076078456`
- active candidate test Brier: `0.18515142216463232`
- delta test Brier: `+0.003400921403847762`
- canonical baseline test AUC: `0.8022388059701493`
- active candidate test AUC: `0.7898474047672087`
- delta test AUC: `-0.012391401202940577`
- blockers:
  - `men:brier_degraded`
  - `men:calibration_degraded`

Final read from the follow-up:

- Adding `XGBoost` and `CatBoost` expanded the research space and produced useful ranking evidence.
- Some pair/triple combos improved raw Test Brier, especially before calibration.
- But the first real men combo candidate failed once it was applied through the actual canonical policy path.
- This means the combo branch did not solve the men promotion problem.
- The repo should treat this line as explored evidence, not as an active promotion candidate.

## M005-S08 Men Residual-Correction Follow-Up

After the combo branch failed at the real gate, a men-only residual-correction seam was run on `2026-03-16` to test whether the strongest raw men policy candidate could be cleaned up by a small second-stage correction layer.

Authoritative runs:

- `20260316T224614Z_m005_s08_men_residual_smoke`
  - First residual-correction run.
  - Result: selection logic bug found; a candidate was marked promising even though it failed the local gate vs the raw reference.
- `20260316T224729Z_m005_s08_men_residual_smoke_v2`
  - Corrected rerun after fixing the selection logic.
  - Result: `reference_raw` remained selected; no residual candidate cleared both local-gate checks.

Corrected final read from `20260316T224729Z_m005_s08_men_residual_smoke_v2`:

- men reference raw candidate:
  - source: `committee_guardrail_medium_only`
  - Val Brier: `0.20312501253846868`
  - Test Brier: `0.1767538639967954`
- strongest residual candidate:
  - `residual_logit_only`
  - Val Brier: `0.21554446625131643`
  - Test Brier: `0.17427266172872244`
  - local gate vs baseline: passed
  - local gate vs reference: failed

Interpretation:

- residual correction could move raw Test Brier a little lower,
- but it did not preserve enough calibration quality relative to the raw reference candidate,
- so this branch did not produce a gate-safe follow-up.

## M005-S09 Men Regime-Routing Follow-Up

After residual correction also stalled, a final repo-internal men axis was run on `2026-03-16` to test whether close/medium/wide seed-gap regimes should route to different existing candidates.

Authoritative run:

- `20260316T231500Z_m005_s09_men_regime_routing_smoke`
  - Research-only regime router over the existing men candidate pool:
    - `baseline_raw`
    - `blend_raw`
    - `external_prior_raw`
    - `combo_raw`

Final read from `20260316T231500Z_m005_s09_men_regime_routing_smoke`:

- research decision:
  - `promising_regime_router`
- selected router:
  - `regime_best_val_router`
- regime choices:
  - `close -> external_prior_raw`
  - `medium -> external_prior_raw`
  - `wide -> external_prior_raw`
- resulting Test metrics:
  - Brier: `0.1767538639967954`
  - AUC: `0.8218979728224549`
  - ECE: `0.058743023353566196`
- local gate vs baseline:
  - passed
  - delta Brier: `-0.008694509018031593`
  - delta ECE: `-0.0334145292686288`

Interpretation:

- the router did not discover a real regime-specialist mix,
- it simply confirmed that the current best men raw candidate is already the external-prior policy across all major seed-gap regimes,
- so regime-routing added evidence, not a new production candidate.

## End State

- Women-side evidence is strong enough to freeze on the `0.6 * LGBM + 0.4 * HistGB` candidate.
- Men-side repo-internal research now strongly suggests that:
  - raw signal exists,
  - the strongest raw candidate is still `committee_guardrail_medium_only`,
  - but no tested repo-internal correction, combo, or routing layer converted it into a clean canonical promotion.
- The practical implication is that the easy repo-internal men research axes are now largely exhausted.

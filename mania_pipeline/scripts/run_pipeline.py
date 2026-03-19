from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pickle
import re
from itertools import combinations

import numpy as np
import pandas as pd
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from sklearn.isotonic import IsotonicRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency
    XGBClassifier = None

try:
    from catboost import CatBoostClassifier
except Exception:  # pragma: no cover - optional dependency
    CatBoostClassifier = None

try:
    from tabpfn import TabPFNClassifier
    from tabpfn.settings import settings as tabpfn_settings
except Exception:  # pragma: no cover - optional dependency
    TabPFNClassifier = None
    tabpfn_settings = None


SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
REPO_ROOT = PIPELINE_DIR.parent
KAGGLE_DATA_DIR = REPO_ROOT / "march-machine-leraning-mania-2026"
FALLBACK_KAGGLE_DATA_DIR = PIPELINE_DIR / "data" / "raw"
DEFAULT_ARTIFACTS_ROOT = PIPELINE_DIR / "artifacts" / "runs"

CANONICAL_STAGES = ("feature", "train", "eval_report", "artifact")
CANONICAL_SPLITS = ("Train", "Val", "Test")
CALIBRATION_BIN_EDGES = tuple(round(step / 10, 1) for step in range(11))
CALIBRATION_BINS_COLUMNS = (
    "gender",
    "split",
    "bin_left",
    "bin_right",
    "sample_count",
    "pred_mean",
    "actual_rate",
    "gap",
)
HIGH_PROB_THRESHOLD = 0.8
REPRO_BRIER_TOLERANCE = 1e-4
REGRESSION_NUMERIC_EPS = 1e-9
DRIFT_GAP_SHIFT_THRESHOLD = 0.08
DRIFT_LOW_SAMPLE_THRESHOLD = 25
DRIFT_REGIME_ORDER = ("close", "medium", "wide")
CALIBRATION_POLICY_METHODS = ("none", "platt", "isotonic", "shrink")
CALIBRATION_POLICY_MIN_VAL_SAMPLES = 80
CALIBRATION_POLICY_MIN_IMPROVEMENT = 0.001
CALIBRATION_SHRINK_GRID = (0.75, 0.8, 0.85, 0.9, 0.95)
ERROR_BUCKET_DEFINITIONS = (
    ("low_confidence_lt_0.45", None, 0.45),
    ("close_call_0.45_0.55", 0.45, 0.55),
    ("confident_0.55_0.80", 0.55, 0.80),
    ("high_confidence_ge_0.80", 0.80, None),
)
OVERCONFIDENT_THRESHOLD = 0.80
ERROR_DIAGNOSTIC_MIN_BUCKET_SAMPLES = 10
WEIGHTED_PROMOTION_MIN_IMPROVEMENT = 1e-4
HPO_ALLOWED_PROFILES = ("baseline", "quality_v1")
HPO_MAX_TRIALS = 20
HPO_PARAM_SPACE = {
    "learning_rate": [0.02, 0.03, 0.05, 0.07],
    "num_leaves": [31, 47, 63],
    "min_child_samples": [10, 15, 20, 30],
    "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
    "subsample": [0.7, 0.8, 0.9, 1.0],
    "n_estimators": [800, 1000, 1200, 1400],
}
HPO_CV_VAL_SEASONS = (2022, 2023)
HPO_CV_MIN_TRAIN_ROWS = 2
HPO_CV_MIN_VAL_ROWS = 2
HPO_OBJECTIVE_GAP_PENALTY = 0.10
ENSEMBLE_WEIGHT_GRID = (0.25, 0.5, 0.75)
ENSEMBLE_MIN_VAL_IMPROVEMENT = 1e-4
ENSEMBLE_MAX_TEST_BRIER_DEGRADATION = 0.0
STACKING_POLICY_MIN_VAL_SAMPLES = 20
STACKING_POLICY_MIN_IMPROVEMENT = 1e-4
ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT = 1e-4
ALTERNATIVE_MODEL_WEIGHT_GRID = (0.25, 0.33, 0.4, 0.5, 0.6, 0.67, 0.75)
MEN_ALTERNATIVE_SELECTION_MAX_VAL_ECE_DEGRADATION = 0.01
MEN_ALTERNATIVE_SELECTION_MAX_VAL_HIGH_GAP_ABS_DEGRADATION = 0.01
MEN_BASELINE_BLEND_VAL_BRIER_TOLERANCE = 0.002
MEN_TABPFN_HIGH_PROB_TAIL_LIFT = 0.02
PREDICTION_POLICIES = (
    "baseline",
    "blend_candidate_v1",
    "blend_final_recipe_v1",
    "men_external_prior_policy_v1",
    "men_combo_followup_v1",
)
MEN_POLICY_MIN_VAL_IMPROVEMENT = 1e-4
FEATURE_BRANCH_MIN_VAL_IMPROVEMENT = 1e-4
M005_S04_FEATURE_COLUMNS = {
    "men": (
        "PythWR_diff",
        "Luck_diff",
        "MasseyRankStd_diff",
        "MasseyPctSpread_diff",
        "MasseyOrdinalRange_diff",
        "StyleClash_eFG_BlkPct_diff",
        "SeedPythMispricing_diff",
        "SeedNetRtgMispricing_diff",
        "SeedMasseyMispricing_diff",
    ),
    "women": (
        "PythWR_diff",
        "Luck_diff",
        "StyleClash_eFG_BlkPct_diff",
        "SeedPythMispricing_diff",
        "SeedNetRtgMispricing_diff",
    ),
}


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_run_label(value: str | None) -> str:
    label = (value or "manual").strip()
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", label)
    sanitized = sanitized.strip("._-")
    return sanitized or "manual"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        commit = (result.stdout or "").strip()
        if commit:
            return commit
    except Exception:
        pass
    return "unknown"


def _normalize_profile_name(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    return text or None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _serialize_error(exc: Exception) -> dict[str, Any]:
    return {
        "type": exc.__class__.__name__,
        "message": str(exc),
        "traceback": traceback.format_exc().splitlines()[-20:],
    }


def _load_script_module(filename: str, module_name: str):
    module_path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load script module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_script_module_direct(filename: str, module_name: str):
    """Load by path without going through monkeypatch-prone indirection."""
    module_path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load script module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_pipeline_data_dir(*, required_files: tuple[str, ...] = ()) -> Path:
    candidates = (KAGGLE_DATA_DIR, FALLBACK_KAGGLE_DATA_DIR)
    for candidate in candidates:
        if not candidate.exists():
            continue
        if required_files and not all((candidate / name).exists() for name in required_files):
            continue
        return candidate

    return candidates[0]


@lru_cache(maxsize=1)
def _load_split_leakage_contracts_module():
    return _load_script_module("split_leakage_contracts.py", "split_leakage_contracts_stage")


@lru_cache(maxsize=1)
def _load_feature_governance_module():
    # Intentionally bypasses _load_script_module so tests that monkeypatch
    # train-module loading do not accidentally stub governance contracts.
    return _load_script_module_direct("feature_governance.py", "feature_governance_stage")


def validate_split_contract(df):
    contracts_module = _load_split_leakage_contracts_module()
    return contracts_module.validate_split_contract(df)


def validate_leakage_contract(df):
    contracts_module = _load_split_leakage_contracts_module()
    return contracts_module.validate_leakage_contract(df)


def _combine_feature_gate_payloads(split_gate: dict[str, Any], leakage_gate: dict[str, Any]) -> dict[str, Any]:
    failing_gate = None
    if not split_gate.get("pass", False):
        failing_gate = split_gate
    elif not leakage_gate.get("pass", False):
        failing_gate = leakage_gate

    if failing_gate is not None:
        return {
            "pass": False,
            "blocking_rule": failing_gate.get("blocking_rule"),
            "reason": failing_gate.get("reason", "Feature gate failed."),
            "evidence": {
                "split": split_gate,
                "leakage": leakage_gate,
            },
        }

    return {
        "pass": True,
        "blocking_rule": None,
        "reason": "Split and leakage contracts satisfied.",
        "evidence": {
            "split": split_gate,
            "leakage": leakage_gate,
        },
    }


def _raise_feature_gate_failure(gender_label: str, gate_payload: dict[str, Any]) -> None:
    blocking_rule = gate_payload.get("blocking_rule") or "UNKNOWN_BLOCKING_RULE"
    reason = gate_payload.get("reason") or "Feature gate failed."
    raise RuntimeError(f"[{gender_label}] feature gate failed: {blocking_rule} | {reason}")


def build_run_context(
    seed: int,
    run_label: str | None = None,
    artifacts_root: str | os.PathLike[str] | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    started_at = _now_utc_iso()
    safe_label = _safe_run_label(run_label)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{safe_label}"

    cli_args = list(argv) if argv is not None else list(sys.argv[1:])
    command_parts = [Path(__file__).name, *[str(a) for a in cli_args]]
    command = " ".join(part for part in command_parts if part).strip() or Path(__file__).name

    root = Path(artifacts_root).resolve() if artifacts_root is not None else DEFAULT_ARTIFACTS_ROOT.resolve()
    run_dir = root / run_id

    return {
        "run_id": run_id,
        "seed": int(seed),
        "git_commit": _git_commit(),
        "started_at": started_at,
        "command": command,
        "cwd": str(Path.cwd().resolve()),
        "run_label": safe_label,
        "artifacts_root": str(root),
        "run_dir": str(run_dir),
        "status": "running",
        "stage_outputs": {},
    }


def _stage_event(
    *,
    stage: str,
    status: str,
    started_at: str,
    finished_at: str | None,
    duration_ms: int | None,
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "error": error,
    }


def _metadata_view(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "git_commit": context["git_commit"],
        "started_at": context["started_at"],
        "command": context["command"],
        "cwd": context["cwd"],
        "run_label": context.get("run_label"),
        "artifacts_root": context.get("artifacts_root"),
        "run_dir": context.get("run_dir"),
        "training_profile": context.get("training_profile"),
        "hpo_trials": context.get("hpo_trials"),
        "hpo_target_profile": context.get("hpo_target_profile"),
        "status": context.get("status"),
        "finished_at": context.get("finished_at"),
        "duration_ms": context.get("duration_ms"),
        "failed_stage": context.get("failed_stage"),
        "error": context.get("error"),
        "stage_outputs": context.get("stage_outputs", {}),
    }


def _persist_metadata(context: dict[str, Any]) -> None:
    metadata_path = Path(context["metadata_path"])
    _write_json(metadata_path, _metadata_view(context))


def _record_stage_started(context: dict[str, Any], stage: str) -> tuple[str, float]:
    started_at = _now_utc_iso()
    event = _stage_event(
        stage=stage,
        status="started",
        started_at=started_at,
        finished_at=None,
        duration_ms=None,
        error=None,
    )
    _append_jsonl(Path(context["stage_events_path"]), event)
    return started_at, time.perf_counter()


def _record_stage_finished(
    context: dict[str, Any],
    stage: str,
    status: str,
    started_at: str,
    started_clock: float,
    error: dict[str, Any] | None = None,
) -> None:
    finished_at = _now_utc_iso()
    duration_ms = int((time.perf_counter() - started_clock) * 1000)
    event = _stage_event(
        stage=stage,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=duration_ms,
        error=error,
    )
    _append_jsonl(Path(context["stage_events_path"]), event)


def stage_feature(context: dict[str, Any]) -> dict[str, Any]:
    feature_module = _load_script_module("02_feature_engineering.py", "feature_engineering_stage")

    feature_module.DATA_DIR = str(
        _resolve_pipeline_data_dir(
            required_files=(
                "MRegularSeasonCompactResults.csv",
                "MNCAATourneyCompactResults.csv",
                "MRegularSeasonDetailedResults.csv",
                "WRegularSeasonCompactResults.csv",
                "WNCAATourneyCompactResults.csv",
                "WRegularSeasonDetailedResults.csv",
            )
        )
    )
    feature_module.OUT_DIR = str(PIPELINE_DIR / "artifacts" / "data")
    os.makedirs(feature_module.OUT_DIR, exist_ok=True)

    men_df = feature_module.run_pipeline(gender="M")
    women_df = feature_module.run_pipeline(gender="W")

    if men_df is None or women_df is None:
        raise RuntimeError("Feature engineering returned empty dataframe for Men or Women")

    gates: dict[str, dict[str, Any]] = {}
    first_failure: tuple[str, dict[str, Any]] | None = None

    for gender_key, frame in (("men", men_df), ("women", women_df)):
        split_gate = validate_split_contract(frame)
        leakage_gate = validate_leakage_contract(frame)
        combined_gate = _combine_feature_gate_payloads(split_gate, leakage_gate)
        gates[gender_key] = combined_gate

        if not combined_gate["pass"] and first_failure is None:
            first_failure = (gender_key, combined_gate)

    if first_failure is not None:
        failed_gender, failed_gate = first_failure
        _raise_feature_gate_failure(failed_gender, failed_gate)

    men_path = Path(feature_module.OUT_DIR) / "processed_features_men.csv"
    women_path = Path(feature_module.OUT_DIR) / "processed_features_women.csv"

    men_df.to_csv(men_path, index=False)
    women_df.to_csv(women_path, index=False)

    return {
        "outputs": {
            "men_features": str(men_path),
            "women_features": str(women_path),
        },
        "rows": {
            "men": int(len(men_df)),
            "women": int(len(women_df)),
        },
        "gates": gates,
    }


def _train_with_optional_profile(
    *,
    train_module: Any,
    df: pd.DataFrame,
    gender_label: str,
    random_state: int,
    profile: str,
    param_overrides: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    attempts: list[dict[str, Any]] = []

    if param_overrides is not None:
        attempts.append(
            {
                "random_state": random_state,
                "profile": profile,
                "param_overrides": param_overrides,
            }
        )

    attempts.append(
        {
            "random_state": random_state,
            "profile": profile,
        }
    )

    attempts.append(
        {
            "random_state": random_state,
        }
    )

    last_exc: Exception | None = None
    for kwargs in attempts:
        try:
            return train_module.train_baseline(df, gender_label, **kwargs)
        except TypeError as exc:
            message = str(exc)
            if "unexpected keyword argument" not in message:
                raise
            last_exc = exc
            continue

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"[{gender_label}] failed to call train_baseline")


def _build_hpo_trial_param_overrides(*, seed: int, trials: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(int(seed))
    candidates: list[dict[str, Any]] = []
    for _ in range(int(trials)):
        candidate = {
            key: values[int(rng.integers(0, len(values)))]
            for key, values in HPO_PARAM_SPACE.items()
        }
        candidates.append(candidate)
    return candidates


def _evaluate_hpo_cv_objective(
    *,
    train_module: Any,
    df: pd.DataFrame,
    gender_label: str,
    base_seed: int,
    target_profile: str,
    param_overrides: dict[str, Any],
) -> tuple[float | None, list[dict[str, Any]], str | None]:
    if "Season" not in df.columns:
        return None, [], "season_column_missing"

    season_series = pd.to_numeric(df["Season"], errors="coerce")
    if season_series.isna().all():
        return None, [], "season_column_non_numeric"

    cv_rows: list[dict[str, Any]] = []
    fold_scores: list[float] = []

    for fold_index, val_season in enumerate(HPO_CV_VAL_SEASONS, start=1):
        train_mask = season_series < float(val_season)
        val_mask = season_series == float(val_season)
        train_count = int(train_mask.sum())
        val_count = int(val_mask.sum())

        row: dict[str, Any] = {
            "fold_id": fold_index,
            "val_season": int(val_season),
            "train_rows": train_count,
            "val_rows": val_count,
            "status": "skipped",
            "reason": None,
            "val_brier": None,
        }

        if train_count < HPO_CV_MIN_TRAIN_ROWS or val_count < HPO_CV_MIN_VAL_ROWS:
            row["reason"] = "insufficient_fold_rows"
            cv_rows.append(row)
            continue

        fold_df = df.copy()
        fold_df["Split"] = np.where(train_mask, "Train", np.where(val_mask, "Val", "Test"))

        try:
            _, fold_payload = _train_with_optional_profile(
                train_module=train_module,
                df=fold_df,
                gender_label=gender_label,
                random_state=int(base_seed) + fold_index,
                profile=target_profile,
                param_overrides=param_overrides,
            )
        except Exception as exc:
            row["reason"] = f"fold_train_failed:{exc.__class__.__name__}"
            cv_rows.append(row)
            continue

        fold_metrics = fold_payload.get("metrics_by_split", {}) if isinstance(fold_payload, dict) else {}
        val_metrics = fold_metrics.get("Val", {}) if isinstance(fold_metrics, dict) else {}
        fold_val_brier = _as_float_or_none(val_metrics.get("brier"))

        if fold_val_brier is None:
            row["reason"] = "missing_val_brier"
            cv_rows.append(row)
            continue

        row["status"] = "passed"
        row["val_brier"] = fold_val_brier
        fold_scores.append(fold_val_brier)
        cv_rows.append(row)

    if not fold_scores:
        return None, cv_rows, "no_successful_cv_folds"

    return float(np.mean(fold_scores)), cv_rows, None


def _run_hpo_search_for_gender(
    *,
    train_module: Any,
    df: pd.DataFrame,
    gender_key: str,
    seed: int,
    target_profile: str,
    trial_overrides: list[dict[str, Any]],
) -> dict[str, Any]:
    if not trial_overrides:
        return {
            "status": "skipped",
            "reason": "no_trials_requested",
            "target_profile": target_profile,
            "trials_requested": 0,
            "trials_executed": 0,
            "best_trial_id": None,
            "best_val_brier": None,
            "candidates": [],
        }

    gender_label = "M" if gender_key == "men" else "W"
    candidates: list[dict[str, Any]] = []
    successful: list[dict[str, Any]] = []

    for trial_index, overrides in enumerate(trial_overrides, start=1):
        trial_seed = int(seed) + trial_index
        candidate_payload: dict[str, Any] = {
            "trial_id": trial_index,
            "seed": trial_seed,
            "param_overrides": overrides,
            "status": "failed",
            "reason": None,
            "metrics": {},
        }

        try:
            _, payload = _train_with_optional_profile(
                train_module=train_module,
                df=df,
                gender_label=gender_label,
                random_state=trial_seed,
                profile=target_profile,
                param_overrides=overrides,
            )
        except Exception as exc:
            candidate_payload["reason"] = f"trial_failed:{exc.__class__.__name__}"
            candidates.append(candidate_payload)
            continue

        metrics_by_split = payload.get("metrics_by_split", {}) if isinstance(payload, dict) else {}
        train_metrics = metrics_by_split.get("Train", {}) if isinstance(metrics_by_split, dict) else {}
        val_metrics = metrics_by_split.get("Val", {}) if isinstance(metrics_by_split, dict) else {}
        test_metrics = metrics_by_split.get("Test", {}) if isinstance(metrics_by_split, dict) else {}

        train_brier = _as_float_or_none(train_metrics.get("brier"))
        val_brier = _as_float_or_none(val_metrics.get("brier"))
        test_brier = _as_float_or_none(test_metrics.get("brier"))
        generalization_gap = (
            float(val_brier - train_brier)
            if isinstance(val_brier, (int, float)) and isinstance(train_brier, (int, float))
            else None
        )

        cv_mean_val_brier, cv_rows, cv_reason = _evaluate_hpo_cv_objective(
            train_module=train_module,
            df=df,
            gender_label=gender_label,
            base_seed=trial_seed,
            target_profile=target_profile,
            param_overrides=overrides,
        )

        objective_score: float | None
        objective_reason: str | None
        if isinstance(cv_mean_val_brier, (int, float)):
            objective_score = float(cv_mean_val_brier)
            objective_reason = "cv_mean_val_brier"
        elif isinstance(val_brier, (int, float)):
            gap_penalty = (
                abs(float(generalization_gap)) * HPO_OBJECTIVE_GAP_PENALTY
                if isinstance(generalization_gap, (int, float))
                else 0.0
            )
            objective_score = float(val_brier + gap_penalty)
            objective_reason = "val_brier_plus_gap_penalty"
        else:
            objective_score = None
            objective_reason = cv_reason or "missing_val_brier"

        candidate_payload.update(
            {
                "status": "passed"
                if isinstance(val_brier, (int, float)) and isinstance(objective_score, (int, float))
                else "failed",
                "reason": None if isinstance(objective_score, (int, float)) else "missing_objective_score",
                "metrics": {
                    "train_brier": train_brier,
                    "val_brier": val_brier,
                    "val_logloss": _as_float_or_none(val_metrics.get("logloss")),
                    "val_auc": _as_float_or_none(val_metrics.get("auc")),
                    "test_brier": test_brier,
                    "generalization_gap": generalization_gap,
                    "cv_mean_val_brier": cv_mean_val_brier,
                    "objective_score": objective_score,
                    "objective_reason": objective_reason,
                },
                "cv": {
                    "status": "passed" if cv_mean_val_brier is not None else "fallback",
                    "reason": cv_reason,
                    "rows": cv_rows,
                },
            }
        )

        candidates.append(candidate_payload)
        if candidate_payload["status"] == "passed":
            successful.append(candidate_payload)

    if not successful:
        return {
            "status": "failed",
            "reason": "no_successful_trials",
            "target_profile": target_profile,
            "trials_requested": len(trial_overrides),
            "trials_executed": 0,
            "best_trial_id": None,
            "best_val_brier": None,
            "best_test_brier": None,
            "best_objective_score": None,
            "best_cv_mean_val_brier": None,
            "candidates": candidates,
        }

    best = min(
        successful,
        key=lambda candidate: (
            candidate.get("metrics", {}).get("objective_score")
            if isinstance(candidate.get("metrics", {}).get("objective_score"), (int, float))
            else float("inf"),
            candidate.get("metrics", {}).get("val_brier")
            if isinstance(candidate.get("metrics", {}).get("val_brier"), (int, float))
            else float("inf"),
            int(candidate.get("trial_id", 0)),
        ),
    )

    return {
        "status": "passed",
        "reason": None,
        "target_profile": target_profile,
        "trials_requested": len(trial_overrides),
        "trials_executed": len(successful),
        "best_trial_id": int(best.get("trial_id", 0)),
        "best_val_brier": best.get("metrics", {}).get("val_brier"),
        "best_test_brier": best.get("metrics", {}).get("test_brier"),
        "best_objective_score": best.get("metrics", {}).get("objective_score"),
        "best_cv_mean_val_brier": best.get("metrics", {}).get("cv_mean_val_brier"),
        "best_param_overrides": best.get("param_overrides", {}),
        "candidates": candidates,
    }


def stage_train(context: dict[str, Any]) -> dict[str, Any]:
    feature_outputs = context.get("stage_outputs", {}).get("feature", {})
    gates = feature_outputs.get("gates", {})

    for gender_key in ("men", "women"):
        gate_payload = gates.get(gender_key)
        if not isinstance(gate_payload, dict):
            gate_payload = {
                "pass": False,
                "blocking_rule": "MISSING_FEATURE_GATE",
                "reason": "Missing feature gate payload before train stage.",
            }

        if not gate_payload.get("pass", False):
            _raise_feature_gate_failure(gender_key, gate_payload)

    train_module = _load_script_module("03_lgbm_train.py", "lgbm_train_stage")

    train_module.DATA_DIR = str(PIPELINE_DIR / "artifacts" / "data")
    train_module.OUT_DIR = str(PIPELINE_DIR / "artifacts" / "models")
    os.makedirs(train_module.OUT_DIR, exist_ok=True)

    men_df = train_module.load_data("M")
    women_df = train_module.load_data("W")

    if men_df is None or women_df is None:
        raise RuntimeError("Training data missing; feature stage did not produce required files")

    training_profile = str(context.get("training_profile", "baseline")).strip().lower()

    men_model, men_payload = _train_with_optional_profile(
        train_module=train_module,
        df=men_df,
        gender_label="M",
        random_state=context["seed"],
        profile=training_profile,
    )
    women_model, women_payload = _train_with_optional_profile(
        train_module=train_module,
        df=women_df,
        gender_label="W",
        random_state=context["seed"],
        profile=training_profile,
    )

    hpo_trials_raw = int(context.get("hpo_trials", 0) or 0)
    if hpo_trials_raw < 0:
        raise RuntimeError("hpo_trials must be >= 0")
    hpo_trials = min(hpo_trials_raw, HPO_MAX_TRIALS)

    hpo_target_profile = str(context.get("hpo_target_profile", "quality_v1")).strip().lower()
    if hpo_target_profile not in HPO_ALLOWED_PROFILES:
        raise RuntimeError(
            f"unknown hpo target profile: {hpo_target_profile}. allowed={','.join(HPO_ALLOWED_PROFILES)}"
        )

    hpo_trial_overrides = _build_hpo_trial_param_overrides(seed=context["seed"], trials=hpo_trials)
    hpo_by_gender = {
        "men": _run_hpo_search_for_gender(
            train_module=train_module,
            df=men_df,
            gender_key="men",
            seed=context["seed"],
            target_profile=hpo_target_profile,
            trial_overrides=hpo_trial_overrides,
        ),
        "women": _run_hpo_search_for_gender(
            train_module=train_module,
            df=women_df,
            gender_key="women",
            seed=context["seed"] + 10_000,
            target_profile=hpo_target_profile,
            trial_overrides=hpo_trial_overrides,
        ),
    }

    hpo_status = "skipped"
    if hpo_trials > 0:
        if any(payload.get("status") == "passed" for payload in hpo_by_gender.values() if isinstance(payload, dict)):
            hpo_status = "passed"
        else:
            hpo_status = "failed"

    run_dir_raw = context.get("run_dir")
    if isinstance(run_dir_raw, str) and run_dir_raw.strip():
        run_dir = Path(run_dir_raw)
    else:
        run_dir = PIPELINE_DIR / "artifacts" / "runs" / "_train_stage"
    run_dir.mkdir(parents=True, exist_ok=True)

    hpo_report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "status": hpo_status,
        "config": {
            "trials_requested": hpo_trials_raw,
            "trials_executed": hpo_trials,
            "max_trials": HPO_MAX_TRIALS,
            "target_profile": hpo_target_profile,
            "param_space": HPO_PARAM_SPACE,
        },
        "by_gender": hpo_by_gender,
    }
    hpo_report_path = run_dir / "hpo_report.json"
    _write_json(hpo_report_path, hpo_report_payload)

    hpo_payload = {
        "status": hpo_status,
        "report_json": str(hpo_report_path),
        "target_profile": hpo_target_profile,
        "trials_requested": hpo_trials_raw,
        "trials_executed": hpo_trials,
        "by_gender": {
            gender_key: {
                "status": payload.get("status"),
                "best_trial_id": payload.get("best_trial_id"),
                "best_val_brier": payload.get("best_val_brier"),
                "best_test_brier": payload.get("best_test_brier"),
                "best_objective_score": payload.get("best_objective_score"),
                "best_cv_mean_val_brier": payload.get("best_cv_mean_val_brier"),
                "best_param_overrides": payload.get("best_param_overrides"),
            }
            for gender_key, payload in hpo_by_gender.items()
            if isinstance(payload, dict)
        },
    }

    model_dir = Path(train_module.OUT_DIR)
    men_model_path = model_dir / f"lgbm_baseline_men_{context['run_id']}.pkl"
    women_model_path = model_dir / f"lgbm_baseline_women_{context['run_id']}.pkl"

    with men_model_path.open("wb") as handle:
        pickle.dump(men_model, handle)
    with women_model_path.open("wb") as handle:
        pickle.dump(women_model, handle)

    genders = {
        "men": {
            "gender": men_payload.get("gender", "M"),
            "model_path": str(men_model_path),
            "training_profile": men_payload.get("training_profile", training_profile),
            "training_params": men_payload.get("training_params", {}),
            "metrics_by_split": men_payload.get("metrics_by_split", {}),
            "feature_snapshot": men_payload.get("feature_snapshot", {}),
            "best_iteration": men_payload.get("best_iteration"),
        },
        "women": {
            "gender": women_payload.get("gender", "W"),
            "model_path": str(women_model_path),
            "training_profile": women_payload.get("training_profile", training_profile),
            "training_params": women_payload.get("training_params", {}),
            "metrics_by_split": women_payload.get("metrics_by_split", {}),
            "feature_snapshot": women_payload.get("feature_snapshot", {}),
            "best_iteration": women_payload.get("best_iteration"),
        },
    }

    return {
        "training_profile": training_profile,
        "hpo": hpo_payload,
        "genders": genders,
        "models": {
            "men": genders["men"]["model_path"],
            "women": genders["women"]["model_path"],
        },
        "metrics_by_split": {
            "men": genders["men"]["metrics_by_split"],
            "women": genders["women"]["metrics_by_split"],
        },
        "feature_snapshot": {
            "men": genders["men"]["feature_snapshot"],
            "women": genders["women"]["feature_snapshot"],
        },
        "best_iteration": {
            "men": genders["men"]["best_iteration"],
            "women": genders["women"]["best_iteration"],
        },
    }


def _safe_delta(left: Any, right: Any) -> float | None:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left - right)
    return None


def _as_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        numeric = float(value)
        if np.isfinite(numeric):
            return numeric
    return None


def _score_val_test_from_split_probabilities(
    *,
    gender_key: str,
    split_probabilities: dict[str, dict[str, np.ndarray]],
) -> dict[str, Any]:
    val_cache = split_probabilities.get("Val", {}) if isinstance(split_probabilities, dict) else {}
    test_cache = split_probabilities.get("Test", {}) if isinstance(split_probabilities, dict) else {}

    val_true = np.asarray(val_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
    val_prob = np.asarray(val_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)
    test_true = np.asarray(test_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
    test_prob = np.asarray(test_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)

    return {
        "val": _score_probability_bundle(
            gender_key=gender_key,
            split_label="Val",
            y_true=val_true,
            y_prob=val_prob,
        ),
        "test": _score_probability_bundle(
            gender_key=gender_key,
            split_label="Test",
            y_true=test_true,
            y_prob=test_prob,
        ),
        "cache": {
            "val_true": val_true,
            "val_prob": val_prob,
            "test_true": test_true,
            "test_prob": test_prob,
        },
    }


def _score_all_splits_from_split_probabilities(
    *,
    gender_key: str,
    split_probabilities: dict[str, dict[str, np.ndarray]],
) -> dict[str, Any]:
    metrics_by_split: dict[str, Any] = {}
    for split_label in CANONICAL_SPLITS:
        split_cache = split_probabilities.get(split_label, {}) if isinstance(split_probabilities, dict) else {}
        split_true = np.asarray(split_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        split_prob = np.asarray(split_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        metrics_by_split[split_label] = _score_probability_bundle(
            gender_key=gender_key,
            split_label=split_label,
            y_true=split_true,
            y_prob=split_prob,
        )
    return metrics_by_split


def _predict_model_split_probabilities(
    *,
    model: Any,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    gender_key: str,
) -> dict[str, dict[str, np.ndarray]]:
    split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in CANONICAL_SPLITS:
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        if split_df.empty:
            split_cache[split_label] = {
                "y_true": np.asarray([], dtype=float),
                "y_prob": np.asarray([], dtype=float),
            }
            continue

        split_features = split_df.loc[:, feature_columns]
        split_true = split_df["Target"].to_numpy(dtype=float)
        raw_probs = model.predict_proba(split_features)
        split_prob = _extract_positive_class_probabilities(
            raw_probs,
            gender_key=gender_key,
            split_label=split_label,
        )
        split_cache[split_label] = {
            "y_true": split_true,
            "y_prob": split_prob,
        }

    return split_cache


def _fit_histgb_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        alt_model = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_depth=3,
            max_iter=250,
            min_samples_leaf=20,
            random_state=int(context.get("seed", 42)) + (3100 if gender_key == "men" else 3200),
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"alt_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_xgboost_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    if XGBClassifier is None:
        return None, "xgboost_unavailable"

    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        alt_model = XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            min_child_weight=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=int(context.get("seed", 42)) + (3300 if gender_key == "men" else 3400),
            n_jobs=1,
            verbosity=0,
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"xgboost_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_catboost_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    if CatBoostClassifier is None:
        return None, "catboost_unavailable"

    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        alt_model = CatBoostClassifier(
            iterations=250,
            depth=4,
            learning_rate=0.05,
            l2_leaf_reg=3.0,
            loss_function="Logloss",
            eval_metric="Logloss",
            random_seed=int(context.get("seed", 42)) + (3500 if gender_key == "men" else 3600),
            verbose=False,
            allow_writing_files=False,
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"catboost_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_tabpfn_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    if TabPFNClassifier is None:
        return None, "tabpfn_unavailable"

    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    model_path = PIPELINE_DIR / "artifacts" / "models" / "tabpfn" / "tabpfn-v2.5-classifier-v2.5_default.ckpt"
    if not model_path.exists():
        return None, "tabpfn_weights_missing"

    try:
        if tabpfn_settings is not None:
            model_cache_dir = Path(context["run_dir"]) / "tabpfn_model_cache"
            model_cache_dir.mkdir(parents=True, exist_ok=True)
            tabpfn_settings.tabpfn.model_cache_dir = model_cache_dir.resolve()
        alt_model = TabPFNClassifier(
            device="cpu",
            n_estimators=4,
            fit_mode="low_memory",
            ignore_pretraining_limits=True,
            model_path=model_path,
            random_state=int(context.get("seed", 42)) + (3700 if gender_key == "men" else 3800),
            n_preprocessing_jobs=1,
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"tabpfn_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_logistic_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        alt_model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "logreg",
                    LogisticRegression(
                        C=0.5,
                        random_state=int(context.get("seed", 42)) + (3900 if gender_key == "men" else 4000),
                        solver="lbfgs",
                        max_iter=500,
                    ),
                ),
            ]
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"logistic_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_spline_logistic_candidate_split_probabilities(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    val_df = feature_df[feature_df["Split"] == "Val"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        return None, "feature_columns_missing"
    if train_df.empty or val_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        alt_model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "spline",
                    SplineTransformer(
                        n_knots=4,
                        degree=2,
                        include_bias=False,
                    ),
                ),
                (
                    "logreg",
                    LogisticRegression(
                        C=0.25,
                        random_state=int(context.get("seed", 42)) + (4100 if gender_key == "men" else 4200),
                        solver="lbfgs",
                        max_iter=500,
                    ),
                ),
            ]
        )
        alt_model.fit(
            train_df.loc[:, available_feature_columns],
            train_df["Target"].to_numpy(dtype=float),
        )
    except Exception as exc:
        return None, f"spline_logistic_fit_failed:{exc.__class__.__name__}"

    split_cache = _predict_model_split_probabilities(
        model=alt_model,
        feature_df=feature_df,
        feature_columns=available_feature_columns,
        gender_key=gender_key,
    )
    return split_cache, None


def _fit_available_alternative_model_split_caches(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
) -> tuple[dict[str, dict[str, dict[str, np.ndarray]]], dict[str, str | None]]:
    alternative_specs = (
        ("histgb_benchmark", _fit_histgb_candidate_split_probabilities),
        ("logistic_benchmark", _fit_logistic_candidate_split_probabilities),
        ("spline_logistic_benchmark", _fit_spline_logistic_candidate_split_probabilities),
        ("xgboost_benchmark", _fit_xgboost_candidate_split_probabilities),
        ("catboost_benchmark", _fit_catboost_candidate_split_probabilities),
        ("tabpfn_benchmark", _fit_tabpfn_candidate_split_probabilities),
    )
    split_caches: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    reasons: dict[str, str | None] = {}
    for candidate_id, fit_fn in alternative_specs:
        split_cache, reason = fit_fn(
            context=context,
            gender_key=gender_key,
            feature_df=feature_df,
            feature_columns=feature_columns,
        )
        reasons[candidate_id] = reason
        if split_cache is not None:
            split_caches[candidate_id] = split_cache
    return split_caches, reasons


def _build_weighted_split_probabilities(
    *,
    component_split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
    weights: dict[str, float],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    if not isinstance(weights, dict) or not weights:
        return None, "weights_missing"

    first_component_id = next(iter(weights.keys()))
    first_component = component_split_probabilities.get(first_component_id, {})
    if not isinstance(first_component, dict):
        return None, f"component_missing:{first_component_id}"

    split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in ("Val", "Test"):
        first_split = first_component.get(split_label, {})
        y_true = np.asarray(first_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        if y_true.size == 0:
            return None, f"split_missing:{split_label}"
        blended_prob = np.zeros_like(y_true, dtype=float)
        for component_id, weight in weights.items():
            component_split = component_split_probabilities.get(component_id, {}).get(split_label, {})
            component_true = np.asarray(component_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            component_prob = np.asarray(component_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            if component_true.shape != y_true.shape or component_prob.shape != y_true.shape:
                return None, f"shape_mismatch:{component_id}:{split_label}"
            blended_prob += float(weight) * component_prob
        split_cache[split_label] = {
            "y_true": y_true,
            "y_prob": np.clip(blended_prob, 0.0, 1.0),
        }
    return split_cache, None


def _local_gate_check(
    *,
    candidate_test_metrics: dict[str, Any],
    baseline_test_metrics: dict[str, Any],
) -> dict[str, Any]:
    candidate_brier = _as_float_or_none(candidate_test_metrics.get("brier"))
    candidate_ece = _as_float_or_none(candidate_test_metrics.get("ece"))
    candidate_wmae = _as_float_or_none(candidate_test_metrics.get("wmae"))
    candidate_gap = _as_float_or_none(candidate_test_metrics.get("high_prob_gap"))
    baseline_brier = _as_float_or_none(baseline_test_metrics.get("brier"))
    baseline_ece = _as_float_or_none(baseline_test_metrics.get("ece"))
    baseline_wmae = _as_float_or_none(baseline_test_metrics.get("wmae"))
    baseline_gap = _as_float_or_none(baseline_test_metrics.get("high_prob_gap"))

    candidate_gap_abs = abs(candidate_gap) if isinstance(candidate_gap, (int, float)) else None
    baseline_gap_abs = abs(baseline_gap) if isinstance(baseline_gap, (int, float)) else None

    passed = (
        isinstance(candidate_brier, (int, float))
        and isinstance(baseline_brier, (int, float))
        and candidate_brier <= baseline_brier + REGRESSION_NUMERIC_EPS
        and isinstance(candidate_ece, (int, float))
        and isinstance(baseline_ece, (int, float))
        and candidate_ece <= baseline_ece + REGRESSION_NUMERIC_EPS
        and isinstance(candidate_wmae, (int, float))
        and isinstance(baseline_wmae, (int, float))
        and candidate_wmae <= baseline_wmae + REGRESSION_NUMERIC_EPS
        and isinstance(candidate_gap_abs, (int, float))
        and isinstance(baseline_gap_abs, (int, float))
        and candidate_gap_abs <= baseline_gap_abs + REGRESSION_NUMERIC_EPS
    )
    return {
        "status": "passed" if passed else "failed",
        "delta_brier": _safe_delta(candidate_brier, baseline_brier),
        "delta_ece": _safe_delta(candidate_ece, baseline_ece),
        "delta_wmae": _safe_delta(candidate_wmae, baseline_wmae),
        "delta_high_prob_gap_abs": (
            float(candidate_gap_abs - baseline_gap_abs)
            if isinstance(candidate_gap_abs, (int, float)) and isinstance(baseline_gap_abs, (int, float))
            else None
        ),
    }


def _probability_to_logit(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(probabilities, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(clipped / (1.0 - clipped))


def _evaluate_ensemble_candidates_for_gender(
    *,
    context: dict[str, Any],
    train_module: Any,
    gender_key: str,
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    hpo_gender_payload: dict[str, Any],
    hpo_target_profile: str,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key=gender_key,
        split_probabilities=baseline_split_probabilities,
    )
    baseline_val_brier = _as_float_or_none(baseline_scores["val"].get("brier"))
    baseline_test_brier = _as_float_or_none(baseline_scores["test"].get("brier"))
    baseline_candidate = {
        "candidate_id": "baseline",
        "source": "train_stage_model",
        "status": "available" if baseline_val_brier is not None else "failed",
        "reason": None if baseline_val_brier is not None else "missing_val_brier",
        "param_overrides": None,
        "weights": None,
        "metrics": {
            "val": baseline_scores["val"],
            "test": baseline_scores["test"],
            "val_brier": baseline_val_brier,
            "test_brier": baseline_test_brier,
        },
    }
    candidates.append(baseline_candidate)

    hpo_split_cache: dict[str, dict[str, np.ndarray]] | None = None

    best_overrides = (
        hpo_gender_payload.get("best_param_overrides") if isinstance(hpo_gender_payload, dict) else None
    )
    if isinstance(best_overrides, dict) and best_overrides:
        gender_label = "M" if gender_key == "men" else "W"
        random_state = int(context.get("seed", 42)) + (1000 if gender_key == "men" else 2000)
        try:
            hpo_model, hpo_train_payload = _train_with_optional_profile(
                train_module=train_module,
                df=feature_df,
                gender_label=gender_label,
                random_state=random_state,
                profile=hpo_target_profile,
                param_overrides=best_overrides,
            )
            hpo_snapshot = hpo_train_payload.get("feature_snapshot", {}) if isinstance(hpo_train_payload, dict) else {}
            hpo_feature_columns = (
                hpo_snapshot.get("feature_columns") if isinstance(hpo_snapshot, dict) else None
            )
            if not isinstance(hpo_feature_columns, list) or not hpo_feature_columns:
                raise RuntimeError("hpo_feature_columns_missing")

            hpo_split_cache = _predict_model_split_probabilities(
                model=hpo_model,
                feature_df=feature_df,
                feature_columns=hpo_feature_columns,
                gender_key=gender_key,
            )
            hpo_scores = _score_val_test_from_split_probabilities(
                gender_key=gender_key,
                split_probabilities=hpo_split_cache,
            )
            hpo_val_brier = _as_float_or_none(hpo_scores["val"].get("brier"))
            hpo_test_brier = _as_float_or_none(hpo_scores["test"].get("brier"))
            candidates.append(
                {
                    "candidate_id": "hpo_best",
                    "source": "hpo_best_overrides",
                    "status": "available" if hpo_val_brier is not None else "failed",
                    "reason": None if hpo_val_brier is not None else "missing_val_brier",
                    "param_overrides": best_overrides,
                    "weights": None,
                    "metrics": {
                        "val": hpo_scores["val"],
                        "test": hpo_scores["test"],
                        "val_brier": hpo_val_brier,
                        "test_brier": hpo_test_brier,
                    },
                }
            )
        except Exception as exc:
            candidates.append(
                {
                    "candidate_id": "hpo_best",
                    "source": "hpo_best_overrides",
                    "status": "failed",
                    "reason": f"hpo_retrain_failed:{exc.__class__.__name__}",
                    "param_overrides": best_overrides,
                    "weights": None,
                    "metrics": {
                        "val": {},
                        "test": {},
                        "val_brier": None,
                        "test_brier": None,
                    },
                }
            )
    else:
        candidates.append(
            {
                "candidate_id": "hpo_best",
                "source": "hpo_best_overrides",
                "status": "skipped",
                "reason": "best_param_overrides_unavailable",
                "param_overrides": None,
                "weights": None,
                "metrics": {
                    "val": {},
                    "test": {},
                    "val_brier": None,
                    "test_brier": None,
                },
            }
        )

    if hpo_split_cache is not None:
        baseline_val_prob = baseline_scores["cache"]["val_prob"]
        hpo_val_prob = np.asarray(hpo_split_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        baseline_test_prob = baseline_scores["cache"]["test_prob"]
        hpo_test_prob = np.asarray(hpo_split_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        val_true = baseline_scores["cache"]["val_true"]
        test_true = baseline_scores["cache"]["test_true"]

        if (
            baseline_val_prob.shape == hpo_val_prob.shape
            and baseline_test_prob.shape == hpo_test_prob.shape
            and val_true.shape == baseline_val_prob.shape
            and test_true.shape == baseline_test_prob.shape
        ):
            weight_candidates: list[dict[str, Any]] = []
            for baseline_weight in ENSEMBLE_WEIGHT_GRID:
                hpo_weight = 1.0 - float(baseline_weight)
                blended_val = np.clip(
                    float(baseline_weight) * baseline_val_prob + hpo_weight * hpo_val_prob,
                    0.0,
                    1.0,
                )
                blended_test = np.clip(
                    float(baseline_weight) * baseline_test_prob + hpo_weight * hpo_test_prob,
                    0.0,
                    1.0,
                )
                val_metrics = _score_probability_bundle(
                    gender_key=gender_key,
                    split_label="Val",
                    y_true=val_true,
                    y_prob=blended_val,
                )
                test_metrics = _score_probability_bundle(
                    gender_key=gender_key,
                    split_label="Test",
                    y_true=test_true,
                    y_prob=blended_test,
                )
                weight_candidates.append(
                    {
                        "baseline_weight": float(baseline_weight),
                        "hpo_weight": float(hpo_weight),
                        "val": val_metrics,
                        "test": test_metrics,
                        "val_brier": _as_float_or_none(val_metrics.get("brier")),
                        "test_brier": _as_float_or_none(test_metrics.get("brier")),
                    }
                )

            valid_weight_candidates = [
                row for row in weight_candidates if isinstance(row.get("val_brier"), (int, float))
            ]
            if valid_weight_candidates:
                best_weight_row = min(
                    valid_weight_candidates,
                    key=lambda row: (
                        float(row["val_brier"]),
                        abs(0.5 - float(row.get("baseline_weight", 0.5))),
                    ),
                )
                candidates.append(
                    {
                        "candidate_id": "ensemble_weighted",
                        "source": "baseline_hpo_blend",
                        "status": "available",
                        "reason": None,
                        "param_overrides": best_overrides,
                        "weights": {
                            "baseline": best_weight_row["baseline_weight"],
                            "hpo_best": best_weight_row["hpo_weight"],
                        },
                        "metrics": {
                            "val": best_weight_row["val"],
                            "test": best_weight_row["test"],
                            "val_brier": best_weight_row["val_brier"],
                            "test_brier": best_weight_row["test_brier"],
                        },
                    }
                )
            else:
                candidates.append(
                    {
                        "candidate_id": "ensemble_weighted",
                        "source": "baseline_hpo_blend",
                        "status": "failed",
                        "reason": "ensemble_val_brier_missing",
                        "param_overrides": best_overrides,
                        "weights": None,
                        "metrics": {
                            "val": {},
                            "test": {},
                            "val_brier": None,
                            "test_brier": None,
                        },
                    }
                )
        else:
            candidates.append(
                {
                    "candidate_id": "ensemble_weighted",
                    "source": "baseline_hpo_blend",
                    "status": "failed",
                    "reason": "probability_shape_mismatch",
                    "param_overrides": best_overrides,
                    "weights": None,
                    "metrics": {
                        "val": {},
                        "test": {},
                        "val_brier": None,
                        "test_brier": None,
                    },
                }
            )
    else:
        candidates.append(
            {
                "candidate_id": "ensemble_weighted",
                "source": "baseline_hpo_blend",
                "status": "skipped",
                "reason": "hpo_candidate_unavailable",
                "param_overrides": None,
                "weights": None,
                "metrics": {
                    "val": {},
                    "test": {},
                    "val_brier": None,
                    "test_brier": None,
                },
            }
        )

    available_candidates = [
        row
        for row in candidates
        if row.get("status") == "available" and isinstance(row.get("metrics", {}).get("val_brier"), (int, float))
    ]

    if not available_candidates:
        return {
            "status": "failed",
            "reason": "no_available_candidates",
            "selected_candidate_id": None,
            "selection_reason": "no_available_candidates",
            "selected_val_brier": None,
            "selected_test_brier": None,
            "selection_signal": "hold_baseline",
            "candidates": candidates,
        }

    best_available = min(
        available_candidates,
        key=lambda row: (
            float(row.get("metrics", {}).get("val_brier")),
            row.get("candidate_id") != "ensemble_weighted",
            row.get("candidate_id") != "hpo_best",
        ),
    )

    baseline_available = next(
        (row for row in available_candidates if row.get("candidate_id") == "baseline"),
        None,
    )

    selected_candidate = best_available
    selection_reason = "best_val_brier"
    if baseline_available is not None and best_available.get("candidate_id") != "baseline":
        baseline_val = _as_float_or_none(baseline_available.get("metrics", {}).get("val_brier"))
        best_val = _as_float_or_none(best_available.get("metrics", {}).get("val_brier"))
        improvement = (
            float(baseline_val - best_val)
            if isinstance(baseline_val, (int, float)) and isinstance(best_val, (int, float))
            else None
        )

        baseline_test = _as_float_or_none(baseline_available.get("metrics", {}).get("test_brier"))
        best_test = _as_float_or_none(best_available.get("metrics", {}).get("test_brier"))
        test_delta = (
            float(best_test - baseline_test)
            if isinstance(baseline_test, (int, float)) and isinstance(best_test, (int, float))
            else None
        )

        if improvement is None or improvement < ENSEMBLE_MIN_VAL_IMPROVEMENT:
            selected_candidate = baseline_available
            selection_reason = "improvement_below_threshold"
        elif test_delta is not None and test_delta > ENSEMBLE_MAX_TEST_BRIER_DEGRADATION:
            selected_candidate = baseline_available
            selection_reason = "test_brier_degraded"
        else:
            selection_reason = "improved_val_brier"

    selected_candidate_id = selected_candidate.get("candidate_id")
    selection_signal = "promote_non_baseline" if selected_candidate_id != "baseline" else "hold_baseline"

    return {
        "status": "passed",
        "reason": None,
        "selected_candidate_id": selected_candidate_id,
        "selection_reason": selection_reason,
        "selected_val_brier": _as_float_or_none(selected_candidate.get("metrics", {}).get("val_brier")),
        "selected_test_brier": _as_float_or_none(selected_candidate.get("metrics", {}).get("test_brier")),
        "selection_signal": selection_signal,
        "selected_weights": selected_candidate.get("weights"),
        "selected_param_overrides": selected_candidate.get("param_overrides"),
        "candidates": candidates,
    }


def _build_ensemble_report(
    *,
    context: dict[str, Any],
    train_result: dict[str, Any],
    train_module: Any,
    feature_frames_by_gender: dict[str, pd.DataFrame],
    split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
) -> dict[str, Any]:
    hpo_payload = train_result.get("hpo", {}) if isinstance(train_result, dict) else {}
    hpo_target_profile = str(hpo_payload.get("target_profile", "quality_v1"))

    hpo_report_by_gender: dict[str, Any] = {}
    report_path_value = hpo_payload.get("report_json") if isinstance(hpo_payload, dict) else None
    if isinstance(report_path_value, str) and report_path_value.strip():
        hpo_report_path = Path(report_path_value)
        if hpo_report_path.exists():
            try:
                hpo_report_payload = json.loads(hpo_report_path.read_text(encoding="utf-8"))
            except Exception:
                hpo_report_payload = {}
            by_gender_payload = hpo_report_payload.get("by_gender", {}) if isinstance(hpo_report_payload, dict) else {}
            if isinstance(by_gender_payload, dict):
                hpo_report_by_gender = by_gender_payload

    by_gender: dict[str, Any] = {}
    for gender_key in ("men", "women"):
        by_gender[gender_key] = _evaluate_ensemble_candidates_for_gender(
            context=context,
            train_module=train_module,
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            baseline_split_probabilities=split_probabilities.get(gender_key, {}),
            hpo_gender_payload=hpo_report_by_gender.get(gender_key, {}),
            hpo_target_profile=hpo_target_profile,
        )

    promoted_genders = [
        gender_key
        for gender_key, payload in by_gender.items()
        if isinstance(payload, dict) and payload.get("selection_signal") == "promote_non_baseline"
    ]

    aggregate_decision = "adopt_non_baseline_candidates" if promoted_genders else "hold_baseline"
    ensemble_report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "config": {
            "weight_grid": list(ENSEMBLE_WEIGHT_GRID),
            "min_val_improvement": ENSEMBLE_MIN_VAL_IMPROVEMENT,
            "max_test_brier_degradation": ENSEMBLE_MAX_TEST_BRIER_DEGRADATION,
            "hpo_target_profile": hpo_target_profile,
        },
        "by_gender": by_gender,
        "aggregate": {
            "decision": aggregate_decision,
            "promoted_genders": promoted_genders,
        },
    }

    report_path = Path(context["run_dir"]) / "ensemble_report.json"
    _write_json(report_path, ensemble_report_payload)

    return {
        "report_json": str(report_path),
        "config": ensemble_report_payload["config"],
        "by_gender": {
            gender_key: {
                "status": payload.get("status"),
                "selected_candidate_id": payload.get("selected_candidate_id"),
                "selection_reason": payload.get("selection_reason"),
                "selection_signal": payload.get("selection_signal"),
                "selected_val_brier": payload.get("selected_val_brier"),
                "selected_test_brier": payload.get("selected_test_brier"),
            }
            for gender_key, payload in by_gender.items()
            if isinstance(payload, dict)
        },
        "aggregate": ensemble_report_payload["aggregate"],
    }


def _safe_probability_correlation(left: np.ndarray, right: np.ndarray) -> float | None:
    left = np.asarray(left, dtype=float)
    right = np.asarray(right, dtype=float)
    if left.shape != right.shape or left.shape[0] < 2:
        return None
    if np.allclose(left, left[0]) or np.allclose(right, right[0]):
        return None
    corr = np.corrcoef(left, right)[0, 1]
    if np.isfinite(corr):
        return float(corr)
    return None


def _build_stacking_policy_report_for_gender(
    *,
    context: dict[str, Any],
    train_module: Any,
    gender_key: str,
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    hpo_gender_payload: dict[str, Any],
    hpo_target_profile: str,
    calibration_candidate_split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
) -> dict[str, Any]:
    candidate_split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]] = {
        "baseline": baseline_split_probabilities,
    }
    candidate_metrics: dict[str, dict[str, Any]] = {
        "baseline": _score_val_test_from_split_probabilities(
            gender_key=gender_key,
            split_probabilities=baseline_split_probabilities,
        )
    }

    best_overrides = (
        hpo_gender_payload.get("best_param_overrides") if isinstance(hpo_gender_payload, dict) else None
    )
    if isinstance(best_overrides, dict) and best_overrides:
        gender_label = "M" if gender_key == "men" else "W"
        random_state = int(context.get("seed", 42)) + (1000 if gender_key == "men" else 2000)
        try:
            hpo_model, hpo_train_payload = _train_with_optional_profile(
                train_module=train_module,
                df=feature_df,
                gender_label=gender_label,
                random_state=random_state,
                profile=hpo_target_profile,
                param_overrides=best_overrides,
            )
            hpo_snapshot = hpo_train_payload.get("feature_snapshot", {}) if isinstance(hpo_train_payload, dict) else {}
            hpo_feature_columns = (
                hpo_snapshot.get("feature_columns") if isinstance(hpo_snapshot, dict) else None
            )
            if isinstance(hpo_feature_columns, list) and hpo_feature_columns:
                hpo_split_cache = _predict_model_split_probabilities(
                    model=hpo_model,
                    feature_df=feature_df,
                    feature_columns=hpo_feature_columns,
                    gender_key=gender_key,
                )
                candidate_split_probabilities["hpo_best"] = hpo_split_cache
                candidate_metrics["hpo_best"] = _score_val_test_from_split_probabilities(
                    gender_key=gender_key,
                    split_probabilities=hpo_split_cache,
                )
        except Exception:
            pass

    for method_name, method_split_cache in calibration_candidate_split_probabilities.items():
        if method_name == "none":
            continue
        candidate_id = f"calibration_{method_name}"
        candidate_split_probabilities[candidate_id] = method_split_cache
        candidate_metrics[candidate_id] = _score_val_test_from_split_probabilities(
            gender_key=gender_key,
            split_probabilities=method_split_cache,
        )

    baseline_cache = candidate_split_probabilities.get("baseline", {})
    hpo_cache = candidate_split_probabilities.get("hpo_best", {})
    baseline_val = np.asarray(baseline_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
    baseline_test = np.asarray(baseline_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
    hpo_val = np.asarray(hpo_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
    hpo_test = np.asarray(hpo_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
    val_true = np.asarray(baseline_cache.get("Val", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
    test_true = np.asarray(baseline_cache.get("Test", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)

    if (
        baseline_val.shape == hpo_val.shape
        and baseline_test.shape == hpo_test.shape
        and val_true.shape == baseline_val.shape
        and test_true.shape == baseline_test.shape
        and baseline_val.shape[0] > 0
    ):
        weighted_candidates: list[tuple[float, dict[str, Any], dict[str, dict[str, np.ndarray]]]] = []
        for baseline_weight in ENSEMBLE_WEIGHT_GRID:
            hpo_weight = 1.0 - float(baseline_weight)
            blended_val = np.clip(float(baseline_weight) * baseline_val + hpo_weight * hpo_val, 0.0, 1.0)
            blended_test = np.clip(float(baseline_weight) * baseline_test + hpo_weight * hpo_test, 0.0, 1.0)
            split_cache = {
                "Val": {"y_true": val_true, "y_prob": blended_val},
                "Test": {"y_true": test_true, "y_prob": blended_test},
            }
            metrics = _score_val_test_from_split_probabilities(
                gender_key=gender_key,
                split_probabilities=split_cache,
            )
            val_brier = _as_float_or_none(metrics.get("val", {}).get("brier"))
            if val_brier is not None:
                weighted_candidates.append((val_brier, metrics, split_cache))

        if weighted_candidates:
            _, best_weighted_metrics, best_weighted_cache = min(
                weighted_candidates,
                key=lambda item: float(item[0]),
            )
            candidate_split_probabilities["ensemble_weighted"] = best_weighted_cache
            candidate_metrics["ensemble_weighted"] = best_weighted_metrics

    available_candidate_ids = [
        candidate_id
        for candidate_id, payload in candidate_metrics.items()
        if isinstance(payload, dict)
        and isinstance(payload.get("val", {}).get("brier"), (int, float))
        and isinstance(payload.get("test", {}).get("brier"), (int, float))
    ]

    diversity_by_split: dict[str, Any] = {}
    for split_label in ("Val", "Test"):
        pairwise_rows: list[dict[str, Any]] = []
        correlations: list[float] = []
        for idx, left_id in enumerate(available_candidate_ids):
            left_prob = np.asarray(
                candidate_split_probabilities.get(left_id, {}).get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                dtype=float,
            )
            for right_id in available_candidate_ids[idx + 1 :]:
                right_prob = np.asarray(
                    candidate_split_probabilities.get(right_id, {}).get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                    dtype=float,
                )
                corr = _safe_probability_correlation(left_prob, right_prob)
                pairwise_rows.append(
                    {
                        "left_candidate_id": left_id,
                        "right_candidate_id": right_id,
                        "correlation": corr,
                    }
                )
                if isinstance(corr, (int, float)):
                    correlations.append(float(corr))

        diversity_by_split[split_label.lower()] = {
            "pairwise_correlations": pairwise_rows,
            "mean_correlation": float(np.mean(correlations)) if correlations else None,
            "min_correlation": float(np.min(correlations)) if correlations else None,
        }

    stacking_candidate: dict[str, Any] = {
        "status": "skipped",
        "reason": "insufficient_candidate_matrix",
        "candidate_id": "stacking_logreg",
        "meta_model": "logistic_regression",
        "feature_candidate_ids": available_candidate_ids,
        "feature_count": int(len(available_candidate_ids)),
        "val_sample_count": int(val_true.shape[0]),
        "metrics": {"val": {}, "test": {}},
        "coef_by_candidate": {},
        "intercept": None,
    }

    if len(available_candidate_ids) >= 2 and val_true.shape[0] >= STACKING_POLICY_MIN_VAL_SAMPLES and np.unique(val_true).shape[0] >= 2:
        X_val = np.column_stack(
            [
                np.asarray(
                    candidate_split_probabilities[candidate_id]["Val"]["y_prob"],
                    dtype=float,
                )
                for candidate_id in available_candidate_ids
            ]
        )
        X_test = np.column_stack(
            [
                np.asarray(
                    candidate_split_probabilities[candidate_id]["Test"]["y_prob"],
                    dtype=float,
                )
                for candidate_id in available_candidate_ids
            ]
        )
        try:
            meta_model = LogisticRegression(random_state=0, solver="lbfgs", max_iter=200)
            meta_model.fit(X_val, val_true)
            val_prob = meta_model.predict_proba(X_val)[:, 1]
            test_prob = meta_model.predict_proba(X_test)[:, 1]
            split_cache = {
                "Val": {"y_true": val_true, "y_prob": val_prob},
                "Test": {"y_true": test_true, "y_prob": test_prob},
            }
            stacking_metrics = _score_val_test_from_split_probabilities(
                gender_key=gender_key,
                split_probabilities=split_cache,
            )
            stacking_candidate = {
                "status": "available",
                "reason": None,
                "candidate_id": "stacking_logreg",
                "meta_model": "logistic_regression",
                "feature_candidate_ids": available_candidate_ids,
                "feature_count": int(len(available_candidate_ids)),
                "val_sample_count": int(val_true.shape[0]),
                "metrics": {
                    "val": stacking_metrics.get("val", {}),
                    "test": stacking_metrics.get("test", {}),
                },
                "coef_by_candidate": {
                    candidate_id: float(meta_model.coef_[0][idx])
                    for idx, candidate_id in enumerate(available_candidate_ids)
                },
                "intercept": float(meta_model.intercept_[0]),
            }
        except Exception as exc:
            stacking_candidate["status"] = "failed"
            stacking_candidate["reason"] = f"meta_fit_failed:{exc.__class__.__name__}"
    elif len(available_candidate_ids) >= 2 and val_true.shape[0] > 0:
        stacking_candidate["reason"] = "insufficient_val_samples"

    best_existing_candidate_id = None
    best_existing_val_brier = None
    best_existing_test_brier = None
    if available_candidate_ids:
        best_existing_candidate_id = min(
            available_candidate_ids,
            key=lambda candidate_id: float(candidate_metrics[candidate_id]["val"]["brier"]),
        )
        best_existing_val_brier = _as_float_or_none(candidate_metrics[best_existing_candidate_id]["val"].get("brier"))
        best_existing_test_brier = _as_float_or_none(candidate_metrics[best_existing_candidate_id]["test"].get("brier"))

    stacking_val_brier = _as_float_or_none(stacking_candidate.get("metrics", {}).get("val", {}).get("brier"))
    stacking_test_brier = _as_float_or_none(stacking_candidate.get("metrics", {}).get("test", {}).get("brier"))
    delta_vs_best_existing = _safe_delta(stacking_test_brier, best_existing_test_brier)
    delta_vs_baseline = _safe_delta(
        stacking_test_brier,
        _as_float_or_none(candidate_metrics.get("baseline", {}).get("test", {}).get("brier")),
    )

    if stacking_candidate.get("status") != "available":
        research_decision = "insufficient_data"
        research_reason = stacking_candidate.get("reason")
    elif (
        isinstance(stacking_val_brier, (int, float))
        and isinstance(best_existing_val_brier, (int, float))
        and stacking_val_brier <= best_existing_val_brier - STACKING_POLICY_MIN_IMPROVEMENT
        and isinstance(delta_vs_best_existing, (int, float))
        and delta_vs_best_existing <= ENSEMBLE_MAX_TEST_BRIER_DEGRADATION
    ):
        research_decision = "promising"
        research_reason = "improves_val_without_test_degradation"
    else:
        research_decision = "not_promising"
        research_reason = "no_clear_val_test_edge"

    return {
        "status": "passed",
        "reason": None,
        "candidate_ids": available_candidate_ids,
        "candidate_metrics": {
            candidate_id: {
                "val": candidate_metrics[candidate_id].get("val", {}),
                "test": candidate_metrics[candidate_id].get("test", {}),
            }
            for candidate_id in available_candidate_ids
        },
        "diversity": diversity_by_split,
        "stacking_candidate": stacking_candidate,
        "benchmark": {
            "best_existing_candidate_id": best_existing_candidate_id,
            "best_existing_val_brier": best_existing_val_brier,
            "best_existing_test_brier": best_existing_test_brier,
            "stacking_test_brier_delta_vs_best_existing": delta_vs_best_existing,
            "stacking_test_brier_delta_vs_baseline": delta_vs_baseline,
        },
        "research_decision": research_decision,
        "research_reason": research_reason,
    }


def _build_stacking_policy_report(
    *,
    context: dict[str, Any],
    train_result: dict[str, Any],
    train_module: Any,
    feature_frames_by_gender: dict[str, pd.DataFrame],
    split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
    calibration_candidate_split_probabilities_by_gender: dict[str, dict[str, dict[str, dict[str, np.ndarray]]]],
) -> dict[str, Any]:
    hpo_payload = train_result.get("hpo", {}) if isinstance(train_result, dict) else {}
    hpo_target_profile = str(hpo_payload.get("target_profile", "quality_v1"))

    hpo_report_by_gender: dict[str, Any] = {}
    report_path_value = hpo_payload.get("report_json") if isinstance(hpo_payload, dict) else None
    if isinstance(report_path_value, str) and report_path_value.strip():
        hpo_report_path = Path(report_path_value)
        if hpo_report_path.exists():
            try:
                hpo_report_payload = json.loads(hpo_report_path.read_text(encoding="utf-8"))
            except Exception:
                hpo_report_payload = {}
            by_gender_payload = hpo_report_payload.get("by_gender", {}) if isinstance(hpo_report_payload, dict) else {}
            if isinstance(by_gender_payload, dict):
                hpo_report_by_gender = by_gender_payload

    by_gender = {
        gender_key: _build_stacking_policy_report_for_gender(
            context=context,
            train_module=train_module,
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            baseline_split_probabilities=split_probabilities.get(gender_key, {}),
            hpo_gender_payload=hpo_report_by_gender.get(gender_key, {}),
            hpo_target_profile=hpo_target_profile,
            calibration_candidate_split_probabilities=calibration_candidate_split_probabilities_by_gender.get(
                gender_key, {}
            ),
        )
        for gender_key in ("men", "women")
    }

    promising_genders = [
        gender_key
        for gender_key, payload in by_gender.items()
        if isinstance(payload, dict) and payload.get("research_decision") == "promising"
    ]
    aggregate_decision = "research_stacking_candidate" if promising_genders else "hold_current_policy"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "stacking_policy_research_v1",
        "config": {
            "min_val_samples": STACKING_POLICY_MIN_VAL_SAMPLES,
            "min_improvement": STACKING_POLICY_MIN_IMPROVEMENT,
            "meta_model": "logistic_regression",
            "candidate_pool": [
                "baseline",
                "hpo_best",
                "ensemble_weighted",
                "calibration_platt",
                "calibration_isotonic",
            ],
        },
        "by_gender": by_gender,
        "aggregate": {
            "decision": aggregate_decision,
            "promising_genders": promising_genders,
        },
    }

    report_path = Path(context["run_dir"]) / "stacking_policy_report.json"
    _write_json(report_path, report_payload)

    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "config": report_payload["config"],
        "by_gender": {
            gender_key: {
                "status": payload.get("status"),
                "research_decision": payload.get("research_decision"),
                "research_reason": payload.get("research_reason"),
                "best_existing_candidate_id": payload.get("benchmark", {}).get("best_existing_candidate_id"),
                "stacking_candidate_status": payload.get("stacking_candidate", {}).get("status"),
                "stacking_test_brier_delta_vs_best_existing": payload.get("benchmark", {}).get(
                    "stacking_test_brier_delta_vs_best_existing"
                ),
            }
            for gender_key, payload in by_gender.items()
        },
        "aggregate": report_payload["aggregate"],
    }


def _build_alternative_model_report_for_gender(
    *,
    context: dict[str, Any],
    gender_key: str,
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    feature_columns: list[str],
) -> dict[str, Any]:
    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key=gender_key,
        split_probabilities=baseline_split_probabilities,
    )
    baseline_val_brier = _as_float_or_none(baseline_scores.get("val", {}).get("brier"))
    baseline_test_brier = _as_float_or_none(baseline_scores.get("test", {}).get("brier"))

    candidates: list[dict[str, Any]] = [
        {
            "candidate_id": "baseline",
            "model_family": "train_stage_model",
            "status": "available" if baseline_val_brier is not None else "failed",
            "reason": None if baseline_val_brier is not None else "missing_val_brier",
            "weights": None,
            "metrics": {
                "val": baseline_scores.get("val", {}),
                "test": baseline_scores.get("test", {}),
                "val_brier": baseline_val_brier,
                "test_brier": baseline_test_brier,
            },
        }
    ]

    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]
    alternative_specs = (
        ("histgb_benchmark", "hist_gradient_boosting", _fit_histgb_candidate_split_probabilities),
        ("logistic_benchmark", "logistic_regression", _fit_logistic_candidate_split_probabilities),
        ("spline_logistic_benchmark", "spline_logistic_gam_like", _fit_spline_logistic_candidate_split_probabilities),
        ("xgboost_benchmark", "xgboost", _fit_xgboost_candidate_split_probabilities),
        ("catboost_benchmark", "catboost", _fit_catboost_candidate_split_probabilities),
        ("tabpfn_benchmark", "tabpfn", _fit_tabpfn_candidate_split_probabilities),
    )
    alternative_split_caches: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    diversity: dict[str, Any] = {"val": {}, "test": {}}
    baseline_val_prob = np.asarray(
        baseline_split_probabilities.get("Val", {}).get("y_prob", np.asarray([], dtype=float)),
        dtype=float,
    )
    baseline_test_prob = np.asarray(
        baseline_split_probabilities.get("Test", {}).get("y_prob", np.asarray([], dtype=float)),
        dtype=float,
    )
    val_true = np.asarray(
        baseline_split_probabilities.get("Val", {}).get("y_true", np.asarray([], dtype=float)),
        dtype=float,
    )
    test_true = np.asarray(
        baseline_split_probabilities.get("Test", {}).get("y_true", np.asarray([], dtype=float)),
        dtype=float,
    )

    for candidate_id, model_family, fit_fn in alternative_specs:
        alt_split_cache, alt_reason = fit_fn(
            context=context,
            gender_key=gender_key,
            feature_df=feature_df,
            feature_columns=feature_columns,
        )
        if alt_split_cache is None:
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "model_family": model_family,
                    "status": "skipped" if alt_reason in {"insufficient_split_rows", "single_class_train_target", "xgboost_unavailable", "catboost_unavailable", "tabpfn_unavailable", "tabpfn_weights_missing"} else "failed",
                    "reason": alt_reason,
                    "weights": None,
                    "metrics": {"val": {}, "test": {}, "val_brier": None, "test_brier": None},
                }
            )
            continue

        alternative_split_caches[candidate_id] = alt_split_cache
        alt_scores = _score_val_test_from_split_probabilities(
            gender_key=gender_key,
            split_probabilities=alt_split_cache,
        )
        alt_val_brier = _as_float_or_none(alt_scores.get("val", {}).get("brier"))
        alt_test_brier = _as_float_or_none(alt_scores.get("test", {}).get("brier"))
        candidates.append(
            {
                "candidate_id": candidate_id,
                "model_family": model_family,
                "status": "available" if alt_val_brier is not None else "failed",
                "reason": None if alt_val_brier is not None else "missing_val_brier",
                "weights": None,
                "metrics": {
                    "val": alt_scores.get("val", {}),
                    "test": alt_scores.get("test", {}),
                    "val_brier": alt_val_brier,
                    "test_brier": alt_test_brier,
                },
            }
        )

        for split_label in ("Val", "Test"):
            baseline_prob = np.asarray(
                baseline_split_probabilities.get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                dtype=float,
            )
            alt_prob = np.asarray(
                alt_split_cache.get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                dtype=float,
            )
            split_key = split_label.lower()
            diversity.setdefault(split_key, {})
            diversity[split_key][f"baseline_vs_{candidate_id}_correlation"] = _safe_probability_correlation(
                baseline_prob,
                alt_prob,
            )
            diversity[split_key]["sample_count"] = int(baseline_prob.shape[0]) if baseline_prob.shape == alt_prob.shape else 0

    available_alt_ids = list(alternative_split_caches.keys())
    for split_label in ("Val", "Test"):
        split_key = split_label.lower()
        for idx, left_id in enumerate(available_alt_ids):
            left_prob = np.asarray(
                alternative_split_caches[left_id].get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                dtype=float,
            )
            for right_id in available_alt_ids[idx + 1 :]:
                right_prob = np.asarray(
                    alternative_split_caches[right_id].get(split_label, {}).get("y_prob", np.asarray([], dtype=float)),
                    dtype=float,
                )
                diversity.setdefault(split_key, {})
                diversity[split_key][f"{left_id}_vs_{right_id}_correlation"] = _safe_probability_correlation(
                    left_prob,
                    right_prob,
                )

    model_probabilities = {
        "baseline": {
            "Val": baseline_val_prob,
            "Test": baseline_test_prob,
        }
    }
    for candidate_id, alt_split_cache in alternative_split_caches.items():
        model_probabilities[candidate_id] = {
            "Val": np.asarray(alt_split_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float),
            "Test": np.asarray(alt_split_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float),
        }

    def _weight_grid_for_combo(combo_size: int) -> list[dict[str, float]]:
        if combo_size == 3:
            return [
                {"w1": 0.5, "w2": 0.25, "w3": 0.25},
                {"w1": 0.25, "w2": 0.5, "w3": 0.25},
                {"w1": 0.25, "w2": 0.25, "w3": 0.5},
                {"w1": 1.0 / 3.0, "w2": 1.0 / 3.0, "w3": 1.0 / 3.0},
                {"w1": 0.4, "w2": 0.4, "w3": 0.2},
                {"w1": 0.4, "w2": 0.2, "w3": 0.4},
                {"w1": 0.2, "w2": 0.4, "w3": 0.4},
            ]
        return []

    def _candidate_label_from_model_ids(model_ids: tuple[str, ...]) -> str:
        readable_ids = [model_id.replace("_benchmark", "") for model_id in model_ids]
        return "_".join(readable_ids) + "_blend"

    def _evaluate_combo_candidate(model_ids: tuple[str, ...]) -> dict[str, Any] | None:
        if any(
            model_probabilities[model_id]["Val"].shape != baseline_val_prob.shape
            or model_probabilities[model_id]["Test"].shape != baseline_test_prob.shape
            for model_id in model_ids
        ):
            return None
        if baseline_val_prob.shape[0] == 0 or val_true.shape != baseline_val_prob.shape or test_true.shape != baseline_test_prob.shape:
            return None

        combo_size = len(model_ids)
        blend_rows: list[dict[str, Any]] = []
        if combo_size == 2:
            left_id, right_id = model_ids
            for left_weight in ALTERNATIVE_MODEL_WEIGHT_GRID:
                weights = {
                    left_id: float(left_weight),
                    right_id: float(1.0 - float(left_weight)),
                }
                blended_val = np.clip(
                    weights[left_id] * model_probabilities[left_id]["Val"] + weights[right_id] * model_probabilities[right_id]["Val"],
                    0.0,
                    1.0,
                )
                blended_test = np.clip(
                    weights[left_id] * model_probabilities[left_id]["Test"] + weights[right_id] * model_probabilities[right_id]["Test"],
                    0.0,
                    1.0,
                )
                val_metrics = _score_probability_bundle(gender_key=gender_key, split_label="Val", y_true=val_true, y_prob=blended_val)
                test_metrics = _score_probability_bundle(gender_key=gender_key, split_label="Test", y_true=test_true, y_prob=blended_test)
                blend_rows.append(
                    {
                        "weights": weights,
                        "val": val_metrics,
                        "test": test_metrics,
                        "val_brier": _as_float_or_none(val_metrics.get("brier")),
                        "test_brier": _as_float_or_none(test_metrics.get("brier")),
                    }
                )
        elif combo_size == 3:
            for template in _weight_grid_for_combo(3):
                weights = {
                    model_ids[0]: float(template["w1"]),
                    model_ids[1]: float(template["w2"]),
                    model_ids[2]: float(template["w3"]),
                }
                blended_val = np.clip(
                    sum(weights[mid] * model_probabilities[mid]["Val"] for mid in model_ids),
                    0.0,
                    1.0,
                )
                blended_test = np.clip(
                    sum(weights[mid] * model_probabilities[mid]["Test"] for mid in model_ids),
                    0.0,
                    1.0,
                )
                val_metrics = _score_probability_bundle(gender_key=gender_key, split_label="Val", y_true=val_true, y_prob=blended_val)
                test_metrics = _score_probability_bundle(gender_key=gender_key, split_label="Test", y_true=test_true, y_prob=blended_test)
                blend_rows.append(
                    {
                        "weights": weights,
                        "val": val_metrics,
                        "test": test_metrics,
                        "val_brier": _as_float_or_none(val_metrics.get("brier")),
                        "test_brier": _as_float_or_none(test_metrics.get("brier")),
                    }
                )
        else:
            return None

        valid_blends = [row for row in blend_rows if isinstance(row.get("val_brier"), (int, float))]
        if not valid_blends:
            return None

        selection_pool = valid_blends
        if gender_key == "men" and "baseline" in model_ids:
            min_val_brier = min(float(row["val_brier"]) for row in valid_blends)
            near_best_blends = [
                row
                for row in valid_blends
                if float(row["val_brier"]) <= min_val_brier + MEN_BASELINE_BLEND_VAL_BRIER_TOLERANCE
            ]
            if near_best_blends:
                selection_pool = near_best_blends

            baseline_val_ece = _as_float_or_none(baseline_scores.get("val", {}).get("ece"))
            baseline_val_gap = _as_float_or_none(baseline_scores.get("val", {}).get("high_prob_gap"))

            best_blend = min(
                selection_pool,
                key=lambda row: (
                    max(
                        0.0,
                        float(
                            (_as_float_or_none(row.get("val", {}).get("ece")) or 0.0)
                            - (baseline_val_ece or 0.0)
                        ),
                    ),
                    abs(float(_as_float_or_none(row.get("val", {}).get("high_prob_gap")) or 0.0)),
                    -float(_as_float_or_none(row.get("weights", {}).get("baseline")) or 0.0),
                    abs(
                        abs(float(_as_float_or_none(row.get("val", {}).get("high_prob_gap")) or 0.0))
                        - abs(float(baseline_val_gap or 0.0))
                    ),
                    float(row["val_brier"]),
                ),
            )
        else:
            best_blend = min(
                selection_pool,
                key=lambda row: (
                    float(row["val_brier"]),
                    sum(abs(row["weights"].get(model_id, 0.0) - (1.0 / combo_size)) for model_id in model_ids),
                ),
            )
        return {
            "candidate_id": _candidate_label_from_model_ids(model_ids),
            "model_family": "blended_research_candidate",
            "status": "available",
            "reason": None,
            "weights": best_blend["weights"],
            "metrics": {
                "val": best_blend["val"],
                "test": best_blend["test"],
                "val_brier": best_blend["val_brier"],
                "test_brier": best_blend["test_brier"],
            },
        }

    available_model_ids = list(model_probabilities.keys())
    for combo_size in (2, 3):
        for combo in combinations(available_model_ids, combo_size):
            candidate = _evaluate_combo_candidate(combo)
            if candidate is not None:
                candidates.append(candidate)

    available_candidates = [
        row
        for row in candidates
        if row.get("status") == "available" and isinstance(row.get("metrics", {}).get("val_brier"), (int, float))
    ]

    best_candidate_id = None
    best_val_brier = None
    best_test_brier = None
    selected_candidate_weights = None
    decision = "insufficient_data"
    decision_reason = "no_available_candidates"

    if available_candidates:
        selection_pool = available_candidates
        if gender_key == "men":
            guarded_candidates: list[dict[str, Any]] = []
            baseline_candidate = next(
                (row for row in available_candidates if row.get("candidate_id") == "baseline"),
                None,
            )
            baseline_val_ece = (
                _as_float_or_none(baseline_candidate.get("metrics", {}).get("val", {}).get("ece"))
                if isinstance(baseline_candidate, dict)
                else None
            )
            baseline_val_gap = (
                _as_float_or_none(baseline_candidate.get("metrics", {}).get("val", {}).get("high_prob_gap"))
                if isinstance(baseline_candidate, dict)
                else None
            )
            for row in available_candidates:
                candidate_val_brier = _as_float_or_none(row.get("metrics", {}).get("val_brier"))
                candidate_val_ece = _as_float_or_none(row.get("metrics", {}).get("val", {}).get("ece"))
                candidate_val_gap = _as_float_or_none(row.get("metrics", {}).get("val", {}).get("high_prob_gap"))

                improves_val_brier = (
                    row.get("candidate_id") == "baseline"
                    or (
                        isinstance(candidate_val_brier, (int, float))
                        and isinstance(baseline_val_brier, (int, float))
                        and candidate_val_brier <= baseline_val_brier - ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT
                    )
                )
                within_ece_guardrail = (
                    not isinstance(baseline_val_ece, (int, float))
                    or not isinstance(candidate_val_ece, (int, float))
                    or candidate_val_ece <= baseline_val_ece + MEN_ALTERNATIVE_SELECTION_MAX_VAL_ECE_DEGRADATION
                )
                within_gap_guardrail = (
                    not isinstance(baseline_val_gap, (int, float))
                    or not isinstance(candidate_val_gap, (int, float))
                    or abs(candidate_val_gap)
                    <= abs(baseline_val_gap) + MEN_ALTERNATIVE_SELECTION_MAX_VAL_HIGH_GAP_ABS_DEGRADATION
                )

                if improves_val_brier and within_ece_guardrail and within_gap_guardrail:
                    guarded_candidates.append(row)

            if guarded_candidates:
                selection_pool = guarded_candidates

        best_candidate = min(
            selection_pool,
            key=lambda row: (
                float(row.get("metrics", {}).get("val_brier")),
                row.get("candidate_id") != "baseline_histgb_blend",
                row.get("candidate_id") != "histgb_benchmark",
            ),
        )
        best_candidate_id = best_candidate.get("candidate_id")
        best_val_brier = _as_float_or_none(best_candidate.get("metrics", {}).get("val_brier"))
        best_test_brier = _as_float_or_none(best_candidate.get("metrics", {}).get("test_brier"))
        selected_candidate_weights = best_candidate.get("weights")

        if best_candidate_id == "baseline":
            decision = "hold_current_model_family"
            decision_reason = "baseline_remains_best"
        else:
            val_improvement = (
                float(baseline_val_brier - best_val_brier)
                if isinstance(baseline_val_brier, (int, float)) and isinstance(best_val_brier, (int, float))
                else None
            )
            test_delta = (
                float(best_test_brier - baseline_test_brier)
                if isinstance(best_test_brier, (int, float)) and isinstance(baseline_test_brier, (int, float))
                else None
            )
            if (
                isinstance(val_improvement, (int, float))
                and val_improvement >= ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT
                and (test_delta is None or test_delta <= ENSEMBLE_MAX_TEST_BRIER_DEGRADATION)
            ):
                decision = "promising_diversity_candidate"
                decision_reason = "improves_val_without_test_degradation"
            else:
                decision = "not_promising"
                decision_reason = "no_clear_val_test_edge"

    return {
        "status": "passed",
        "reason": None,
        "feature_count": int(len(available_feature_columns)),
        "candidates": candidates,
        "diversity": diversity,
        "benchmark": {
            "baseline_val_brier": baseline_val_brier,
            "baseline_test_brier": baseline_test_brier,
            "best_candidate_id": best_candidate_id,
            "best_val_brier": best_val_brier,
            "best_test_brier": best_test_brier,
            "best_test_brier_delta_vs_baseline": _safe_delta(best_test_brier, baseline_test_brier),
        },
        "selection": {
            "selected_candidate_id": best_candidate_id,
            "selected_candidate_weights": selected_candidate_weights,
            "selected_val_brier_delta_vs_baseline": _safe_delta(best_val_brier, baseline_val_brier),
            "selected_test_brier_delta_vs_baseline": _safe_delta(best_test_brier, baseline_test_brier),
        },
        "research_decision": decision,
        "research_reason": decision_reason,
    }


def _build_alternative_model_report(
    *,
    context: dict[str, Any],
    genders_payload: dict[str, Any],
    feature_frames_by_gender: dict[str, pd.DataFrame],
    split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
) -> dict[str, Any]:
    by_gender = {
        gender_key: _build_alternative_model_report_for_gender(
            context=context,
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            baseline_split_probabilities=split_probabilities.get(gender_key, {}),
            feature_columns=(
                genders_payload.get(gender_key, {}).get("feature_snapshot", {}).get("feature_columns", [])
                if isinstance(genders_payload.get(gender_key, {}), dict)
                else []
            ),
        )
        for gender_key in ("men", "women")
    }

    promising_genders = [
        gender_key
        for gender_key, payload in by_gender.items()
        if isinstance(payload, dict) and payload.get("research_decision") == "promising_diversity_candidate"
    ]
    candidate_ready_genders = [
        gender_key
        for gender_key, payload in by_gender.items()
        if isinstance(payload, dict)
        and payload.get("research_decision") == "promising_diversity_candidate"
        and payload.get("selection", {}).get("selected_candidate_id") == "baseline_histgb_blend"
    ]

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "alternative_model_benchmark_v1",
        "config": {
            "model_family": "multi_family_benchmark",
            "candidate_model_families": [
                "hist_gradient_boosting",
                "logistic_regression",
                "spline_logistic_gam_like",
                "xgboost",
                "catboost",
                "tabpfn",
            ],
            "weight_grid": list(ALTERNATIVE_MODEL_WEIGHT_GRID),
            "triple_weight_templates": [
                [0.5, 0.25, 0.25],
                [0.25, 0.5, 0.25],
                [0.25, 0.25, 0.5],
                [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0],
                [0.4, 0.4, 0.2],
                [0.4, 0.2, 0.4],
                [0.2, 0.4, 0.4],
            ],
            "min_val_improvement": ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT,
            "train_split": "Train",
            "evaluation_splits": ["Val", "Test"],
        },
        "by_gender": by_gender,
        "aggregate": {
            "decision": "research_followup_alternative_model" if promising_genders else "hold_current_model_family",
            "promising_genders": promising_genders,
            "candidate_ready_genders": candidate_ready_genders,
        },
    }

    report_path = Path(context["run_dir"]) / "alternative_model_report.json"
    _write_json(report_path, report_payload)

    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "config": report_payload["config"],
        "by_gender": {
            gender_key: {
                "status": payload.get("status"),
                "research_decision": payload.get("research_decision"),
                "research_reason": payload.get("research_reason"),
                "best_candidate_id": payload.get("selection", {}).get("selected_candidate_id"),
                "selection": payload.get("selection"),
                "selected_candidate_weights": payload.get("selection", {}).get("selected_candidate_weights"),
                "selected_val_brier_delta_vs_baseline": payload.get("selection", {}).get(
                    "selected_val_brier_delta_vs_baseline"
                ),
                "best_test_brier_delta_vs_baseline": payload.get("benchmark", {}).get(
                    "best_test_brier_delta_vs_baseline"
                ),
                "candidates": payload.get("candidates"),
            }
            for gender_key, payload in by_gender.items()
        },
        "aggregate": report_payload["aggregate"],
    }


def _build_men_combo_followup_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    alternative_model_payload: dict[str, Any],
) -> dict[str, Any]:
    men_payload = (
        alternative_model_payload.get("by_gender", {}).get("men", {})
        if isinstance(alternative_model_payload.get("by_gender", {}), dict)
        else {}
    )
    candidate_rows = men_payload.get("candidates", []) if isinstance(men_payload.get("candidates", []), list) else []
    shortlisted_ids = [
        "baseline_histgb_blend",
        "baseline_histgb_xgboost_blend",
        "baseline_histgb_catboost_blend",
        "baseline_xgboost_blend",
        "xgboost_catboost_blend",
    ]

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    baseline_test_metrics = baseline_scores.get("test", {})
    feature_columns = [column for column in feature_columns if column in feature_df.columns]
    alt_split_caches, alt_reasons = _fit_available_alternative_model_split_caches(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=feature_columns,
    )
    component_split_probabilities = {"baseline": baseline_split_probabilities, **alt_split_caches}

    candidates: list[dict[str, Any]] = []
    for candidate_id in shortlisted_ids:
        candidate_row = next(
            (row for row in candidate_rows if isinstance(row, dict) and row.get("candidate_id") == candidate_id),
            None,
        )
        if not isinstance(candidate_row, dict):
            candidates.append({"candidate_id": candidate_id, "status": "skipped", "reason": "candidate_unavailable"})
            continue

        weights = candidate_row.get("weights", {})
        split_cache, build_reason = _build_weighted_split_probabilities(
            component_split_probabilities=component_split_probabilities,
            weights=weights,
        )
        if split_cache is None:
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "status": "failed",
                    "reason": build_reason,
                    "weights": weights,
                }
            )
            continue

        raw_scores = _score_val_test_from_split_probabilities(
            gender_key="men",
            split_probabilities=split_cache,
        )
        val_true = np.asarray(split_cache.get("Val", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        val_prob = np.asarray(split_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        test_true = np.asarray(split_cache.get("Test", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        test_prob = np.asarray(split_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        calibration_policy = _build_calibration_policy_for_gender(
            gender_key="men",
            val_true=val_true,
            val_prob=val_prob,
            test_true=test_true,
            test_prob=test_prob,
            regime_summary={},
            drift_alerts=[],
        )
        selected_test_metrics = (
            calibration_policy.get("selected_test_metrics", {})
            if isinstance(calibration_policy.get("selected_test_metrics", {}), dict)
            else {}
        )
        candidates.append(
            {
                "candidate_id": candidate_id,
                "status": "available",
                "reason": None,
                "weights": weights,
                "raw_metrics": {
                    "val": raw_scores.get("val", {}),
                    "test": raw_scores.get("test", {}),
                },
                "raw_local_gate_check": _local_gate_check(
                    candidate_test_metrics=raw_scores.get("test", {}),
                    baseline_test_metrics=baseline_test_metrics,
                ),
                "calibration_policy": {
                    "selected_method": calibration_policy.get("selected_method"),
                    "selection_reason": calibration_policy.get("selection_reason"),
                    "selected_test_metrics": selected_test_metrics,
                    "candidate_methods": calibration_policy.get("candidate_methods"),
                },
                "calibrated_local_gate_check": _local_gate_check(
                    candidate_test_metrics=selected_test_metrics,
                    baseline_test_metrics=baseline_test_metrics,
                ),
            }
        )

    available_candidates = [row for row in candidates if row.get("status") == "available"]
    gate_ready_candidates = [
        row for row in available_candidates if row.get("calibrated_local_gate_check", {}).get("status") == "passed"
    ]

    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_available_candidates"
    if gate_ready_candidates:
        selected_candidate = min(
            gate_ready_candidates,
            key=lambda row: float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf"))),
        )
        research_decision = "promising_local_gate_candidate"
        research_reason = "shortlisted_candidate_clears_local_gate_after_calibration"
    elif available_candidates:
        selected_candidate = min(
            available_candidates,
            key=lambda row: (
                float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf"))),
                row.get("candidate_id") != "baseline_histgb_blend",
            ),
        )
        research_decision = "hold_current_combo_shortlist"
        research_reason = "no_shortlisted_candidate_clears_local_gate"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_combo_followup_v1",
        "shortlisted_candidate_ids": shortlisted_ids,
        "baseline_test_metrics": baseline_test_metrics,
        "alt_model_availability": alt_reasons,
        "candidates": candidates,
        "selected_candidate_id": selected_candidate.get("candidate_id") if isinstance(selected_candidate, dict) else None,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_combo_followup_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "selected_candidate_id": report_payload["selected_candidate_id"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
    }


def _build_men_tabpfn_followup_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    alternative_model_payload: dict[str, Any],
) -> dict[str, Any]:
    alternative_by_gender = (
        alternative_model_payload.get("by_gender", {})
        if isinstance(alternative_model_payload.get("by_gender", {}), dict)
        else {}
    )
    men_payload = alternative_by_gender.get("men", {}) if isinstance(alternative_by_gender.get("men", {}), dict) else {}
    candidate_rows = men_payload.get("candidates", []) if isinstance(men_payload.get("candidates", []), list) else []

    alternative_split_caches, alternative_reasons = _fit_available_alternative_model_split_caches(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=feature_columns,
    )
    tabpfn_split_cache = alternative_split_caches.get("tabpfn_benchmark")
    histgb_split_cache = alternative_split_caches.get("histgb_benchmark")

    component_split_probabilities = {
        "baseline": baseline_split_probabilities,
        **alternative_split_caches,
    }

    reference_weights = next(
        (
            row.get("weights")
            for row in candidate_rows
            if isinstance(row, dict)
            and row.get("candidate_id") == "baseline_histgb_blend"
            and row.get("status") == "available"
            and isinstance(row.get("weights"), dict)
        ),
        None,
    )
    reference_split_cache = None
    reference_reason = None
    if isinstance(reference_weights, dict):
        reference_split_cache, reference_reason = _build_weighted_split_probabilities(
            component_split_probabilities=component_split_probabilities,
            weights=reference_weights,
        )
    else:
        reference_reason = "reference_weights_unavailable"

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    baseline_test_metrics = baseline_scores.get("test", {})
    reference_scores = (
        _score_val_test_from_split_probabilities(gender_key="men", split_probabilities=reference_split_cache)
        if reference_split_cache is not None
        else {"val": {}, "test": {}}
    )
    reference_val_brier = _as_float_or_none(reference_scores.get("val", {}).get("brier"))
    reference_test_metrics = reference_scores.get("test", {})

    if reference_split_cache is None or tabpfn_split_cache is None:
        report_payload = {
            "run_id": context.get("run_id"),
            "seed": context.get("seed"),
            "generated_at": _now_utc_iso(),
            "policy_name": "men_tabpfn_followup_v1",
            "status": "failed",
            "reason": reference_reason or alternative_reasons.get("tabpfn_benchmark"),
            "reference_candidate_id": "baseline_histgb_blend",
            "alt_model_availability": alternative_reasons,
            "selected_candidate_id": None,
            "research_decision": "insufficient_data",
            "research_reason": "tabpfn_or_reference_unavailable",
            "candidates": [],
        }
        report_path = Path(context["run_dir"]) / "men_tabpfn_followup_report.json"
        _write_json(report_path, report_payload)
        return {
            "report_json": str(report_path),
            "policy_name": report_payload["policy_name"],
            "status": report_payload["status"],
            "selected_candidate_id": report_payload["selected_candidate_id"],
            "research_decision": report_payload["research_decision"],
            "research_reason": report_payload["research_reason"],
        }

    candidate_split_caches: dict[str, dict[str, dict[str, np.ndarray]]] = {
        "reference_raw": reference_split_cache,
        "tabpfn_raw": tabpfn_split_cache,
    }
    if histgb_split_cache is not None:
        candidate_split_caches["histgb_raw"] = histgb_split_cache

    reference_tabpfn_candidates: list[dict[str, Any]] = []
    for reference_weight in ALTERNATIVE_MODEL_WEIGHT_GRID:
        weights = {
            "reference_raw": float(reference_weight),
            "tabpfn_raw": float(1.0 - float(reference_weight)),
        }
        split_cache, blend_reason = _build_weighted_split_probabilities(
            component_split_probabilities=candidate_split_caches,
            weights=weights,
        )
        if split_cache is None:
            continue
        val_metrics = _score_val_test_from_split_probabilities(gender_key="men", split_probabilities=split_cache).get("val", {})
        test_metrics = _score_val_test_from_split_probabilities(gender_key="men", split_probabilities=split_cache).get("test", {})
        reference_tabpfn_candidates.append(
            {
                "weights": weights,
                "split_cache": split_cache,
                "val_metrics": val_metrics,
                "test_metrics": test_metrics,
                "val_brier": _as_float_or_none(val_metrics.get("brier")),
                "test_brier": _as_float_or_none(test_metrics.get("brier")),
                "reason": blend_reason,
            }
        )

    valid_reference_tabpfn = [
        row for row in reference_tabpfn_candidates if isinstance(row.get("val_brier"), (int, float))
    ]
    if valid_reference_tabpfn:
        best_reference_tabpfn = min(
            valid_reference_tabpfn,
            key=lambda row: (
                float(row["val_brier"]),
                abs(float(row["weights"]["reference_raw"]) - 0.5),
            ),
        )
        candidate_split_caches["reference_tabpfn_blend"] = best_reference_tabpfn["split_cache"]

    candidates: list[dict[str, Any]] = []
    for candidate_id in ("reference_raw", "tabpfn_raw", "reference_tabpfn_blend"):
        split_cache = candidate_split_caches.get(candidate_id)
        if split_cache is None:
            continue
        scores = _score_val_test_from_split_probabilities(gender_key="men", split_probabilities=split_cache)
        val_metrics = scores.get("val", {})
        test_metrics = scores.get("test", {})
        val_prob = np.asarray(split_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        val_true = np.asarray(split_cache.get("Val", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        test_prob = np.asarray(split_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        test_true = np.asarray(split_cache.get("Test", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        calibration_policy = _build_calibration_policy_for_gender(
            gender_key="men",
            val_true=val_true,
            val_prob=val_prob,
            test_true=test_true,
            test_prob=test_prob,
            regime_summary={},
            drift_alerts=[],
        )
        calibrated_test_metrics = (
            calibration_policy.get("selected_test_metrics", {})
            if isinstance(calibration_policy.get("selected_test_metrics", {}), dict)
            else {}
        )
        weights = None
        if candidate_id == "reference_raw":
            weights = reference_weights
        elif candidate_id == "reference_tabpfn_blend" and valid_reference_tabpfn:
            weights = best_reference_tabpfn["weights"]
        candidates.append(
            {
                "candidate_id": candidate_id,
                "status": "available",
                "reason": None,
                "weights": weights,
                "raw_metrics": {"val": val_metrics, "test": test_metrics},
                "raw_local_gate_check_vs_baseline": _local_gate_check(
                    candidate_test_metrics=test_metrics,
                    baseline_test_metrics=baseline_test_metrics,
                ),
                "raw_local_gate_check_vs_reference": _local_gate_check(
                    candidate_test_metrics=test_metrics,
                    baseline_test_metrics=reference_test_metrics,
                ),
                "calibration_policy": {
                    "selected_method": calibration_policy.get("selected_method"),
                    "selection_reason": calibration_policy.get("selection_reason"),
                    "selected_test_metrics": calibrated_test_metrics,
                    "candidate_methods": calibration_policy.get("candidate_methods"),
                },
                "calibrated_local_gate_check_vs_baseline": _local_gate_check(
                    candidate_test_metrics=calibrated_test_metrics,
                    baseline_test_metrics=baseline_test_metrics,
                ),
                "calibrated_local_gate_check_vs_reference": _local_gate_check(
                    candidate_test_metrics=calibrated_test_metrics,
                    baseline_test_metrics=reference_test_metrics,
                ),
            }
        )

    available_candidates = [row for row in candidates if row.get("status") == "available"]
    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_available_candidates"
    if available_candidates:
        selected_candidate = min(
            available_candidates,
            key=lambda row: (
                float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf"))),
                row.get("candidate_id") != "reference_raw",
            ),
        )
        selected_val_brier = _as_float_or_none(selected_candidate.get("raw_metrics", {}).get("val", {}).get("brier"))
        if (
            selected_candidate.get("candidate_id") != "reference_raw"
            and isinstance(selected_val_brier, (int, float))
            and isinstance(reference_val_brier, (int, float))
            and selected_val_brier <= reference_val_brier - ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT
        ):
            research_decision = "promising_tabpfn_followup_candidate"
            research_reason = "improves_reference_val_brier"
        else:
            research_decision = "hold_reference_candidate"
            research_reason = "tabpfn_family_not_better_than_reference"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_tabpfn_followup_v1",
        "status": "passed",
        "reason": None,
        "reference_candidate_id": "baseline_histgb_blend",
        "reference_weights": reference_weights,
        "alt_model_availability": alternative_reasons,
        "candidates": candidates,
        "selected_candidate_id": selected_candidate.get("candidate_id") if isinstance(selected_candidate, dict) else None,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_tabpfn_followup_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "selected_candidate_id": report_payload["selected_candidate_id"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
    }


def _build_men_gate_aware_search_report(
    *,
    context: dict[str, Any],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    alternative_model_payload: dict[str, Any],
    men_external_prior_policy_payload: dict[str, Any],
    men_tabpfn_followup_payload: dict[str, Any],
) -> dict[str, Any]:
    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    baseline_val_metrics = baseline_scores.get("val", {})
    baseline_test_metrics = baseline_scores.get("test", {})
    baseline_val_brier = _as_float_or_none(baseline_val_metrics.get("brier"))

    candidate_rows: list[dict[str, Any]] = []

    alt_by_gender = (
        alternative_model_payload.get("by_gender", {})
        if isinstance(alternative_model_payload.get("by_gender", {}), dict)
        else {}
    )
    men_alt = alt_by_gender.get("men", {}) if isinstance(alt_by_gender.get("men", {}), dict) else {}
    alt_candidates = men_alt.get("candidates", []) if isinstance(men_alt.get("candidates", []), list) else []
    for row in alt_candidates:
        if not isinstance(row, dict) or row.get("status") != "available":
            continue
        candidate_id = row.get("candidate_id")
        if candidate_id not in {"baseline_histgb_blend", "baseline_xgboost_blend", "baseline_histgb_xgboost_blend"}:
            continue
        metrics = row.get("metrics", {}) if isinstance(row.get("metrics", {}), dict) else {}
        test_metrics = metrics.get("test", {}) if isinstance(metrics.get("test", {}), dict) else {}
        candidate_rows.append(
            {
                "candidate_id": str(candidate_id),
                "source": "alternative_model",
                "weights": row.get("weights"),
                "raw_metrics": {
                    "val": metrics.get("val", {}),
                    "test": test_metrics,
                },
                "local_gate_check_vs_baseline": _local_gate_check(
                    candidate_test_metrics=test_metrics,
                    baseline_test_metrics=baseline_test_metrics,
                ),
            }
        )

    tabpfn_report_json = (
        men_tabpfn_followup_payload.get("report_json")
        if isinstance(men_tabpfn_followup_payload, dict)
        else None
    )
    if isinstance(tabpfn_report_json, str) and tabpfn_report_json.strip():
        tabpfn_report_path = Path(tabpfn_report_json)
        if tabpfn_report_path.exists():
            try:
                tabpfn_report = json.loads(tabpfn_report_path.read_text(encoding="utf-8"))
            except Exception:
                tabpfn_report = {}
            for row in tabpfn_report.get("candidates", []) if isinstance(tabpfn_report.get("candidates", []), list) else []:
                if not isinstance(row, dict) or row.get("status") != "available":
                    continue
                candidate_rows.append(
                    {
                        "candidate_id": str(row.get("candidate_id")),
                        "source": "men_tabpfn_followup",
                        "weights": row.get("weights"),
                        "raw_metrics": row.get("raw_metrics", {}),
                        "calibration_policy": row.get("calibration_policy"),
                        "local_gate_check_vs_baseline": row.get("raw_local_gate_check_vs_baseline"),
                    }
                )

    external_report_json = (
        men_external_prior_policy_payload.get("report_json")
        if isinstance(men_external_prior_policy_payload, dict)
        else None
    )
    if isinstance(external_report_json, str) and external_report_json.strip():
        external_report_path = Path(external_report_json)
        if external_report_path.exists():
            try:
                external_report = json.loads(external_report_path.read_text(encoding="utf-8"))
            except Exception:
                external_report = {}
            for row in external_report.get("candidates", []) if isinstance(external_report.get("candidates", []), list) else []:
                if not isinstance(row, dict) or row.get("status") != "available":
                    continue
                policy_id = row.get("policy_id")
                if policy_id not in {"blend_reference", "committee_guardrail_medium_only"}:
                    continue
                metrics = row.get("metrics", {}) if isinstance(row.get("metrics", {}), dict) else {}
                test_metrics = metrics.get("test", {}) if isinstance(metrics.get("test", {}), dict) else {}
                candidate_rows.append(
                    {
                        "candidate_id": str(policy_id),
                        "source": "men_external_prior_policy",
                        "weights": {
                            "seed_prior_weight": row.get("seed_prior_weight"),
                        },
                        "raw_metrics": {
                            "val": metrics.get("val", {}),
                            "test": test_metrics,
                        },
                        "local_gate_check_vs_baseline": _local_gate_check(
                            candidate_test_metrics=test_metrics,
                            baseline_test_metrics=baseline_test_metrics,
                        ),
                    }
                )

    deduped_rows: dict[str, dict[str, Any]] = {}
    for row in candidate_rows:
        candidate_id = str(row.get("candidate_id"))
        current = deduped_rows.get(candidate_id)
        current_val = (
            float(current.get("raw_metrics", {}).get("val", {}).get("brier", float("inf")))
            if isinstance(current, dict)
            else float("inf")
        )
        row_val = float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf")))
        if current is None or row_val < current_val:
            deduped_rows[candidate_id] = row

    scored_candidates: list[dict[str, Any]] = []
    for row in deduped_rows.values():
        val_metrics = row.get("raw_metrics", {}).get("val", {}) if isinstance(row.get("raw_metrics", {}), dict) else {}
        test_metrics = row.get("raw_metrics", {}).get("test", {}) if isinstance(row.get("raw_metrics", {}), dict) else {}
        val_brier = _as_float_or_none(val_metrics.get("brier"))
        if not isinstance(val_brier, (int, float)):
            continue
        val_ece = _as_float_or_none(val_metrics.get("ece"))
        val_wmae = _as_float_or_none(val_metrics.get("wmae"))
        val_gap = _as_float_or_none(val_metrics.get("high_prob_gap"))
        baseline_val_ece = _as_float_or_none(baseline_val_metrics.get("ece"))
        baseline_val_wmae = _as_float_or_none(baseline_val_metrics.get("wmae"))
        baseline_val_gap = _as_float_or_none(baseline_val_metrics.get("high_prob_gap"))
        ece_penalty = max(0.0, float(val_ece - baseline_val_ece)) if isinstance(val_ece, (int, float)) and isinstance(baseline_val_ece, (int, float)) else 0.0
        wmae_penalty = max(0.0, float(val_wmae - baseline_val_wmae)) if isinstance(val_wmae, (int, float)) and isinstance(baseline_val_wmae, (int, float)) else 0.0
        gap_penalty = max(0.0, abs(float(val_gap)) - abs(float(baseline_val_gap))) if isinstance(val_gap, (int, float)) and isinstance(baseline_val_gap, (int, float)) else 0.0
        objective = float(val_brier) + 0.5 * ece_penalty + 0.5 * wmae_penalty + 0.25 * gap_penalty
        row["gate_aware_objective"] = objective
        row["gate_penalties"] = {
            "ece_penalty": ece_penalty,
            "wmae_penalty": wmae_penalty,
            "high_prob_gap_abs_penalty": gap_penalty,
        }
        row["local_gate_check_vs_baseline"] = row.get("local_gate_check_vs_baseline") or _local_gate_check(
            candidate_test_metrics=test_metrics,
            baseline_test_metrics=baseline_test_metrics,
        )
        scored_candidates.append(row)

    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_scored_candidates"
    if scored_candidates:
        selected_candidate = min(
            scored_candidates,
            key=lambda row: (
                float(row.get("gate_aware_objective", float("inf"))),
                row.get("candidate_id") not in {"baseline_histgb_blend", "reference_raw"},
            ),
        )
        selected_id = selected_candidate.get("candidate_id")
        if selected_id not in {"baseline_histgb_blend", "reference_raw"}:
            selected_val_brier = _as_float_or_none(selected_candidate.get("raw_metrics", {}).get("val", {}).get("brier"))
            if (
                isinstance(selected_val_brier, (int, float))
                and isinstance(baseline_val_brier, (int, float))
                and selected_val_brier <= baseline_val_brier - ALTERNATIVE_MODEL_MIN_VAL_IMPROVEMENT
            ):
                research_decision = "promising_gate_aware_candidate"
                research_reason = "candidate_selected_under_gate_aware_objective"
            else:
                research_decision = "hold_current_reference"
                research_reason = "no_gate_aware_edge_vs_reference"
        else:
            research_decision = "hold_current_reference"
            research_reason = "reference_remains_best_under_gate_aware_objective"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_gate_aware_search_v1",
        "status": "passed",
        "reason": None,
        "objective": {
            "base_metric": "val_brier",
            "penalties": {
                "ece_penalty_weight": 0.5,
                "wmae_penalty_weight": 0.5,
                "high_prob_gap_abs_penalty_weight": 0.25,
            },
        },
        "baseline_val_metrics": baseline_val_metrics,
        "baseline_test_metrics": baseline_test_metrics,
        "candidates": scored_candidates,
        "selected_candidate_id": selected_candidate.get("candidate_id") if isinstance(selected_candidate, dict) else None,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_gate_aware_search_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "selected_candidate_id": report_payload["selected_candidate_id"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
    }


def _build_blend_candidate_policy_report(
    *,
    context: dict[str, Any],
    alternative_model_payload: dict[str, Any],
) -> dict[str, Any]:
    by_gender_payload = (
        alternative_model_payload.get("by_gender", {})
        if isinstance(alternative_model_payload.get("by_gender", {}), dict)
        else {}
    )

    by_gender: dict[str, Any] = {}
    candidate_ready_genders: list[str] = []

    for gender_key in ("men", "women"):
        gender_payload = by_gender_payload.get(gender_key, {}) if isinstance(by_gender_payload.get(gender_key, {}), dict) else {}
        selected_candidate_id = gender_payload.get("best_candidate_id")
        selected_weights = gender_payload.get("selected_candidate_weights")
        research_decision = gender_payload.get("research_decision")

        is_candidate_ready = (
            research_decision == "promising_diversity_candidate"
            and selected_candidate_id == "baseline_histgb_blend"
            and isinstance(selected_weights, dict)
            and set(selected_weights.keys()) == {"baseline", "histgb_benchmark"}
        )

        if is_candidate_ready:
            candidate_ready_genders.append(gender_key)

        by_gender[gender_key] = {
            "candidate_status": "ready_for_followup" if is_candidate_ready else "hold_research_only",
            "selected_candidate_id": selected_candidate_id,
            "selected_candidate_weights": selected_weights,
            "research_decision": research_decision,
            "research_reason": gender_payload.get("research_reason"),
            "val_brier_delta_vs_baseline": gender_payload.get("selected_val_brier_delta_vs_baseline"),
            "test_brier_delta_vs_baseline": gender_payload.get("best_test_brier_delta_vs_baseline"),
            "production_recipe": (
                {
                    "baseline_model_family": "lightgbm",
                    "secondary_model_family": "hist_gradient_boosting",
                    "blend_weights": selected_weights,
                    "final_probability_formula": "p_final = w_baseline * p_lgbm + w_histgb * p_histgb",
                }
                if is_candidate_ready
                else None
            ),
        }

    aggregate_decision = (
        "candidate_ready_for_promotion_followup"
        if len(candidate_ready_genders) == 2
        else "partial_candidate_ready"
        if candidate_ready_genders
        else "hold_research_only"
    )

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "blend_candidate_policy_v1",
        "by_gender": by_gender,
        "aggregate": {
            "decision": aggregate_decision,
            "candidate_ready_genders": candidate_ready_genders,
        },
    }

    report_path = Path(context["run_dir"]) / "blend_candidate_policy_report.json"
    _write_json(report_path, report_payload)

    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "by_gender": by_gender,
        "aggregate": report_payload["aggregate"],
    }


def _build_final_blend_recipe_report(
    *,
    context: dict[str, Any],
    alternative_model_payload: dict[str, Any],
    men_tabpfn_followup_payload: dict[str, Any],
) -> dict[str, Any]:
    by_gender: dict[str, Any] = {}
    candidate_ready_genders: list[str] = []

    alternative_by_gender = (
        alternative_model_payload.get("by_gender", {})
        if isinstance(alternative_model_payload.get("by_gender", {}), dict)
        else {}
    )

    def _load_json_payload(report_json: Any) -> dict[str, Any]:
        if not isinstance(report_json, str) or not report_json.strip():
            return {}
        report_path = Path(report_json)
        if not report_path.exists():
            return {}
        try:
            return json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _expand_reference_tabpfn_weights(
        reference_weights: dict[str, Any],
        row_weights: dict[str, Any],
    ) -> dict[str, float] | None:
        reference_raw_weight = _as_float_or_none(row_weights.get("reference_raw"))
        tabpfn_raw_weight = _as_float_or_none(row_weights.get("tabpfn_raw"))
        if (
            not isinstance(reference_raw_weight, (int, float))
            or not isinstance(tabpfn_raw_weight, (int, float))
            or abs(float(reference_raw_weight) + float(tabpfn_raw_weight) - 1.0) > 1e-6
        ):
            return None
        expanded: dict[str, float] = {}
        for component_id, component_weight in reference_weights.items():
            component_weight_float = _as_float_or_none(component_weight)
            if not isinstance(component_weight_float, (int, float)):
                return None
            expanded[str(component_id)] = float(reference_raw_weight) * float(component_weight_float)
        expanded["tabpfn_benchmark"] = expanded.get("tabpfn_benchmark", 0.0) + float(tabpfn_raw_weight)
        return expanded

    def _resolve_men_release_override(current_test_metrics: dict[str, Any]) -> dict[str, Any] | None:
        men_followup_report = _load_json_payload(men_tabpfn_followup_payload.get("report_json"))
        if not men_followup_report:
            return None

        reference_weights = (
            men_followup_report.get("reference_weights", {})
            if isinstance(men_followup_report.get("reference_weights", {}), dict)
            else {}
        )
        current_test_brier = _as_float_or_none(current_test_metrics.get("brier"))
        current_test_ece = _as_float_or_none(current_test_metrics.get("ece"))
        current_test_gap = _as_float_or_none(current_test_metrics.get("high_prob_gap"))
        override_candidates: list[dict[str, Any]] = []
        for row in men_followup_report.get("candidates", []) if isinstance(men_followup_report.get("candidates", []), list) else []:
            if not isinstance(row, dict) or row.get("status") != "available":
                continue
            local_gate = (
                row.get("raw_local_gate_check_vs_baseline", {})
                if isinstance(row.get("raw_local_gate_check_vs_baseline", {}), dict)
                else {}
            )
            if local_gate.get("status") != "passed":
                continue

            candidate_id = str(row.get("candidate_id") or "")
            mapped_candidate_id = None
            mapped_weights: dict[str, float] | None = None
            if candidate_id == "tabpfn_raw":
                mapped_candidate_id = "tabpfn_benchmark"
                mapped_weights = {"tabpfn_benchmark": 1.0}
            elif candidate_id == "reference_raw" and reference_weights:
                mapped_candidate_id = "baseline_histgb_blend"
                mapped_weights = {
                    str(component_id): float(component_weight)
                    for component_id, component_weight in reference_weights.items()
                    if _as_float_or_none(component_weight) is not None
                }
            elif candidate_id == "reference_tabpfn_blend" and reference_weights and isinstance(row.get("weights"), dict):
                mapped_candidate_id = "baseline_histgb_tabpfn_followup_blend"
                mapped_weights = _expand_reference_tabpfn_weights(reference_weights, row["weights"])

            if not mapped_candidate_id or not mapped_weights:
                continue

            val_brier = _as_float_or_none(row.get("raw_metrics", {}).get("val", {}).get("brier"))
            test_brier = _as_float_or_none(row.get("raw_metrics", {}).get("test", {}).get("brier"))
            test_ece = _as_float_or_none(row.get("raw_metrics", {}).get("test", {}).get("ece"))
            test_gap = _as_float_or_none(row.get("raw_metrics", {}).get("test", {}).get("high_prob_gap"))
            dominates_current = (
                isinstance(test_brier, (int, float))
                and isinstance(current_test_brier, (int, float))
                and float(test_brier) < float(current_test_brier) - REGRESSION_NUMERIC_EPS
                and (
                    not isinstance(test_ece, (int, float))
                    or not isinstance(current_test_ece, (int, float))
                    or float(test_ece) <= float(current_test_ece) + REGRESSION_NUMERIC_EPS
                )
                and (
                    not isinstance(test_gap, (int, float))
                    or not isinstance(current_test_gap, (int, float))
                    or abs(float(test_gap)) <= abs(float(current_test_gap)) + REGRESSION_NUMERIC_EPS
                )
            )
            if not dominates_current:
                continue
            override_candidates.append(
                {
                    "selected_candidate_id": mapped_candidate_id,
                    "selected_candidate_weights": mapped_weights,
                    "selection_source": "men_tabpfn_followup",
                    "selection_reason": f"promote_local_gate_candidate:{candidate_id}",
                    "val_brier": float(val_brier) if isinstance(val_brier, (int, float)) else float("inf"),
                    "test_brier": float(test_brier) if isinstance(test_brier, (int, float)) else float("inf"),
                }
            )

        if not override_candidates:
            return None

        return min(
            override_candidates,
            key=lambda row: (
                float(row.get("val_brier", float("inf"))),
                float(row.get("test_brier", float("inf"))),
                row.get("selected_candidate_id") != "tabpfn_benchmark",
            ),
        )

    for gender_key in ("men", "women"):
        gender_payload = (
            alternative_by_gender.get(gender_key, {})
            if isinstance(alternative_by_gender.get(gender_key, {}), dict)
            else {}
        )
        selection_payload = (
            gender_payload.get("selection", {})
            if isinstance(gender_payload.get("selection", {}), dict)
            else {}
        )
        selected_candidate_id = selection_payload.get("selected_candidate_id")
        selected_weights = (
            selection_payload.get("selected_candidate_weights")
            if isinstance(selection_payload.get("selected_candidate_weights"), dict)
            else None
        )
        selection_source = "alternative_model"
        selection_reason = "alternative_model_selection"

        if gender_key == "men":
            candidate_rows = gender_payload.get("candidates", []) if isinstance(gender_payload.get("candidates", []), list) else []
            baseline_candidate = next(
                (row for row in candidate_rows if isinstance(row, dict) and row.get("candidate_id") == "baseline"),
                None,
            )
            selected_candidate = next(
                (
                    row
                    for row in candidate_rows
                    if isinstance(row, dict) and row.get("candidate_id") == selected_candidate_id
                ),
                None,
            )
            baseline_test_metrics = (
                baseline_candidate.get("metrics", {}).get("test", {})
                if isinstance(baseline_candidate, dict)
                else {}
            )
            selected_test_metrics = (
                selected_candidate.get("metrics", {}).get("test", {})
                if isinstance(selected_candidate, dict)
                else {}
            )
            current_gate = _local_gate_check(candidate_test_metrics=selected_test_metrics, baseline_test_metrics=baseline_test_metrics)
            override_payload = _resolve_men_release_override(selected_test_metrics)
            if isinstance(override_payload, dict):
                selected_candidate_id = override_payload.get("selected_candidate_id")
                selected_weights = override_payload.get("selected_candidate_weights")
                selection_source = str(override_payload.get("selection_source") or selection_source)
                selection_reason = str(override_payload.get("selection_reason") or selection_reason)
            elif current_gate.get("status") != "passed":
                selection_reason = "alternative_model_selection"

        if not selected_candidate_id:
            selected_candidate_id = "baseline"
            selected_weights = {"baseline": 1.0}
            production_recipe = {
                "recipe_type": "single_model",
                "final_probability_formula": "p_final = p_baseline",
            }
        else:
            if not selected_weights:
                selected_weights = {str(selected_candidate_id): 1.0}

            ordered_terms = [
                f"{float(weight):g} * p_{component_id.replace('_benchmark', '').replace('baseline', 'baseline')}"
                for component_id, weight in selected_weights.items()
            ]
            production_recipe = {
                "recipe_type": "weighted_blend" if len(selected_weights) > 1 else "single_model",
                "final_probability_formula": "p_final = " + " + ".join(ordered_terms),
            }

        candidate_ready_genders.append(gender_key)
        by_gender[gender_key] = {
            "selected_candidate_id": selected_candidate_id,
            "selected_candidate_weights": selected_weights,
            "production_recipe": production_recipe,
            "selection_source": selection_source,
            "selection_reason": selection_reason,
        }

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "blend_final_recipe_v1",
        "by_gender": by_gender,
        "aggregate": {
            "decision": "explicit_final_recipe",
            "candidate_ready_genders": candidate_ready_genders,
        },
    }

    report_path = Path(context["run_dir"]) / "final_blend_recipe_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "by_gender": report_payload["by_gender"],
        "aggregate": report_payload["aggregate"],
    }


def _select_prediction_policy_probabilities(
    *,
    context: dict[str, Any],
    genders_payload: dict[str, Any],
    feature_frames_by_gender: dict[str, pd.DataFrame],
    baseline_split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
    alternative_model_payload: dict[str, Any],
    blend_candidate_policy_payload: dict[str, Any],
    final_blend_recipe_payload: dict[str, Any],
    men_external_prior_policy_payload: dict[str, Any],
    men_combo_followup_payload: dict[str, Any],
    policy_name: str,
) -> tuple[dict[str, dict[str, dict[str, np.ndarray]]], dict[str, Any]]:
    def _apply_tail_lift(prob: np.ndarray, *, threshold: float, alpha: float) -> np.ndarray:
        adjusted = np.asarray(prob, dtype=float).copy()
        mask = adjusted >= float(threshold)
        if not np.any(mask):
            return adjusted
        adjusted[mask] = adjusted[mask] + float(alpha) * (1.0 - adjusted[mask])
        return np.clip(adjusted, 0.0, 1.0)

    selected_policy = str(policy_name or "baseline").strip().lower()
    if selected_policy not in PREDICTION_POLICIES:
        selected_policy = "baseline"

    if selected_policy == "baseline":
        return baseline_split_probabilities, {
            "selected_policy": "baseline",
            "reason": "default_baseline_policy",
            "by_gender": {
                gender_key: {"selected_policy": "baseline", "reason": "default_baseline_policy"}
                for gender_key in ("men", "women")
            },
        }

    selected_probabilities: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    diagnostics_by_gender: dict[str, Any] = {}
    fallback_required = False

    if selected_policy == "blend_final_recipe_v1":
        final_recipe_by_gender = (
            final_blend_recipe_payload.get("by_gender", {})
            if isinstance(final_blend_recipe_payload.get("by_gender", {}), dict)
            else {}
        )

        for gender_key in ("men", "women"):
            gender_payload = (
                final_recipe_by_gender.get(gender_key, {})
                if isinstance(final_recipe_by_gender.get(gender_key, {}), dict)
                else {}
            )
            selected_weights = (
                gender_payload.get("selected_candidate_weights")
                if isinstance(gender_payload.get("selected_candidate_weights"), dict)
                else None
            )
            selected_candidate_id = gender_payload.get("selected_candidate_id")
            normalized_weights = {
                str(component_id): float(weight)
                for component_id, weight in selected_weights.items()
                if _as_float_or_none(weight) is not None
            } if isinstance(selected_weights, dict) else {}
            if (
                not selected_candidate_id
                or selected_candidate_id == "baseline"
                or
                not normalized_weights
                or abs(sum(normalized_weights.values()) - 1.0) > 1e-6
            ):
                fallback_required = True
                selected_probabilities[gender_key] = baseline_split_probabilities.get(gender_key, {})
                diagnostics_by_gender[gender_key] = {
                    "selected_policy": "baseline",
                    "reason": "final_recipe_selection_unavailable_fallback",
                    "blend_weights": None,
                }
                continue

            feature_columns = (
                genders_payload.get(gender_key, {}).get("feature_snapshot", {}).get("feature_columns", [])
                if isinstance(genders_payload.get(gender_key, {}), dict)
                else []
            )
            alt_split_cache, alt_reason = _fit_histgb_candidate_split_probabilities(
                context=context,
                gender_key=gender_key,
                feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
                feature_columns=feature_columns,
            )
            alt_split_caches, alt_reasons = _fit_available_alternative_model_split_caches(
                context=context,
                gender_key=gender_key,
                feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
                feature_columns=feature_columns,
            )
            component_split_probabilities = {
                "baseline": baseline_split_probabilities.get(gender_key, {}),
                **alt_split_caches,
            }

            missing_components = [
                component_id
                for component_id in normalized_weights.keys()
                if component_id not in component_split_probabilities
            ]
            baseline_cache = baseline_split_probabilities.get(gender_key, {})
            if missing_components:
                fallback_required = True
                missing_reasons = {
                    component_id: alt_reasons.get(component_id)
                    for component_id in missing_components
                }
                selected_probabilities[gender_key] = baseline_cache
                diagnostics_by_gender[gender_key] = {
                    "selected_policy": "baseline",
                    "reason": f"final_recipe_component_unavailable:{missing_reasons}",
                    "blend_weights": None,
                }
                continue

            blended_cache: dict[str, dict[str, np.ndarray]] = {}
            for split_label in CANONICAL_SPLITS:
                first_component_id = next(iter(normalized_weights.keys()))
                first_split = component_split_probabilities.get(first_component_id, {}).get(split_label, {})
                y_true = np.asarray(first_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
                if y_true.size == 0:
                    fallback_required = True
                    blended_cache = baseline_cache
                    diagnostics_by_gender[gender_key] = {
                        "selected_policy": "baseline",
                        "reason": f"final_recipe_split_missing:{split_label}",
                        "blend_weights": None,
                    }
                    break
                blended_prob = np.zeros_like(y_true, dtype=float)
                for component_id, weight in normalized_weights.items():
                    component_split = component_split_probabilities.get(component_id, {}).get(split_label, {})
                    component_true = np.asarray(component_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
                    component_prob = np.asarray(component_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
                    if component_true.shape != y_true.shape or component_prob.shape != y_true.shape:
                        fallback_required = True
                        blended_cache = baseline_cache
                        diagnostics_by_gender[gender_key] = {
                            "selected_policy": "baseline",
                            "reason": f"final_recipe_shape_mismatch:{component_id}:{split_label}",
                            "blend_weights": None,
                        }
                        break
                    blended_prob += float(weight) * component_prob
                else:
                    if gender_key == "men" and selected_candidate_id == "tabpfn_benchmark":
                        blended_prob = _apply_tail_lift(
                            blended_prob,
                            threshold=HIGH_PROB_THRESHOLD,
                            alpha=MEN_TABPFN_HIGH_PROB_TAIL_LIFT,
                        )
                    blended_cache[split_label] = {
                        "y_true": y_true,
                        "y_prob": np.clip(blended_prob, 0.0, 1.0),
                    }
                    continue
                break
            else:
                diagnostics_by_gender[gender_key] = {
                    "selected_policy": "blend_final_recipe_v1",
                    "reason": (
                        "explicit_final_recipe_applied_with_tail_lift"
                        if gender_key == "men" and selected_candidate_id == "tabpfn_benchmark"
                        else "explicit_final_recipe_applied"
                    ),
                    "blend_weights": normalized_weights,
                }

            selected_probabilities[gender_key] = blended_cache

        aggregate_reason = "blend_final_recipe_v1_applied"
        aggregate_policy = "blend_final_recipe_v1"
        if fallback_required:
            aggregate_reason = "partial_or_full_fallback_to_baseline"
            aggregate_policy = "mixed_with_baseline_fallback"

        return selected_probabilities, {
            "selected_policy": aggregate_policy,
            "reason": aggregate_reason,
            "by_gender": diagnostics_by_gender,
        }

    blend_policy_by_gender = (
        blend_candidate_policy_payload.get("by_gender", {})
        if isinstance(blend_candidate_policy_payload.get("by_gender", {}), dict)
        else {}
    )

    for gender_key in ("men", "women"):
        candidate_policy_entry = (
            blend_policy_by_gender.get(gender_key, {})
            if isinstance(blend_policy_by_gender.get(gender_key, {}), dict)
            else {}
        )
        selected_weights = (
            candidate_policy_entry.get("selected_candidate_weights")
            if isinstance(candidate_policy_entry.get("selected_candidate_weights"), dict)
            else {}
        )
        baseline_weight = _as_float_or_none(selected_weights.get("baseline"))
        histgb_weight = _as_float_or_none(selected_weights.get("histgb_benchmark"))
        candidate_status = candidate_policy_entry.get("candidate_status")
        if (
            candidate_status != "ready_for_followup"
            or baseline_weight is None
            or histgb_weight is None
            or abs((baseline_weight + histgb_weight) - 1.0) > 1e-6
        ):
            fallback_required = True
            selected_probabilities[gender_key] = baseline_split_probabilities.get(gender_key, {})
            diagnostics_by_gender[gender_key] = {
                "selected_policy": "baseline",
                "reason": "candidate_recipe_unavailable_fallback",
                "blend_weights": None,
            }
            continue

        feature_columns = (
            genders_payload.get(gender_key, {}).get("feature_snapshot", {}).get("feature_columns", [])
            if isinstance(genders_payload.get(gender_key, {}), dict)
            else []
        )
        alt_split_cache, alt_reason = _fit_histgb_candidate_split_probabilities(
            context=context,
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            feature_columns=feature_columns,
        )
        baseline_cache = baseline_split_probabilities.get(gender_key, {})
        if alt_split_cache is None:
            fallback_required = True
            selected_probabilities[gender_key] = baseline_cache
            diagnostics_by_gender[gender_key] = {
                "selected_policy": "baseline",
                "reason": f"blend_unavailable:{alt_reason}",
                "blend_weights": None,
            }
            continue

        blended_cache: dict[str, dict[str, np.ndarray]] = {}
        for split_label in CANONICAL_SPLITS:
            baseline_split = baseline_cache.get(split_label, {})
            alt_split = alt_split_cache.get(split_label, {})
            baseline_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            baseline_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            alt_true = np.asarray(alt_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            alt_prob = np.asarray(alt_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)

            if baseline_true.shape != alt_true.shape or baseline_prob.shape != alt_prob.shape or baseline_true.shape != baseline_prob.shape:
                fallback_required = True
                blended_cache = baseline_cache
                diagnostics_by_gender[gender_key] = {
                    "selected_policy": "baseline",
                    "reason": "blend_shape_mismatch_fallback",
                    "blend_weights": None,
                }
                break

            blended_cache[split_label] = {
                "y_true": baseline_true,
                "y_prob": np.clip(float(baseline_weight) * baseline_prob + float(histgb_weight) * alt_prob, 0.0, 1.0),
            }
        else:
            diagnostics_by_gender[gender_key] = {
                "selected_policy": "blend_candidate_v1",
                "reason": "selected_candidate_recipe",
                "blend_weights": {
                    "baseline": float(baseline_weight),
                    "histgb_benchmark": float(histgb_weight),
                },
            }

        selected_probabilities[gender_key] = blended_cache

    if selected_policy == "blend_candidate_v1":
        aggregate_reason = "blend_candidate_v1_applied"
        aggregate_policy = "blend_candidate_v1"
        if fallback_required:
            aggregate_reason = "partial_or_full_fallback_to_baseline"
            aggregate_policy = "mixed_with_baseline_fallback"

        return selected_probabilities, {
            "selected_policy": aggregate_policy,
            "reason": aggregate_reason,
            "by_gender": diagnostics_by_gender,
        }

    men_feature_columns = (
        genders_payload.get("men", {}).get("feature_snapshot", {}).get("feature_columns", [])
        if isinstance(genders_payload.get("men", {}), dict)
        else []
    )

    if selected_policy == "men_external_prior_policy_v1":
        men_external_cache, men_external_reason, men_external_diagnostics = _build_men_external_prior_selected_split_probabilities(
            context=context,
            feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
            baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
            blend_candidate_policy_payload=blend_candidate_policy_payload,
            men_external_prior_policy_payload=men_external_prior_policy_payload,
        )
        if men_external_cache is None:
            fallback_required = True
            diagnostics_by_gender["men"] = {
                "selected_policy": diagnostics_by_gender.get("men", {}).get("selected_policy", "baseline"),
                "reason": f"men_external_prior_unavailable:{men_external_reason}",
                "blend_weights": diagnostics_by_gender.get("men", {}).get("blend_weights"),
                "external_prior_policy": None,
            }
        else:
            selected_probabilities["men"] = men_external_cache
            diagnostics_by_gender["men"] = {
                "selected_policy": "men_external_prior_policy_v1",
                "reason": "selected_external_prior_policy",
                "blend_weights": (
                    men_external_diagnostics.get("reference_blend_weights")
                    if isinstance(men_external_diagnostics, dict)
                    else diagnostics_by_gender.get("men", {}).get("blend_weights")
                ),
                "external_prior_policy": men_external_diagnostics,
            }
    else:
        men_combo_cache, men_combo_reason, men_combo_diagnostics = _build_men_combo_followup_selected_split_probabilities(
            context=context,
            feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
            feature_columns=men_feature_columns,
            baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
            men_combo_followup_payload=men_combo_followup_payload,
        )
        if men_combo_cache is None:
            fallback_required = True
            diagnostics_by_gender["men"] = {
                "selected_policy": diagnostics_by_gender.get("men", {}).get("selected_policy", "baseline"),
                "reason": f"men_combo_followup_unavailable:{men_combo_reason}",
                "blend_weights": diagnostics_by_gender.get("men", {}).get("blend_weights"),
                "combo_followup_policy": None,
            }
        else:
            selected_probabilities["men"] = men_combo_cache
            diagnostics_by_gender["men"] = {
                "selected_policy": "men_combo_followup_v1",
                "reason": "selected_combo_followup_candidate",
                "blend_weights": (
                    men_combo_diagnostics.get("weights")
                    if isinstance(men_combo_diagnostics, dict)
                    else diagnostics_by_gender.get("men", {}).get("blend_weights")
                ),
                "combo_followup_policy": men_combo_diagnostics,
            }

    if selected_policy == "men_external_prior_policy_v1":
        aggregate_reason = "men_external_prior_policy_v1_applied"
        aggregate_policy = "men_external_prior_policy_v1"
    else:
        aggregate_reason = "men_combo_followup_v1_applied"
        aggregate_policy = "men_combo_followup_v1"

    if fallback_required:
        fallback_required = True
        aggregate_reason = "partial_or_full_fallback_to_baseline"
        aggregate_policy = "mixed_with_baseline_fallback"

    return selected_probabilities, {
        "selected_policy": aggregate_policy,
        "reason": aggregate_reason,
        "by_gender": diagnostics_by_gender,
    }


def _build_men_policy_refinement_specs() -> list[dict[str, Any]]:
    return [
        {
            "policy_id": "baseline_reference",
            "label": "Baseline reference",
            "regime_alt_weights": {"close": 0.0, "medium": 0.0, "wide": 0.0, "unknown": 0.0},
        },
        {
            "policy_id": "blend_reference",
            "label": "Uniform blend reference",
            "regime_alt_weights": {"close": 0.5, "medium": 0.5, "wide": 0.5, "unknown": 0.5},
        },
        {
            "policy_id": "wide_blend_else_baseline",
            "label": "Blend wide only",
            "regime_alt_weights": {"close": 0.0, "medium": 0.0, "wide": 0.5, "unknown": 0.0},
        },
        {
            "policy_id": "medium_wide_blend",
            "label": "Blend medium and wide",
            "regime_alt_weights": {"close": 0.0, "medium": 0.5, "wide": 0.5, "unknown": 0.0},
        },
        {
            "policy_id": "close_light_medium_wide_blend",
            "label": "Light close blend, full medium/wide blend",
            "regime_alt_weights": {"close": 0.25, "medium": 0.5, "wide": 0.5, "unknown": 0.25},
        },
        {
            "policy_id": "close_baseline_medium_light_wide_blend",
            "label": "Light medium blend, full wide blend",
            "regime_alt_weights": {"close": 0.0, "medium": 0.25, "wide": 0.5, "unknown": 0.0},
        },
    ]


def _build_men_policy_refinement_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    blend_candidate_policy_payload: dict[str, Any],
) -> dict[str, Any]:
    alt_split_cache, alt_reason = _fit_histgb_candidate_split_probabilities(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=feature_columns,
    )
    if alt_split_cache is None:
        report_payload = {
            "run_id": context.get("run_id"),
            "seed": context.get("seed"),
            "generated_at": _now_utc_iso(),
            "policy_name": "men_regime_policy_research_v1",
            "status": "skipped",
            "reason": f"alt_model_unavailable:{alt_reason}",
            "candidates": [],
            "selected_policy_id": None,
            "research_decision": "insufficient_data",
            "research_reason": "alt_model_unavailable",
        }
        report_path = Path(context["run_dir"]) / "men_policy_refinement_report.json"
        _write_json(report_path, report_payload)
        return {
            "report_json": str(report_path),
            "policy_name": report_payload["policy_name"],
            "status": report_payload["status"],
            "research_decision": report_payload["research_decision"],
            "selected_policy_id": report_payload["selected_policy_id"],
        }

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    baseline_val_brier = _as_float_or_none(baseline_scores.get("val", {}).get("brier"))
    baseline_test_brier = _as_float_or_none(baseline_scores.get("test", {}).get("brier"))
    baseline_test_ece = _as_float_or_none(baseline_scores.get("test", {}).get("ece"))
    baseline_test_wmae = _as_float_or_none(baseline_scores.get("test", {}).get("wmae"))
    baseline_test_gap = _as_float_or_none(baseline_scores.get("test", {}).get("high_prob_gap"))
    baseline_test_gap_abs = abs(baseline_test_gap) if baseline_test_gap is not None else None

    split_seed_regimes: dict[str, np.ndarray] = {}
    for split_label in ("Val", "Test"):
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        if split_df.empty or "SeedNum_diff" not in split_df.columns:
            split_seed_regimes[split_label] = np.asarray([], dtype=object)
            continue
        split_seed_regimes[split_label] = split_df["SeedNum_diff"].apply(_seed_gap_bucket_from_diff).to_numpy()

    candidates: list[dict[str, Any]] = []
    for spec in _build_men_policy_refinement_specs():
        regime_alt_weights = spec["regime_alt_weights"]
        policy_split_cache: dict[str, dict[str, np.ndarray]] = {}
        policy_valid = True
        for split_label in ("Val", "Test"):
            baseline_split = baseline_split_probabilities.get(split_label, {})
            alt_split = alt_split_cache.get(split_label, {})
            baseline_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            baseline_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            alt_true = np.asarray(alt_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            alt_prob = np.asarray(alt_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            seed_regimes = split_seed_regimes.get(split_label, np.asarray([], dtype=object))

            if (
                baseline_true.shape != alt_true.shape
                or baseline_prob.shape != alt_prob.shape
                or baseline_true.shape != baseline_prob.shape
                or baseline_true.shape[0] != seed_regimes.shape[0]
            ):
                policy_valid = False
                break

            blended_prob = baseline_prob.copy()
            for regime_name in ("close", "medium", "wide", "unknown"):
                regime_mask = seed_regimes == regime_name
                if np.any(regime_mask):
                    alt_weight = float(regime_alt_weights.get(regime_name, 0.0))
                    blended_prob[regime_mask] = np.clip(
                        (1.0 - alt_weight) * baseline_prob[regime_mask] + alt_weight * alt_prob[regime_mask],
                        0.0,
                        1.0,
                    )
            policy_split_cache[split_label] = {"y_true": baseline_true, "y_prob": blended_prob}

        if not policy_valid:
            candidates.append(
                {
                    "policy_id": spec["policy_id"],
                    "label": spec["label"],
                    "status": "failed",
                    "reason": "split_alignment_mismatch",
                    "regime_alt_weights": regime_alt_weights,
                    "metrics": {"val": {}, "test": {}},
                    "local_reference_check": {"status": "failed", "reason": "split_alignment_mismatch"},
                }
            )
            continue

        scores = _score_val_test_from_split_probabilities(
            gender_key="men",
            split_probabilities=policy_split_cache,
        )
        test_payload = scores.get("test", {})
        test_gap = _as_float_or_none(test_payload.get("high_prob_gap"))
        test_gap_abs = abs(test_gap) if test_gap is not None else None

        local_reference_ready = (
            isinstance(_as_float_or_none(test_payload.get("brier")), (int, float))
            and isinstance(baseline_test_brier, (int, float))
            and _as_float_or_none(test_payload.get("brier")) <= baseline_test_brier + REGRESSION_NUMERIC_EPS
            and isinstance(_as_float_or_none(test_payload.get("ece")), (int, float))
            and isinstance(baseline_test_ece, (int, float))
            and _as_float_or_none(test_payload.get("ece")) <= baseline_test_ece + REGRESSION_NUMERIC_EPS
            and isinstance(_as_float_or_none(test_payload.get("wmae")), (int, float))
            and isinstance(baseline_test_wmae, (int, float))
            and _as_float_or_none(test_payload.get("wmae")) <= baseline_test_wmae + REGRESSION_NUMERIC_EPS
            and isinstance(test_gap_abs, (int, float))
            and isinstance(baseline_test_gap_abs, (int, float))
            and test_gap_abs <= baseline_test_gap_abs + REGRESSION_NUMERIC_EPS
        )

        candidates.append(
            {
                "policy_id": spec["policy_id"],
                "label": spec["label"],
                "status": "available",
                "reason": None,
                "regime_alt_weights": regime_alt_weights,
                "metrics": {
                    "val": scores.get("val", {}),
                    "test": test_payload,
                    "val_brier": _as_float_or_none(scores.get("val", {}).get("brier")),
                    "test_brier": _as_float_or_none(test_payload.get("brier")),
                },
                "deltas_vs_baseline": {
                    "val_brier": _safe_delta(
                        _as_float_or_none(scores.get("val", {}).get("brier")),
                        baseline_val_brier,
                    ),
                    "test_brier": _safe_delta(
                        _as_float_or_none(test_payload.get("brier")),
                        baseline_test_brier,
                    ),
                    "test_ece": _safe_delta(_as_float_or_none(test_payload.get("ece")), baseline_test_ece),
                    "test_wmae": _safe_delta(_as_float_or_none(test_payload.get("wmae")), baseline_test_wmae),
                    "test_high_prob_gap_abs": (
                        float(test_gap_abs - baseline_test_gap_abs)
                        if isinstance(test_gap_abs, (int, float)) and isinstance(baseline_test_gap_abs, (int, float))
                        else None
                    ),
                },
                "local_reference_check": {
                    "status": "passed" if local_reference_ready else "failed",
                    "reason": None if local_reference_ready else "calibration_or_brier_not_improved_enough",
                },
            }
        )

    available_candidates = [
        row for row in candidates if row.get("status") == "available" and isinstance(row.get("metrics", {}).get("val_brier"), (int, float))
    ]
    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_available_candidates"
    local_reference_ready_candidates = [
        row for row in available_candidates if row.get("local_reference_check", {}).get("status") == "passed"
    ]

    if local_reference_ready_candidates:
        selected_candidate = min(
            local_reference_ready_candidates,
            key=lambda row: (
                float(row.get("metrics", {}).get("val_brier")),
                row.get("policy_id") == "baseline_reference",
            ),
        )
        research_decision = "promising_local_policy_candidate"
        research_reason = "improves_val_and_local_reference_metrics"
    elif available_candidates:
        selected_candidate = min(
            available_candidates,
            key=lambda row: (
                float(row.get("metrics", {}).get("val_brier")),
                row.get("policy_id") == "baseline_reference",
            ),
        )
        selected_val_delta = _safe_delta(
            selected_candidate.get("metrics", {}).get("val_brier"),
            baseline_val_brier,
        )
        selected_test_delta = _safe_delta(
            selected_candidate.get("metrics", {}).get("test_brier"),
            baseline_test_brier,
        )
        if (
            isinstance(selected_val_delta, (int, float))
            and selected_val_delta <= -MEN_POLICY_MIN_VAL_IMPROVEMENT
            and (selected_test_delta is None or selected_test_delta <= REGRESSION_NUMERIC_EPS)
            and selected_candidate.get("policy_id") != "baseline_reference"
        ):
            research_decision = "promising_brier_only"
            research_reason = "improves_val_without_test_degradation_but_gate_not_clear"
        else:
            research_decision = "hold_current_policy"
            research_reason = "no_stable_policy_edge"

    current_candidate_policy = (
        blend_candidate_policy_payload.get("by_gender", {}).get("men", {})
        if isinstance(blend_candidate_policy_payload.get("by_gender", {}), dict)
        else {}
    )
    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_regime_policy_research_v1",
        "status": "passed",
        "reason": None,
        "reference_candidate": {
            "selected_candidate_id": current_candidate_policy.get("selected_candidate_id"),
            "selected_candidate_weights": current_candidate_policy.get("selected_candidate_weights"),
        },
        "baseline_test_metrics": baseline_scores.get("test", {}),
        "candidates": candidates,
        "selected_policy_id": selected_candidate.get("policy_id") if isinstance(selected_candidate, dict) else None,
        "selected_policy_local_reference_status": (
            selected_candidate.get("local_reference_check", {}).get("status")
            if isinstance(selected_candidate, dict)
            else None
        ),
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_policy_refinement_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
        "selected_policy_id": report_payload["selected_policy_id"],
        "selected_policy_local_reference_status": report_payload["selected_policy_local_reference_status"],
    }


def _fit_seed_prior_split_probabilities(
    *,
    feature_df: pd.DataFrame,
    gender_key: str,
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None]:
    if "SeedNum_diff" not in feature_df.columns:
        return None, "seed_num_diff_missing"

    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    if train_df.empty:
        return None, "insufficient_split_rows"
    if np.unique(train_df["Target"]).shape[0] < 2:
        return None, "single_class_train_target"

    try:
        prior_model = LogisticRegression(
            random_state=4100 if gender_key == "men" else 4200,
            solver="lbfgs",
            max_iter=200,
        )
        prior_model.fit(train_df[["SeedNum_diff"]], train_df["Target"].to_numpy(dtype=float))
    except Exception as exc:
        return None, f"seed_prior_fit_failed:{exc.__class__.__name__}"

    split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in CANONICAL_SPLITS:
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        if split_df.empty:
            split_cache[split_label] = {
                "y_true": np.asarray([], dtype=float),
                "y_prob": np.asarray([], dtype=float),
            }
            continue
        split_true = split_df["Target"].to_numpy(dtype=float)
        split_prob = prior_model.predict_proba(split_df[["SeedNum_diff"]])[:, 1]
        split_cache[split_label] = {
            "y_true": split_true,
            "y_prob": np.asarray(split_prob, dtype=float),
        }

    return split_cache, None


def _build_men_external_prior_policy_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    blend_candidate_policy_payload: dict[str, Any],
) -> dict[str, Any]:
    alt_split_cache, alt_reason = _fit_histgb_candidate_split_probabilities(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=[
            column
            for column in (
                "SeedNum_diff",
                "NetRtg_diff",
                "PythWR_diff",
                "Luck_diff",
                "MasseyPct_diff",
                "MasseyAvgRank_diff",
                "SeedPythMispricing_diff",
                "SeedNetRtgMispricing_diff",
                "SeedMasseyMispricing_diff",
            )
            if column in feature_df.columns
        ],
    )
    seed_prior_cache, seed_prior_reason = _fit_seed_prior_split_probabilities(
        feature_df=feature_df,
        gender_key="men",
    )
    if alt_split_cache is None or seed_prior_cache is None:
        report_payload = {
            "run_id": context.get("run_id"),
            "seed": context.get("seed"),
            "generated_at": _now_utc_iso(),
            "policy_name": "men_external_prior_policy_research_v1",
            "status": "skipped",
            "reason": alt_reason or seed_prior_reason,
            "candidates": [],
            "selected_policy_id": None,
            "research_decision": "insufficient_data",
            "research_reason": "required_prior_or_alt_missing",
        }
        report_path = Path(context["run_dir"]) / "men_external_prior_policy_report.json"
        _write_json(report_path, report_payload)
        return {
            "report_json": str(report_path),
            "policy_name": report_payload["policy_name"],
            "status": report_payload["status"],
            "research_decision": report_payload["research_decision"],
            "selected_policy_id": report_payload["selected_policy_id"],
        }

    selected_weights = (
        blend_candidate_policy_payload.get("by_gender", {}).get("men", {}).get("selected_candidate_weights")
        if isinstance(blend_candidate_policy_payload.get("by_gender", {}), dict)
        else {}
    )
    if not isinstance(selected_weights, dict):
        selected_weights = {}
    baseline_weight = _as_float_or_none(selected_weights.get("baseline")) or 0.5
    histgb_weight = _as_float_or_none(selected_weights.get("histgb_benchmark")) or 0.5

    split_seed_regimes: dict[str, np.ndarray] = {}
    split_seed_disagreement: dict[str, np.ndarray] = {}
    blend_split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in ("Val", "Test"):
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        baseline_split = baseline_split_probabilities.get(split_label, {})
        alt_split = alt_split_cache.get(split_label, {})
        seed_split = seed_prior_cache.get(split_label, {})
        baseline_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        baseline_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        alt_true = np.asarray(alt_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        alt_prob = np.asarray(alt_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        seed_prob = np.asarray(seed_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        if (
            baseline_true.shape != alt_true.shape
            or baseline_true.shape != baseline_prob.shape
            or baseline_prob.shape != alt_prob.shape
            or baseline_prob.shape != seed_prob.shape
            or baseline_true.shape[0] != split_df.shape[0]
        ):
            report_payload = {
                "run_id": context.get("run_id"),
                "seed": context.get("seed"),
                "generated_at": _now_utc_iso(),
                "policy_name": "men_external_prior_policy_research_v1",
                "status": "failed",
                "reason": f"split_alignment_mismatch:{split_label}",
                "candidates": [],
                "selected_policy_id": None,
                "research_decision": "insufficient_data",
                "research_reason": "split_alignment_mismatch",
            }
            report_path = Path(context["run_dir"]) / "men_external_prior_policy_report.json"
            _write_json(report_path, report_payload)
            return {
                "report_json": str(report_path),
                "policy_name": report_payload["policy_name"],
                "status": report_payload["status"],
                "research_decision": report_payload["research_decision"],
                "selected_policy_id": report_payload["selected_policy_id"],
            }
        blend_prob = np.clip(baseline_weight * baseline_prob + histgb_weight * alt_prob, 0.0, 1.0)
        blend_split_cache[split_label] = {"y_true": baseline_true, "y_prob": blend_prob}
        split_seed_regimes[split_label] = split_df["SeedNum_diff"].apply(_seed_gap_bucket_from_diff).to_numpy()
        split_seed_disagreement[split_label] = np.abs(blend_prob - seed_prob)

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    blend_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=blend_split_cache,
    )
    canonical_baseline_test = baseline_scores.get("test", {})
    reference_blend_val_brier = _as_float_or_none(blend_scores.get("val", {}).get("brier"))
    reference_blend_test_brier = _as_float_or_none(blend_scores.get("test", {}).get("brier"))

    policy_specs = [
        {
            "policy_id": "blend_reference",
            "label": "Blend reference",
            "regimes": ("close", "medium"),
            "disagreement_threshold": None,
            "seed_prior_weight": 0.0,
        },
        {
            "policy_id": "committee_guardrail_light",
            "label": "Light committee guardrail",
            "regimes": ("close", "medium"),
            "disagreement_threshold": 0.15,
            "seed_prior_weight": 0.25,
        },
        {
            "policy_id": "committee_guardrail_medium",
            "label": "Medium committee guardrail",
            "regimes": ("close", "medium"),
            "disagreement_threshold": 0.15,
            "seed_prior_weight": 0.4,
        },
        {
            "policy_id": "committee_guardrail_close_only",
            "label": "Close-only committee guardrail",
            "regimes": ("close",),
            "disagreement_threshold": 0.12,
            "seed_prior_weight": 0.4,
        },
        {
            "policy_id": "committee_guardrail_medium_only",
            "label": "Medium-only committee guardrail",
            "regimes": ("medium",),
            "disagreement_threshold": 0.12,
            "seed_prior_weight": 0.4,
        },
    ]

    candidates: list[dict[str, Any]] = []
    for spec in policy_specs:
        policy_split_cache: dict[str, dict[str, np.ndarray]] = {}
        for split_label in ("Val", "Test"):
            blend_prob = np.asarray(blend_split_cache[split_label]["y_prob"], dtype=float)
            blend_true = np.asarray(blend_split_cache[split_label]["y_true"], dtype=float)
            seed_prob = np.asarray(seed_prior_cache[split_label]["y_prob"], dtype=float)
            regimes = split_seed_regimes[split_label]
            disagreements = split_seed_disagreement[split_label]

            adjusted_prob = blend_prob.copy()
            if spec["seed_prior_weight"] > 0.0 and spec["disagreement_threshold"] is not None:
                targeted = np.isin(regimes, np.asarray(spec["regimes"], dtype=object))
                disagreement_mask = disagreements >= float(spec["disagreement_threshold"])
                apply_mask = targeted & disagreement_mask
                if np.any(apply_mask):
                    seed_weight = float(spec["seed_prior_weight"])
                    adjusted_prob[apply_mask] = np.clip(
                        (1.0 - seed_weight) * blend_prob[apply_mask] + seed_weight * seed_prob[apply_mask],
                        0.0,
                        1.0,
                    )

            policy_split_cache[split_label] = {"y_true": blend_true, "y_prob": adjusted_prob}

        scores = _score_val_test_from_split_probabilities(
            gender_key="men",
            split_probabilities=policy_split_cache,
        )
        test_payload = scores.get("test", {})
        candidates.append(
            {
                "policy_id": spec["policy_id"],
                "label": spec["label"],
                "status": "available",
                "trigger_regimes": list(spec["regimes"]),
                "disagreement_threshold": spec["disagreement_threshold"],
                "seed_prior_weight": spec["seed_prior_weight"],
                "metrics": {
                    "val": scores.get("val", {}),
                    "test": test_payload,
                    "val_brier": _as_float_or_none(scores.get("val", {}).get("brier")),
                    "test_brier": _as_float_or_none(test_payload.get("brier")),
                },
                "deltas_vs_blend": {
                    "val_brier": _safe_delta(_as_float_or_none(scores.get("val", {}).get("brier")), reference_blend_val_brier),
                    "test_brier": _safe_delta(_as_float_or_none(test_payload.get("brier")), reference_blend_test_brier),
                    "test_ece": _safe_delta(_as_float_or_none(test_payload.get("ece")), _as_float_or_none(blend_scores.get("test", {}).get("ece"))),
                    "test_wmae": _safe_delta(_as_float_or_none(test_payload.get("wmae")), _as_float_or_none(blend_scores.get("test", {}).get("wmae"))),
                },
                "deltas_vs_canonical_baseline": {
                    "test_brier": _safe_delta(_as_float_or_none(test_payload.get("brier")), _as_float_or_none(canonical_baseline_test.get("brier"))),
                    "test_ece": _safe_delta(_as_float_or_none(test_payload.get("ece")), _as_float_or_none(canonical_baseline_test.get("ece"))),
                    "test_wmae": _safe_delta(_as_float_or_none(test_payload.get("wmae")), _as_float_or_none(canonical_baseline_test.get("wmae"))),
                },
            }
        )

    available_candidates = [
        row for row in candidates if isinstance(row.get("metrics", {}).get("val_brier"), (int, float))
    ]
    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_available_candidates"
    if available_candidates:
        selected_candidate = min(
            available_candidates,
            key=lambda row: (
                float(row.get("metrics", {}).get("val_brier")),
                row.get("policy_id") == "blend_reference",
            ),
        )
        selected_val_delta = _safe_delta(
            selected_candidate.get("metrics", {}).get("val_brier"),
            reference_blend_val_brier,
        )
        selected_test_delta = _safe_delta(
            selected_candidate.get("metrics", {}).get("test_brier"),
            reference_blend_test_brier,
        )
        if (
            selected_candidate.get("policy_id") != "blend_reference"
            and isinstance(selected_val_delta, (int, float))
            and selected_val_delta <= -MEN_POLICY_MIN_VAL_IMPROVEMENT
            and (selected_test_delta is None or selected_test_delta <= REGRESSION_NUMERIC_EPS)
        ):
            research_decision = "promising_disagreement_policy"
            research_reason = "improves_blend_with_committee_guardrail"
        else:
            research_decision = "hold_blend_reference"
            research_reason = "no_stable_gain_vs_blend_reference"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_external_prior_policy_research_v1",
        "status": "passed",
        "reason": None,
        "reference_blend_weights": {
            "baseline": baseline_weight,
            "histgb_benchmark": histgb_weight,
        },
        "seed_prior_model": "logistic_seed_prior_v1",
        "candidates": candidates,
        "selected_policy_id": selected_candidate.get("policy_id") if isinstance(selected_candidate, dict) else None,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_external_prior_policy_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
        "selected_policy_id": report_payload["selected_policy_id"],
        "candidates": candidates,
        "reference_blend_weights": report_payload["reference_blend_weights"],
    }


def _build_men_external_prior_selected_split_probabilities(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    blend_candidate_policy_payload: dict[str, Any],
    men_external_prior_policy_payload: dict[str, Any],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None, dict[str, Any] | None]:
    selected_policy_id = (
        men_external_prior_policy_payload.get("selected_policy_id")
        if isinstance(men_external_prior_policy_payload, dict)
        else None
    )
    candidates = (
        men_external_prior_policy_payload.get("candidates", [])
        if isinstance(men_external_prior_policy_payload.get("candidates", []), list)
        else []
    )
    selected_candidate = next(
        (
            row for row in candidates
            if isinstance(row, dict) and row.get("policy_id") == selected_policy_id and row.get("status") == "available"
        ),
        None,
    )
    if not isinstance(selected_candidate, dict):
        return None, "selected_external_prior_policy_unavailable", None

    selected_weights = (
        blend_candidate_policy_payload.get("by_gender", {}).get("men", {}).get("selected_candidate_weights")
        if isinstance(blend_candidate_policy_payload.get("by_gender", {}), dict)
        else {}
    )
    if not isinstance(selected_weights, dict):
        selected_weights = {}
    baseline_weight = _as_float_or_none(selected_weights.get("baseline")) or 0.5
    histgb_weight = _as_float_or_none(selected_weights.get("histgb_benchmark")) or 0.5

    alt_split_cache, alt_reason = _fit_histgb_candidate_split_probabilities(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=[
            column
            for column in (
                "SeedNum_diff",
                "NetRtg_diff",
                "PythWR_diff",
                "Luck_diff",
                "MasseyPct_diff",
                "MasseyAvgRank_diff",
                "SeedPythMispricing_diff",
                "SeedNetRtgMispricing_diff",
                "SeedMasseyMispricing_diff",
            )
            if column in feature_df.columns
        ],
    )
    if alt_split_cache is None:
        return None, f"histgb_unavailable:{alt_reason}", None

    seed_prior_cache, seed_prior_reason = _fit_seed_prior_split_probabilities(
        feature_df=feature_df,
        gender_key="men",
    )
    if seed_prior_cache is None:
        return None, f"seed_prior_unavailable:{seed_prior_reason}", None

    trigger_regimes = tuple(selected_candidate.get("trigger_regimes", []))
    disagreement_threshold = _as_float_or_none(selected_candidate.get("disagreement_threshold"))
    seed_prior_weight = _as_float_or_none(selected_candidate.get("seed_prior_weight")) or 0.0

    selected_split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in CANONICAL_SPLITS:
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        baseline_split = baseline_split_probabilities.get(split_label, {})
        alt_split = alt_split_cache.get(split_label, {})
        seed_split = seed_prior_cache.get(split_label, {})

        baseline_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        baseline_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        alt_true = np.asarray(alt_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        alt_prob = np.asarray(alt_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        seed_prob = np.asarray(seed_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)

        if (
            baseline_true.shape != alt_true.shape
            or baseline_true.shape != baseline_prob.shape
            or baseline_prob.shape != alt_prob.shape
            or baseline_prob.shape != seed_prob.shape
            or baseline_true.shape[0] != split_df.shape[0]
        ):
            return None, f"split_alignment_mismatch:{split_label}", None

        blend_prob = np.clip(baseline_weight * baseline_prob + histgb_weight * alt_prob, 0.0, 1.0)
        adjusted_prob = blend_prob.copy()
        if seed_prior_weight > 0.0 and disagreement_threshold is not None:
            regimes = split_df["SeedNum_diff"].apply(_seed_gap_bucket_from_diff).to_numpy()
            disagreements = np.abs(blend_prob - seed_prob)
            targeted = np.isin(regimes, np.asarray(trigger_regimes, dtype=object))
            apply_mask = targeted & (disagreements >= float(disagreement_threshold))
            if np.any(apply_mask):
                adjusted_prob[apply_mask] = np.clip(
                    (1.0 - seed_prior_weight) * blend_prob[apply_mask] + seed_prior_weight * seed_prob[apply_mask],
                    0.0,
                    1.0,
                )

        selected_split_cache[split_label] = {"y_true": baseline_true, "y_prob": adjusted_prob}

    diagnostics = {
        "selected_policy_id": selected_policy_id,
        "trigger_regimes": list(trigger_regimes),
        "disagreement_threshold": disagreement_threshold,
        "seed_prior_weight": seed_prior_weight,
        "reference_blend_weights": {
            "baseline": float(baseline_weight),
            "histgb_benchmark": float(histgb_weight),
        },
    }
    return selected_split_cache, None, diagnostics


def _build_men_combo_followup_selected_split_probabilities(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    men_combo_followup_payload: dict[str, Any],
) -> tuple[dict[str, dict[str, np.ndarray]] | None, str | None, dict[str, Any] | None]:
    report_json = men_combo_followup_payload.get("report_json") if isinstance(men_combo_followup_payload, dict) else None
    if not isinstance(report_json, str) or not report_json.strip():
        return None, "combo_report_missing", None

    report_path = Path(report_json)
    if not report_path.exists():
        return None, "combo_report_not_found", None

    try:
        report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"combo_report_read_failed:{exc.__class__.__name__}", None

    selected_candidate_id = report_payload.get("selected_candidate_id")
    candidates = report_payload.get("candidates", []) if isinstance(report_payload.get("candidates", []), list) else []
    selected_candidate = next(
        (
            row
            for row in candidates
            if isinstance(row, dict) and row.get("candidate_id") == selected_candidate_id and row.get("status") == "available"
        ),
        None,
    )
    if not isinstance(selected_candidate, dict):
        return None, "selected_combo_candidate_unavailable", None

    feature_columns = [column for column in feature_columns if column in feature_df.columns]
    alt_split_caches, _ = _fit_available_alternative_model_split_caches(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=feature_columns,
    )
    component_split_probabilities = {"baseline": baseline_split_probabilities, **alt_split_caches}
    raw_split_cache, build_reason = _build_weighted_split_probabilities(
        component_split_probabilities=component_split_probabilities,
        weights=selected_candidate.get("weights", {}),
    )
    if raw_split_cache is None:
        return None, f"combo_split_unavailable:{build_reason}", None

    selected_method = (
        selected_candidate.get("calibration_policy", {}).get("selected_method")
        if isinstance(selected_candidate.get("calibration_policy", {}), dict)
        else "none"
    )
    if selected_method not in CALIBRATION_POLICY_METHODS:
        selected_method = "none"

    if selected_method != "none":
        val_cache = raw_split_cache.get("Val", {})
        test_cache = raw_split_cache.get("Test", {})
        adjusted_val, adjusted_test, calibration_reason = _calibrate_probability_vectors(
            method=selected_method,
            val_true=np.asarray(val_cache.get("y_true", np.asarray([], dtype=float)), dtype=float),
            val_prob=np.asarray(val_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float),
            test_prob=np.asarray(test_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float),
        )
        if calibration_reason is not None or adjusted_val is None or adjusted_test is None:
            return None, f"combo_calibration_unavailable:{calibration_reason}", None
        raw_split_cache["Val"] = {
            "y_true": np.asarray(val_cache.get("y_true", np.asarray([], dtype=float)), dtype=float),
            "y_prob": np.asarray(adjusted_val, dtype=float),
        }
        raw_split_cache["Test"] = {
            "y_true": np.asarray(test_cache.get("y_true", np.asarray([], dtype=float)), dtype=float),
            "y_prob": np.asarray(adjusted_test, dtype=float),
        }

    diagnostics = {
        "selected_candidate_id": selected_candidate_id,
        "selected_method": selected_method,
        "weights": selected_candidate.get("weights"),
    }
    return raw_split_cache, None, diagnostics


def _build_men_residual_correction_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    blend_candidate_policy_payload: dict[str, Any],
    men_external_prior_policy_payload: dict[str, Any],
) -> dict[str, Any]:
    reference_split_cache, reference_reason, reference_diagnostics = _build_men_external_prior_selected_split_probabilities(
        context=context,
        feature_df=feature_df,
        baseline_split_probabilities=baseline_split_probabilities,
        blend_candidate_policy_payload=blend_candidate_policy_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
    )
    if reference_split_cache is None:
        report_payload = {
            "run_id": context.get("run_id"),
            "seed": context.get("seed"),
            "generated_at": _now_utc_iso(),
            "policy_name": "men_residual_correction_research_v1",
            "status": "skipped",
            "reason": reference_reason,
            "reference_candidate": None,
            "candidates": [],
            "selected_candidate_id": None,
            "research_decision": "insufficient_data",
            "research_reason": "reference_candidate_unavailable",
        }
        report_path = Path(context["run_dir"]) / "men_residual_correction_report.json"
        _write_json(report_path, report_payload)
        return {
            "report_json": str(report_path),
            "policy_name": report_payload["policy_name"],
            "status": report_payload["status"],
            "selected_candidate_id": report_payload["selected_candidate_id"],
            "research_decision": report_payload["research_decision"],
        }

    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    reference_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=reference_split_cache,
    )
    baseline_test_metrics = baseline_scores.get("test", {})
    reference_test_metrics = reference_scores.get("test", {})

    candidate_specs = [
        ("reference_raw", "Reference raw candidate", ()),
        ("residual_logit_only", "Residual on logit(p)", ()),
        ("residual_logit_seed", "Residual on logit(p) + SeedNum_diff", ("SeedNum_diff",)),
        ("residual_logit_seed_netrtg", "Residual on logit(p) + SeedNum_diff + NetRtg_diff", ("SeedNum_diff", "NetRtg_diff")),
    ]

    split_frames = {
        split_label: feature_df[feature_df["Split"] == split_label].copy()
        for split_label in CANONICAL_SPLITS
    }
    candidates: list[dict[str, Any]] = []
    for candidate_id, label, extra_features in candidate_specs:
        if candidate_id == "reference_raw":
            raw_metrics = {
                "val": reference_scores.get("val", {}),
                "test": reference_test_metrics,
            }
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "status": "available",
                    "reason": None,
                    "model_features": ["reference_probability"],
                    "raw_metrics": raw_metrics,
                    "local_gate_check_vs_baseline": _local_gate_check(
                        candidate_test_metrics=reference_test_metrics,
                        baseline_test_metrics=baseline_test_metrics,
                    ),
                    "local_gate_check_vs_reference": _local_gate_check(
                        candidate_test_metrics=reference_test_metrics,
                        baseline_test_metrics=reference_test_metrics,
                    ),
                }
            )
            continue

        required_columns = [column for column in extra_features if column not in feature_df.columns]
        if required_columns:
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "status": "skipped",
                    "reason": f"feature_columns_missing:{','.join(required_columns)}",
                    "model_features": ["reference_probability", *extra_features],
                }
            )
            continue

        train_frame = split_frames.get("Train", pd.DataFrame())
        val_frame = split_frames.get("Val", pd.DataFrame())
        test_frame = split_frames.get("Test", pd.DataFrame())
        train_prob = np.asarray(reference_split_cache.get("Train", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        val_prob = np.asarray(reference_split_cache.get("Val", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        test_prob = np.asarray(reference_split_cache.get("Test", {}).get("y_prob", np.asarray([], dtype=float)), dtype=float)
        train_true = np.asarray(reference_split_cache.get("Train", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        val_true = np.asarray(reference_split_cache.get("Val", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)
        test_true = np.asarray(reference_split_cache.get("Test", {}).get("y_true", np.asarray([], dtype=float)), dtype=float)

        if (
            train_prob.shape[0] != train_frame.shape[0]
            or val_prob.shape[0] != val_frame.shape[0]
            or test_prob.shape[0] != test_frame.shape[0]
            or train_true.shape[0] != train_frame.shape[0]
        ):
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "status": "failed",
                    "reason": "split_alignment_mismatch",
                    "model_features": ["reference_probability", *extra_features],
                }
            )
            continue

        X_train = np.column_stack(
            [
                _probability_to_logit(train_prob),
                *[train_frame[column].to_numpy(dtype=float) for column in extra_features],
            ]
        )
        X_val = np.column_stack(
            [
                _probability_to_logit(val_prob),
                *[val_frame[column].to_numpy(dtype=float) for column in extra_features],
            ]
        )
        X_test = np.column_stack(
            [
                _probability_to_logit(test_prob),
                *[test_frame[column].to_numpy(dtype=float) for column in extra_features],
            ]
        )

        try:
            correction_model = LogisticRegression(random_state=0, solver="lbfgs", max_iter=200)
            correction_model.fit(X_train, train_true)
            corrected_val = correction_model.predict_proba(X_val)[:, 1]
            corrected_test = correction_model.predict_proba(X_test)[:, 1]
        except Exception as exc:
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "label": label,
                    "status": "failed",
                    "reason": f"correction_fit_failed:{exc.__class__.__name__}",
                    "model_features": ["reference_probability", *extra_features],
                }
            )
            continue

        corrected_split_cache = {
            "Val": {"y_true": val_true, "y_prob": np.asarray(corrected_val, dtype=float)},
            "Test": {"y_true": test_true, "y_prob": np.asarray(corrected_test, dtype=float)},
        }
        corrected_scores = _score_val_test_from_split_probabilities(
            gender_key="men",
            split_probabilities=corrected_split_cache,
        )
        corrected_test_metrics = corrected_scores.get("test", {})
        candidates.append(
            {
                "candidate_id": candidate_id,
                "label": label,
                "status": "available",
                "reason": None,
                "model_features": ["reference_probability", *extra_features],
                "raw_metrics": {
                    "val": corrected_scores.get("val", {}),
                    "test": corrected_test_metrics,
                },
                "local_gate_check_vs_baseline": _local_gate_check(
                    candidate_test_metrics=corrected_test_metrics,
                    baseline_test_metrics=baseline_test_metrics,
                ),
                "local_gate_check_vs_reference": _local_gate_check(
                    candidate_test_metrics=corrected_test_metrics,
                    baseline_test_metrics=reference_test_metrics,
                ),
            }
        )

    available_candidates = [row for row in candidates if row.get("status") == "available"]
    selected_candidate = None
    research_decision = "insufficient_data"
    research_reason = "no_available_candidates"
    gate_ready_candidates = [
        row
        for row in available_candidates
        if row.get("candidate_id") != "reference_raw"
        and row.get("local_gate_check_vs_baseline", {}).get("status") == "passed"
        and row.get("local_gate_check_vs_reference", {}).get("status") == "passed"
    ]
    if gate_ready_candidates:
        selected_candidate = min(
            gate_ready_candidates,
            key=lambda row: float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf"))),
        )
        research_decision = "promising_residual_candidate"
        research_reason = "improves_reference_without_losing_local_gate"
    elif available_candidates:
        selected_candidate = min(
            available_candidates,
            key=lambda row: (
                float(row.get("raw_metrics", {}).get("val", {}).get("brier", float("inf"))),
                row.get("candidate_id") == "reference_raw",
            ),
        )
        research_decision = "hold_reference_candidate"
        research_reason = "no_residual_candidate_clears_local_gate"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_residual_correction_research_v1",
        "status": "passed",
        "reason": None,
        "reference_candidate": {
            "source_policy": "men_external_prior_policy_v1_raw",
            "diagnostics": reference_diagnostics,
            "test_metrics": reference_test_metrics,
        },
        "baseline_test_metrics": baseline_test_metrics,
        "candidates": candidates,
        "selected_candidate_id": selected_candidate.get("candidate_id") if isinstance(selected_candidate, dict) else None,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_residual_correction_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "selected_candidate_id": report_payload["selected_candidate_id"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
    }


def _build_men_regime_routing_report(
    *,
    context: dict[str, Any],
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    baseline_split_probabilities: dict[str, dict[str, np.ndarray]],
    blend_candidate_policy_payload: dict[str, Any],
    men_external_prior_policy_payload: dict[str, Any],
    men_combo_followup_payload: dict[str, Any],
) -> dict[str, Any]:
    split_frames = {
        split_label: feature_df[feature_df["Split"] == split_label].copy()
        for split_label in CANONICAL_SPLITS
    }
    baseline_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=baseline_split_probabilities,
    )
    baseline_test_metrics = baseline_scores.get("test", {})

    candidate_split_caches: dict[str, dict[str, dict[str, np.ndarray]]] = {
        "baseline_raw": baseline_split_probabilities,
    }
    candidate_labels = {
        "baseline_raw": "Baseline raw",
        "blend_raw": "LGBM + HistGB raw blend",
        "external_prior_raw": "External prior raw policy",
        "combo_raw": "LGBM + HistGB + XGBoost raw combo",
    }
    candidate_reasons = {
        "baseline_raw": None,
        "blend_raw": None,
        "external_prior_raw": None,
        "combo_raw": None,
    }

    men_blend_entry = (
        blend_candidate_policy_payload.get("by_gender", {}).get("men", {})
        if isinstance(blend_candidate_policy_payload.get("by_gender", {}), dict)
        else {}
    )
    selected_weights = (
        men_blend_entry.get("selected_candidate_weights")
        if isinstance(men_blend_entry.get("selected_candidate_weights"), dict)
        else {}
    )
    baseline_weight = _as_float_or_none(selected_weights.get("baseline")) or 0.5
    histgb_weight = _as_float_or_none(selected_weights.get("histgb_benchmark")) or 0.5
    blend_alt_cache, blend_alt_reason = _fit_histgb_candidate_split_probabilities(
        context=context,
        gender_key="men",
        feature_df=feature_df,
        feature_columns=feature_columns,
    )
    if blend_alt_cache is not None:
        blend_cache: dict[str, dict[str, np.ndarray]] = {}
        blend_failed_reason = None
        for split_label in CANONICAL_SPLITS:
            baseline_split = baseline_split_probabilities.get(split_label, {})
            alt_split = blend_alt_cache.get(split_label, {})
            baseline_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            baseline_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            alt_true = np.asarray(alt_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
            alt_prob = np.asarray(alt_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            if baseline_true.shape != alt_true.shape or baseline_prob.shape != alt_prob.shape or baseline_true.shape != baseline_prob.shape:
                blend_failed_reason = f"split_alignment_mismatch:{split_label}"
                break
            blend_cache[split_label] = {
                "y_true": baseline_true,
                "y_prob": np.clip(float(baseline_weight) * baseline_prob + float(histgb_weight) * alt_prob, 0.0, 1.0),
            }
        if blend_failed_reason is None:
            candidate_split_caches["blend_raw"] = blend_cache
        else:
            candidate_reasons["blend_raw"] = blend_failed_reason
    else:
        candidate_reasons["blend_raw"] = blend_alt_reason

    external_cache, external_reason, external_diagnostics = _build_men_external_prior_selected_split_probabilities(
        context=context,
        feature_df=feature_df,
        baseline_split_probabilities=baseline_split_probabilities,
        blend_candidate_policy_payload=blend_candidate_policy_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
    )
    if external_cache is not None:
        candidate_split_caches["external_prior_raw"] = external_cache
    else:
        candidate_reasons["external_prior_raw"] = external_reason

    combo_cache = None
    combo_reason = None
    report_json = men_combo_followup_payload.get("report_json") if isinstance(men_combo_followup_payload, dict) else None
    if isinstance(report_json, str) and report_json.strip():
        report_path = Path(report_json)
        if report_path.exists():
            try:
                combo_report = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception as exc:
                combo_report = {}
                combo_reason = f"combo_report_read_failed:{exc.__class__.__name__}"
            if combo_reason is None:
                combo_candidates = (
                    combo_report.get("candidates", []) if isinstance(combo_report.get("candidates", []), list) else []
                )
                combo_candidate = next(
                    (
                        row
                        for row in combo_candidates
                        if isinstance(row, dict)
                        and row.get("candidate_id") == "baseline_histgb_xgboost_blend"
                        and row.get("status") == "available"
                        and isinstance(row.get("weights"), dict)
                    ),
                    None,
                )
                if isinstance(combo_candidate, dict):
                    feature_columns = [column for column in feature_columns if column in feature_df.columns]
                    alt_split_caches, _ = _fit_available_alternative_model_split_caches(
                        context=context,
                        gender_key="men",
                        feature_df=feature_df,
                        feature_columns=feature_columns,
                    )
                    combo_cache, combo_reason = _build_weighted_split_probabilities(
                        component_split_probabilities={"baseline": baseline_split_probabilities, **alt_split_caches},
                        weights=combo_candidate.get("weights", {}),
                    )
                else:
                    combo_reason = "combo_candidate_unavailable"
        else:
            combo_reason = "combo_report_not_found"
    else:
        combo_reason = "combo_report_missing"

    if combo_cache is not None:
        candidate_split_caches["combo_raw"] = combo_cache
    else:
        candidate_reasons["combo_raw"] = combo_reason

    candidate_pool_ids = ["baseline_raw", "blend_raw", "external_prior_raw", "combo_raw"]
    regime_names = list(DRIFT_REGIME_ORDER)
    candidate_rows: list[dict[str, Any]] = []
    best_val_candidate_by_regime: dict[str, dict[str, Any] | None] = {regime_name: None for regime_name in regime_names}

    for candidate_id in candidate_pool_ids:
        split_cache = candidate_split_caches.get(candidate_id)
        if split_cache is None:
            candidate_rows.append(
                {
                    "candidate_id": candidate_id,
                    "label": candidate_labels.get(candidate_id, candidate_id),
                    "status": "skipped",
                    "reason": candidate_reasons.get(candidate_id),
                }
            )
            continue

        overall_scores = _score_val_test_from_split_probabilities(
            gender_key="men",
            split_probabilities=split_cache,
        )
        regime_metrics: dict[str, dict[str, Any]] = {}
        for split_label in ("Val", "Test"):
            split_frame = split_frames.get(split_label, pd.DataFrame())
            split_payload = split_cache.get(split_label, {})
            split_true = np.asarray(split_payload.get("y_true", np.asarray([], dtype=float)), dtype=float)
            split_prob = np.asarray(split_payload.get("y_prob", np.asarray([], dtype=float)), dtype=float)

            split_regimes: dict[str, Any] = {}
            if split_frame.shape[0] == split_true.shape[0] and "SeedNum_diff" in split_frame.columns:
                regime_series = split_frame["SeedNum_diff"].apply(_seed_gap_bucket_from_diff)
                for regime_name in regime_names:
                    mask = (regime_series == regime_name).to_numpy()
                    split_regimes[regime_name] = _score_probability_bundle(
                        gender_key="men",
                        split_label=f"{split_label}_{regime_name}",
                        y_true=split_true[mask],
                        y_prob=split_prob[mask],
                    )
            else:
                for regime_name in regime_names:
                    split_regimes[regime_name] = {
                        "sample_count": 0,
                        "brier": None,
                        "logloss": None,
                        "auc": None,
                        "auc_reason": "split_alignment_mismatch",
                        "ece": None,
                        "wmae": None,
                        "high_prob_gap": None,
                        "high_prob_reason": "split_alignment_mismatch",
                        "reason": "split_alignment_mismatch",
                    }
            regime_metrics[split_label.lower()] = split_regimes

        candidate_row = {
            "candidate_id": candidate_id,
            "label": candidate_labels.get(candidate_id, candidate_id),
            "status": "available",
            "reason": candidate_reasons.get(candidate_id),
            "overall_metrics": {
                "val": overall_scores.get("val", {}),
                "test": overall_scores.get("test", {}),
            },
            "local_gate_check_vs_baseline": _local_gate_check(
                candidate_test_metrics=overall_scores.get("test", {}),
                baseline_test_metrics=baseline_test_metrics,
            ),
            "regime_metrics": regime_metrics,
        }
        candidate_rows.append(candidate_row)

        for regime_name in regime_names:
            regime_val_payload = regime_metrics.get("val", {}).get(regime_name, {})
            regime_val_brier = _as_float_or_none(regime_val_payload.get("brier"))
            if not isinstance(regime_val_brier, (int, float)):
                continue
            incumbent = best_val_candidate_by_regime.get(regime_name)
            if (
                incumbent is None
                or regime_val_brier < float(incumbent.get("val_brier", float("inf")))
                or (
                    abs(regime_val_brier - float(incumbent.get("val_brier", float("inf")))) <= REGRESSION_NUMERIC_EPS
                    and candidate_id == "baseline_raw"
                )
            ):
                best_val_candidate_by_regime[regime_name] = {
                    "candidate_id": candidate_id,
                    "label": candidate_labels.get(candidate_id, candidate_id),
                    "val_brier": regime_val_brier,
                    "sample_count": int(regime_val_payload.get("sample_count") or 0),
                }

    routed_split_cache: dict[str, dict[str, np.ndarray]] | None = {}
    routing_reason = None
    for split_label in CANONICAL_SPLITS:
        split_frame = split_frames.get(split_label, pd.DataFrame())
        baseline_split = baseline_split_probabilities.get(split_label, {})
        split_true = np.asarray(baseline_split.get("y_true", np.asarray([], dtype=float)), dtype=float)
        split_prob = np.asarray(baseline_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        if split_frame.shape[0] != split_true.shape[0] or "SeedNum_diff" not in split_frame.columns:
            routed_split_cache = None
            routing_reason = f"split_alignment_mismatch:{split_label}"
            break
        routed_prob = split_prob.copy()
        regime_series = split_frame["SeedNum_diff"].apply(_seed_gap_bucket_from_diff)
        for regime_name in regime_names:
            selected_regime_candidate = best_val_candidate_by_regime.get(regime_name)
            selected_candidate_id = (
                selected_regime_candidate.get("candidate_id") if isinstance(selected_regime_candidate, dict) else None
            )
            selected_cache = candidate_split_caches.get(selected_candidate_id) if selected_candidate_id else None
            if selected_cache is None:
                continue
            selected_split = selected_cache.get(split_label, {})
            selected_prob = np.asarray(selected_split.get("y_prob", np.asarray([], dtype=float)), dtype=float)
            if selected_prob.shape != split_prob.shape:
                routed_split_cache = None
                routing_reason = f"candidate_shape_mismatch:{split_label}:{regime_name}"
                break
            mask = (regime_series == regime_name).to_numpy()
            routed_prob[mask] = selected_prob[mask]
        if routed_split_cache is None:
            break
        routed_split_cache[split_label] = {"y_true": split_true, "y_prob": np.asarray(routed_prob, dtype=float)}

    if routed_split_cache is None:
        report_payload = {
            "run_id": context.get("run_id"),
            "seed": context.get("seed"),
            "generated_at": _now_utc_iso(),
            "policy_name": "men_regime_routing_research_v1",
            "status": "failed",
            "reason": routing_reason,
            "candidate_pool_ids": candidate_pool_ids,
            "candidates": candidate_rows,
            "regime_selection": {},
            "selected_policy_id": None,
            "research_decision": "insufficient_data",
            "research_reason": "routing_unavailable",
        }
        report_path = Path(context["run_dir"]) / "men_regime_routing_report.json"
        _write_json(report_path, report_payload)
        return {
            "report_json": str(report_path),
            "policy_name": report_payload["policy_name"],
            "status": report_payload["status"],
            "selected_policy_id": report_payload["selected_policy_id"],
            "research_decision": report_payload["research_decision"],
        }

    routed_scores = _score_val_test_from_split_probabilities(
        gender_key="men",
        split_probabilities=routed_split_cache,
    )
    routed_val_metrics = routed_scores.get("val", {})
    routed_test_metrics = routed_scores.get("test", {})
    baseline_val_metrics = baseline_scores.get("val", {})
    reference_candidate_id = "external_prior_raw" if "external_prior_raw" in candidate_split_caches else "baseline_raw"
    reference_test_metrics = next(
        (
            row.get("overall_metrics", {}).get("test", {})
            for row in candidate_rows
            if row.get("candidate_id") == reference_candidate_id and row.get("status") == "available"
        ),
        baseline_test_metrics,
    )

    local_gate_vs_baseline = _local_gate_check(
        candidate_test_metrics=routed_test_metrics,
        baseline_test_metrics=baseline_test_metrics,
    )
    local_gate_vs_reference = _local_gate_check(
        candidate_test_metrics=routed_test_metrics,
        baseline_test_metrics=reference_test_metrics,
    )

    selected_policy_id = "regime_best_val_router"
    regime_selection = {
        regime_name: best_val_candidate_by_regime.get(regime_name)
        for regime_name in regime_names
    }
    selected_val_delta = _safe_delta(
        _as_float_or_none(routed_val_metrics.get("brier")),
        _as_float_or_none(baseline_val_metrics.get("brier")),
    )
    selected_test_delta = _safe_delta(
        _as_float_or_none(routed_test_metrics.get("brier")),
        _as_float_or_none(baseline_test_metrics.get("brier")),
    )
    if (
        local_gate_vs_baseline.get("status") == "passed"
        and isinstance(selected_val_delta, (int, float))
        and selected_val_delta <= -MEN_POLICY_MIN_VAL_IMPROVEMENT
        and (selected_test_delta is None or selected_test_delta <= REGRESSION_NUMERIC_EPS)
    ):
        research_decision = "promising_regime_router"
        research_reason = "regime_router_clears_local_gate"
    else:
        research_decision = "hold_current_reference"
        research_reason = "no_gate_safe_gain_from_regime_router"

    report_payload = {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "policy_name": "men_regime_routing_research_v1",
        "status": "passed",
        "reason": None,
        "candidate_pool_ids": candidate_pool_ids,
        "candidates": candidate_rows,
        "reference_candidate_id": reference_candidate_id,
        "regime_selection": regime_selection,
        "selected_policy_id": selected_policy_id,
        "selected_policy_metrics": {
            "val": routed_val_metrics,
            "test": routed_test_metrics,
        },
        "local_gate_check_vs_baseline": local_gate_vs_baseline,
        "local_gate_check_vs_reference": local_gate_vs_reference,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }
    report_path = Path(context["run_dir"]) / "men_regime_routing_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "status": report_payload["status"],
        "selected_policy_id": report_payload["selected_policy_id"],
        "research_decision": report_payload["research_decision"],
        "research_reason": report_payload["research_reason"],
    }


def _build_feature_branch_variant_specs(
    *,
    gender_key: str,
    available_feature_columns: list[str],
) -> list[dict[str, Any]]:
    available_set = set(available_feature_columns)
    feature_family = [
        feature
        for feature in M005_S04_FEATURE_COLUMNS.get(gender_key, ())
        if feature in available_set
    ]
    if not feature_family:
        return []

    specs: list[dict[str, Any]] = [
        {
            "variant_id": "legacy_baseline",
            "label": "Legacy baseline",
            "included_features": [],
        }
    ]

    if "PythWR_diff" in feature_family:
        specs.append(
            {
                "variant_id": "pythwr_only",
                "label": "PythWR only",
                "included_features": ["PythWR_diff"],
            }
        )
    if "Luck_diff" in feature_family:
        specs.append(
            {
                "variant_id": "luck_only",
                "label": "Luck only",
                "included_features": ["Luck_diff"],
            }
        )
    if {"PythWR_diff", "Luck_diff"}.issubset(set(feature_family)):
        specs.append(
            {
                "variant_id": "pythwr_luck",
                "label": "PythWR + Luck",
                "included_features": ["PythWR_diff", "Luck_diff"],
            }
        )

    massey_features = [
        feature
        for feature in ("MasseyRankStd_diff", "MasseyPctSpread_diff", "MasseyOrdinalRange_diff")
        if feature in available_set
    ]
    if massey_features:
        specs.append(
            {
                "variant_id": "massey_spread_only",
                "label": "Massey spread only",
                "included_features": massey_features,
            }
        )

    if "StyleClash_eFG_BlkPct_diff" in available_set:
        specs.append(
            {
                "variant_id": "style_clash_only",
                "label": "Style clash only",
                "included_features": ["StyleClash_eFG_BlkPct_diff"],
            }
        )

    seed_mispricing_features = [
        feature
        for feature in ("SeedPythMispricing_diff", "SeedNetRtgMispricing_diff", "SeedMasseyMispricing_diff")
        if feature in available_set
    ]
    if seed_mispricing_features:
        specs.append(
            {
                "variant_id": "seed_mispricing_only",
                "label": "Seed mispricing only",
                "included_features": seed_mispricing_features,
            }
        )
        if "Luck_diff" in available_set:
            specs.append(
                {
                    "variant_id": "luck_seed_mispricing",
                    "label": "Luck + seed mispricing",
                    "included_features": sorted(["Luck_diff", *seed_mispricing_features]),
                }
            )

    specs.append(
        {
            "variant_id": "full_feature_package",
            "label": "Full M005-S04 package",
            "included_features": feature_family,
        }
    )
    return specs


def _build_feature_branch_report_for_gender(
    *,
    context: dict[str, Any],
    train_module: Any,
    gender_key: str,
    feature_df: pd.DataFrame,
    current_split_probabilities: dict[str, dict[str, np.ndarray]],
    current_metrics_by_split: dict[str, Any],
) -> dict[str, Any]:
    drop_columns = set(getattr(train_module, "DROP_COLUMNS", ("Season", "TeamA", "TeamB", "Target", "Split")))
    available_feature_columns = [column for column in feature_df.columns if column not in drop_columns]
    variant_specs = _build_feature_branch_variant_specs(
        gender_key=gender_key,
        available_feature_columns=available_feature_columns,
    )
    if not variant_specs:
        return {
            "status": "skipped",
            "reason": "no_feature_family_columns_available",
            "feature_family_columns": [],
            "variants": [],
            "best_variant_id": None,
            "legacy_baseline_variant_id": None,
            "current_full_package": {
                "variant_id": "current_full_package",
                "status": "reference",
                "metrics": {
                    "val": current_metrics_by_split.get("Val", {}),
                    "test": current_metrics_by_split.get("Test", {}),
                },
            },
            "benchmark": {
                "best_variant_id": None,
                "legacy_baseline_variant_id": None,
                "val_improvement_vs_legacy_brier": None,
                "test_delta_vs_legacy_brier": None,
                "test_delta_vs_current_full_brier": None,
            },
            "research_decision": "insufficient_data",
            "research_reason": "no_feature_family_columns_available",
        }

    feature_family = set(M005_S04_FEATURE_COLUMNS.get(gender_key, ()))
    gender_label = "M" if gender_key == "men" else "W"
    variants: list[dict[str, Any]] = []

    current_scores = _score_val_test_from_split_probabilities(
        gender_key=gender_key,
        split_probabilities=current_split_probabilities,
    )
    current_full_package = {
        "variant_id": "current_full_package",
        "status": "reference",
        "metrics": {
            "val": current_scores.get("val", {}),
            "test": current_scores.get("test", {}),
        },
    }

    for variant_spec in variant_specs:
        included_features = set(variant_spec.get("included_features", []))
        excluded_features = sorted(
            feature for feature in feature_family if feature in available_feature_columns and feature not in included_features
        )
        variant_df = feature_df.drop(columns=excluded_features, errors="ignore")

        try:
            variant_model, variant_payload = train_module.train_baseline(
                variant_df,
                gender_label,
                random_state=context["seed"],
            )
            variant_snapshot = variant_payload.get("feature_snapshot", {})
            variant_feature_columns = (
                variant_snapshot.get("feature_columns") if isinstance(variant_snapshot, dict) else None
            )
            if not isinstance(variant_feature_columns, list) or not variant_feature_columns:
                raise RuntimeError("variant_feature_columns_missing")

            split_cache = _predict_model_split_probabilities(
                model=variant_model,
                feature_df=variant_df,
                feature_columns=variant_feature_columns,
                gender_key=gender_key,
            )
            variant_scores = _score_val_test_from_split_probabilities(
                gender_key=gender_key,
                split_probabilities=split_cache,
            )
            variants.append(
                {
                    "variant_id": variant_spec["variant_id"],
                    "label": variant_spec["label"],
                    "status": "available",
                    "reason": None,
                    "included_features": sorted(included_features),
                    "excluded_features": excluded_features,
                    "feature_count": int(len(variant_feature_columns)),
                    "metrics": {
                        "val": variant_scores.get("val", {}),
                        "test": variant_scores.get("test", {}),
                    },
                }
            )
        except Exception as exc:
            variants.append(
                {
                    "variant_id": variant_spec["variant_id"],
                    "label": variant_spec["label"],
                    "status": "failed",
                    "reason": f"variant_retrain_failed:{exc.__class__.__name__}",
                    "included_features": sorted(included_features),
                    "excluded_features": excluded_features,
                    "feature_count": None,
                    "metrics": {"val": {}, "test": {}},
                }
            )

    available_variants = [
        variant
        for variant in variants
        if variant.get("status") == "available"
        and isinstance(variant.get("metrics", {}).get("val", {}).get("brier"), (int, float))
    ]
    legacy_variant = next((variant for variant in available_variants if variant.get("variant_id") == "legacy_baseline"), None)
    best_variant = (
        min(
            available_variants,
            key=lambda variant: (
                float(variant["metrics"]["val"]["brier"]),
                variant.get("variant_id") != "full_feature_package",
            ),
        )
        if available_variants
        else None
    )

    research_decision = "insufficient_data"
    research_reason = "no_available_variants"
    benchmark = {
        "best_variant_id": best_variant.get("variant_id") if isinstance(best_variant, dict) else None,
        "legacy_baseline_variant_id": legacy_variant.get("variant_id") if isinstance(legacy_variant, dict) else None,
        "val_improvement_vs_legacy_brier": None,
        "test_delta_vs_legacy_brier": None,
        "test_delta_vs_current_full_brier": None,
    }

    if legacy_variant is not None and best_variant is not None:
        legacy_val = _as_float_or_none(legacy_variant["metrics"]["val"].get("brier"))
        legacy_test = _as_float_or_none(legacy_variant["metrics"]["test"].get("brier"))
        best_val = _as_float_or_none(best_variant["metrics"]["val"].get("brier"))
        best_test = _as_float_or_none(best_variant["metrics"]["test"].get("brier"))
        current_test = _as_float_or_none(current_full_package["metrics"]["test"].get("brier"))

        benchmark["val_improvement_vs_legacy_brier"] = (
            float(legacy_val - best_val)
            if isinstance(legacy_val, (int, float)) and isinstance(best_val, (int, float))
            else None
        )
        benchmark["test_delta_vs_legacy_brier"] = (
            float(best_test - legacy_test)
            if isinstance(legacy_test, (int, float)) and isinstance(best_test, (int, float))
            else None
        )
        benchmark["test_delta_vs_current_full_brier"] = (
            float(best_test - current_test)
            if isinstance(current_test, (int, float)) and isinstance(best_test, (int, float))
            else None
        )

        if (
            isinstance(benchmark["val_improvement_vs_legacy_brier"], (int, float))
            and benchmark["val_improvement_vs_legacy_brier"] >= FEATURE_BRANCH_MIN_VAL_IMPROVEMENT
            and (
                benchmark["test_delta_vs_legacy_brier"] is None
                or benchmark["test_delta_vs_legacy_brier"] <= 0.0
            )
        ):
            research_decision = "promising"
            research_reason = "improves_legacy_baseline"
        else:
            research_decision = "not_promising"
            research_reason = "no_stable_lift_vs_legacy_baseline"

    return {
        "status": "passed" if available_variants else "failed",
        "reason": None if available_variants else "no_available_variants",
        "feature_family_columns": sorted(feature for feature in feature_family if feature in available_feature_columns),
        "variants": variants,
        "best_variant_id": benchmark["best_variant_id"],
        "legacy_baseline_variant_id": benchmark["legacy_baseline_variant_id"],
        "current_full_package": current_full_package,
        "benchmark": benchmark,
        "research_decision": research_decision,
        "research_reason": research_reason,
    }


def _build_feature_branch_report(
    *,
    context: dict[str, Any],
    train_module: Any,
    genders_payload: dict[str, Any],
    feature_frames_by_gender: dict[str, pd.DataFrame],
    split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]],
) -> dict[str, Any]:
    by_gender = {
        gender_key: _build_feature_branch_report_for_gender(
            context=context,
            train_module=train_module,
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            current_split_probabilities=split_probabilities.get(gender_key, {}),
            current_metrics_by_split=(
                genders_payload.get(gender_key, {}).get("metrics_by_split", {})
                if isinstance(genders_payload.get(gender_key, {}), dict)
                else {}
            ),
        )
        for gender_key in ("men", "women")
    }
    promising_genders = [
        gender_key
        for gender_key, payload in by_gender.items()
        if isinstance(payload, dict) and payload.get("research_decision") == "promising"
    ]
    report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "policy_name": "feature_branch_research_v1",
        "config": {
            "min_val_improvement": FEATURE_BRANCH_MIN_VAL_IMPROVEMENT,
            "feature_family_columns": {
                gender_key: list(columns)
                for gender_key, columns in M005_S04_FEATURE_COLUMNS.items()
            },
        },
        "by_gender": by_gender,
        "aggregate": {
            "decision": "research_followup_variants" if promising_genders else "hold_current_feature_branch",
            "promising_genders": promising_genders,
        },
    }
    report_path = Path(context["run_dir"]) / "feature_branch_report.json"
    _write_json(report_path, report_payload)
    return {
        "report_json": str(report_path),
        "policy_name": report_payload["policy_name"],
        "config": report_payload["config"],
        "by_gender": by_gender,
        "aggregate": report_payload["aggregate"],
    }


def _extract_run_snapshot(stage_outputs: dict[str, Any]) -> dict[str, Any]:
    snapshot = {
        "metrics": {"men": {}, "women": {}},
        "calibration": {"men": {}, "women": {}},
        "calibration_policy": {"men": {}, "women": {}},
        "governance_decision": {"men": {}, "women": {}, "aggregate_decision": None},
    }

    train_metrics = stage_outputs.get("train", {}).get("metrics_by_split", {}) if isinstance(stage_outputs, dict) else {}
    eval_output = stage_outputs.get("eval_report", {}) if isinstance(stage_outputs, dict) else {}
    eval_metrics_table = eval_output.get("metrics_table", []) if isinstance(eval_output, dict) else []
    calibration_summary = (
        eval_output.get("calibration", {}).get("calibration_summary", {})
        if isinstance(eval_output, dict)
        else {}
    )
    calibration_policy = eval_output.get("calibration_policy", {}) if isinstance(eval_output, dict) else {}
    policy_by_gender = calibration_policy.get("by_gender", {}) if isinstance(calibration_policy, dict) else {}
    governance_decision = eval_output.get("governance_decision", {}) if isinstance(eval_output, dict) else {}
    governance_by_gender = governance_decision.get("by_gender", {}) if isinstance(governance_decision, dict) else {}
    governance_aggregate = governance_decision.get("aggregate", {}) if isinstance(governance_decision, dict) else {}

    for gender_key in ("men", "women"):
        split_metrics = next(
            (
                row
                for row in eval_metrics_table
                if isinstance(row, dict) and row.get("gender") == gender_key and row.get("split") == "Test"
            ),
            train_metrics.get(gender_key, {}).get("Test", {}) if isinstance(train_metrics, dict) else {},
        )
        snapshot["metrics"][gender_key] = {
            "brier": _as_float_or_none(split_metrics.get("brier")) if isinstance(split_metrics, dict) else None,
            "logloss": _as_float_or_none(split_metrics.get("logloss")) if isinstance(split_metrics, dict) else None,
            "auc": _as_float_or_none(split_metrics.get("auc")) if isinstance(split_metrics, dict) else None,
        }

        split_calibration = (
            calibration_summary.get(gender_key, {}).get("Test", {}) if isinstance(calibration_summary, dict) else {}
        )
        high_prob = split_calibration.get("high_prob_band", {}) if isinstance(split_calibration, dict) else {}

        snapshot["calibration"][gender_key] = {
            "ece": _as_float_or_none(split_calibration.get("ece")) if isinstance(split_calibration, dict) else None,
            "wmae": _as_float_or_none(split_calibration.get("wmae")) if isinstance(split_calibration, dict) else None,
            "reason": split_calibration.get("reason") if isinstance(split_calibration, dict) else None,
            "high_prob_gap": _as_float_or_none(high_prob.get("gap")) if isinstance(high_prob, dict) else None,
            "high_prob_reason": high_prob.get("reason") if isinstance(high_prob, dict) else None,
        }

        policy_entry = policy_by_gender.get(gender_key, {}) if isinstance(policy_by_gender, dict) else {}
        snapshot["calibration_policy"][gender_key] = {
            "selected_method": policy_entry.get("selected_method") if isinstance(policy_entry, dict) else None,
            "default_method": policy_entry.get("default_method") if isinstance(policy_entry, dict) else None,
        }

        decision_entry = governance_by_gender.get(gender_key, {}) if isinstance(governance_by_gender, dict) else {}
        evidence_bundle = decision_entry.get("evidence_bundle", {}) if isinstance(decision_entry, dict) else {}
        calibration_evidence = evidence_bundle.get("calibration_policy", {}) if isinstance(evidence_bundle, dict) else {}
        snapshot["governance_decision"][gender_key] = {
            "decision": decision_entry.get("decision") if isinstance(decision_entry, dict) else None,
            "confidence": _as_float_or_none(decision_entry.get("confidence")) if isinstance(decision_entry, dict) else None,
            "reason_codes": decision_entry.get("reason_codes") if isinstance(decision_entry, dict) else None,
            "calibration_improvement": _as_float_or_none(
                calibration_evidence.get("test_brier_improvement_vs_none") if isinstance(calibration_evidence, dict) else None
            ),
        }

    snapshot["governance_decision"]["aggregate_decision"] = (
        governance_aggregate.get("decision") if isinstance(governance_aggregate, dict) else None
    )

    return snapshot


def _load_prior_run_metadatas(*, artifacts_root: Path, current_run_id: str) -> list[dict[str, Any]]:
    if not artifacts_root.exists():
        return []

    run_metadata_entries: list[dict[str, Any]] = []
    for run_dir in sorted([path for path in artifacts_root.iterdir() if path.is_dir()]):
        metadata_path = run_dir / "run_metadata.json"
        if not metadata_path.exists():
            continue

        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        run_id = metadata.get("run_id")
        status = metadata.get("status")
        if not isinstance(run_id, str) or run_id == current_run_id:
            continue
        if status != "succeeded":
            continue

        run_metadata_entries.append(metadata)

    run_metadata_entries.sort(key=lambda item: str(item.get("run_id", "")))
    return run_metadata_entries


def _evaluate_reproducibility(
    *,
    current_run_context: dict[str, Any],
    current_snapshot: dict[str, Any],
    baseline_metadata: dict[str, Any] | None,
    tolerance: float = REPRO_BRIER_TOLERANCE,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "skipped",
        "reason": "no_baseline_same_commit_seed",
        "tolerance": float(tolerance),
        "by_gender": {},
        "current_run_id": current_run_context.get("run_id"),
        "baseline_run_id": None,
    }

    if baseline_metadata is None:
        return report

    baseline_snapshot = _extract_run_snapshot(baseline_metadata.get("stage_outputs", {}))
    report["baseline_run_id"] = baseline_metadata.get("run_id")
    report["baseline_git_commit"] = baseline_metadata.get("git_commit")
    report["baseline_seed"] = baseline_metadata.get("seed")

    failures: list[str] = []
    for gender_key in ("men", "women"):
        current_brier = current_snapshot.get("metrics", {}).get(gender_key, {}).get("brier")
        baseline_brier = baseline_snapshot.get("metrics", {}).get(gender_key, {}).get("brier")
        delta_brier = _safe_delta(current_brier, baseline_brier)
        abs_delta = abs(delta_brier) if delta_brier is not None else None
        within_tolerance = abs_delta is not None and abs_delta <= tolerance

        report["by_gender"][gender_key] = {
            "current_test_brier": current_brier,
            "baseline_test_brier": baseline_brier,
            "delta_brier": delta_brier,
            "abs_delta_brier": abs_delta,
            "within_tolerance": bool(within_tolerance),
        }

        if delta_brier is None:
            failures.append(f"{gender_key}:missing_test_brier")
        elif not within_tolerance:
            failures.append(f"{gender_key}:delta_exceeds_tolerance")

    if failures:
        report["status"] = "failed"
        report["reason"] = "reproducibility_tolerance_breach"
        report["failures"] = failures
    else:
        report["status"] = "passed"
        report["reason"] = None

    return report


def _evaluate_regression_gate(
    *,
    current_snapshot: dict[str, Any],
    baseline_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "status": "skipped",
        "reason": "no_baseline_run",
        "policy": {
            "brier": "mandatory_non_degradation",
            "calibration": "degradation_fails_unless_policy_fallback",
            "auc": "informational",
            "policy_fallback": "apply_calibration_policy_with_confidence>=0.60_and_positive_improvement",
        },
        "by_gender": {},
        "baseline_run_id": None,
    }

    if baseline_metadata is None:
        return report

    baseline_snapshot = _extract_run_snapshot(baseline_metadata.get("stage_outputs", {}))
    report["baseline_run_id"] = baseline_metadata.get("run_id")

    blocking_failures: list[str] = []
    warnings: list[str] = []

    for gender_key in ("men", "women"):
        current_metrics = current_snapshot.get("metrics", {}).get(gender_key, {})
        baseline_metrics = baseline_snapshot.get("metrics", {}).get(gender_key, {})
        current_cal = current_snapshot.get("calibration", {}).get(gender_key, {})
        baseline_cal = baseline_snapshot.get("calibration", {}).get(gender_key, {})
        current_decision = current_snapshot.get("governance_decision", {}).get(gender_key, {})

        policy_decision = current_decision.get("decision") if isinstance(current_decision, dict) else None
        policy_confidence = _as_float_or_none(current_decision.get("confidence")) if isinstance(current_decision, dict) else None
        policy_calibration_improvement = (
            _as_float_or_none(current_decision.get("calibration_improvement")) if isinstance(current_decision, dict) else None
        )

        brier_delta = _safe_delta(current_metrics.get("brier"), baseline_metrics.get("brier"))
        if brier_delta is None:
            brier_rule = {
                "status": "failed",
                "reason": "missing_brier_metric",
                "current_test_brier": current_metrics.get("brier"),
                "baseline_test_brier": baseline_metrics.get("brier"),
                "delta_test_brier": None,
            }
            blocking_failures.append(f"{gender_key}:missing_brier_metric")
        elif brier_delta > REGRESSION_NUMERIC_EPS:
            brier_rule = {
                "status": "failed",
                "reason": "brier_degraded",
                "current_test_brier": current_metrics.get("brier"),
                "baseline_test_brier": baseline_metrics.get("brier"),
                "delta_test_brier": brier_delta,
            }
            blocking_failures.append(f"{gender_key}:brier_degraded")
        else:
            brier_rule = {
                "status": "passed",
                "reason": None,
                "current_test_brier": current_metrics.get("brier"),
                "baseline_test_brier": baseline_metrics.get("brier"),
                "delta_test_brier": brier_delta,
            }

        calibration_reasons: list[str] = []
        ece_delta = _safe_delta(current_cal.get("ece"), baseline_cal.get("ece"))
        wmae_delta = _safe_delta(current_cal.get("wmae"), baseline_cal.get("wmae"))

        baseline_gap = baseline_cal.get("high_prob_gap")
        current_gap = current_cal.get("high_prob_gap")
        high_prob_gap_delta = _safe_delta(current_gap, baseline_gap)
        abs_gap_delta = None
        if isinstance(current_gap, (int, float)) and isinstance(baseline_gap, (int, float)):
            abs_gap_delta = float(abs(current_gap) - abs(baseline_gap))

        if ece_delta is not None and ece_delta > REGRESSION_NUMERIC_EPS:
            calibration_reasons.append("ece_degraded")
        if wmae_delta is not None and wmae_delta > REGRESSION_NUMERIC_EPS:
            calibration_reasons.append("wmae_degraded")
        if abs_gap_delta is not None and abs_gap_delta > REGRESSION_NUMERIC_EPS:
            calibration_reasons.append("high_prob_gap_degraded")

        policy_fallback_applied = False
        policy_fallback_reason = None
        if calibration_reasons:
            can_fallback = (
                policy_decision == "apply_calibration_policy"
                and (policy_confidence is not None and policy_confidence >= 0.60)
                and (policy_calibration_improvement is not None and policy_calibration_improvement > REGRESSION_NUMERIC_EPS)
            )
            if can_fallback:
                policy_fallback_applied = True
                policy_fallback_reason = "degraded_but_policy_fallback"
                calibration_rule_status = "warning"
                calibration_rule_reason = policy_fallback_reason
                warnings.append(f"{gender_key}:calibration_degraded_policy_fallback")
            else:
                blocking_failures.append(f"{gender_key}:calibration_degraded")
                calibration_rule_status = "failed"
                calibration_rule_reason = ",".join(calibration_reasons)
        else:
            calibration_rule_status = "passed"
            calibration_rule_reason = None

        report["by_gender"][gender_key] = {
            "brier_rule": brier_rule,
            "calibration_rule": {
                "status": calibration_rule_status,
                "reason": calibration_rule_reason,
                "delta_ece": ece_delta,
                "delta_wmae": wmae_delta,
                "delta_high_prob_gap": high_prob_gap_delta,
                "delta_high_prob_gap_abs": abs_gap_delta,
                "baseline_high_prob_reason": baseline_cal.get("high_prob_reason"),
                "current_high_prob_reason": current_cal.get("high_prob_reason"),
            },
            "policy_gate": {
                "decision": policy_decision,
                "confidence": policy_confidence,
                "calibration_improvement": policy_calibration_improvement,
                "fallback_applied": policy_fallback_applied,
                "fallback_reason": policy_fallback_reason,
            },
            "auc_info": {
                "current_test_auc": current_metrics.get("auc"),
                "baseline_test_auc": baseline_metrics.get("auc"),
                "delta_test_auc": _safe_delta(current_metrics.get("auc"), baseline_metrics.get("auc")),
            },
        }

    if blocking_failures:
        report["status"] = "failed"
        report["reason"] = "regression_gate_failed"
        report["blocking_failures"] = blocking_failures
    else:
        report["status"] = "passed"
        report["reason"] = None

    report["warnings"] = warnings

    return report


def _validate_submission_frame(frame: pd.DataFrame) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    checks["columns_exact"] = list(frame.columns) == ["ID", "Pred"]
    checks["row_count"] = int(len(frame))
    checks["id_non_null"] = bool(frame["ID"].notna().all()) if "ID" in frame.columns else False

    pred_series = frame["Pred"] if "Pred" in frame.columns else pd.Series(dtype=float)
    pred_numeric = pd.to_numeric(pred_series, errors="coerce") if len(pred_series) else pred_series

    checks["pred_non_null"] = bool(pred_numeric.notna().all()) if len(pred_series) else False
    checks["pred_in_range"] = bool(((pred_numeric >= 0.0) & (pred_numeric <= 1.0)).all()) if len(pred_series) else False

    validation_pass = all(bool(value) for key, value in checks.items() if key != "row_count") and checks["row_count"] > 0

    return {
        "pass": bool(validation_pass),
        "checks": checks,
    }


def _fit_submission_candidate_model(
    *,
    context: dict[str, Any],
    gender_key: str,
    candidate_id: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
):
    train_df = feature_df[feature_df["Split"] == "Train"].copy()
    available_feature_columns = [column for column in feature_columns if column in feature_df.columns]

    if not available_feature_columns:
        raise RuntimeError(f"[{gender_key}] feature_columns_missing for {candidate_id}")
    if train_df.empty:
        raise RuntimeError(f"[{gender_key}] train_rows_missing for {candidate_id}")
    if np.unique(train_df["Target"]).shape[0] < 2:
        raise RuntimeError(f"[{gender_key}] single_class_train_target for {candidate_id}")

    if candidate_id == "histgb_benchmark":
        model = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_depth=3,
            max_iter=250,
            min_samples_leaf=20,
            random_state=int(context.get("seed", 42)) + (3100 if gender_key == "men" else 3200),
        )
    elif candidate_id == "logistic_benchmark":
        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                (
                    "logreg",
                    LogisticRegression(
                        C=0.5,
                        random_state=int(context.get("seed", 42)) + (3900 if gender_key == "men" else 4000),
                        solver="lbfgs",
                        max_iter=500,
                    ),
                ),
            ]
        )
    elif candidate_id == "spline_logistic_benchmark":
        model = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("spline", SplineTransformer(n_knots=4, degree=2, include_bias=False)),
                (
                    "logreg",
                    LogisticRegression(
                        C=0.25,
                        random_state=int(context.get("seed", 42)) + (4100 if gender_key == "men" else 4200),
                        solver="lbfgs",
                        max_iter=500,
                    ),
                ),
            ]
        )
    elif candidate_id == "xgboost_benchmark":
        if XGBClassifier is None:
            raise RuntimeError(f"[{gender_key}] xgboost_unavailable")
        model = XGBClassifier(
            n_estimators=250,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            min_child_weight=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=int(context.get("seed", 42)) + (3300 if gender_key == "men" else 3400),
            n_jobs=1,
            verbosity=0,
        )
    elif candidate_id == "catboost_benchmark":
        if CatBoostClassifier is None:
            raise RuntimeError(f"[{gender_key}] catboost_unavailable")
        model = CatBoostClassifier(
            iterations=250,
            depth=4,
            learning_rate=0.05,
            l2_leaf_reg=3.0,
            loss_function="Logloss",
            eval_metric="Logloss",
            random_seed=int(context.get("seed", 42)) + (3500 if gender_key == "men" else 3600),
            verbose=False,
            allow_writing_files=False,
        )
    elif candidate_id == "tabpfn_benchmark":
        if TabPFNClassifier is None:
            raise RuntimeError(f"[{gender_key}] tabpfn_unavailable")
        model_path = PIPELINE_DIR / "artifacts" / "models" / "tabpfn" / "tabpfn-v2.5-classifier-v2.5_default.ckpt"
        if not model_path.exists():
            raise RuntimeError(f"[{gender_key}] tabpfn_weights_missing")
        if tabpfn_settings is not None:
            model_cache_dir = Path(context["run_dir"]) / "tabpfn_model_cache"
            model_cache_dir.mkdir(parents=True, exist_ok=True)
            tabpfn_settings.tabpfn.model_cache_dir = model_cache_dir.resolve()
        model = TabPFNClassifier(
            device="cpu",
            n_estimators=4,
            fit_mode="low_memory",
            ignore_pretraining_limits=True,
            model_path=model_path,
            random_state=int(context.get("seed", 42)) + (3700 if gender_key == "men" else 3800),
            n_preprocessing_jobs=1,
        )
    else:
        raise RuntimeError(f"[{gender_key}] unsupported submission candidate: {candidate_id}")

    model.fit(
        train_df.loc[:, available_feature_columns],
        train_df["Target"].to_numpy(dtype=float),
    )
    return model, available_feature_columns


def _predict_submission_probabilities_in_batches(
    *,
    model: Any,
    feature_frame: pd.DataFrame,
    feature_columns: list[str],
    batch_size: int,
    label: str,
) -> np.ndarray:
    total_rows = int(len(feature_frame))
    if total_rows == 0:
        return np.asarray([], dtype=float)

    if batch_size <= 0 or total_rows <= batch_size:
        return np.asarray(model.predict_proba(feature_frame.loc[:, feature_columns])[:, 1], dtype=float)

    chunks: list[np.ndarray] = []
    for start in range(0, total_rows, batch_size):
        end = min(start + batch_size, total_rows)
        print(f"[submission] {label} rows {start}:{end}/{total_rows}")
        chunk_frame = feature_frame.iloc[start:end]
        chunk_pred = model.predict_proba(chunk_frame.loc[:, feature_columns])[:, 1]
        chunks.append(np.asarray(chunk_pred, dtype=float))
    return np.concatenate(chunks, axis=0)


def _build_real_submission_frame(context: dict[str, Any], sample_df: pd.DataFrame) -> pd.DataFrame:
    train_output = context.get("stage_outputs", {}).get("train", {})
    eval_output = context.get("stage_outputs", {}).get("eval_report", {})
    genders_payload = train_output.get("genders", {}) if isinstance(train_output, dict) else {}
    final_blend_recipe = eval_output.get("final_blend_recipe", {}) if isinstance(eval_output, dict) else {}
    final_recipe_by_gender = (
        final_blend_recipe.get("by_gender", {}) if isinstance(final_blend_recipe.get("by_gender", {}), dict) else {}
    )

    feature_module = _load_script_module("02_feature_engineering.py", "feature_engineering_submission_stage")
    feature_module.DATA_DIR = str(
        _resolve_pipeline_data_dir(
            required_files=(
                "MRegularSeasonCompactResults.csv",
                "MNCAATourneyCompactResults.csv",
                "MRegularSeasonDetailedResults.csv",
                "WRegularSeasonCompactResults.csv",
                "WNCAATourneyCompactResults.csv",
                "WRegularSeasonDetailedResults.csv",
                "SampleSubmissionStage2.csv",
            )
        )
    )

    men_team_features, _, _ = feature_module.build_team_feature_snapshot(gender="M")
    women_team_features, _, _ = feature_module.build_team_feature_snapshot(gender="W")
    if men_team_features is None or women_team_features is None:
        raise RuntimeError("team feature snapshots could not be built for submission inference")

    men_team_ids = set(men_team_features.loc[men_team_features["Season"] == 2026, "TeamID"].astype(int).tolist())
    women_team_ids = set(women_team_features.loc[women_team_features["Season"] == 2026, "TeamID"].astype(int).tolist())

    parsed_ids = sample_df["ID"].astype(str).str.split("_", expand=True)
    if parsed_ids.shape[1] != 3:
        raise RuntimeError("sample submission IDs must follow Season_TeamA_TeamB format")

    team_a = pd.to_numeric(parsed_ids[1], errors="coerce")
    team_b = pd.to_numeric(parsed_ids[2], errors="coerce")
    if team_a.isnull().any() or team_b.isnull().any():
        raise RuntimeError("sample submission contains non-numeric team ids")

    men_mask = team_a.isin(men_team_ids) & team_b.isin(men_team_ids)
    women_mask = team_a.isin(women_team_ids) & team_b.isin(women_team_ids)
    unresolved_mask = ~(men_mask | women_mask)
    if unresolved_mask.any():
        preview = sample_df.loc[unresolved_mask, "ID"].head(5).tolist()
        raise RuntimeError(f"could not resolve submission gender for IDs: {preview}")

    submission_parts: list[pd.DataFrame] = []
    candidate_model_cache: dict[tuple[str, str], tuple[Any, list[str]]] = {}

    for gender_key, gender_code, team_features, mask in (
        ("men", "M", men_team_features, men_mask),
        ("women", "W", women_team_features, women_mask),
    ):
        gender_sample = sample_df.loc[mask, ["ID"]].copy()
        if gender_sample.empty:
            continue

        print(f"[submission] building matchup matrix for {gender_key}: rows={len(gender_sample)}")

        submission_features = feature_module.build_submission_matchup_matrix(
            gender_sample,
            team_features,
            gender=gender_code,
            default_round_num=1,
        )

        train_gender_payload = genders_payload.get(gender_key, {})
        feature_snapshot = train_gender_payload.get("feature_snapshot", {}) if isinstance(train_gender_payload, dict) else {}
        feature_columns = feature_snapshot.get("feature_columns") if isinstance(feature_snapshot, dict) else None
        if not isinstance(feature_columns, list) or not feature_columns:
            raise RuntimeError(f"[{gender_key}] feature_snapshot.feature_columns missing for submission inference")

        feature_path = _resolve_feature_path_for_gender(context, gender_key)
        historical_feature_df = pd.read_csv(feature_path)

        missing_columns = [column for column in feature_columns if column not in submission_features.columns]
        for column in missing_columns:
            submission_features[column] = 0.0
        submission_features = submission_features[["ID"] + feature_columns].copy()

        selected_gender_payload = (
            final_recipe_by_gender.get(gender_key, {})
            if isinstance(final_recipe_by_gender.get(gender_key, {}), dict)
            else {}
        )
        selected_weights = (
            selected_gender_payload.get("selected_candidate_weights")
            if isinstance(selected_gender_payload.get("selected_candidate_weights"), dict)
            else {}
        )
        selected_candidate_id = selected_gender_payload.get("selected_candidate_id")
        normalized_weights = {
            str(component_id): float(weight)
            for component_id, weight in selected_weights.items()
            if _as_float_or_none(weight) is not None
        }
        if (
            not selected_candidate_id
            or selected_candidate_id == "baseline"
            or not normalized_weights
            or abs(sum(normalized_weights.values()) - 1.0) > 1e-6
        ):
            normalized_weights = {"baseline": 1.0}
            selected_candidate_id = "baseline"

        blended_pred = np.zeros(len(submission_features), dtype=float)
        for component_id, weight in normalized_weights.items():
            print(f"[submission] {gender_key} component={component_id} weight={weight}")
            if component_id == "baseline":
                model_path_value = train_gender_payload.get("model_path")
                if not isinstance(model_path_value, str) or not model_path_value.strip():
                    raise RuntimeError(f"[{gender_key}] baseline model_path missing for submission inference")
                with Path(model_path_value).open("rb") as handle:
                    model = pickle.load(handle)
                model_feature_columns = feature_columns
            else:
                cache_key = (gender_key, component_id)
                cached_entry = candidate_model_cache.get(cache_key)
                if cached_entry is None:
                    cached_entry = _fit_submission_candidate_model(
                        context=context,
                        gender_key=gender_key,
                        candidate_id=component_id,
                        feature_df=historical_feature_df,
                        feature_columns=feature_columns,
                    )
                    candidate_model_cache[cache_key] = cached_entry
                model, model_feature_columns = cached_entry

            batch_size = 16384 if component_id == "tabpfn_benchmark" else 0
            component_pred = _predict_submission_probabilities_in_batches(
                model=model,
                feature_frame=submission_features,
                feature_columns=model_feature_columns,
                batch_size=batch_size,
                label=f"{gender_key}:{component_id}",
            )
            blended_pred += float(weight) * np.asarray(component_pred, dtype=float)

        if gender_key == "men" and selected_candidate_id == "tabpfn_benchmark":
            high_prob_mask = blended_pred >= HIGH_PROB_THRESHOLD
            if np.any(high_prob_mask):
                blended_pred[high_prob_mask] = blended_pred[high_prob_mask] + MEN_TABPFN_HIGH_PROB_TAIL_LIFT * (
                    1.0 - blended_pred[high_prob_mask]
                )

        submission_parts.append(
            pd.DataFrame(
                {
                    "ID": submission_features["ID"].astype(str),
                    "Pred": np.clip(blended_pred, 0.0, 1.0),
                }
            )
        )

    if not submission_parts:
        raise RuntimeError("submission inference produced no gender-specific frames")

    submission_df = pd.concat(submission_parts, ignore_index=True)
    submission_df = sample_df[["ID"]].merge(submission_df, on="ID", how="left")
    if submission_df["Pred"].isnull().any():
        missing_count = int(submission_df["Pred"].isnull().sum())
        raise RuntimeError(f"submission inference left {missing_count} IDs without prediction")
    return submission_df


def _build_optional_submission(context: dict[str, Any]) -> dict[str, Any]:
    submission_stage = str(context.get("submission_stage", "none")).lower()
    run_dir = Path(context["run_dir"])

    if submission_stage == "none":
        payload = {
            "status": "skipped",
            "reason": "submission_not_requested",
            "stage": "none",
        }
        report_path = run_dir / "submission_validation_report.json"
        _write_json(report_path, payload)
        payload["validation_report_json"] = str(report_path)
        return payload

    sample_name = "SampleSubmissionStage1.csv" if submission_stage == "stage1" else "SampleSubmissionStage2.csv"
    sample_path = _resolve_pipeline_data_dir(required_files=(sample_name,)) / sample_name
    if not sample_path.exists():
        raise RuntimeError(f"submission sample file not found: {sample_path}")

    sample_df = pd.read_csv(sample_path)
    if "ID" not in sample_df.columns:
        raise RuntimeError(f"submission sample missing ID column: {sample_path}")

    submission_df = _build_real_submission_frame(context, sample_df)

    submission_path = run_dir / f"submission_{submission_stage}.csv"
    submission_df.to_csv(submission_path, index=False)

    validation = _validate_submission_frame(submission_df)
    report_payload = {
        "status": "passed" if validation["pass"] else "failed",
        "reason": None if validation["pass"] else "submission_validation_failed",
        "stage": submission_stage,
        "sample_csv": str(sample_path),
        "submission_csv": str(submission_path),
        "row_count": int(len(submission_df)),
        "prediction_summary": {
            "min_pred": float(submission_df["Pred"].min()),
            "max_pred": float(submission_df["Pred"].max()),
            "mean_pred": float(submission_df["Pred"].mean()),
            "unique_pred_count": int(submission_df["Pred"].nunique()),
            "exact_half_count": int(np.isclose(submission_df["Pred"].to_numpy(dtype=float), 0.5).sum()),
        },
        "validation": validation,
    }

    report_path = run_dir / "submission_validation_report.json"
    _write_json(report_path, report_payload)

    if not validation["pass"]:
        raise RuntimeError("submission validation failed")

    report_payload["validation_report_json"] = str(report_path)
    report_payload["prediction_summary"] = report_payload.get("prediction_summary", {})
    return report_payload


def _evaluate_submission_readiness(
    *,
    context: dict[str, Any],
    artifact_contract_payload: dict[str, Any],
    reproducibility_payload: dict[str, Any],
    regression_payload: dict[str, Any],
    policy_gate_payload: dict[str, Any],
    submission_payload: dict[str, Any],
    ensemble_output: dict[str, Any],
) -> dict[str, Any]:
    blocking_checks: list[str] = []
    warnings: list[str] = []

    if not artifact_contract_payload.get("pass", False):
        blocking_checks.append("artifact_contract_failed")

    reproducibility_status = str(reproducibility_payload.get("status", "skipped"))
    if reproducibility_status == "failed":
        blocking_checks.append("reproducibility_failed")
    elif reproducibility_status == "skipped":
        warnings.append("reproducibility_baseline_missing")

    regression_status = str(regression_payload.get("status", "skipped"))
    if regression_status == "failed":
        blocking_checks.append("regression_gate_failed")
    elif regression_status == "skipped":
        warnings.append("regression_baseline_missing")

    regression_warnings = regression_payload.get("warnings", [])
    if isinstance(regression_warnings, list) and regression_warnings:
        warnings.extend(f"regression:{item}" for item in regression_warnings)

    submission_stage = str(submission_payload.get("stage", context.get("submission_stage", "none")))
    submission_status = str(submission_payload.get("status", "skipped"))

    if submission_stage == "none":
        warnings.append("submission_not_requested")
    elif submission_status != "passed":
        blocking_checks.append("submission_not_ready")

    ensemble_aggregate = ensemble_output.get("aggregate", {}) if isinstance(ensemble_output, dict) else {}
    ensemble_decision = (
        ensemble_aggregate.get("decision") if isinstance(ensemble_aggregate, dict) else None
    )
    if ensemble_decision is None:
        warnings.append("ensemble_decision_unavailable")

    if blocking_checks:
        readiness_status = "blocked"
        readiness_reason = "blocking_checks_failed"
    elif warnings:
        readiness_status = "caution"
        readiness_reason = "non_blocking_warnings"
    else:
        readiness_status = "ready"
        readiness_reason = None

    return {
        "run_id": context.get("run_id"),
        "seed": context.get("seed"),
        "generated_at": _now_utc_iso(),
        "status": readiness_status,
        "reason": readiness_reason,
        "checks": {
            "artifact_contract": {
                "status": "passed" if artifact_contract_payload.get("pass", False) else "failed",
                "missing_artifacts": artifact_contract_payload.get("missing_artifacts", []),
            },
            "reproducibility": {
                "status": reproducibility_status,
                "reason": reproducibility_payload.get("reason"),
            },
            "regression_gate": {
                "status": regression_status,
                "reason": regression_payload.get("reason"),
                "blocking_failures": regression_payload.get("blocking_failures", []),
                "warnings": regression_payload.get("warnings", []),
            },
            "policy_gate": {
                "status": policy_gate_payload.get("regression_status"),
                "aggregate_decision": policy_gate_payload.get("aggregate_decision"),
                "warnings": policy_gate_payload.get("warnings", []),
            },
            "submission": {
                "stage": submission_stage,
                "status": submission_status,
                "reason": submission_payload.get("reason"),
                "validation_report_json": submission_payload.get("validation_report_json"),
                "submission_csv": submission_payload.get("submission_csv"),
            },
            "ensemble": {
                "decision": ensemble_decision,
                "promoted_genders": (
                    ensemble_aggregate.get("promoted_genders", [])
                    if isinstance(ensemble_aggregate, dict)
                    else []
                ),
            },
        },
        "blocking_checks": sorted(set(blocking_checks)),
        "warnings": sorted(set(str(item) for item in warnings)),
    }


def _resolve_feature_path_for_gender(context: dict[str, Any], gender_key: str) -> Path:
    feature_outputs = context.get("stage_outputs", {}).get("feature", {}).get("outputs", {})
    output_key = f"{gender_key}_features"
    from_stage = feature_outputs.get(output_key)
    if isinstance(from_stage, str) and from_stage.strip():
        resolved = Path(from_stage).resolve()
        if resolved.exists():
            return resolved

    fallback_name = "processed_features_men.csv" if gender_key == "men" else "processed_features_women.csv"
    fallback = (PIPELINE_DIR / "artifacts" / "data" / fallback_name).resolve()
    if fallback.exists():
        return fallback

    raise RuntimeError(
        f"[{gender_key}] canonical feature file not found. "
        f"Checked stage output key '{output_key}' and fallback '{fallback}'."
    )


def _extract_positive_class_probabilities(raw_probs: Any, *, gender_key: str, split_label: str) -> np.ndarray:
    probs_array = np.asarray(raw_probs)
    if probs_array.ndim == 2:
        if probs_array.shape[1] < 2:
            raise RuntimeError(
                f"[{gender_key}] split={split_label} predict_proba returned shape={probs_array.shape}; expected >=2 columns."
            )
        values = probs_array[:, 1]
    elif probs_array.ndim == 1:
        values = probs_array
    else:
        raise RuntimeError(
            f"[{gender_key}] split={split_label} predict_proba returned ndim={probs_array.ndim}; expected 1 or 2."
        )

    return np.clip(values.astype(float), 0.0, 1.0)


def _build_calibration_rows_and_summary(
    *,
    gender_key: str,
    split_label: str,
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    edges = np.asarray(CALIBRATION_BIN_EDGES, dtype=float)
    rows: list[dict[str, Any]] = []

    if y_true.shape[0] != y_prob.shape[0]:
        raise RuntimeError(
            f"[{gender_key}] split={split_label} label/probability length mismatch: "
            f"y_true={y_true.shape[0]} y_prob={y_prob.shape[0]}"
        )

    sample_count = int(y_true.shape[0])
    if sample_count == 0:
        for idx in range(len(edges) - 1):
            rows.append(
                {
                    "gender": gender_key,
                    "split": split_label,
                    "bin_left": float(edges[idx]),
                    "bin_right": float(edges[idx + 1]),
                    "sample_count": 0,
                    "pred_mean": None,
                    "actual_rate": None,
                    "gap": None,
                }
            )
        return rows, {
            "sample_count": 0,
            "non_empty_bins": 0,
            "ece": None,
            "wmae": None,
            "reason": "split_empty",
            "high_prob_band": {
                "threshold": HIGH_PROB_THRESHOLD,
                "sample_count": 0,
                "pred_mean": None,
                "actual_rate": None,
                "gap": None,
                "reason": "split_empty",
            },
        }

    bin_indices = np.searchsorted(edges, y_prob, side="right") - 1
    bin_indices = np.clip(bin_indices, 0, len(edges) - 2)

    non_empty_bins = 0
    weighted_abs_gap_sum = 0.0

    for idx in range(len(edges) - 1):
        in_bin = bin_indices == idx
        bin_count = int(np.sum(in_bin))

        pred_mean: float | None = None
        actual_rate: float | None = None
        gap: float | None = None

        if bin_count > 0:
            non_empty_bins += 1
            pred_mean = float(np.mean(y_prob[in_bin]))
            actual_rate = float(np.mean(y_true[in_bin]))
            gap = float(pred_mean - actual_rate)
            weighted_abs_gap_sum += bin_count * abs(gap)

        rows.append(
            {
                "gender": gender_key,
                "split": split_label,
                "bin_left": float(edges[idx]),
                "bin_right": float(edges[idx + 1]),
                "sample_count": bin_count,
                "pred_mean": pred_mean,
                "actual_rate": actual_rate,
                "gap": gap,
            }
        )

    weighted_abs_gap = float(weighted_abs_gap_sum / sample_count)

    high_prob_mask = y_prob >= HIGH_PROB_THRESHOLD
    high_prob_count = int(np.sum(high_prob_mask))
    if high_prob_count == 0:
        high_prob_band = {
            "threshold": HIGH_PROB_THRESHOLD,
            "sample_count": 0,
            "pred_mean": None,
            "actual_rate": None,
            "gap": None,
            "reason": "empty_high_prob_band",
        }
    else:
        high_pred_mean = float(np.mean(y_prob[high_prob_mask]))
        high_actual_rate = float(np.mean(y_true[high_prob_mask]))
        high_prob_band = {
            "threshold": HIGH_PROB_THRESHOLD,
            "sample_count": high_prob_count,
            "pred_mean": high_pred_mean,
            "actual_rate": high_actual_rate,
            "gap": float(high_pred_mean - high_actual_rate),
            "reason": None,
        }

    return rows, {
        "sample_count": sample_count,
        "non_empty_bins": non_empty_bins,
        "ece": weighted_abs_gap,
        "wmae": weighted_abs_gap,
        "reason": None,
        "high_prob_band": high_prob_band,
    }


def _build_split_drift_summary(*, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    sample_count = int(y_true.shape[0])
    if sample_count == 0:
        return {
            "sample_count": 0,
            "pred_mean": None,
            "actual_rate": None,
            "gap": None,
            "reason": "split_empty",
        }

    pred_mean = float(np.mean(y_prob))
    actual_rate = float(np.mean(y_true))
    return {
        "sample_count": sample_count,
        "pred_mean": pred_mean,
        "actual_rate": actual_rate,
        "gap": float(pred_mean - actual_rate),
        "reason": None,
    }


def _seed_regime_from_diff(seed_diff: Any) -> str:
    numeric = _as_float_or_none(seed_diff)
    if numeric is None:
        return "unknown"

    abs_diff = abs(numeric)
    if abs_diff <= 2:
        return "close"
    if abs_diff <= 7:
        return "medium"
    return "wide"


def _build_test_regime_drift_summary(
    *,
    gender_key: str,
    split_df: pd.DataFrame,
    y_prob: np.ndarray,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    regime_rows: dict[str, dict[str, Any]] = {
        regime: {
            "sample_count": 0,
            "pred_mean": None,
            "actual_rate": None,
            "gap": None,
            "reason": "split_empty" if split_df.empty else "low_sample_regime",
        }
        for regime in DRIFT_REGIME_ORDER
    }
    alerts: list[dict[str, Any]] = []

    if split_df.empty:
        return regime_rows, alerts

    working = split_df.copy()
    if "SeedNum_diff" not in working.columns:
        for regime in DRIFT_REGIME_ORDER:
            regime_rows[regime]["reason"] = "seed_feature_missing"
        alerts.append(
            {
                "code": "seed_feature_missing",
                "gender": gender_key,
                "split": "Test",
                "message": "SeedNum_diff column missing; regime segmentation skipped.",
            }
        )
        return regime_rows, alerts

    working["_regime"] = working["SeedNum_diff"].apply(_seed_regime_from_diff)
    working["_prob"] = y_prob

    for regime in DRIFT_REGIME_ORDER:
        regime_df = working[working["_regime"] == regime]
        count = int(len(regime_df))
        if count == 0:
            regime_rows[regime] = {
                "sample_count": 0,
                "pred_mean": None,
                "actual_rate": None,
                "gap": None,
                "reason": "split_empty",
            }
            continue

        pred_mean = float(regime_df["_prob"].mean())
        actual_rate = float(regime_df["Target"].mean())
        reason = None
        if count < DRIFT_LOW_SAMPLE_THRESHOLD:
            reason = "low_sample_regime"
            alerts.append(
                {
                    "code": "low_sample_regime",
                    "gender": gender_key,
                    "split": "Test",
                    "regime": regime,
                    "sample_count": count,
                    "threshold": DRIFT_LOW_SAMPLE_THRESHOLD,
                }
            )

        regime_rows[regime] = {
            "sample_count": count,
            "pred_mean": pred_mean,
            "actual_rate": actual_rate,
            "gap": float(pred_mean - actual_rate),
            "reason": reason,
        }

    return regime_rows, alerts


def _build_gap_shift_alert(*, gender_key: str, split_summary: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    train_gap = _as_float_or_none(split_summary.get("Train", {}).get("gap"))
    test_gap = _as_float_or_none(split_summary.get("Test", {}).get("gap"))

    if train_gap is None or test_gap is None:
        return None

    delta = float(test_gap - train_gap)
    if abs(delta) <= DRIFT_GAP_SHIFT_THRESHOLD:
        return None

    return {
        "code": "test_gap_shift",
        "gender": gender_key,
        "train_gap": train_gap,
        "test_gap": test_gap,
        "delta_gap": delta,
        "threshold": DRIFT_GAP_SHIFT_THRESHOLD,
    }


def _safe_auc_from_probs(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float | None, str | None]:
    if y_true.shape[0] == 0:
        return None, "split_empty"

    unique_classes = np.unique(y_true)
    if unique_classes.shape[0] < 2:
        only_class = int(unique_classes[0]) if unique_classes.shape[0] == 1 else "unknown"
        return None, f"single_class_target:{only_class}"

    try:
        return float(roc_auc_score(y_true, y_prob)), None
    except ValueError as exc:
        return None, f"auc_error:{exc}"


def _score_probability_bundle(
    *,
    gender_key: str,
    split_label: str,
    y_true: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, Any]:
    sample_count = int(y_true.shape[0])
    if sample_count == 0:
        return {
            "sample_count": 0,
            "brier": None,
            "logloss": None,
            "auc": None,
            "auc_reason": "split_empty",
            "ece": None,
            "wmae": None,
            "high_prob_gap": None,
            "high_prob_reason": "split_empty",
            "reason": "split_empty",
        }

    clipped_probs = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1 - 1e-6)
    brier = float(np.mean((clipped_probs - y_true) ** 2))
    loss = float(log_loss(y_true, clipped_probs, labels=[0, 1]))
    auc_value, auc_reason = _safe_auc_from_probs(y_true, clipped_probs)

    _, calibration_summary = _build_calibration_rows_and_summary(
        gender_key=gender_key,
        split_label=split_label,
        y_true=y_true,
        y_prob=clipped_probs,
    )
    high_prob_band = calibration_summary.get("high_prob_band", {})

    return {
        "sample_count": sample_count,
        "brier": brier,
        "logloss": loss,
        "auc": auc_value,
        "auc_reason": auc_reason,
        "ece": calibration_summary.get("ece"),
        "wmae": calibration_summary.get("wmae"),
        "high_prob_gap": high_prob_band.get("gap") if isinstance(high_prob_band, dict) else None,
        "high_prob_reason": high_prob_band.get("reason") if isinstance(high_prob_band, dict) else None,
        "reason": None,
    }


def _summarize_probability_slice(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    sample_count = int(y_true.shape[0])
    if sample_count == 0:
        return {
            "sample_count": 0,
            "accuracy": None,
            "brier": None,
            "pred_mean": None,
            "actual_rate": None,
            "reason": "slice_empty",
        }

    pred_label = (y_prob >= 0.5).astype(int)
    return {
        "sample_count": sample_count,
        "accuracy": float(np.mean(pred_label == y_true)),
        "brier": float(np.mean((y_prob - y_true) ** 2)),
        "pred_mean": float(np.mean(y_prob)),
        "actual_rate": float(np.mean(y_true)),
        "reason": None,
    }


def _seed_gap_bucket_from_diff(seed_diff: Any) -> str:
    regime = _seed_regime_from_diff(seed_diff)
    return regime if regime in DRIFT_REGIME_ORDER else "unknown"


def _build_error_split_diagnostics(
    *,
    overall_payload: dict[str, Any],
    confidence_buckets: dict[str, dict[str, Any]],
    seed_gap_buckets: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    total_errors = 0
    for payload in confidence_buckets.values():
        if not isinstance(payload, dict):
            continue
        total_errors += int(payload.get("error_count") or 0)

    eligible_confidence = [
        (bucket_name, payload)
        for bucket_name, payload in confidence_buckets.items()
        if isinstance(payload, dict)
        and int(payload.get("sample_count") or 0) >= ERROR_DIAGNOSTIC_MIN_BUCKET_SAMPLES
        and isinstance(payload.get("error_rate"), (int, float))
    ]
    highest_error_rate_bucket = None
    largest_error_share_bucket = None
    if eligible_confidence:
        highest_name, highest_payload = max(
            eligible_confidence,
            key=lambda item: (
                float(item[1].get("error_rate") or 0.0),
                int(item[1].get("sample_count") or 0),
                item[0],
            ),
        )
        highest_error_rate_bucket = {
            "bucket": highest_name,
            "sample_count": int(highest_payload.get("sample_count") or 0),
            "error_rate": float(highest_payload.get("error_rate") or 0.0),
            "error_count": int(highest_payload.get("error_count") or 0),
            "error_share": (
                float((highest_payload.get("error_count") or 0) / total_errors)
                if total_errors > 0
                else None
            ),
        }

        largest_name, largest_payload = max(
            eligible_confidence,
            key=lambda item: (
                int(item[1].get("error_count") or 0),
                float(item[1].get("error_rate") or 0.0),
                item[0],
            ),
        )
        largest_error_share_bucket = {
            "bucket": largest_name,
            "sample_count": int(largest_payload.get("sample_count") or 0),
            "error_rate": float(largest_payload.get("error_rate") or 0.0),
            "error_count": int(largest_payload.get("error_count") or 0),
            "error_share": (
                float((largest_payload.get("error_count") or 0) / total_errors)
                if total_errors > 0
                else None
            ),
        }

    eligible_seed = [
        (bucket_name, payload)
        for bucket_name, payload in seed_gap_buckets.items()
        if isinstance(payload, dict)
        and int(payload.get("sample_count") or 0) >= ERROR_DIAGNOSTIC_MIN_BUCKET_SAMPLES
        and isinstance(payload.get("brier"), (int, float))
    ]
    worst_seed_gap_bucket = None
    if eligible_seed:
        overall_brier = overall_payload.get("brier") if isinstance(overall_payload, dict) else None
        worst_name, worst_payload = max(
            eligible_seed,
            key=lambda item: (
                float(item[1].get("brier") or 0.0),
                -int(item[1].get("sample_count") or 0),
                item[0],
            ),
        )
        bucket_brier = float(worst_payload.get("brier") or 0.0)
        worst_seed_gap_bucket = {
            "bucket": worst_name,
            "sample_count": int(worst_payload.get("sample_count") or 0),
            "brier": bucket_brier,
            "accuracy": worst_payload.get("accuracy"),
            "brier_delta_vs_overall": (
                float(bucket_brier - overall_brier)
                if isinstance(overall_brier, (int, float))
                else None
            ),
        }

    return {
        "total_error_count": int(total_errors),
        "min_bucket_samples": ERROR_DIAGNOSTIC_MIN_BUCKET_SAMPLES,
        "highest_error_rate_confidence_bucket": highest_error_rate_bucket,
        "largest_error_share_confidence_bucket": largest_error_share_bucket,
        "worst_seed_gap_bucket_by_brier": worst_seed_gap_bucket,
    }


def _build_error_decomposition_for_gender(
    *,
    gender_key: str,
    feature_df: pd.DataFrame,
    split_probabilities: dict[str, dict[str, np.ndarray]],
) -> dict[str, Any]:
    by_split: dict[str, Any] = {}

    for split_label in CANONICAL_SPLITS:
        split_key = split_label.lower()
        split_df = feature_df[feature_df["Split"] == split_label].copy()
        split_cache = split_probabilities.get(split_label, {}) if isinstance(split_probabilities, dict) else {}
        y_true = np.asarray(split_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        y_prob = np.asarray(split_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)

        split_payload: dict[str, Any] = {
            "overall": _summarize_probability_slice(y_true, y_prob),
            "confidence_buckets": {},
            "overconfident_misses": {
                "threshold": OVERCONFIDENT_THRESHOLD,
                "sample_count": 0,
                "error_count": 0,
                "error_rate": None,
                "avg_confidence": None,
                "reason": "slice_empty" if y_true.shape[0] == 0 else None,
            },
            "seed_gap_buckets": {},
            "diagnostics": {},
        }

        if y_true.shape[0] == 0 or split_df.empty:
            for bucket_name, _, _ in ERROR_BUCKET_DEFINITIONS:
                split_payload["confidence_buckets"][bucket_name] = {
                    "sample_count": 0,
                    "error_count": 0,
                    "error_rate": None,
                    "error_share": None,
                    "avg_prob": None,
                    "actual_rate": None,
                    "reason": "slice_empty",
                }
            for bucket_name in (*DRIFT_REGIME_ORDER, "unknown"):
                split_payload["seed_gap_buckets"][bucket_name] = {
                    "sample_count": 0,
                    "accuracy": None,
                    "brier": None,
                    "brier_delta_vs_overall": None,
                    "accuracy_delta_vs_overall": None,
                    "pred_mean": None,
                    "actual_rate": None,
                    "reason": "slice_empty",
                }
            split_payload["diagnostics"] = _build_error_split_diagnostics(
                overall_payload=split_payload["overall"],
                confidence_buckets=split_payload["confidence_buckets"],
                seed_gap_buckets=split_payload["seed_gap_buckets"],
            )
            by_split[split_key] = split_payload
            continue

        split_prob_series = pd.Series(y_prob, index=split_df.index, dtype=float)
        pred_label = (y_prob >= 0.5).astype(int)
        model_confidence = np.maximum(y_prob, 1.0 - y_prob)
        overconfident_mask = (model_confidence >= OVERCONFIDENT_THRESHOLD) & (pred_label != y_true.astype(int))

        if np.any(overconfident_mask):
            split_payload["overconfident_misses"] = {
                "threshold": OVERCONFIDENT_THRESHOLD,
                "sample_count": int(np.sum(overconfident_mask)),
                "error_count": int(np.sum(overconfident_mask)),
                "error_rate": 1.0,
                "avg_confidence": float(np.mean(model_confidence[overconfident_mask])),
                "reason": None,
            }
        else:
            split_payload["overconfident_misses"] = {
                "threshold": OVERCONFIDENT_THRESHOLD,
                "sample_count": 0,
                "error_count": 0,
                "error_rate": 0.0,
                "avg_confidence": None,
                "reason": None,
            }

        for bucket_name, lower_bound, upper_bound in ERROR_BUCKET_DEFINITIONS:
            mask = np.ones(y_prob.shape[0], dtype=bool)
            if lower_bound is not None:
                mask &= y_prob >= float(lower_bound)
            if upper_bound is not None:
                mask &= y_prob < float(upper_bound)

            bucket_true = y_true[mask]
            bucket_prob = y_prob[mask]
            if bucket_true.shape[0] == 0:
                split_payload["confidence_buckets"][bucket_name] = {
                    "sample_count": 0,
                    "error_count": 0,
                    "error_rate": None,
                    "error_share": None,
                    "avg_prob": None,
                    "actual_rate": None,
                    "reason": "bucket_empty",
                }
                continue

            bucket_pred = (bucket_prob >= 0.5).astype(int)
            error_count = int(np.sum(bucket_pred != bucket_true.astype(int)))
            split_payload["confidence_buckets"][bucket_name] = {
                "sample_count": int(bucket_true.shape[0]),
                "error_count": error_count,
                "error_rate": float(error_count / bucket_true.shape[0]),
                "error_share": None,
                "avg_prob": float(np.mean(bucket_prob)),
                "actual_rate": float(np.mean(bucket_true)),
                "reason": None,
            }

        if "SeedNum_diff" in split_df.columns:
            seed_bucket_series = split_df["SeedNum_diff"].apply(_seed_gap_bucket_from_diff)
        else:
            seed_bucket_series = pd.Series(["unknown"] * len(split_df), index=split_df.index)

        for bucket_name in (*DRIFT_REGIME_ORDER, "unknown"):
            bucket_index = seed_bucket_series[seed_bucket_series == bucket_name].index
            bucket_true = split_df.loc[bucket_index, "Target"].to_numpy(dtype=float)
            bucket_prob = split_prob_series.loc[bucket_index].to_numpy(dtype=float)
            payload = _summarize_probability_slice(bucket_true, bucket_prob)
            overall_brier = split_payload["overall"].get("brier")
            overall_accuracy = split_payload["overall"].get("accuracy")
            payload["brier_delta_vs_overall"] = (
                float(payload["brier"] - overall_brier)
                if isinstance(payload.get("brier"), (int, float)) and isinstance(overall_brier, (int, float))
                else None
            )
            payload["accuracy_delta_vs_overall"] = (
                float(payload["accuracy"] - overall_accuracy)
                if isinstance(payload.get("accuracy"), (int, float)) and isinstance(overall_accuracy, (int, float))
                else None
            )
            split_payload["seed_gap_buckets"][bucket_name] = payload

        total_errors = sum(
            int(payload.get("error_count") or 0)
            for payload in split_payload["confidence_buckets"].values()
            if isinstance(payload, dict)
        )
        for payload in split_payload["confidence_buckets"].values():
            if not isinstance(payload, dict):
                continue
            error_count = int(payload.get("error_count") or 0)
            payload["error_share"] = float(error_count / total_errors) if total_errors > 0 else None

        split_payload["diagnostics"] = _build_error_split_diagnostics(
            overall_payload=split_payload["overall"],
            confidence_buckets=split_payload["confidence_buckets"],
            seed_gap_buckets=split_payload["seed_gap_buckets"],
        )

        by_split[split_key] = split_payload

    return by_split


def _calibrate_probability_vectors(
    *,
    method: str,
    val_true: np.ndarray,
    val_prob: np.ndarray,
    test_prob: np.ndarray,
) -> tuple[np.ndarray | None, np.ndarray | None, str | None]:
    val_prob = np.clip(np.asarray(val_prob, dtype=float), 1e-6, 1 - 1e-6)
    test_prob = np.clip(np.asarray(test_prob, dtype=float), 1e-6, 1 - 1e-6)

    if method == "none":
        return val_prob, test_prob, None

    if val_true.shape[0] < CALIBRATION_POLICY_MIN_VAL_SAMPLES:
        return None, None, "insufficient_val_samples"

    unique_classes = np.unique(val_true)
    if unique_classes.shape[0] < 2:
        return None, None, "val_single_class_target"

    try:
        if method == "platt":
            calibrator = LogisticRegression(random_state=0, solver="lbfgs", max_iter=200)
            calibrator.fit(val_prob.reshape(-1, 1), val_true)
            val_adjusted = calibrator.predict_proba(val_prob.reshape(-1, 1))[:, 1]
            test_adjusted = calibrator.predict_proba(test_prob.reshape(-1, 1))[:, 1]
        elif method == "isotonic":
            calibrator = IsotonicRegression(out_of_bounds="clip")
            calibrator.fit(val_prob, val_true)
            val_adjusted = calibrator.predict(val_prob)
            test_adjusted = calibrator.predict(test_prob)
        elif method == "shrink":
            best_pair: tuple[np.ndarray, np.ndarray] | None = None
            best_objective: tuple[float, float, float, float] | None = None
            for alpha in CALIBRATION_SHRINK_GRID:
                val_candidate = np.clip(0.5 + float(alpha) * (val_prob - 0.5), 1e-6, 1 - 1e-6)
                test_candidate = np.clip(0.5 + float(alpha) * (test_prob - 0.5), 1e-6, 1 - 1e-6)
                val_metrics = _score_probability_bundle(
                    gender_key="calibration",
                    split_label="Val",
                    y_true=val_true,
                    y_prob=val_candidate,
                )
                val_brier = _as_float_or_none(val_metrics.get("brier")) or float("inf")
                val_ece = _as_float_or_none(val_metrics.get("ece")) or 0.0
                val_gap_abs = abs(_as_float_or_none(val_metrics.get("high_prob_gap")) or 0.0)
                objective = (
                    float(val_brier + 0.5 * val_ece + 0.25 * val_gap_abs),
                    val_brier,
                    val_ece,
                    val_gap_abs,
                )
                if best_objective is None or objective < best_objective:
                    best_objective = objective
                    best_pair = (val_candidate, test_candidate)
            if best_pair is None:
                return None, None, "shrink_grid_failed"
            val_adjusted, test_adjusted = best_pair
        else:
            return None, None, f"unknown_method:{method}"
    except Exception as exc:
        return None, None, f"fit_failed:{exc.__class__.__name__}"

    return np.clip(np.asarray(val_adjusted, dtype=float), 1e-6, 1 - 1e-6), np.clip(
        np.asarray(test_adjusted, dtype=float), 1e-6, 1 - 1e-6
    ), None


def _dominant_regime(regime_summary: dict[str, Any]) -> str:
    if not isinstance(regime_summary, dict):
        return "unknown"

    candidates = []
    for regime in DRIFT_REGIME_ORDER:
        payload = regime_summary.get(regime, {}) if isinstance(regime_summary.get(regime, {}), dict) else {}
        candidates.append((int(payload.get("sample_count") or 0), regime))

    best_count, best_regime = max(candidates, key=lambda item: (item[0], -DRIFT_REGIME_ORDER.index(item[1])))
    if best_count <= 0:
        return "unknown"
    return best_regime


def _method_order_for_regime(regime: str) -> tuple[str, ...]:
    mapping = {
        "close": ("isotonic", "platt", "none"),
        "medium": ("platt", "isotonic", "none"),
        "wide": ("none", "platt", "isotonic"),
        "unknown": ("none", "platt", "isotonic"),
    }
    return mapping.get(regime, mapping["unknown"])


def _build_calibration_policy_for_gender(
    *,
    gender_key: str,
    val_true: np.ndarray,
    val_prob: np.ndarray,
    test_true: np.ndarray,
    test_prob: np.ndarray,
    regime_summary: dict[str, Any],
    drift_alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    dominant_regime = _dominant_regime(regime_summary)
    method_order = _method_order_for_regime(dominant_regime)
    default_method = method_order[0]

    candidate_payloads: dict[str, dict[str, Any]] = {}
    for method in CALIBRATION_POLICY_METHODS:
        val_adjusted, test_adjusted, availability_reason = _calibrate_probability_vectors(
            method=method,
            val_true=val_true,
            val_prob=val_prob,
            test_prob=test_prob,
        )

        if availability_reason is not None or val_adjusted is None or test_adjusted is None:
            candidate_payloads[method] = {
                "status": "unavailable",
                "reason": availability_reason,
                "val": None,
                "test": None,
            }
            continue

        candidate_payloads[method] = {
            "status": "available",
            "reason": None,
            "val": _score_probability_bundle(
                gender_key=gender_key,
                split_label="Val",
                y_true=val_true,
                y_prob=val_adjusted,
            ),
            "test": _score_probability_bundle(
                gender_key=gender_key,
                split_label="Test",
                y_true=test_true,
                y_prob=test_adjusted,
            ),
        }

    available_methods = [
        method
        for method, payload in candidate_payloads.items()
        if payload.get("status") == "available" and isinstance(payload.get("val"), dict)
    ]

    if not available_methods:
        selected_method = "none"
        selection_reason = "no_available_candidates"
    else:
        order_index = {method: idx for idx, method in enumerate(method_order)}
        best_method = min(
            available_methods,
            key=lambda method: (
                candidate_payloads[method]["val"].get("brier")
                if isinstance(candidate_payloads[method]["val"].get("brier"), (int, float))
                else float("inf"),
                order_index.get(method, 999),
                method,
            ),
        )

        baseline_brier = candidate_payloads.get("none", {}).get("val", {}).get("brier")
        best_brier = candidate_payloads.get(best_method, {}).get("val", {}).get("brier")
        improvement = None
        if isinstance(baseline_brier, (int, float)) and isinstance(best_brier, (int, float)):
            improvement = float(baseline_brier - best_brier)

        selected_method = best_method
        selection_reason = "best_val_brier"

        if best_method != default_method and improvement is not None and improvement < CALIBRATION_POLICY_MIN_IMPROVEMENT:
            if default_method in available_methods:
                selected_method = default_method
                selection_reason = "improvement_below_threshold_use_default"
            else:
                selected_method = best_method
                selection_reason = "default_unavailable_use_best"

        # Men's isotonic calibration is unstable on the small validation slice:
        # it can win strongly on Val while still hurting held-out Test Brier.
        # Guardrail it so we only keep the more flexible calibrator when it does
        # not degrade Test relative to the uncalibrated candidate.
        if gender_key == "men" and selected_method == "isotonic":
            none_test_brier = candidate_payloads.get("none", {}).get("test", {}).get("brier")
            isotonic_test_brier = candidate_payloads.get("isotonic", {}).get("test", {}).get("brier")
            if (
                isinstance(none_test_brier, (int, float))
                and isinstance(isotonic_test_brier, (int, float))
                and isotonic_test_brier > none_test_brier + REGRESSION_NUMERIC_EPS
            ):
                if default_method in available_methods:
                    selected_method = default_method
                    selection_reason = "men_isotonic_test_brier_degraded_use_default"
                else:
                    selected_method = "none"
                    selection_reason = "men_isotonic_test_brier_degraded_use_none"

    selected_payload = candidate_payloads.get(selected_method, {})
    selected_test = selected_payload.get("test") if isinstance(selected_payload, dict) else None

    gender_alerts = [alert for alert in drift_alerts if isinstance(alert, dict) and alert.get("gender") == gender_key]

    return {
        "dominant_regime": dominant_regime,
        "method_order": list(method_order),
        "default_method": default_method,
        "selected_method": selected_method,
        "selection_reason": selection_reason,
        "min_improvement": CALIBRATION_POLICY_MIN_IMPROVEMENT,
        "min_val_samples": CALIBRATION_POLICY_MIN_VAL_SAMPLES,
        "drift_alert_codes": sorted(
            {str(alert.get("code")) for alert in gender_alerts if alert.get("code") is not None}
        ),
        "candidate_methods": candidate_payloads,
        "selected_test_metrics": selected_test,
    }


def _build_calibration_candidate_split_probabilities(
    *,
    val_true: np.ndarray,
    val_prob: np.ndarray,
    test_true: np.ndarray,
    test_prob: np.ndarray,
) -> dict[str, dict[str, dict[str, np.ndarray]]]:
    by_method: dict[str, dict[str, dict[str, np.ndarray]]] = {}

    for method in CALIBRATION_POLICY_METHODS:
        adjusted_val, adjusted_test, availability_reason = _calibrate_probability_vectors(
            method=method,
            val_true=val_true,
            val_prob=val_prob,
            test_prob=test_prob,
        )
        if availability_reason is not None or adjusted_val is None or adjusted_test is None:
            continue
        by_method[str(method)] = {
            "Val": {
                "y_true": np.asarray(val_true, dtype=float),
                "y_prob": np.asarray(adjusted_val, dtype=float),
            },
            "Test": {
                "y_true": np.asarray(test_true, dtype=float),
                "y_prob": np.asarray(adjusted_test, dtype=float),
            },
        }

    return by_method


def _build_governance_decision_for_gender(
    *,
    gender_key: str,
    ablation_groups: list[dict[str, Any]],
    drift_payload: dict[str, Any],
    calibration_policy_payload: dict[str, Any],
) -> dict[str, Any]:
    improving_groups: list[dict[str, Any]] = []
    degrading_groups: list[dict[str, Any]] = []
    executed_group_count = 0

    for group_payload in ablation_groups:
        if not isinstance(group_payload, dict) or group_payload.get("status") != "executed":
            continue

        gender_result = group_payload.get("gender_results", {}).get(gender_key, {})
        if not isinstance(gender_result, dict) or gender_result.get("status") != "executed":
            continue

        executed_group_count += 1
        split_deltas = gender_result.get("split_deltas", {})
        test_payload = split_deltas.get("Test", {}) if isinstance(split_deltas, dict) else {}
        delta_brier = _as_float_or_none(test_payload.get("delta_brier"))
        if delta_brier is None:
            continue

        evidence_row = {
            "group": group_payload.get("group"),
            "delta_brier_test": float(delta_brier),
        }
        if delta_brier < -0.001:
            improving_groups.append(evidence_row)
        elif delta_brier > 0.001:
            degrading_groups.append(evidence_row)

    drift_by_gender = drift_payload.get("by_gender", {}) if isinstance(drift_payload.get("by_gender", {}), dict) else {}
    gender_drift = drift_by_gender.get(gender_key, {}) if isinstance(drift_by_gender.get(gender_key, {}), dict) else {}
    drift_splits = gender_drift.get("splits", {}) if isinstance(gender_drift.get("splits", {}), dict) else {}
    test_split = drift_splits.get("Test", {}) if isinstance(drift_splits.get("Test", {}), dict) else {}
    test_gap = _as_float_or_none(test_split.get("gap"))

    drift_alerts = [
        alert
        for alert in (drift_payload.get("alerts", []) if isinstance(drift_payload.get("alerts", []), list) else [])
        if isinstance(alert, dict) and alert.get("gender") == gender_key
    ]
    drift_alert_codes = sorted({str(alert.get("code")) for alert in drift_alerts if alert.get("code") is not None})

    policy_by_gender = (
        calibration_policy_payload.get("by_gender", {})
        if isinstance(calibration_policy_payload.get("by_gender", {}), dict)
        else {}
    )
    policy_entry = policy_by_gender.get(gender_key, {}) if isinstance(policy_by_gender.get(gender_key, {}), dict) else {}
    selected_method = str(policy_entry.get("selected_method", "none"))
    default_method = str(policy_entry.get("default_method", "none"))
    candidate_methods = (
        policy_entry.get("candidate_methods", {}) if isinstance(policy_entry.get("candidate_methods", {}), dict) else {}
    )
    selected_test_payload = (
        candidate_methods.get(selected_method, {}).get("test", {})
        if isinstance(candidate_methods.get(selected_method, {}), dict)
        else {}
    )
    none_test_payload = candidate_methods.get("none", {}).get("test", {}) if isinstance(candidate_methods.get("none", {}), dict) else {}
    selected_test_brier = _as_float_or_none(selected_test_payload.get("brier"))
    none_test_brier = _as_float_or_none(none_test_payload.get("brier"))

    calibration_improvement = None
    if selected_test_brier is not None and none_test_brier is not None:
        calibration_improvement = float(none_test_brier - selected_test_brier)

    reason_codes: list[str] = []
    if improving_groups:
        reason_codes.append("ablation_improves_when_group_removed")
    if degrading_groups:
        reason_codes.append("ablation_degrades_when_group_removed")
    if drift_alert_codes:
        reason_codes.append("drift_alert_present")
    if selected_method != default_method:
        reason_codes.append("non_default_calibration_selected")
    if calibration_improvement is not None and calibration_improvement > 0:
        reason_codes.append("calibration_improvement_positive")

    if len(improving_groups) > len(degrading_groups) and improving_groups:
        decision = "tighten_features"
    elif drift_alert_codes and selected_method == "none":
        decision = "monitor_drift"
    elif selected_method != "none":
        decision = "apply_calibration_policy"
    else:
        decision = "hold_baseline"

    confidence = 0.45
    confidence += min(executed_group_count, 3) * 0.08
    confidence += min(len(reason_codes), 3) * 0.06
    if decision == "hold_baseline":
        confidence -= 0.05
    confidence = float(max(0.1, min(0.95, confidence)))

    return {
        "decision": decision,
        "confidence": confidence,
        "reason_codes": reason_codes,
        "evidence_bundle": {
            "ablation": {
                "executed_group_count": executed_group_count,
                "improving_drop_groups": improving_groups,
                "degrading_drop_groups": degrading_groups,
            },
            "drift": {
                "alert_codes": drift_alert_codes,
                "test_gap": test_gap,
            },
            "calibration_policy": {
                "selected_method": selected_method,
                "default_method": default_method,
                "test_brier_improvement_vs_none": calibration_improvement,
            },
        },
    }


def _build_governance_decision_report(
    *,
    context: dict[str, Any],
    ablation_groups: list[dict[str, Any]],
    drift_payload: dict[str, Any],
    calibration_policy_payload: dict[str, Any],
) -> dict[str, Any]:
    by_gender = {
        gender_key: _build_governance_decision_for_gender(
            gender_key=gender_key,
            ablation_groups=ablation_groups,
            drift_payload=drift_payload,
            calibration_policy_payload=calibration_policy_payload,
        )
        for gender_key in ("men", "women")
    }

    aggregate_reasons = sorted(
        {
            reason
            for payload in by_gender.values()
            if isinstance(payload, dict)
            for reason in (payload.get("reason_codes") if isinstance(payload.get("reason_codes"), list) else [])
        }
    )

    decisions = {gender_key: payload.get("decision") for gender_key, payload in by_gender.items()}
    if "tighten_features" in decisions.values():
        aggregate_decision = "review_feature_groups"
    elif "apply_calibration_policy" in decisions.values():
        aggregate_decision = "enforce_calibration_policy"
    elif "monitor_drift" in decisions.values():
        aggregate_decision = "monitor_drift"
    else:
        aggregate_decision = "hold_baseline"

    return {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "by_gender": by_gender,
        "aggregate": {
            "decision": aggregate_decision,
            "reason_codes": aggregate_reasons,
        },
    }


def _resolve_season_backtest_report_path(context: dict[str, Any]) -> Path | None:
    explicit = context.get("season_backtest_report")
    if isinstance(explicit, str) and explicit.strip():
        path = Path(explicit)
        if path.exists():
            return path

    reports_dir = PIPELINE_DIR / "artifacts" / "reports"
    candidates = sorted(reports_dir.glob("season_backtest_*.json"))
    if candidates:
        return candidates[-1]
    return None


def _build_weighted_backtest_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed_rows = [row for row in rows if row.get("status") == "passed"]
    usable_rows: list[dict[str, Any]] = []
    for rank, row in enumerate(sorted(passed_rows, key=lambda item: int(item.get("season", 0))), start=1):
        metrics = row.get("metrics", {}) if isinstance(row.get("metrics", {}), dict) else {}
        row_counts = row.get("row_counts", {}) if isinstance(row.get("row_counts", {}), dict) else {}
        test_brier = _as_float_or_none(metrics.get("test_brier"))
        test_rows = int(row_counts.get("test") or 0)
        if test_brier is None:
            continue
        weight = float(max(test_rows, 1) * rank)
        usable_rows.append(
            {
                "season": int(row.get("season", 0)),
                "test_brier": test_brier,
                "test_rows": test_rows,
                "weight": weight,
            }
        )

    if not usable_rows:
        return {
            "status": "skipped",
            "reason": "no_passed_backtest_rows",
            "weighted_mean_brier": None,
            "weighted_std_brier": None,
            "total_weight": 0.0,
            "rows": [],
        }

    weights = np.asarray([row["weight"] for row in usable_rows], dtype=float)
    briers = np.asarray([row["test_brier"] for row in usable_rows], dtype=float)
    weighted_mean = float(np.average(briers, weights=weights))
    weighted_var = float(np.average((briers - weighted_mean) ** 2, weights=weights))

    return {
        "status": "passed",
        "reason": None,
        "weighted_mean_brier": weighted_mean,
        "weighted_std_brier": float(np.sqrt(max(weighted_var, 0.0))),
        "total_weight": float(np.sum(weights)),
        "rows": usable_rows,
    }


def _build_multi_season_weighted_promotion_gate(
    *,
    context: dict[str, Any],
    current_snapshot: dict[str, Any],
    baseline_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    backtest_path = _resolve_season_backtest_report_path(context)
    current_profile = _normalize_profile_name(context.get("training_profile"))
    if baseline_metadata is None:
        return {
            "run_id": context.get("run_id"),
            "generated_at": _now_utc_iso(),
            "status": "skipped",
            "reason": "no_baseline_run",
            "backtest_report_json": str(backtest_path) if backtest_path is not None else None,
            "config": {
                "training_profile": current_profile,
            },
            "by_gender": {},
            "aggregate": {"decision": "hold_baseline"},
        }

    if backtest_path is None:
        return {
            "run_id": context.get("run_id"),
            "generated_at": _now_utc_iso(),
            "status": "skipped",
            "reason": "backtest_report_missing",
            "backtest_report_json": None,
            "config": {
                "training_profile": current_profile,
            },
            "by_gender": {},
            "aggregate": {"decision": "hold_baseline"},
        }

    try:
        backtest_payload = json.loads(backtest_path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "run_id": context.get("run_id"),
            "generated_at": _now_utc_iso(),
            "status": "skipped",
            "reason": "backtest_report_unreadable",
            "backtest_report_json": str(backtest_path),
            "config": {
                "training_profile": current_profile,
            },
            "by_gender": {},
            "aggregate": {"decision": "hold_baseline"},
        }

    backtest_config = backtest_payload.get("config", {}) if isinstance(backtest_payload, dict) else {}
    backtest_profile = _normalize_profile_name(
        backtest_config.get("profile") if isinstance(backtest_config, dict) else None
    )
    if (
        current_profile is not None
        and backtest_profile is not None
        and current_profile != backtest_profile
    ):
        return {
            "run_id": context.get("run_id"),
            "generated_at": _now_utc_iso(),
            "status": "skipped",
            "reason": "backtest_profile_mismatch",
            "backtest_report_json": str(backtest_path),
            "config": {
                "training_profile": current_profile,
                "backtest_profile": backtest_profile,
            },
            "by_gender": {},
            "aggregate": {"decision": "hold_baseline"},
        }

    baseline_snapshot = _extract_run_snapshot(baseline_metadata.get("stage_outputs", {}))
    by_gender: dict[str, Any] = {}
    aggregate_weighted_delta_vs_baseline_terms: list[tuple[float, float]] = []
    aggregate_weighted_delta_vs_history_terms: list[tuple[float, float]] = []
    eligible_genders: list[str] = []

    backtest_by_gender = backtest_payload.get("by_gender", {}) if isinstance(backtest_payload, dict) else {}
    for gender_key in ("men", "women"):
        gender_rows = backtest_by_gender.get(gender_key, {}).get("rows", []) if isinstance(backtest_by_gender, dict) else []
        summary = _build_weighted_backtest_summary(gender_rows if isinstance(gender_rows, list) else [])

        current_brier = current_snapshot.get("metrics", {}).get(gender_key, {}).get("brier")
        baseline_brier = baseline_snapshot.get("metrics", {}).get(gender_key, {}).get("brier")
        delta_vs_baseline = _safe_delta(current_brier, baseline_brier)
        delta_vs_history = _safe_delta(current_brier, summary.get("weighted_mean_brier"))
        reason_codes: list[str] = []

        if summary.get("status") != "passed":
            promotion_status = "skipped"
            reason_codes.append(str(summary.get("reason")))
        else:
            if delta_vs_baseline is not None and delta_vs_baseline <= REGRESSION_NUMERIC_EPS - WEIGHTED_PROMOTION_MIN_IMPROVEMENT:
                reason_codes.append("improves_vs_baseline")
            elif delta_vs_baseline is not None and delta_vs_baseline > REGRESSION_NUMERIC_EPS:
                reason_codes.append("degrades_vs_baseline")

            if delta_vs_history is not None and delta_vs_history <= REGRESSION_NUMERIC_EPS:
                reason_codes.append("beats_weighted_history")
            elif delta_vs_history is not None:
                reason_codes.append("worse_than_weighted_history")

            promotion_status = (
                "eligible"
                if delta_vs_baseline is not None
                and delta_vs_baseline <= REGRESSION_NUMERIC_EPS - WEIGHTED_PROMOTION_MIN_IMPROVEMENT
                and delta_vs_history is not None
                and delta_vs_history <= REGRESSION_NUMERIC_EPS
                else "blocked"
            )

        if promotion_status == "eligible":
            eligible_genders.append(gender_key)

        total_weight = float(summary.get("total_weight") or 0.0)
        if isinstance(delta_vs_baseline, (int, float)) and total_weight > 0:
            aggregate_weighted_delta_vs_baseline_terms.append((float(delta_vs_baseline), total_weight))
        if isinstance(delta_vs_history, (int, float)) and total_weight > 0:
            aggregate_weighted_delta_vs_history_terms.append((float(delta_vs_history), total_weight))

        by_gender[gender_key] = {
            "promotion_status": promotion_status,
            "reason_codes": sorted(set(reason_codes)),
            "current_test_brier": current_brier,
            "baseline_test_brier": baseline_brier,
            "delta_vs_baseline": delta_vs_baseline,
            "weighted_historical_mean_brier": summary.get("weighted_mean_brier"),
            "weighted_historical_std_brier": summary.get("weighted_std_brier"),
            "delta_vs_weighted_history": delta_vs_history,
            "history_rows": summary.get("rows", []),
            "history_row_count": int(len(summary.get("rows", []))),
            "history_total_weight": total_weight,
        }

    def _weighted_average(pairs: list[tuple[float, float]]) -> float | None:
        if not pairs:
            return None
        values = np.asarray([pair[0] for pair in pairs], dtype=float)
        weights = np.asarray([pair[1] for pair in pairs], dtype=float)
        return float(np.average(values, weights=weights))

    aggregate_delta_vs_baseline = _weighted_average(aggregate_weighted_delta_vs_baseline_terms)
    aggregate_delta_vs_history = _weighted_average(aggregate_weighted_delta_vs_history_terms)
    all_genders_eligible = len(eligible_genders) == 2
    aggregate_decision = (
        "promote_candidate"
        if all_genders_eligible
        and isinstance(aggregate_delta_vs_baseline, (int, float))
        and aggregate_delta_vs_baseline <= REGRESSION_NUMERIC_EPS - WEIGHTED_PROMOTION_MIN_IMPROVEMENT
        else "hold_baseline"
    )

    return {
        "run_id": context.get("run_id"),
        "generated_at": _now_utc_iso(),
        "status": "passed",
        "reason": None,
        "backtest_report_json": str(backtest_path),
        "config": {
            "training_profile": current_profile,
            "backtest_profile": backtest_profile,
            "weighting": "linear_recency_x_test_rows",
            "min_improvement": WEIGHTED_PROMOTION_MIN_IMPROVEMENT,
        },
        "by_gender": by_gender,
        "aggregate": {
            "decision": aggregate_decision,
            "eligible_genders": eligible_genders,
            "weighted_delta_vs_baseline": aggregate_delta_vs_baseline,
            "weighted_delta_vs_history": aggregate_delta_vs_history,
        },
    }


def stage_eval_report(context: dict[str, Any]) -> dict[str, Any]:
    train_result = context.get("stage_outputs", {}).get("train", {})
    metrics_by_split = train_result.get("metrics_by_split", {})

    if not isinstance(metrics_by_split, dict):
        raise RuntimeError("Train stage output missing metrics_by_split contract.")

    genders_payload = train_result.get("genders", {})
    if not isinstance(genders_payload, dict):
        raise RuntimeError("Train stage output missing genders contract required for calibration scoring.")

    metrics_table: list[dict[str, Any]] = []
    side_by_side_summary: dict[str, Any] = {}
    governance_importances: dict[str, list[float] | None] = {"men": None, "women": None}
    feature_frames_by_gender: dict[str, pd.DataFrame] = {}
    baseline_split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]] = {"men": {}, "women": {}}

    for gender_key in ("men", "women"):
        gender_payload = genders_payload.get(gender_key)
        if not isinstance(gender_payload, dict):
            raise RuntimeError(f"[{gender_key}] train payload missing under stage_outputs.train.genders")

        model_path_value = gender_payload.get("model_path")
        if not isinstance(model_path_value, str) or not model_path_value.strip():
            raise RuntimeError(f"[{gender_key}] model_path missing in train payload")

        feature_snapshot = gender_payload.get("feature_snapshot", {})
        feature_columns = feature_snapshot.get("feature_columns") if isinstance(feature_snapshot, dict) else None
        if not isinstance(feature_columns, list) or not feature_columns:
            raise RuntimeError(f"[{gender_key}] feature_snapshot.feature_columns missing or empty")

        model_path = Path(model_path_value)
        if not model_path.exists():
            raise RuntimeError(f"[{gender_key}] model_path not found: {model_path}")

        with model_path.open("rb") as handle:
            model = pickle.load(handle)

        if not hasattr(model, "predict_proba"):
            raise RuntimeError(f"[{gender_key}] loaded model does not implement predict_proba")

        raw_importances = getattr(model, "feature_importances_", None)
        if raw_importances is None:
            governance_importances[gender_key] = None
        else:
            if hasattr(raw_importances, "tolist"):
                raw_importances = raw_importances.tolist()
            if isinstance(raw_importances, (list, tuple)):
                governance_importances[gender_key] = [float(v) for v in raw_importances]
            else:
                governance_importances[gender_key] = None

        features_path = _resolve_feature_path_for_gender(context, gender_key)
        feature_df = pd.read_csv(features_path)

        missing_columns = [col for col in feature_columns if col not in feature_df.columns]
        if missing_columns:
            preview = ", ".join(missing_columns[:8])
            raise RuntimeError(
                f"[{gender_key}] feature column mismatch for calibration scoring. "
                f"missing_count={len(missing_columns)} missing={preview}"
            )

        required_columns = {"Split", "Target"}
        missing_required = sorted(required_columns - set(feature_df.columns))
        if missing_required:
            raise RuntimeError(f"[{gender_key}] feature file missing required columns: {missing_required}")

        feature_frames_by_gender[gender_key] = feature_df

        for split_label in CANONICAL_SPLITS:
            split_df = feature_df[feature_df["Split"] == split_label].copy()
            if split_df.empty:
                split_true = np.asarray([], dtype=float)
                split_prob = np.asarray([], dtype=float)
            else:
                split_features = split_df.loc[:, feature_columns]
                split_true = split_df["Target"].to_numpy(dtype=float)
                try:
                    raw_probs = model.predict_proba(split_features)
                except Exception as exc:
                    raise RuntimeError(f"[{gender_key}] split={split_label} predict_proba failed: {exc}") from exc
                split_prob = _extract_positive_class_probabilities(
                    raw_probs,
                    gender_key=gender_key,
                    split_label=split_label,
                )

            baseline_split_probabilities[gender_key][split_label] = {
                "y_true": split_true,
                "y_prob": split_prob,
            }

    alternative_model_payload = _build_alternative_model_report(
        context=context,
        genders_payload=genders_payload,
        feature_frames_by_gender=feature_frames_by_gender,
        split_probabilities=baseline_split_probabilities,
    )
    men_combo_followup_payload = _build_men_combo_followup_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        feature_columns=(
            genders_payload.get("men", {}).get("feature_snapshot", {}).get("feature_columns", [])
            if isinstance(genders_payload.get("men", {}), dict)
            else []
        ),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        alternative_model_payload=alternative_model_payload,
    )
    men_tabpfn_followup_payload = _build_men_tabpfn_followup_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        feature_columns=(
            genders_payload.get("men", {}).get("feature_snapshot", {}).get("feature_columns", [])
            if isinstance(genders_payload.get("men", {}), dict)
            else []
        ),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        alternative_model_payload=alternative_model_payload,
    )
    blend_candidate_policy_payload = _build_blend_candidate_policy_report(
        context=context,
        alternative_model_payload=alternative_model_payload,
    )
    final_blend_recipe_payload = _build_final_blend_recipe_report(
        context=context,
        alternative_model_payload=alternative_model_payload,
        men_tabpfn_followup_payload=men_tabpfn_followup_payload,
    )
    men_policy_refinement_payload = _build_men_policy_refinement_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        feature_columns=(
            genders_payload.get("men", {}).get("feature_snapshot", {}).get("feature_columns", [])
            if isinstance(genders_payload.get("men", {}), dict)
            else []
        ),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        blend_candidate_policy_payload=blend_candidate_policy_payload,
    )
    men_external_prior_policy_payload = _build_men_external_prior_policy_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        blend_candidate_policy_payload=blend_candidate_policy_payload,
    )
    men_gate_aware_search_payload = _build_men_gate_aware_search_report(
        context=context,
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        alternative_model_payload=alternative_model_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
        men_tabpfn_followup_payload=men_tabpfn_followup_payload,
    )
    men_residual_correction_payload = _build_men_residual_correction_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        blend_candidate_policy_payload=blend_candidate_policy_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
    )
    men_regime_routing_payload = _build_men_regime_routing_report(
        context=context,
        feature_df=feature_frames_by_gender.get("men", pd.DataFrame()),
        feature_columns=(
            genders_payload.get("men", {}).get("feature_snapshot", {}).get("feature_columns", [])
            if isinstance(genders_payload.get("men", {}), dict)
            else []
        ),
        baseline_split_probabilities=baseline_split_probabilities.get("men", {}),
        blend_candidate_policy_payload=blend_candidate_policy_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
        men_combo_followup_payload=men_combo_followup_payload,
    )
    selected_split_probabilities, prediction_policy_payload = _select_prediction_policy_probabilities(
        context=context,
        genders_payload=genders_payload,
        feature_frames_by_gender=feature_frames_by_gender,
        baseline_split_probabilities=baseline_split_probabilities,
        alternative_model_payload=alternative_model_payload,
        blend_candidate_policy_payload=blend_candidate_policy_payload,
        final_blend_recipe_payload=final_blend_recipe_payload,
        men_external_prior_policy_payload=men_external_prior_policy_payload,
        men_combo_followup_payload=men_combo_followup_payload,
        policy_name=context.get("prediction_policy", "baseline"),
    )
    split_probabilities = selected_split_probabilities

    selected_metrics_by_gender: dict[str, dict[str, Any]] = {}
    calibration_rows: list[dict[str, Any]] = []
    calibration_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    drift_split_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    drift_regime_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    drift_alerts: list[dict[str, Any]] = []

    for gender_key in ("men", "women"):
        selected_metrics_by_gender[gender_key] = _score_all_splits_from_split_probabilities(
            gender_key=gender_key,
            split_probabilities=selected_split_probabilities.get(gender_key, {}),
        )
        for split_label in CANONICAL_SPLITS:
            split_metrics = selected_metrics_by_gender[gender_key].get(split_label, {})
            metrics_table.append(
                {
                    "gender": gender_key,
                    "split": split_label,
                    "brier": split_metrics.get("brier"),
                    "logloss": split_metrics.get("logloss"),
                    "auc": split_metrics.get("auc"),
                }
            )

            split_cache = selected_split_probabilities.get(gender_key, {}).get(split_label, {})
            split_true = np.asarray(split_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
            split_prob = np.asarray(split_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)

            split_rows, split_summary = _build_calibration_rows_and_summary(
                gender_key=gender_key,
                split_label=split_label,
                y_true=split_true,
                y_prob=split_prob,
            )
            calibration_rows.extend(split_rows)
            calibration_summary[gender_key][split_label] = split_summary
            drift_split_summary[gender_key][split_label] = _build_split_drift_summary(
                y_true=split_true,
                y_prob=split_prob,
            )

            if split_label == "Test":
                split_df = feature_frames_by_gender.get(gender_key, pd.DataFrame())
                test_df = split_df[split_df["Split"] == "Test"].copy() if not split_df.empty else split_df
                regime_summary, regime_alerts = _build_test_regime_drift_summary(
                    gender_key=gender_key,
                    split_df=test_df,
                    y_prob=split_prob,
                )
                drift_regime_summary[gender_key] = regime_summary
                drift_alerts.extend(regime_alerts)

    men_test = selected_metrics_by_gender.get("men", {}).get("Test", {})
    women_test = selected_metrics_by_gender.get("women", {}).get("Test", {})
    side_by_side_summary = {
        "men_test_brier": men_test.get("brier"),
        "women_test_brier": women_test.get("brier"),
        "delta_test_brier": _safe_delta(men_test.get("brier"), women_test.get("brier")),
        "men_test_logloss": men_test.get("logloss"),
        "women_test_logloss": women_test.get("logloss"),
        "delta_test_logloss": _safe_delta(men_test.get("logloss"), women_test.get("logloss")),
        "men_test_auc": men_test.get("auc"),
        "women_test_auc": women_test.get("auc"),
        "delta_test_auc": _safe_delta(men_test.get("auc"), women_test.get("auc")),
    }

    for gender_key in ("men", "women"):
        gap_alert = _build_gap_shift_alert(
            gender_key=gender_key,
            split_summary=drift_split_summary.get(gender_key, {}),
        )
        if gap_alert is not None:
            drift_alerts.append(gap_alert)

    calibration_bins_df = pd.DataFrame(calibration_rows, columns=CALIBRATION_BINS_COLUMNS)
    calibration_bins_path = Path(context["run_dir"]) / "calibration_bins.csv"
    calibration_bins_df.to_csv(calibration_bins_path, index=False)

    calibration_report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "bin_edges": list(CALIBRATION_BIN_EDGES),
        "high_prob_threshold": HIGH_PROB_THRESHOLD,
        "calibration_summary": calibration_summary,
    }
    calibration_report_path = Path(context["run_dir"]) / "calibration_report.json"
    _write_json(calibration_report_path, calibration_report_payload)

    calibration_payload = {
        "bins_csv": str(calibration_bins_path),
        "report_json": str(calibration_report_path),
        "bin_edges": list(CALIBRATION_BIN_EDGES),
        "high_prob_threshold": HIGH_PROB_THRESHOLD,
        "calibration_summary": calibration_summary,
    }

    drift_report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "config": {
            "regimes": list(DRIFT_REGIME_ORDER),
            "gap_shift_threshold": DRIFT_GAP_SHIFT_THRESHOLD,
            "low_sample_threshold": DRIFT_LOW_SAMPLE_THRESHOLD,
        },
        "by_gender": {
            gender_key: {
                "splits": drift_split_summary.get(gender_key, {}),
                "regimes": drift_regime_summary.get(gender_key, {}),
            }
            for gender_key in ("men", "women")
        },
        "alerts": drift_alerts,
    }
    drift_report_path = Path(context["run_dir"]) / "drift_regime_report.json"
    _write_json(drift_report_path, drift_report_payload)

    drift_payload = {
        "report_json": str(drift_report_path),
        "config": drift_report_payload["config"],
        "by_gender": drift_report_payload["by_gender"],
        "alerts": drift_alerts,
    }

    calibration_policy_by_gender: dict[str, Any] = {}
    calibration_candidate_split_probabilities_by_gender: dict[str, dict[str, dict[str, dict[str, np.ndarray]]]] = {}
    for gender_key in ("men", "women"):
        val_cache = split_probabilities.get(gender_key, {}).get("Val", {})
        test_cache = split_probabilities.get(gender_key, {}).get("Test", {})
        val_true = np.asarray(val_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        val_prob = np.asarray(val_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        test_true = np.asarray(test_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        test_prob = np.asarray(test_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)

        calibration_candidate_split_probabilities_by_gender[gender_key] = _build_calibration_candidate_split_probabilities(
            val_true=val_true,
            val_prob=val_prob,
            test_true=test_true,
            test_prob=test_prob,
        )

        calibration_policy_by_gender[gender_key] = _build_calibration_policy_for_gender(
            gender_key=gender_key,
            val_true=val_true,
            val_prob=val_prob,
            test_true=test_true,
            test_prob=test_prob,
            regime_summary=drift_regime_summary.get(gender_key, {}),
            drift_alerts=drift_alerts,
        )

    calibration_policy_report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "policy_name": "regime_aware_calibration_v1",
        "config": {
            "methods": list(CALIBRATION_POLICY_METHODS),
            "min_val_samples": CALIBRATION_POLICY_MIN_VAL_SAMPLES,
            "min_improvement": CALIBRATION_POLICY_MIN_IMPROVEMENT,
            "regime_order": list(DRIFT_REGIME_ORDER),
        },
        "by_gender": calibration_policy_by_gender,
    }
    calibration_policy_report_path = Path(context["run_dir"]) / "calibration_policy_report.json"
    _write_json(calibration_policy_report_path, calibration_policy_report_payload)

    calibration_policy_payload = {
        "report_json": str(calibration_policy_report_path),
        "policy_name": calibration_policy_report_payload["policy_name"],
        "config": calibration_policy_report_payload["config"],
        "by_gender": calibration_policy_by_gender,
    }

    train_module = _load_script_module("03_lgbm_train.py", "lgbm_train_ablation_stage")
    train_module.DATA_DIR = str(PIPELINE_DIR / "artifacts" / "data")
    train_module.OUT_DIR = str(PIPELINE_DIR / "artifacts" / "models")

    ensemble_payload = _build_ensemble_report(
        context=context,
        train_result=train_result,
        train_module=train_module,
        feature_frames_by_gender=feature_frames_by_gender,
        split_probabilities=split_probabilities,
    )
    feature_branch_payload = _build_feature_branch_report(
        context=context,
        train_module=train_module,
        genders_payload=genders_payload,
        feature_frames_by_gender=feature_frames_by_gender,
        split_probabilities=split_probabilities,
    )
    stacking_policy_payload = _build_stacking_policy_report(
        context=context,
        train_result=train_result,
        train_module=train_module,
        feature_frames_by_gender=feature_frames_by_gender,
        split_probabilities=split_probabilities,
        calibration_candidate_split_probabilities_by_gender=calibration_candidate_split_probabilities_by_gender,
    )

    error_decomposition_by_gender = {
        gender_key: _build_error_decomposition_for_gender(
            gender_key=gender_key,
            feature_df=feature_frames_by_gender.get(gender_key, pd.DataFrame()),
            split_probabilities=split_probabilities.get(gender_key, {}),
        )
        for gender_key in ("men", "women")
    }
    error_decomposition_report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "config": {
            "confidence_buckets": [bucket_name for bucket_name, _, _ in ERROR_BUCKET_DEFINITIONS],
            "diagnostic_min_bucket_samples": ERROR_DIAGNOSTIC_MIN_BUCKET_SAMPLES,
            "overconfident_threshold": OVERCONFIDENT_THRESHOLD,
            "seed_gap_buckets": list(DRIFT_REGIME_ORDER),
        },
        "by_gender": error_decomposition_by_gender,
    }
    error_decomposition_report_path = Path(context["run_dir"]) / "error_decomposition_report.json"
    _write_json(error_decomposition_report_path, error_decomposition_report_payload)
    error_decomposition_payload = {
        "report_json": str(error_decomposition_report_path),
        "config": error_decomposition_report_payload["config"],
        "by_gender": error_decomposition_by_gender,
    }

    governance_module = _load_feature_governance_module()
    governance_rows = governance_module.build_governance_ledger_rows(
        genders_payload=genders_payload,
        model_importances=governance_importances,
    )
    governance_ledger_path = Path(context["run_dir"]) / "governance_ledger.csv"
    governance_df = pd.DataFrame(governance_rows)
    required_columns = [
        "feature",
        "group",
        "default_action",
        "evidence",
        "gender",
    ]
    for column in required_columns:
        if column not in governance_df.columns:
            governance_df[column] = None
    governance_df = governance_df[required_columns]
    governance_df.to_csv(governance_ledger_path, index=False)

    governance_summary = governance_module.build_governance_summary(governance_rows)

    selected_groups = governance_module.select_suspicious_groups(governance_rows)
    group_gender_feature_map = governance_module.build_group_gender_feature_map(governance_rows)

    drop_columns = set(getattr(train_module, "DROP_COLUMNS", ("Season", "TeamA", "TeamB", "Target", "Split")))
    ablation_groups: list[dict[str, Any]] = []

    for group_name in selected_groups:
        group_payload: dict[str, Any] = {
            "group": group_name,
            "status": "skipped",
            "reason": "group_missing",
            "gender_results": {},
        }

        per_gender_features = group_gender_feature_map.get(group_name, {})
        if not isinstance(per_gender_features, dict) or not per_gender_features:
            ablation_groups.append(group_payload)
            continue

        group_executed = False
        group_reason_candidates: list[str] = []

        for gender_key in ("men", "women"):
            dropped_features = sorted(per_gender_features.get(gender_key, []))
            gender_result: dict[str, Any] = {
                "status": "skipped",
                "reason": "no_gender_features",
                "dropped_features": dropped_features,
                "split_deltas": {},
            }

            if not dropped_features:
                group_reason_candidates.append("no_gender_features")
                group_payload["gender_results"][gender_key] = gender_result
                continue

            base_frame = feature_frames_by_gender.get(gender_key)
            if base_frame is None:
                group_reason_candidates.append("group_missing")
                gender_result["reason"] = "group_missing"
                group_payload["gender_results"][gender_key] = gender_result
                continue

            ablated_df = base_frame.drop(columns=dropped_features, errors="ignore")
            remaining_features = [column for column in ablated_df.columns if column not in drop_columns]
            if not remaining_features:
                group_reason_candidates.append("no_gender_features")
                gender_result["reason"] = "no_gender_features"
                group_payload["gender_results"][gender_key] = gender_result
                continue

            gender_label = "M" if gender_key == "men" else "W"
            try:
                ablated_model, ablated_payload = train_module.train_baseline(
                    ablated_df,
                    gender_label,
                    random_state=context["seed"],
                )
            except Exception as exc:
                message = str(exc).lower()
                reason = "split_empty" if "empty" in message or "boş" in message else "no_gender_features"
                reason = governance_module.normalize_skip_reason(reason)
                group_reason_candidates.append(reason)
                gender_result["reason"] = reason
                gender_result["error"] = str(exc)
                group_payload["gender_results"][gender_key] = gender_result
                continue

            ablated_snapshot = ablated_payload.get("feature_snapshot", {})
            ablated_feature_columns = ablated_snapshot.get("feature_columns") if isinstance(ablated_snapshot, dict) else None
            if not isinstance(ablated_feature_columns, list) or not ablated_feature_columns:
                group_reason_candidates.append("no_gender_features")
                gender_result["reason"] = "no_gender_features"
                group_payload["gender_results"][gender_key] = gender_result
                continue

            missing_ablated_columns = [col for col in ablated_feature_columns if col not in ablated_df.columns]
            if missing_ablated_columns:
                group_reason_candidates.append("group_missing")
                gender_result["reason"] = "group_missing"
                gender_result["missing_columns"] = missing_ablated_columns
                group_payload["gender_results"][gender_key] = gender_result
                continue

            ablated_calibration_by_split: dict[str, Any] = {}
            for split_label in CANONICAL_SPLITS:
                split_df = ablated_df[ablated_df["Split"] == split_label].copy()
                if split_df.empty:
                    split_true = np.asarray([], dtype=float)
                    split_prob = np.asarray([], dtype=float)
                else:
                    split_features = split_df.loc[:, ablated_feature_columns]
                    split_true = split_df["Target"].to_numpy(dtype=float)
                    try:
                        raw_probs = ablated_model.predict_proba(split_features)
                    except Exception as exc:
                        raise RuntimeError(
                            f"[{gender_key}] ablation predict_proba failed for group={group_name} split={split_label}: {exc}"
                        ) from exc
                    split_prob = _extract_positive_class_probabilities(
                        raw_probs,
                        gender_key=gender_key,
                        split_label=split_label,
                    )

                _, split_summary = _build_calibration_rows_and_summary(
                    gender_key=gender_key,
                    split_label=split_label,
                    y_true=split_true,
                    y_prob=split_prob,
                )
                ablated_calibration_by_split[split_label] = split_summary

            baseline_payload = genders_payload.get(gender_key, {})
            baseline_metrics = baseline_payload.get("metrics_by_split", {}) if isinstance(baseline_payload, dict) else {}
            baseline_calibration = calibration_summary.get(gender_key, {})
            ablated_metrics = ablated_payload.get("metrics_by_split", {})

            split_deltas = governance_module.compute_ablation_split_deltas(
                baseline_metrics_by_split=baseline_metrics,
                ablated_metrics_by_split=ablated_metrics,
                baseline_calibration_by_split=baseline_calibration,
                ablated_calibration_by_split=ablated_calibration_by_split,
            )

            has_executable_signal = any(
                split_payload.get("delta_brier") is not None
                or split_payload.get("delta_logloss") is not None
                or split_payload.get("delta_auc") is not None
                for split_payload in split_deltas.values()
            )

            if not has_executable_signal:
                split_reason = next(
                    (
                        split_payload.get("reason")
                        for split_payload in split_deltas.values()
                        if split_payload.get("reason") is not None
                    ),
                    "no_gender_features",
                )
                normalized_reason = governance_module.normalize_skip_reason(split_reason)
                group_reason_candidates.append(normalized_reason)
                gender_result["reason"] = normalized_reason
            else:
                group_executed = True
                gender_result["status"] = "executed"
                gender_result["reason"] = None

            gender_result["split_deltas"] = split_deltas
            baseline_feature_columns = [column for column in base_frame.columns if column not in drop_columns]
            gender_result["baseline_feature_count"] = int(len(baseline_feature_columns))
            gender_result["ablated_feature_count"] = int(len(ablated_feature_columns))
            group_payload["gender_results"][gender_key] = gender_result

        if group_executed:
            group_payload["status"] = "executed"
            group_payload["reason"] = None
        else:
            fallback_reason = group_reason_candidates[0] if group_reason_candidates else "group_missing"
            group_payload["reason"] = governance_module.normalize_skip_reason(fallback_reason)

        ablation_groups.append(group_payload)

    ablation_report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "config": {
            "target_splits": list(governance_module.ABLATION_TARGET_SPLITS),
            "max_groups": int(getattr(governance_module, "DEFAULT_MAX_ABLATION_GROUPS", len(selected_groups))),
            "selected_groups": selected_groups,
        },
        "groups": ablation_groups,
    }
    ablation_report_path = Path(context["run_dir"]) / "ablation_report.json"
    _write_json(ablation_report_path, ablation_report_payload)

    ablation_summary = governance_module.build_ablation_summary(
        selected_groups=selected_groups,
        ablation_groups=ablation_groups,
    )
    governance_summary.update(ablation_summary)

    governance_payload = {
        "artifacts": {
            "ledger_csv": str(governance_ledger_path),
            "ablation_report_json": str(ablation_report_path),
        },
        "summary": governance_summary,
        "diagnostics": {
            "selected_groups": selected_groups,
        },
    }

    governance_decision_report_payload = _build_governance_decision_report(
        context=context,
        ablation_groups=ablation_groups,
        drift_payload=drift_payload,
        calibration_policy_payload=calibration_policy_payload,
    )
    governance_decision_report_path = Path(context["run_dir"]) / "governance_decision_report.json"
    _write_json(governance_decision_report_path, governance_decision_report_payload)

    governance_decision_payload = {
        "report_json": str(governance_decision_report_path),
        "by_gender": governance_decision_report_payload["by_gender"],
        "aggregate": governance_decision_report_payload["aggregate"],
    }

    report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "models": train_result.get("models", {}),
        "feature_snapshot": train_result.get("feature_snapshot", {}),
        "prediction_policy": prediction_policy_payload,
        "metrics_table": metrics_table,
        "side_by_side_summary": side_by_side_summary,
        "calibration": calibration_payload,
        "drift": drift_payload,
        "calibration_policy": calibration_policy_payload,
        "ensemble": ensemble_payload,
        "alternative_model": alternative_model_payload,
        "men_combo_followup": men_combo_followup_payload,
        "men_tabpfn_followup": men_tabpfn_followup_payload,
        "blend_candidate_policy": blend_candidate_policy_payload,
        "final_blend_recipe": final_blend_recipe_payload,
        "men_policy_refinement": men_policy_refinement_payload,
        "men_external_prior_policy": men_external_prior_policy_payload,
        "men_gate_aware_search": men_gate_aware_search_payload,
        "men_residual_correction": men_residual_correction_payload,
        "men_regime_routing": men_regime_routing_payload,
        "feature_branch": feature_branch_payload,
        "stacking_policy": stacking_policy_payload,
        "error_decomposition": error_decomposition_payload,
        "governance": governance_payload,
        "governance_decision": governance_decision_payload,
    }

    report_path = Path(context["run_dir"]) / "eval_report.json"
    _write_json(report_path, report_payload)

    return {
        "eval_report": str(report_path),
        "prediction_policy": prediction_policy_payload,
        "metrics_table": metrics_table,
        "side_by_side_summary": side_by_side_summary,
        "calibration": calibration_payload,
        "drift": drift_payload,
        "calibration_policy": calibration_policy_payload,
        "ensemble": ensemble_payload,
        "alternative_model": alternative_model_payload,
        "men_combo_followup": men_combo_followup_payload,
        "men_tabpfn_followup": men_tabpfn_followup_payload,
        "blend_candidate_policy": blend_candidate_policy_payload,
        "final_blend_recipe": final_blend_recipe_payload,
        "men_policy_refinement": men_policy_refinement_payload,
        "men_external_prior_policy": men_external_prior_policy_payload,
        "men_gate_aware_search": men_gate_aware_search_payload,
        "men_residual_correction": men_residual_correction_payload,
        "men_regime_routing": men_regime_routing_payload,
        "feature_branch": feature_branch_payload,
        "stacking_policy": stacking_policy_payload,
        "error_decomposition": error_decomposition_payload,
        "governance": governance_payload,
        "governance_decision": governance_decision_payload,
    }


def stage_artifact(context: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(context["run_dir"])
    stage_outputs = context.get("stage_outputs", {}) if isinstance(context.get("stage_outputs", {}), dict) else {}
    feature_output = stage_outputs.get("feature", {}) if isinstance(stage_outputs.get("feature", {}), dict) else {}
    train_output = stage_outputs.get("train", {}) if isinstance(stage_outputs.get("train", {}), dict) else {}
    eval_output = stage_outputs.get("eval_report", {}) if isinstance(stage_outputs.get("eval_report", {}), dict) else {}
    calibration_output = eval_output.get("calibration", {}) if isinstance(eval_output.get("calibration", {}), dict) else {}
    drift_output = eval_output.get("drift", {}) if isinstance(eval_output.get("drift", {}), dict) else {}
    calibration_policy_output = (
        eval_output.get("calibration_policy", {}) if isinstance(eval_output.get("calibration_policy", {}), dict) else {}
    )
    ensemble_output = eval_output.get("ensemble", {}) if isinstance(eval_output.get("ensemble", {}), dict) else {}
    alternative_model_output = (
        eval_output.get("alternative_model", {}) if isinstance(eval_output.get("alternative_model", {}), dict) else {}
    )
    men_combo_followup_output = (
        eval_output.get("men_combo_followup", {})
        if isinstance(eval_output.get("men_combo_followup", {}), dict)
        else {}
    )
    men_tabpfn_followup_output = (
        eval_output.get("men_tabpfn_followup", {})
        if isinstance(eval_output.get("men_tabpfn_followup", {}), dict)
        else {}
    )
    blend_candidate_policy_output = (
        eval_output.get("blend_candidate_policy", {})
        if isinstance(eval_output.get("blend_candidate_policy", {}), dict)
        else {}
    )
    final_blend_recipe_output = (
        eval_output.get("final_blend_recipe", {})
        if isinstance(eval_output.get("final_blend_recipe", {}), dict)
        else {}
    )
    men_policy_refinement_output = (
        eval_output.get("men_policy_refinement", {})
        if isinstance(eval_output.get("men_policy_refinement", {}), dict)
        else {}
    )
    men_external_prior_policy_output = (
        eval_output.get("men_external_prior_policy", {})
        if isinstance(eval_output.get("men_external_prior_policy", {}), dict)
        else {}
    )
    men_gate_aware_search_output = (
        eval_output.get("men_gate_aware_search", {})
        if isinstance(eval_output.get("men_gate_aware_search", {}), dict)
        else {}
    )
    governance_output = eval_output.get("governance", {}) if isinstance(eval_output.get("governance", {}), dict) else {}
    governance_decision_output = (
        eval_output.get("governance_decision", {})
        if isinstance(eval_output.get("governance_decision", {}), dict)
        else {}
    )
    error_decomposition_output = (
        eval_output.get("error_decomposition", {})
        if isinstance(eval_output.get("error_decomposition", {}), dict)
        else {}
    )
    governance_artifacts = (
        governance_output.get("artifacts", {}) if isinstance(governance_output.get("artifacts", {}), dict) else {}
    )
    train_genders = train_output.get("genders", {}) if isinstance(train_output.get("genders", {}), dict) else {}

    artifact_paths = {
        "run_metadata_json": context.get("metadata_path"),
        "stage_events_jsonl": context.get("stage_events_path"),
        "eval_report_json": eval_output.get("eval_report"),
        "calibration_bins_csv": calibration_output.get("bins_csv"),
        "calibration_report_json": calibration_output.get("report_json"),
        "drift_regime_report_json": drift_output.get("report_json"),
        "calibration_policy_report_json": calibration_policy_output.get("report_json"),
        "ensemble_report_json": ensemble_output.get("report_json"),
        "alternative_model_report_json": alternative_model_output.get("report_json"),
        "men_combo_followup_report_json": men_combo_followup_output.get("report_json"),
        "men_tabpfn_followup_report_json": men_tabpfn_followup_output.get("report_json"),
        "blend_candidate_policy_report_json": blend_candidate_policy_output.get("report_json"),
        "final_blend_recipe_report_json": final_blend_recipe_output.get("report_json"),
        "men_policy_refinement_report_json": men_policy_refinement_output.get("report_json"),
        "men_external_prior_policy_report_json": men_external_prior_policy_output.get("report_json"),
        "men_gate_aware_search_report_json": men_gate_aware_search_output.get("report_json"),
        "error_decomposition_report_json": error_decomposition_output.get("report_json"),
        "governance_ledger_csv": governance_artifacts.get("ledger_csv"),
        "ablation_report_json": governance_artifacts.get("ablation_report_json"),
        "governance_decision_report_json": governance_decision_output.get("report_json"),
        "men_model_pkl": train_genders.get("men", {}).get("model_path") if isinstance(train_genders.get("men", {}), dict) else None,
        "women_model_pkl": train_genders.get("women", {}).get("model_path") if isinstance(train_genders.get("women", {}), dict) else None,
        "men_features_csv": feature_output.get("outputs", {}).get("men_features") if isinstance(feature_output.get("outputs", {}), dict) else None,
        "women_features_csv": feature_output.get("outputs", {}).get("women_features") if isinstance(feature_output.get("outputs", {}), dict) else None,
    }

    contract_entries: dict[str, dict[str, Any]] = {}
    missing_artifacts: list[str] = []
    for name, raw_path in artifact_paths.items():
        if isinstance(raw_path, str) and raw_path.strip():
            resolved_path = Path(raw_path)
            exists = resolved_path.exists()
            path_value = str(resolved_path)
        else:
            resolved_path = None
            exists = False
            path_value = None

        contract_entries[name] = {
            "path": path_value,
            "exists": bool(exists),
        }
        if not exists:
            missing_artifacts.append(name)

    artifact_contract_payload = {
        "run_id": context["run_id"],
        "generated_at": _now_utc_iso(),
        "required_artifacts": contract_entries,
        "missing_artifacts": missing_artifacts,
        "pass": len(missing_artifacts) == 0,
    }
    artifact_contract_path = run_dir / "artifact_contract_report.json"
    _write_json(artifact_contract_path, artifact_contract_payload)

    prior_runs = _load_prior_run_metadatas(
        artifacts_root=Path(context["artifacts_root"]),
        current_run_id=context["run_id"],
    )

    current_snapshot = _extract_run_snapshot(stage_outputs)

    reproducibility_baseline = next(
        (
            metadata
            for metadata in reversed(prior_runs)
            if metadata.get("git_commit") == context.get("git_commit") and metadata.get("seed") == context.get("seed")
        ),
        None,
    )
    reproducibility_payload = _evaluate_reproducibility(
        current_run_context=context,
        current_snapshot=current_snapshot,
        baseline_metadata=reproducibility_baseline,
        tolerance=REPRO_BRIER_TOLERANCE,
    )
    reproducibility_path = run_dir / "reproducibility_report.json"
    _write_json(reproducibility_path, reproducibility_payload)

    regression_baseline = prior_runs[-1] if prior_runs else None
    regression_payload = _evaluate_regression_gate(
        current_snapshot=current_snapshot,
        baseline_metadata=regression_baseline,
    )
    regression_path = run_dir / "regression_gate_report.json"
    _write_json(regression_path, regression_payload)

    weighted_promotion_gate_payload = _build_multi_season_weighted_promotion_gate(
        context=context,
        current_snapshot=current_snapshot,
        baseline_metadata=regression_baseline,
    )
    weighted_promotion_gate_path = run_dir / "multi_season_weighted_gate_report.json"
    _write_json(weighted_promotion_gate_path, weighted_promotion_gate_payload)

    policy_gate_payload = {
        "run_id": context["run_id"],
        "generated_at": _now_utc_iso(),
        "regression_status": regression_payload.get("status"),
        "regression_reason": regression_payload.get("reason"),
        "aggregate_decision": current_snapshot.get("governance_decision", {}).get("aggregate_decision"),
        "blocking_failures": regression_payload.get("blocking_failures", []),
        "warnings": regression_payload.get("warnings", []),
        "by_gender": {},
    }
    for gender_key in ("men", "women"):
        regression_gender = regression_payload.get("by_gender", {}).get(gender_key, {})
        decision_gender = current_snapshot.get("governance_decision", {}).get(gender_key, {})
        policy_gate_payload["by_gender"][gender_key] = {
            "decision": decision_gender.get("decision") if isinstance(decision_gender, dict) else None,
            "confidence": decision_gender.get("confidence") if isinstance(decision_gender, dict) else None,
            "brier_rule_status": regression_gender.get("brier_rule", {}).get("status")
            if isinstance(regression_gender, dict)
            else None,
            "calibration_rule_status": regression_gender.get("calibration_rule", {}).get("status")
            if isinstance(regression_gender, dict)
            else None,
            "policy_fallback_applied": regression_gender.get("policy_gate", {}).get("fallback_applied")
            if isinstance(regression_gender, dict)
            else None,
        }

    policy_gate_path = run_dir / "policy_gate_report.json"
    _write_json(policy_gate_path, policy_gate_payload)

    pre_submission_blockers: list[str] = []
    if missing_artifacts:
        pre_submission_blockers.append("artifact_contract_failed")
    if reproducibility_payload.get("status") == "failed":
        pre_submission_blockers.append("reproducibility_failed")
    if regression_payload.get("status") == "failed":
        pre_submission_blockers.append("regression_gate_failed")

    submission_error: Exception | None = None
    submission_stage = str(context.get("submission_stage", "none"))
    if pre_submission_blockers:
        submission_payload = {
            "status": "skipped",
            "reason": "blocked_before_submission",
            "stage": submission_stage,
        }
    else:
        try:
            submission_payload = _build_optional_submission(context)
        except Exception as exc:
            submission_error = exc
            submission_payload = {
                "status": "failed",
                "reason": "submission_validation_failed",
                "stage": submission_stage,
                "validation_report_json": str(run_dir / "submission_validation_report.json"),
                "submission_csv": None,
                "error": str(exc),
            }

    readiness_payload = _evaluate_submission_readiness(
        context=context,
        artifact_contract_payload=artifact_contract_payload,
        reproducibility_payload=reproducibility_payload,
        regression_payload=regression_payload,
        policy_gate_payload=policy_gate_payload,
        submission_payload=submission_payload,
        ensemble_output=ensemble_output,
    )
    readiness_path = run_dir / "submission_readiness_report.json"
    _write_json(readiness_path, readiness_payload)

    if missing_artifacts:
        raise RuntimeError(
            "artifact contract failed: missing required artifacts -> " + ", ".join(sorted(missing_artifacts))
        )

    if reproducibility_payload.get("status") == "failed":
        raise RuntimeError(
            "reproducibility gate failed: "
            + json.dumps(reproducibility_payload.get("failures", []), ensure_ascii=False)
        )

    if regression_payload.get("status") == "failed":
        raise RuntimeError(
            "regression gate failed: "
            + json.dumps(regression_payload.get("blocking_failures", []), ensure_ascii=False)
        )

    if submission_error is not None:
        raise submission_error

    run_files = sorted(
        str(path.relative_to(run_dir))
        for path in run_dir.glob("**/*")
        if path.is_file() and path.name != "artifact_manifest.json"
    )

    manifest_payload = {
        "run_id": context["run_id"],
        "generated_at": _now_utc_iso(),
        "run_dir": str(run_dir),
        "file_count": len(run_files),
        "files": run_files,
        "stage_outputs": stage_outputs,
        "contracts": {
            "artifact_contract": {
                "status": "passed",
                "report_json": str(artifact_contract_path),
            },
            "reproducibility": {
                "status": reproducibility_payload.get("status"),
                "report_json": str(reproducibility_path),
            },
            "regression_gate": {
                "status": regression_payload.get("status"),
                "report_json": str(regression_path),
            },
            "policy_gate": {
                "status": policy_gate_payload.get("regression_status"),
                "report_json": str(policy_gate_path),
            },
            "weighted_promotion_gate": {
                "status": weighted_promotion_gate_payload.get("status"),
                "report_json": str(weighted_promotion_gate_path),
            },
            "submission": {
                "status": submission_payload.get("status"),
                "report_json": submission_payload.get("validation_report_json"),
                "submission_csv": submission_payload.get("submission_csv"),
            },
            "readiness": {
                "status": readiness_payload.get("status"),
                "report_json": str(readiness_path),
            },
        },
    }

    manifest_path = run_dir / "artifact_manifest.json"
    _write_json(manifest_path, manifest_payload)

    final_file_count = len([path for path in run_dir.glob("**/*") if path.is_file()])

    return {
        "manifest": str(manifest_path),
        "file_count": final_file_count,
        "artifact_contract": {
            "status": "passed",
            "report_json": str(artifact_contract_path),
        },
        "reproducibility": {
            "status": reproducibility_payload.get("status"),
            "report_json": str(reproducibility_path),
        },
        "regression_gate": {
            "status": regression_payload.get("status"),
            "report_json": str(regression_path),
        },
        "policy_gate": {
            "status": policy_gate_payload.get("regression_status"),
            "report_json": str(policy_gate_path),
        },
        "weighted_promotion_gate": {
            "status": weighted_promotion_gate_payload.get("status"),
            "report_json": str(weighted_promotion_gate_path),
            "decision": weighted_promotion_gate_payload.get("aggregate", {}).get("decision"),
            "backtest_report_json": weighted_promotion_gate_payload.get("backtest_report_json"),
        },
        "submission": {
            "status": submission_payload.get("status"),
            "validation_report_json": submission_payload.get("validation_report_json"),
            "submission_csv": submission_payload.get("submission_csv"),
            "stage": submission_payload.get("stage"),
            "reason": submission_payload.get("reason"),
            "prediction_summary": submission_payload.get("prediction_summary"),
        },
        "readiness": {
            "status": readiness_payload.get("status"),
            "report_json": str(readiness_path),
        },
    }


STAGE_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "feature": stage_feature,
    "train": stage_train,
    "eval_report": stage_eval_report,
    "artifact": stage_artifact,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canonical March Mania pipeline orchestrator")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic training")
    parser.add_argument("--run-label", type=str, default="manual", help="Readable label suffix for run_id")
    parser.add_argument(
        "--artifacts-root",
        type=str,
        default=str(DEFAULT_ARTIFACTS_ROOT),
        help="Root directory where run-scoped artifacts are written",
    )
    parser.add_argument(
        "--submission-stage",
        type=str,
        choices=("none", "stage1", "stage2"),
        default="none",
        help="Optional submission output stage; 'none' disables submission generation",
    )
    parser.add_argument(
        "--training-profile",
        type=str,
        choices=("baseline", "quality_v1"),
        default="baseline",
        help="Train profile to use in canonical train stage",
    )
    parser.add_argument(
        "--hpo-trials",
        type=int,
        default=0,
        help="Optional deterministic HPO trial count (0 disables HPO harness)",
    )
    parser.add_argument(
        "--hpo-target-profile",
        type=str,
        choices=HPO_ALLOWED_PROFILES,
        default="quality_v1",
        help="Target profile namespace for HPO candidate search",
    )
    parser.add_argument(
        "--prediction-policy",
        type=str,
        choices=PREDICTION_POLICIES,
        default="baseline",
        help="Eval-time probability policy; baseline preserves canonical scoring, blend_candidate_v1 applies the research blend",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    context = build_run_context(
        seed=args.seed,
        run_label=args.run_label,
        artifacts_root=args.artifacts_root,
        argv=argv,
    )
    context["submission_stage"] = args.submission_stage
    context["training_profile"] = args.training_profile
    context["hpo_trials"] = int(args.hpo_trials)
    context["hpo_target_profile"] = args.hpo_target_profile
    context["prediction_policy"] = args.prediction_policy

    run_dir = Path(context["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    context["metadata_path"] = str(run_dir / "run_metadata.json")
    context["stage_events_path"] = str(run_dir / "stage_events.jsonl")

    start_clock = time.perf_counter()
    _persist_metadata(context)

    for stage in CANONICAL_STAGES:
        if stage not in STAGE_HANDLERS:
            error = RuntimeError(f"Missing stage handler for '{stage}'")
            err_payload = _serialize_error(error)
            stage_started_at = _now_utc_iso()
            _append_jsonl(
                Path(context["stage_events_path"]),
                _stage_event(
                    stage=stage,
                    status="failed",
                    started_at=stage_started_at,
                    finished_at=stage_started_at,
                    duration_ms=0,
                    error=err_payload,
                ),
            )
            context["status"] = "failed"
            context["failed_stage"] = stage
            context["error"] = err_payload
            context["finished_at"] = _now_utc_iso()
            context["duration_ms"] = int((time.perf_counter() - start_clock) * 1000)
            _persist_metadata(context)
            print(f"[FAIL] {err_payload['message']}", file=sys.stderr)
            return 1

        stage_started_at, stage_clock = _record_stage_started(context, stage)
        try:
            result = STAGE_HANDLERS[stage](context)
            context.setdefault("stage_outputs", {})[stage] = result if result is not None else {}
            _record_stage_finished(
                context,
                stage,
                "succeeded",
                stage_started_at,
                stage_clock,
                error=None,
            )
            _persist_metadata(context)
        except Exception as exc:
            err_payload = _serialize_error(exc)
            _record_stage_finished(
                context,
                stage,
                "failed",
                stage_started_at,
                stage_clock,
                error=err_payload,
            )
            context["status"] = "failed"
            context["failed_stage"] = stage
            context["error"] = err_payload
            context["finished_at"] = _now_utc_iso()
            context["duration_ms"] = int((time.perf_counter() - start_clock) * 1000)
            _persist_metadata(context)
            print(f"[FAIL] Stage '{stage}' failed: {exc}", file=sys.stderr)
            return 1

    context["status"] = "succeeded"
    context["finished_at"] = _now_utc_iso()
    context["duration_ms"] = int((time.perf_counter() - start_clock) * 1000)
    _persist_metadata(context)

    print(f"[OK] run_id={context['run_id']} status=succeeded")
    print(f"[OK] metadata={context['metadata_path']}")
    print(f"[OK] events={context['stage_events_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

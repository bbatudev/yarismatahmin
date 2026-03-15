from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pickle
import re

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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score


SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
REPO_ROOT = PIPELINE_DIR.parent
KAGGLE_DATA_DIR = REPO_ROOT / "march-machine-leraning-mania-2026"
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
CALIBRATION_POLICY_METHODS = ("none", "platt", "isotonic")
CALIBRATION_POLICY_MIN_VAL_SAMPLES = 80
CALIBRATION_POLICY_MIN_IMPROVEMENT = 0.001
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
ENSEMBLE_WEIGHT_GRID = (0.25, 0.5, 0.75)
ENSEMBLE_MIN_VAL_IMPROVEMENT = 1e-4


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

    feature_module.DATA_DIR = str(REPO_ROOT / "march-machine-leraning-mania-2026")
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
        val_metrics = metrics_by_split.get("Val", {}) if isinstance(metrics_by_split, dict) else {}
        test_metrics = metrics_by_split.get("Test", {}) if isinstance(metrics_by_split, dict) else {}
        val_brier = _as_float_or_none(val_metrics.get("brier"))

        candidate_payload.update(
            {
                "status": "passed" if val_brier is not None else "failed",
                "reason": None if val_brier is not None else "missing_val_brier",
                "metrics": {
                    "val_brier": val_brier,
                    "val_logloss": _as_float_or_none(val_metrics.get("logloss")),
                    "val_auc": _as_float_or_none(val_metrics.get("auc")),
                    "test_brier": _as_float_or_none(test_metrics.get("brier")),
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
            "candidates": candidates,
        }

    best = min(
        successful,
        key=lambda candidate: (
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


def _predict_model_split_probabilities(
    *,
    model: Any,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    gender_key: str,
) -> dict[str, dict[str, np.ndarray]]:
    split_cache: dict[str, dict[str, np.ndarray]] = {}
    for split_label in ("Val", "Test"):
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
        if improvement is None or improvement < ENSEMBLE_MIN_VAL_IMPROVEMENT:
            selected_candidate = baseline_available
            selection_reason = "improvement_below_threshold"
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


def _extract_run_snapshot(stage_outputs: dict[str, Any]) -> dict[str, Any]:
    snapshot = {
        "metrics": {"men": {}, "women": {}},
        "calibration": {"men": {}, "women": {}},
        "calibration_policy": {"men": {}, "women": {}},
        "governance_decision": {"men": {}, "women": {}, "aggregate_decision": None},
    }

    train_metrics = stage_outputs.get("train", {}).get("metrics_by_split", {}) if isinstance(stage_outputs, dict) else {}
    eval_output = stage_outputs.get("eval_report", {}) if isinstance(stage_outputs, dict) else {}
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
        split_metrics = train_metrics.get(gender_key, {}).get("Test", {}) if isinstance(train_metrics, dict) else {}
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
    sample_path = KAGGLE_DATA_DIR / sample_name
    if not sample_path.exists():
        raise RuntimeError(f"submission sample file not found: {sample_path}")

    sample_df = pd.read_csv(sample_path)
    if "ID" not in sample_df.columns:
        raise RuntimeError(f"submission sample missing ID column: {sample_path}")

    submission_df = pd.DataFrame(
        {
            "ID": sample_df["ID"].astype(str),
            "Pred": np.full(len(sample_df), 0.5, dtype=float),
        }
    )

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
        "validation": validation,
    }

    report_path = run_dir / "submission_validation_report.json"
    _write_json(report_path, report_payload)

    if not validation["pass"]:
        raise RuntimeError("submission validation failed")

    report_payload["validation_report_json"] = str(report_path)
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

        if best_method != default_method and improvement is not None and improvement < CALIBRATION_POLICY_MIN_IMPROVEMENT:
            if default_method in available_methods:
                selected_method = default_method
                selection_reason = "improvement_below_threshold_use_default"
            else:
                selected_method = best_method
                selection_reason = "default_unavailable_use_best"
        else:
            selected_method = best_method
            selection_reason = "best_val_brier"

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


def stage_eval_report(context: dict[str, Any]) -> dict[str, Any]:
    train_result = context.get("stage_outputs", {}).get("train", {})
    metrics_by_split = train_result.get("metrics_by_split", {})

    if not isinstance(metrics_by_split, dict):
        raise RuntimeError("Train stage output missing metrics_by_split contract.")

    genders_payload = train_result.get("genders", {})
    if not isinstance(genders_payload, dict):
        raise RuntimeError("Train stage output missing genders contract required for calibration scoring.")

    metrics_table: list[dict[str, Any]] = []
    for gender_key in ("men", "women"):
        gender_metrics = metrics_by_split.get(gender_key, {})
        for split_label in CANONICAL_SPLITS:
            split_metrics = gender_metrics.get(split_label, {})
            metrics_table.append(
                {
                    "gender": gender_key,
                    "split": split_label,
                    "brier": split_metrics.get("brier"),
                    "logloss": split_metrics.get("logloss"),
                    "auc": split_metrics.get("auc"),
                }
            )

    men_test = metrics_by_split.get("men", {}).get("Test", {})
    women_test = metrics_by_split.get("women", {}).get("Test", {})

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

    calibration_rows: list[dict[str, Any]] = []
    calibration_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    governance_importances: dict[str, list[float] | None] = {"men": None, "women": None}
    feature_frames_by_gender: dict[str, pd.DataFrame] = {}
    split_probabilities: dict[str, dict[str, dict[str, np.ndarray]]] = {"men": {}, "women": {}}
    drift_split_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    drift_regime_summary: dict[str, dict[str, Any]] = {"men": {}, "women": {}}
    drift_alerts: list[dict[str, Any]] = []

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

            split_rows, split_summary = _build_calibration_rows_and_summary(
                gender_key=gender_key,
                split_label=split_label,
                y_true=split_true,
                y_prob=split_prob,
            )
            calibration_rows.extend(split_rows)
            calibration_summary[gender_key][split_label] = split_summary
            split_probabilities[gender_key][split_label] = {
                "y_true": split_true,
                "y_prob": split_prob,
            }

            drift_split_summary[gender_key][split_label] = _build_split_drift_summary(
                y_true=split_true,
                y_prob=split_prob,
            )

            if split_label == "Test":
                regime_summary, regime_alerts = _build_test_regime_drift_summary(
                    gender_key=gender_key,
                    split_df=split_df,
                    y_prob=split_prob,
                )
                drift_regime_summary[gender_key] = regime_summary
                drift_alerts.extend(regime_alerts)

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
    for gender_key in ("men", "women"):
        val_cache = split_probabilities.get(gender_key, {}).get("Val", {})
        test_cache = split_probabilities.get(gender_key, {}).get("Test", {})
        val_true = np.asarray(val_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        val_prob = np.asarray(val_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)
        test_true = np.asarray(test_cache.get("y_true", np.asarray([], dtype=float)), dtype=float)
        test_prob = np.asarray(test_cache.get("y_prob", np.asarray([], dtype=float)), dtype=float)

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
        "metrics_table": metrics_table,
        "side_by_side_summary": side_by_side_summary,
        "calibration": calibration_payload,
        "drift": drift_payload,
        "calibration_policy": calibration_policy_payload,
        "ensemble": ensemble_payload,
        "governance": governance_payload,
        "governance_decision": governance_decision_payload,
    }

    report_path = Path(context["run_dir"]) / "eval_report.json"
    _write_json(report_path, report_payload)

    return {
        "eval_report": str(report_path),
        "calibration": calibration_payload,
        "drift": drift_payload,
        "calibration_policy": calibration_policy_payload,
        "ensemble": ensemble_payload,
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
    governance_output = eval_output.get("governance", {}) if isinstance(eval_output.get("governance", {}), dict) else {}
    governance_decision_output = (
        eval_output.get("governance_decision", {})
        if isinstance(eval_output.get("governance_decision", {}), dict)
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
        "submission": {
            "status": submission_payload.get("status"),
            "validation_report_json": submission_payload.get("validation_report_json"),
            "submission_csv": submission_payload.get("submission_csv"),
            "stage": submission_payload.get("stage"),
            "reason": submission_payload.get("reason"),
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

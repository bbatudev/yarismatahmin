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


SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SCRIPT_DIR.parent
REPO_ROOT = PIPELINE_DIR.parent
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

    men_model, men_payload = train_module.train_baseline(men_df, "M", random_state=context["seed"])
    women_model, women_payload = train_module.train_baseline(women_df, "W", random_state=context["seed"])

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
            "metrics_by_split": men_payload.get("metrics_by_split", {}),
            "feature_snapshot": men_payload.get("feature_snapshot", {}),
            "best_iteration": men_payload.get("best_iteration"),
        },
        "women": {
            "gender": women_payload.get("gender", "W"),
            "model_path": str(women_model_path),
            "metrics_by_split": women_payload.get("metrics_by_split", {}),
            "feature_snapshot": women_payload.get("feature_snapshot", {}),
            "best_iteration": women_payload.get("best_iteration"),
        },
    }

    return {
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


def _extract_run_snapshot(stage_outputs: dict[str, Any]) -> dict[str, Any]:
    snapshot = {
        "metrics": {"men": {}, "women": {}},
        "calibration": {"men": {}, "women": {}},
    }

    train_metrics = stage_outputs.get("train", {}).get("metrics_by_split", {}) if isinstance(stage_outputs, dict) else {}
    calibration_summary = (
        stage_outputs.get("eval_report", {}).get("calibration", {}).get("calibration_summary", {})
        if isinstance(stage_outputs, dict)
        else {}
    )

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
            "calibration": "degradation_fails",
            "auc": "informational",
        },
        "by_gender": {},
        "baseline_run_id": None,
    }

    if baseline_metadata is None:
        return report

    baseline_snapshot = _extract_run_snapshot(baseline_metadata.get("stage_outputs", {}))
    report["baseline_run_id"] = baseline_metadata.get("run_id")

    blocking_failures: list[str] = []

    for gender_key in ("men", "women"):
        current_metrics = current_snapshot.get("metrics", {}).get(gender_key, {})
        baseline_metrics = baseline_snapshot.get("metrics", {}).get(gender_key, {})
        current_cal = current_snapshot.get("calibration", {}).get(gender_key, {})
        baseline_cal = baseline_snapshot.get("calibration", {}).get(gender_key, {})

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

        if calibration_reasons:
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

    return report


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

    train_module = _load_script_module("03_lgbm_train.py", "lgbm_train_ablation_stage")
    train_module.DATA_DIR = str(PIPELINE_DIR / "artifacts" / "data")
    train_module.OUT_DIR = str(PIPELINE_DIR / "artifacts" / "models")

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

    report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "models": train_result.get("models", {}),
        "feature_snapshot": train_result.get("feature_snapshot", {}),
        "metrics_table": metrics_table,
        "side_by_side_summary": side_by_side_summary,
        "calibration": calibration_payload,
        "governance": governance_payload,
    }

    report_path = Path(context["run_dir"]) / "eval_report.json"
    _write_json(report_path, report_payload)

    return {
        "eval_report": str(report_path),
        "calibration": calibration_payload,
        "governance": governance_payload,
    }


def stage_artifact(context: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(context["run_dir"])
    stage_outputs = context.get("stage_outputs", {}) if isinstance(context.get("stage_outputs", {}), dict) else {}
    feature_output = stage_outputs.get("feature", {}) if isinstance(stage_outputs.get("feature", {}), dict) else {}
    train_output = stage_outputs.get("train", {}) if isinstance(stage_outputs.get("train", {}), dict) else {}
    eval_output = stage_outputs.get("eval_report", {}) if isinstance(stage_outputs.get("eval_report", {}), dict) else {}
    calibration_output = eval_output.get("calibration", {}) if isinstance(eval_output.get("calibration", {}), dict) else {}
    governance_output = eval_output.get("governance", {}) if isinstance(eval_output.get("governance", {}), dict) else {}
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
        "governance_ledger_csv": governance_artifacts.get("ledger_csv"),
        "ablation_report_json": governance_artifacts.get("ablation_report_json"),
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
                "status": "passed" if artifact_contract_payload["pass"] else "failed",
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
        },
    }

    manifest_path = run_dir / "artifact_manifest.json"
    _write_json(manifest_path, manifest_payload)

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

    final_file_count = len(
        [path for path in run_dir.glob("**/*") if path.is_file()]
    )

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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    context = build_run_context(
        seed=args.seed,
        run_label=args.run_label,
        artifacts_root=args.artifacts_root,
        argv=argv,
    )

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

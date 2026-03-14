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


@lru_cache(maxsize=1)
def _load_split_leakage_contracts_module():
    return _load_script_module("split_leakage_contracts.py", "split_leakage_contracts_stage")


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

    report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "models": train_result.get("models", {}),
        "feature_snapshot": train_result.get("feature_snapshot", {}),
        "metrics_table": metrics_table,
        "side_by_side_summary": side_by_side_summary,
        "calibration": calibration_payload,
    }

    report_path = Path(context["run_dir"]) / "eval_report.json"
    _write_json(report_path, report_payload)

    return {
        "eval_report": str(report_path),
        "calibration": calibration_payload,
    }


def stage_artifact(context: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(context["run_dir"])
    run_files = sorted(
        str(path.relative_to(run_dir))
        for path in run_dir.glob("**/*")
        if path.is_file()
    )

    payload = {
        "run_id": context["run_id"],
        "generated_at": _now_utc_iso(),
        "run_dir": str(run_dir),
        "file_count": len(run_files),
        "files": run_files,
        "stage_outputs": context.get("stage_outputs", {}),
    }

    manifest_path = run_dir / "artifact_manifest.json"
    _write_json(manifest_path, payload)

    return {
        "manifest": str(manifest_path),
        "file_count": len(run_files) + 1,
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

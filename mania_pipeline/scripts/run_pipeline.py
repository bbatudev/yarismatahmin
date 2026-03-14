from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pickle
import re
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
    train_module = _load_script_module("03_lgbm_train.py", "lgbm_train_stage")

    train_module.DATA_DIR = str(PIPELINE_DIR / "artifacts" / "data")
    train_module.OUT_DIR = str(PIPELINE_DIR / "artifacts" / "models")
    os.makedirs(train_module.OUT_DIR, exist_ok=True)

    men_df = train_module.load_data("M")
    women_df = train_module.load_data("W")

    if men_df is None or women_df is None:
        raise RuntimeError("Training data missing; feature stage did not produce required files")

    men_model, men_brier = train_module.train_baseline(men_df, "M", random_state=context["seed"])
    women_model, women_brier = train_module.train_baseline(women_df, "W", random_state=context["seed"])

    model_dir = Path(train_module.OUT_DIR)
    men_model_path = model_dir / f"lgbm_baseline_men_{context['run_id']}.pkl"
    women_model_path = model_dir / f"lgbm_baseline_women_{context['run_id']}.pkl"

    with men_model_path.open("wb") as handle:
        pickle.dump(men_model, handle)
    with women_model_path.open("wb") as handle:
        pickle.dump(women_model, handle)

    return {
        "models": {
            "men": str(men_model_path),
            "women": str(women_model_path),
        },
        "metrics": {
            "men_test_brier": men_brier,
            "women_test_brier": women_brier,
        },
    }


def stage_eval_report(context: dict[str, Any]) -> dict[str, Any]:
    train_result = context.get("stage_outputs", {}).get("train", {})
    report_payload = {
        "run_id": context["run_id"],
        "seed": context["seed"],
        "generated_at": _now_utc_iso(),
        "metrics": train_result.get("metrics", {}),
        "models": train_result.get("models", {}),
    }

    report_path = Path(context["run_dir"]) / "eval_report.json"
    _write_json(report_path, report_payload)

    return {
        "eval_report": str(report_path),
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

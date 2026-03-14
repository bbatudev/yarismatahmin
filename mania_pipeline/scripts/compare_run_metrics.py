from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_metadata_path(value: str) -> Path:
    path = Path(value)
    if path.is_dir():
        path = path / "run_metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"run metadata not found: {path}")
    return path


def _to_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _safe_delta(current: Any, baseline: Any) -> float | None:
    c = _to_float_or_none(current)
    b = _to_float_or_none(baseline)
    if c is None or b is None:
        return None
    return c - b


def _extract_test_metrics(metadata: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    train = metadata.get("stage_outputs", {}).get("train", {})
    metrics = train.get("metrics_by_split", {}) if isinstance(train, dict) else {}

    result: dict[str, dict[str, float | None]] = {}
    for gender in ("men", "women"):
        test_metrics = metrics.get(gender, {}).get("Test", {}) if isinstance(metrics, dict) else {}
        result[gender] = {
            "brier": _to_float_or_none(test_metrics.get("brier")),
            "logloss": _to_float_or_none(test_metrics.get("logloss")),
            "auc": _to_float_or_none(test_metrics.get("auc")),
        }
    return result


def _extract_aux(metadata: dict[str, Any]) -> dict[str, Any]:
    stage_outputs = metadata.get("stage_outputs", {}) if isinstance(metadata.get("stage_outputs", {}), dict) else {}
    eval_output = stage_outputs.get("eval_report", {}) if isinstance(stage_outputs.get("eval_report", {}), dict) else {}
    artifact_output = stage_outputs.get("artifact", {}) if isinstance(stage_outputs.get("artifact", {}), dict) else {}

    ensemble = eval_output.get("ensemble", {}) if isinstance(eval_output.get("ensemble", {}), dict) else {}
    ensemble_aggregate = ensemble.get("aggregate", {}) if isinstance(ensemble.get("aggregate", {}), dict) else {}

    readiness = artifact_output.get("readiness", {}) if isinstance(artifact_output.get("readiness", {}), dict) else {}
    readiness_status = readiness.get("status")

    return {
        "ensemble_decision": ensemble_aggregate.get("decision"),
        "readiness_status": readiness_status,
    }


def build_comparison(*, baseline_metadata: dict[str, Any], candidate_metadata: dict[str, Any]) -> dict[str, Any]:
    baseline_metrics = _extract_test_metrics(baseline_metadata)
    candidate_metrics = _extract_test_metrics(candidate_metadata)

    by_gender: dict[str, Any] = {}
    for gender in ("men", "women"):
        by_gender[gender] = {
            "baseline": baseline_metrics.get(gender, {}),
            "candidate": candidate_metrics.get(gender, {}),
            "delta": {
                "brier": _safe_delta(candidate_metrics.get(gender, {}).get("brier"), baseline_metrics.get(gender, {}).get("brier")),
                "logloss": _safe_delta(
                    candidate_metrics.get(gender, {}).get("logloss"), baseline_metrics.get(gender, {}).get("logloss")
                ),
                "auc": _safe_delta(candidate_metrics.get(gender, {}).get("auc"), baseline_metrics.get(gender, {}).get("auc")),
            },
        }

    baseline_aux = _extract_aux(baseline_metadata)
    candidate_aux = _extract_aux(candidate_metadata)

    return {
        "baseline_run_id": baseline_metadata.get("run_id"),
        "candidate_run_id": candidate_metadata.get("run_id"),
        "by_gender": by_gender,
        "aux": {
            "baseline": baseline_aux,
            "candidate": candidate_aux,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Test metrics between two run_metadata artifacts")
    parser.add_argument("--baseline-run", required=True, help="Baseline run dir path or run_metadata.json path")
    parser.add_argument("--candidate-run", required=True, help="Candidate run dir path or run_metadata.json path")
    parser.add_argument("--output-json", default=None, help="Optional path to write comparison json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    baseline_path = _resolve_metadata_path(args.baseline_run)
    candidate_path = _resolve_metadata_path(args.candidate_run)

    baseline_md = _load_json(baseline_path)
    candidate_md = _load_json(candidate_path)
    payload = build_comparison(baseline_metadata=baseline_md, candidate_metadata=candidate_md)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_s06", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_text(path: Path, content: str = "ok") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _split_metrics(brier: float, logloss: float, auc: float) -> dict:
    return {
        "Train": {"brier": brier - 0.01, "logloss": logloss - 0.01, "auc": auc + 0.01},
        "Val": {"brier": brier - 0.005, "logloss": logloss - 0.005, "auc": auc + 0.005},
        "Test": {"brier": brier, "logloss": logloss, "auc": auc},
    }


def _calibration_summary(ece: float, wmae: float, high_gap: float) -> dict:
    split_payload = {
        "sample_count": 100,
        "non_empty_bins": 8,
        "ece": ece,
        "wmae": wmae,
        "reason": None,
        "high_prob_band": {
            "threshold": 0.8,
            "sample_count": 20,
            "pred_mean": 0.87,
            "actual_rate": 0.81,
            "gap": high_gap,
            "reason": None,
        },
    }
    return {"Train": split_payload, "Val": split_payload, "Test": split_payload}


def _build_context(tmp_path: Path, *, run_id: str, seed: int, git_commit: str, men_brier: float, women_brier: float, men_ece: float, women_ece: float) -> dict:
    artifacts_root = tmp_path / "runs"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = _write_json(run_dir / "run_metadata.json", {"run_id": run_id, "status": "running"})
    events_path = _write_text(run_dir / "stage_events.jsonl", "{}\n")

    men_model = _write_text(tmp_path / "models" / f"men_{run_id}.pkl")
    women_model = _write_text(tmp_path / "models" / f"women_{run_id}.pkl")
    men_features = _write_text(tmp_path / "data" / f"men_{run_id}.csv")
    women_features = _write_text(tmp_path / "data" / f"women_{run_id}.csv")

    eval_report = _write_json(run_dir / "eval_report.json", {"ok": True})
    calibration_bins = _write_text(run_dir / "calibration_bins.csv", "gender,split\n")
    calibration_report = _write_json(run_dir / "calibration_report.json", {"ok": True})
    governance_ledger = _write_text(run_dir / "governance_ledger.csv", "feature,group\n")
    ablation_report = _write_json(run_dir / "ablation_report.json", {"ok": True})

    stage_outputs = {
        "feature": {
            "outputs": {
                "men_features": str(men_features),
                "women_features": str(women_features),
            }
        },
        "train": {
            "metrics_by_split": {
                "men": _split_metrics(men_brier, 0.55, 0.75),
                "women": _split_metrics(women_brier, 0.57, 0.73),
            },
            "genders": {
                "men": {"model_path": str(men_model)},
                "women": {"model_path": str(women_model)},
            },
        },
        "eval_report": {
            "eval_report": str(eval_report),
            "calibration": {
                "bins_csv": str(calibration_bins),
                "report_json": str(calibration_report),
                "calibration_summary": {
                    "men": _calibration_summary(men_ece, men_ece, 0.04),
                    "women": _calibration_summary(women_ece, women_ece, 0.03),
                },
            },
            "governance": {
                "artifacts": {
                    "ledger_csv": str(governance_ledger),
                    "ablation_report_json": str(ablation_report),
                },
                "summary": {
                    "executed_group_count": 1,
                    "skipped_groups": [],
                },
            },
        },
    }

    return {
        "run_id": run_id,
        "seed": seed,
        "git_commit": git_commit,
        "artifacts_root": str(artifacts_root),
        "run_dir": str(run_dir),
        "metadata_path": str(metadata_path),
        "stage_events_path": str(events_path),
        "stage_outputs": stage_outputs,
    }


def _write_baseline_run(tmp_path: Path, *, run_id: str, seed: int, git_commit: str, men_brier: float, women_brier: float, men_ece: float, women_ece: float):
    context = _build_context(
        tmp_path,
        run_id=run_id,
        seed=seed,
        git_commit=git_commit,
        men_brier=men_brier,
        women_brier=women_brier,
        men_ece=men_ece,
        women_ece=women_ece,
    )

    baseline_metadata = {
        "run_id": run_id,
        "status": "succeeded",
        "seed": seed,
        "git_commit": git_commit,
        "stage_outputs": context["stage_outputs"],
    }
    _write_json(Path(context["run_dir"]) / "run_metadata.json", baseline_metadata)


def test_stage_artifact_writes_contract_reports_with_skip_without_baseline(tmp_path):
    module = _load_module()
    context = _build_context(
        tmp_path,
        run_id="20260315T000100Z_s06_current",
        seed=42,
        git_commit="abc123",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.03,
        women_ece=0.04,
    )

    result = module.stage_artifact(context)

    assert Path(result["manifest"]).exists()
    assert result["artifact_contract"]["status"] == "passed"
    assert result["reproducibility"]["status"] == "skipped"
    assert result["regression_gate"]["status"] == "skipped"

    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    assert manifest["contracts"]["artifact_contract"]["status"] == "passed"
    assert manifest["contracts"]["reproducibility"]["status"] == "skipped"


def test_stage_artifact_fails_when_reproducibility_tolerance_breaches(tmp_path):
    module = _load_module()

    _write_baseline_run(
        tmp_path,
        run_id="20260315T000000Z_s06_baseline",
        seed=42,
        git_commit="abc123",
        men_brier=0.10,
        women_brier=0.10,
        men_ece=0.02,
        women_ece=0.02,
    )

    context = _build_context(
        tmp_path,
        run_id="20260315T000100Z_s06_current",
        seed=42,
        git_commit="abc123",
        men_brier=0.30,
        women_brier=0.30,
        men_ece=0.03,
        women_ece=0.03,
    )

    with pytest.raises(RuntimeError, match="reproducibility gate failed"):
        module.stage_artifact(context)


def test_stage_artifact_fails_when_regression_gate_detects_calibration_degradation(tmp_path):
    module = _load_module()

    _write_baseline_run(
        tmp_path,
        run_id="20260315T000000Z_s06_baseline",
        seed=11,
        git_commit="older",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.02,
        women_ece=0.02,
    )

    context = _build_context(
        tmp_path,
        run_id="20260315T000100Z_s06_current",
        seed=42,
        git_commit="newer",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.05,
        women_ece=0.06,
    )

    with pytest.raises(RuntimeError, match="regression gate failed"):
        module.stage_artifact(context)

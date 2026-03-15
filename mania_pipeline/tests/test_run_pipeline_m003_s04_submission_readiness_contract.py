import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m003_s04", SCRIPT_PATH)
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
            "actual_rate": 0.82,
            "gap": high_gap,
            "reason": None,
        },
    }
    return {"Train": split_payload, "Val": split_payload, "Test": split_payload}


def _build_context(
    tmp_path: Path,
    *,
    run_id: str,
    seed: int,
    git_commit: str,
    submission_stage: str,
    men_brier: float,
    women_brier: float,
    men_ece: float,
    women_ece: float,
) -> dict:
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
    drift_report = _write_json(run_dir / "drift_regime_report.json", {"ok": True})
    calibration_policy_report = _write_json(run_dir / "calibration_policy_report.json", {"ok": True})
    ensemble_report = _write_json(run_dir / "ensemble_report.json", {"ok": True})
    governance_ledger = _write_text(run_dir / "governance_ledger.csv", "feature,group\n")
    governance_decision_report = _write_json(run_dir / "governance_decision_report.json", {"ok": True})
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
            "drift": {
                "report_json": str(drift_report),
                "by_gender": {
                    "men": {"splits": {}, "regimes": {}},
                    "women": {"splits": {}, "regimes": {}},
                },
                "alerts": [],
            },
            "calibration_policy": {
                "report_json": str(calibration_policy_report),
                "policy_name": "regime_aware_calibration_v1",
                "config": {},
                "by_gender": {
                    "men": {"selected_method": "none", "candidate_methods": {}},
                    "women": {"selected_method": "none", "candidate_methods": {}},
                },
            },
            "ensemble": {
                "report_json": str(ensemble_report),
                "aggregate": {"decision": "hold_baseline", "promoted_genders": []},
                "by_gender": {
                    "men": {"selected_candidate_id": "baseline"},
                    "women": {"selected_candidate_id": "baseline"},
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
            "governance_decision": {
                "report_json": str(governance_decision_report),
                "by_gender": {
                    "men": {
                        "decision": "hold_baseline",
                        "confidence": 0.50,
                        "reason_codes": [],
                        "evidence_bundle": {
                            "calibration_policy": {
                                "test_brier_improvement_vs_none": 0.0,
                            }
                        },
                    },
                    "women": {
                        "decision": "hold_baseline",
                        "confidence": 0.50,
                        "reason_codes": [],
                        "evidence_bundle": {
                            "calibration_policy": {
                                "test_brier_improvement_vs_none": 0.0,
                            }
                        },
                    },
                },
                "aggregate": {"decision": "hold_baseline", "reason_codes": []},
            },
        },
    }

    return {
        "run_id": run_id,
        "seed": seed,
        "git_commit": git_commit,
        "submission_stage": submission_stage,
        "artifacts_root": str(artifacts_root),
        "run_dir": str(run_dir),
        "metadata_path": str(metadata_path),
        "stage_events_path": str(events_path),
        "stage_outputs": stage_outputs,
    }


def _write_baseline_metadata(context: dict):
    baseline_metadata = {
        "run_id": context["run_id"],
        "status": "succeeded",
        "seed": context["seed"],
        "git_commit": context["git_commit"],
        "stage_outputs": context["stage_outputs"],
    }
    _write_json(Path(context["run_dir"]) / "run_metadata.json", baseline_metadata)


def test_stage_artifact_emits_caution_readiness_when_submission_not_requested(tmp_path):
    module = _load_module()

    context = _build_context(
        tmp_path,
        run_id="20260315T040100Z_m003_s04_caution",
        seed=42,
        git_commit="abc123",
        submission_stage="none",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.03,
        women_ece=0.03,
    )

    result = module.stage_artifact(context)
    readiness_path = Path(result["readiness"]["report_json"])
    assert readiness_path.exists()

    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    assert readiness["status"] == "caution"
    assert "submission_not_requested" in readiness["warnings"]


def test_stage_artifact_writes_readiness_blocked_before_raising_regression_failure(tmp_path):
    module = _load_module()

    baseline_context = _build_context(
        tmp_path,
        run_id="20260315T040000Z_m003_s04_baseline_blocked",
        seed=42,
        git_commit="abc123",
        submission_stage="none",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.02,
        women_ece=0.02,
    )
    _write_baseline_metadata(baseline_context)

    current_context = _build_context(
        tmp_path,
        run_id="20260315T040300Z_m003_s04_blocked",
        seed=42,
        git_commit="newer",
        submission_stage="none",
        men_brier=0.18,
        women_brier=0.20,
        men_ece=0.02,
        women_ece=0.06,
    )

    with pytest.raises(RuntimeError, match="regression gate failed"):
        module.stage_artifact(current_context)

    readiness_path = Path(current_context["run_dir"]) / "submission_readiness_report.json"
    assert readiness_path.exists()
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    assert readiness["status"] == "blocked"
    assert "regression_gate_failed" in readiness["blocking_checks"]


def test_stage_artifact_emits_ready_readiness_when_submission_and_gates_pass(tmp_path, monkeypatch):
    module = _load_module()

    baseline_context = _build_context(
        tmp_path,
        run_id="20260315T040000Z_m003_s04_baseline",
        seed=42,
        git_commit="abc123",
        submission_stage="none",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.03,
        women_ece=0.03,
    )
    _write_baseline_metadata(baseline_context)

    sample_dir = tmp_path / "kaggle"
    sample_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"ID": ["2026_1101_1102", "2026_1103_1104"], "Pred": [0.5, 0.5]}).to_csv(
        sample_dir / "SampleSubmissionStage2.csv", index=False
    )
    monkeypatch.setattr(module, "KAGGLE_DATA_DIR", sample_dir, raising=False)

    current_context = _build_context(
        tmp_path,
        run_id="20260315T040200Z_m003_s04_ready",
        seed=42,
        git_commit="abc123",
        submission_stage="stage2",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.03,
        women_ece=0.03,
    )

    result = module.stage_artifact(current_context)
    readiness = json.loads(Path(result["readiness"]["report_json"]).read_text(encoding="utf-8"))

    assert readiness["status"] == "ready"
    assert readiness["blocking_checks"] == []
    assert readiness["checks"]["submission"]["status"] == "passed"
    assert result["submission"]["status"] == "passed"

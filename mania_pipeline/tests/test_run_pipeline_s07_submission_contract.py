import importlib.util
import json
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_s07", SCRIPT_PATH)
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


def _build_context(tmp_path: Path, run_id: str, submission_stage: str = "none") -> dict:
    artifacts_root = tmp_path / "runs"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = _write_json(run_dir / "run_metadata.json", {"run_id": run_id, "status": "running"})
    events_path = _write_text(run_dir / "stage_events.jsonl", "{}\n")

    men_model = _write_text(tmp_path / "models" / "men.pkl")
    women_model = _write_text(tmp_path / "models" / "women.pkl")
    men_features = _write_text(tmp_path / "data" / "men.csv")
    women_features = _write_text(tmp_path / "data" / "women.csv")

    eval_report = _write_json(run_dir / "eval_report.json", {"ok": True})
    calibration_bins = _write_text(run_dir / "calibration_bins.csv", "gender,split\n")
    calibration_report = _write_json(
        run_dir / "calibration_report.json",
        {
            "calibration_summary": {
                "men": {
                    "Test": {
                        "ece": 0.03,
                        "wmae": 0.03,
                        "reason": None,
                        "high_prob_band": {"gap": 0.04, "reason": None},
                    }
                },
                "women": {
                    "Test": {
                        "ece": 0.03,
                        "wmae": 0.03,
                        "reason": None,
                        "high_prob_band": {"gap": 0.03, "reason": None},
                    }
                },
            }
        },
    )
    drift_report = _write_json(run_dir / "drift_regime_report.json", {"ok": True})
    calibration_policy_report = _write_json(run_dir / "calibration_policy_report.json", {"ok": True})
    governance_ledger = _write_text(run_dir / "governance_ledger.csv", "feature,group\n")
    governance_decision_report = _write_json(run_dir / "governance_decision_report.json", {"ok": True})
    ablation_report = _write_json(run_dir / "ablation_report.json", {"ok": True})

    return {
        "run_id": run_id,
        "seed": 42,
        "git_commit": "abc123",
        "submission_stage": submission_stage,
        "artifacts_root": str(artifacts_root),
        "run_dir": str(run_dir),
        "metadata_path": str(metadata_path),
        "stage_events_path": str(events_path),
        "stage_outputs": {
            "feature": {
                "outputs": {
                    "men_features": str(men_features),
                    "women_features": str(women_features),
                }
            },
            "train": {
                "metrics_by_split": {
                    "men": {"Test": {"brier": 0.18, "logloss": 0.55, "auc": 0.75}},
                    "women": {"Test": {"brier": 0.16, "logloss": 0.53, "auc": 0.77}},
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
                        "men": {
                            "Test": {
                                "ece": 0.03,
                                "wmae": 0.03,
                                "reason": None,
                                "high_prob_band": {"gap": 0.04, "reason": None},
                            }
                        },
                        "women": {
                            "Test": {
                                "ece": 0.03,
                                "wmae": 0.03,
                                "reason": None,
                                "high_prob_band": {"gap": 0.03, "reason": None},
                            }
                        },
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
                "governance": {
                    "artifacts": {
                        "ledger_csv": str(governance_ledger),
                        "ablation_report_json": str(ablation_report),
                    }
                },
                "governance_decision": {
                    "report_json": str(governance_decision_report),
                    "by_gender": {
                        "men": {"decision": "hold_baseline", "confidence": 0.5, "reason_codes": []},
                        "women": {"decision": "hold_baseline", "confidence": 0.5, "reason_codes": []},
                    },
                    "aggregate": {"decision": "hold_baseline", "reason_codes": []},
                },
            },
        },
    }


def test_stage_artifact_submission_skips_when_not_requested(tmp_path):
    module = _load_module()
    context = _build_context(tmp_path, run_id="20260315T010000Z_s07_skip", submission_stage="none")

    result = module.stage_artifact(context)

    assert result["submission"]["status"] == "skipped"
    report_path = Path(result["submission"]["validation_report_json"])
    assert report_path.exists()


def test_stage_artifact_generates_submission_and_validates_schema(tmp_path, monkeypatch):
    module = _load_module()

    sample_dir = tmp_path / "kaggle"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample = pd.DataFrame({"ID": ["2026_1101_1102", "2026_1103_1104"], "Pred": [0.5, 0.5]})
    sample.to_csv(sample_dir / "SampleSubmissionStage2.csv", index=False)

    monkeypatch.setattr(module, "KAGGLE_DATA_DIR", sample_dir, raising=False)

    context = _build_context(tmp_path, run_id="20260315T010100Z_s07_stage2", submission_stage="stage2")
    result = module.stage_artifact(context)

    submission = result["submission"]
    assert submission["status"] == "passed"
    assert submission["stage"] == "stage2"

    submission_path = Path(submission["submission_csv"])
    assert submission_path.exists()

    frame = pd.read_csv(submission_path)
    assert list(frame.columns) == ["ID", "Pred"]
    assert frame["Pred"].between(0.0, 1.0).all()

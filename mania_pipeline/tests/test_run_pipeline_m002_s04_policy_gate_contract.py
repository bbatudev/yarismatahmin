import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m002_s04", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_text(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _split_metrics(brier: float, logloss: float, auc: float) -> dict:
    return {
        "Train": {"brier": brier + 0.01, "logloss": logloss + 0.01, "auc": auc - 0.01},
        "Val": {"brier": brier + 0.005, "logloss": logloss + 0.005, "auc": auc - 0.005},
        "Test": {"brier": brier, "logloss": logloss, "auc": auc},
    }


def _calibration_summary(ece: float, wmae: float, high_gap: float) -> dict:
    return {
        "Train": {
            "ece": ece * 0.9,
            "wmae": wmae * 0.9,
            "reason": None,
            "high_prob_band": {"gap": high_gap * 0.9, "reason": None},
        },
        "Val": {
            "ece": ece,
            "wmae": wmae,
            "reason": None,
            "high_prob_band": {"gap": high_gap, "reason": None},
        },
        "Test": {
            "ece": ece,
            "wmae": wmae,
            "reason": None,
            "high_prob_band": {"gap": high_gap, "reason": None},
        },
    }


def _build_context(
    tmp_path: Path,
    *,
    run_id: str,
    seed: int,
    git_commit: str,
    men_brier: float,
    women_brier: float,
    men_ece: float,
    women_ece: float,
    decision: str,
    decision_confidence: float,
    decision_improvement: float,
):
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
                    "men": {
                        "selected_method": "platt",
                        "default_method": "none",
                    },
                    "women": {
                        "selected_method": "platt",
                        "default_method": "none",
                    },
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
                        "decision": decision,
                        "confidence": decision_confidence,
                        "reason_codes": ["calibration_improvement_positive"],
                        "evidence_bundle": {
                            "calibration_policy": {
                                "test_brier_improvement_vs_none": decision_improvement,
                            }
                        },
                    },
                    "women": {
                        "decision": decision,
                        "confidence": decision_confidence,
                        "reason_codes": ["calibration_improvement_positive"],
                        "evidence_bundle": {
                            "calibration_policy": {
                                "test_brier_improvement_vs_none": decision_improvement,
                            }
                        },
                    },
                },
                "aggregate": {
                    "decision": "enforce_calibration_policy",
                    "reason_codes": ["calibration_improvement_positive"],
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
        "submission_stage": "none",
    }


def _write_baseline_run(tmp_path: Path):
    context = _build_context(
        tmp_path,
        run_id="20260315T030000Z_s04_baseline",
        seed=42,
        git_commit="abc123",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.02,
        women_ece=0.02,
        decision="hold_baseline",
        decision_confidence=0.50,
        decision_improvement=0.0,
    )

    baseline_metadata = {
        "run_id": context["run_id"],
        "status": "succeeded",
        "seed": context["seed"],
        "git_commit": context["git_commit"],
        "stage_outputs": context["stage_outputs"],
    }
    _write_json(Path(context["run_dir"]) / "run_metadata.json", baseline_metadata)


def test_stage_artifact_allows_policy_fallback_for_calibration_degradation(tmp_path):
    module = _load_module()

    _write_baseline_run(tmp_path)

    context = _build_context(
        tmp_path,
        run_id="20260315T030100Z_s04_current",
        seed=42,
        git_commit="abc123",
        men_brier=0.18,
        women_brier=0.16,
        men_ece=0.04,
        women_ece=0.05,
        decision="apply_calibration_policy",
        decision_confidence=0.82,
        decision_improvement=0.012,
    )

    result = module.stage_artifact(context)

    assert result["regression_gate"]["status"] == "passed"
    assert result["policy_gate"]["status"] == "passed"

    regression_report = json.loads(Path(result["regression_gate"]["report_json"]).read_text(encoding="utf-8"))
    assert "men:calibration_degraded_policy_fallback" in regression_report.get("warnings", [])
    assert "women:calibration_degraded_policy_fallback" in regression_report.get("warnings", [])
    assert regression_report["by_gender"]["men"]["calibration_rule"]["status"] == "warning"
    assert regression_report["by_gender"]["men"]["policy_gate"]["fallback_applied"] is True

    policy_gate_report = json.loads(Path(result["policy_gate"]["report_json"]).read_text(encoding="utf-8"))
    assert policy_gate_report["aggregate_decision"] == "enforce_calibration_policy"
    assert policy_gate_report["by_gender"]["men"]["policy_fallback_applied"] is True

import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m005_s01", SCRIPT_PATH)
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


def _build_context(
    tmp_path: Path,
    *,
    run_id: str,
    seed: int,
    git_commit: str,
    men_brier: float,
    women_brier: float,
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
    alternative_model_report = _write_json(run_dir / "alternative_model_report.json", {"ok": True})
    blend_candidate_policy_report = _write_json(run_dir / "blend_candidate_policy_report.json", {"ok": True})
    governance_ledger = _write_text(run_dir / "governance_ledger.csv", "feature,group\n")
    governance_decision_report = _write_json(run_dir / "governance_decision_report.json", {"ok": True})
    ablation_report = _write_json(run_dir / "ablation_report.json", {"ok": True})
    error_report = _write_json(run_dir / "error_decomposition_report.json", {"ok": True})

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
                    "men": _calibration_summary(0.03, 0.03, 0.04),
                    "women": _calibration_summary(0.03, 0.03, 0.03),
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
            "alternative_model": {
                "report_json": str(alternative_model_report),
                "aggregate": {"decision": "hold_current_model_family", "promising_genders": []},
                "by_gender": {
                    "men": {"research_decision": "hold_current_model_family"},
                    "women": {"research_decision": "hold_current_model_family"},
                },
            },
            "blend_candidate_policy": {
                "report_json": str(blend_candidate_policy_report),
                "aggregate": {"decision": "hold_research_only", "candidate_ready_genders": []},
                "by_gender": {
                    "men": {"candidate_status": "hold_research_only"},
                    "women": {"candidate_status": "hold_research_only"},
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
                    "men": {"decision": "hold_baseline", "confidence": 0.5, "reason_codes": []},
                    "women": {"decision": "hold_baseline", "confidence": 0.5, "reason_codes": []},
                },
                "aggregate": {"decision": "hold_baseline", "reason_codes": []},
            },
            "error_decomposition": {
                "report_json": str(error_report),
                "by_gender": {
                    "men": {"overall": {"sample_count": 10}},
                    "women": {"overall": {"sample_count": 10}},
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
        run_id="20260315T050000Z_m005_s01_baseline",
        seed=42,
        git_commit="abc123",
        men_brier=0.18,
        women_brier=0.16,
    )
    baseline_metadata = {
        "run_id": context["run_id"],
        "status": "succeeded",
        "seed": context["seed"],
        "git_commit": context["git_commit"],
        "stage_outputs": context["stage_outputs"],
    }
    _write_json(Path(context["run_dir"]) / "run_metadata.json", baseline_metadata)


def _write_backtest_report(path: Path) -> Path:
    payload = {
        "generated_at": "2026-03-15T00:40:14.896873Z",
        "by_gender": {
            "men": {
                "rows": [
                    {"season": 2018, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.20995}},
                    {"season": 2019, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.18064}},
                    {"season": 2022, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.22894}},
                    {"season": 2023, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.20961}},
                    {"season": 2024, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.20629}},
                    {"season": 2025, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.15861}},
                ]
            },
            "women": {
                "rows": [
                    {"season": 2018, "status": "passed", "row_counts": {"test": 126}, "metrics": {"test_brier": 0.16350}},
                    {"season": 2019, "status": "passed", "row_counts": {"test": 126}, "metrics": {"test_brier": 0.13377}},
                    {"season": 2022, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.18414}},
                    {"season": 2023, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.17721}},
                    {"season": 2024, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.13818}},
                    {"season": 2025, "status": "passed", "row_counts": {"test": 134}, "metrics": {"test_brier": 0.13936}},
                ]
            },
        },
    }
    return _write_json(path, payload)


def test_stage_artifact_emits_multi_season_weighted_promotion_gate_report(tmp_path):
    module = _load_module()

    _write_baseline_run(tmp_path)
    backtest_report = _write_backtest_report(tmp_path / "reports" / "season_backtest.json")

    context = _build_context(
        tmp_path,
        run_id="20260315T050100Z_m005_s01_current",
        seed=42,
        git_commit="newer",
        men_brier=0.18,
        women_brier=0.1421,
    )
    context["season_backtest_report"] = str(backtest_report)

    result = module.stage_artifact(context)

    payload = result["weighted_promotion_gate"]
    report_path = Path(payload["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["aggregate"]["decision"] in {"hold_baseline", "promote_candidate"}
    assert set(report["by_gender"].keys()) == {"men", "women"}
    assert report["by_gender"]["men"]["weighted_historical_mean_brier"] is not None
    assert report["by_gender"]["women"]["current_test_brier"] == 0.1421
    assert report["aggregate"]["decision"] == "hold_baseline"

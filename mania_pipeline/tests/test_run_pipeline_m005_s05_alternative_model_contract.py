import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class AlternativeBenchmarkProbModel:
    def __init__(self, feature_columns: list[str], weights: dict[str, float], bias: float = 0.0):
        self.feature_columns = list(feature_columns)
        self.weights = dict(weights)
        self.bias = float(bias)
        self.feature_importances_ = np.asarray(
            [abs(self.weights.get(column, 1.0)) for column in self.feature_columns],
            dtype=float,
        )

    def predict_proba(self, X):
        score = np.full(len(X), self.bias, dtype=float)
        for column in self.feature_columns:
            score += np.asarray(X[column], dtype=float) * float(self.weights.get(column, 0.0))
        probs = 1.0 / (1.0 + np.exp(-score))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m005_s05", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_model(path: Path, model: AlternativeBenchmarkProbModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(model, handle)
    return path


def _write_feature_csv(path: Path) -> Path:
    rows = []
    seed_values = [1.7, -1.6, 1.5, -1.4, 1.2, -1.1, 1.0, -0.9, 0.8, -0.7, 0.6, -0.5, 0.4, -0.3]
    for idx, seed_diff in enumerate(seed_values, start=1):
        if idx <= 6:
            split = "Train"
            season = 2022
        elif idx <= 10:
            split = "Val"
            season = 2023
        else:
            split = "Test"
            season = 2024
        rows.append(
            {
                "Season": season,
                "TeamA": idx,
                "TeamB": idx + 100,
                "Target": 1 if seed_diff > 0 else 0,
                "Split": split,
                "SeedNum_diff": seed_diff,
                "NetRtg_diff": seed_diff * 0.8,
                "PythWR_diff": seed_diff * 0.7,
                "Luck_diff": seed_diff * 0.3,
            }
        )
    frame = pd.DataFrame(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _metrics(base_brier: float) -> dict:
    return {
        "Train": {"brier": base_brier - 0.02, "logloss": 0.50, "auc": 0.78},
        "Val": {"brier": base_brier - 0.01, "logloss": 0.54, "auc": 0.75},
        "Test": {"brier": base_brier, "logloss": 0.58, "auc": 0.73},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_features = _write_feature_csv(data_dir / "processed_features_men.csv")
    women_features = _write_feature_csv(data_dir / "processed_features_women.csv")

    feature_columns = ["SeedNum_diff", "NetRtg_diff", "PythWR_diff", "Luck_diff"]
    men_model_path = _write_model(
        model_dir / "men.pkl",
        AlternativeBenchmarkProbModel(feature_columns, weights={"SeedNum_diff": 1.4, "NetRtg_diff": 0.4}, bias=-0.2),
    )
    women_model_path = _write_model(
        model_dir / "women.pkl",
        AlternativeBenchmarkProbModel(feature_columns, weights={"SeedNum_diff": 1.2, "PythWR_diff": 0.3}, bias=-0.1),
    )

    return {
        "run_id": "m005_s05_alternative_model_contract",
        "seed": 42,
        "run_dir": str(run_dir),
        "prediction_policy": "men_external_prior_policy_v1",
        "stage_outputs": {
            "feature": {
                "outputs": {
                    "men_features": str(men_features),
                    "women_features": str(women_features),
                }
            },
            "train": {
                "models": {
                    "men": str(men_model_path),
                    "women": str(women_model_path),
                },
                "metrics_by_split": {
                    "men": _metrics(0.22),
                    "women": _metrics(0.21),
                },
                "feature_snapshot": {
                    "men": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                    "women": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                        "metrics_by_split": _metrics(0.22),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                        "metrics_by_split": _metrics(0.21),
                    },
                },
                "hpo": {
                    "status": "skipped",
                    "report_json": str(run_dir / "hpo_report.json"),
                    "target_profile": "quality_v1",
                    "trials_requested": 0,
                    "trials_executed": 0,
                },
            },
        },
    }


def test_stage_eval_report_emits_alternative_model_benchmark_contract(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "CALIBRATION_POLICY_MIN_VAL_SAMPLES", 2, raising=False)
    monkeypatch.setattr(
        module,
        "_build_ensemble_report",
        lambda **kwargs: {"report_json": str(Path(kwargs["context"]["run_dir"]) / "ensemble_report.json"), "aggregate": {"decision": "hold_baseline"}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_build_feature_branch_report",
        lambda **kwargs: {"report_json": str(Path(kwargs["context"]["run_dir"]) / "feature_branch_report.json"), "aggregate": {"decision": "hold_current_feature_branch"}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_build_stacking_policy_report",
        lambda **kwargs: {"report_json": str(Path(kwargs["context"]["run_dir"]) / "stacking_policy_report.json"), "aggregate": {"decision": "hold_current_policy"}},
        raising=False,
    )

    context = _build_context(tmp_path)
    result = module.stage_eval_report(context)

    payload = result["alternative_model"]
    report_path = Path(payload["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["policy_name"] == "alternative_model_benchmark_v1"
    assert set(report["by_gender"].keys()) == {"men", "women"}

    for gender_key in ("men", "women"):
        gender_payload = report["by_gender"][gender_key]
        candidate_ids = {candidate["candidate_id"] for candidate in gender_payload["candidates"]}
        assert "baseline" in candidate_ids
        assert "histgb_benchmark" in candidate_ids
        assert "logistic_benchmark" in candidate_ids
        assert "spline_logistic_benchmark" in candidate_ids
        assert "xgboost_benchmark" in candidate_ids
        assert "catboost_benchmark" in candidate_ids
        assert "tabpfn_benchmark" in candidate_ids
        assert "diversity" in gender_payload
        assert "val" in gender_payload["diversity"]
        assert "test" in gender_payload["diversity"]
        assert "selection" in gender_payload
        assert "selected_candidate_id" in gender_payload["selection"]
        assert gender_payload["research_decision"] in {
            "promising_diversity_candidate",
            "hold_current_model_family",
            "not_promising",
            "insufficient_data",
        }

    assert "candidate_ready_genders" in report["aggregate"]

    eval_report = json.loads(Path(result["eval_report"]).read_text(encoding="utf-8"))
    assert eval_report["alternative_model"]["report_json"] == str(report_path)
    men_combo_report_path = Path(result["men_combo_followup"]["report_json"])
    assert men_combo_report_path.exists()
    men_combo_report = json.loads(men_combo_report_path.read_text(encoding="utf-8"))
    assert men_combo_report["policy_name"] == "men_combo_followup_v1"
    assert men_combo_report["research_decision"] in {
        "promising_local_gate_candidate",
        "hold_current_combo_shortlist",
        "insufficient_data",
    }
    assert isinstance(men_combo_report["candidates"], list)
    assert eval_report["men_combo_followup"]["report_json"] == str(men_combo_report_path)
    men_tabpfn_report_path = Path(result["men_tabpfn_followup"]["report_json"])
    assert men_tabpfn_report_path.exists()
    men_tabpfn_report = json.loads(men_tabpfn_report_path.read_text(encoding="utf-8"))
    assert men_tabpfn_report["policy_name"] == "men_tabpfn_followup_v1"
    assert men_tabpfn_report["research_decision"] in {
        "promising_tabpfn_followup_candidate",
        "hold_reference_candidate",
        "insufficient_data",
    }
    assert isinstance(men_tabpfn_report["candidates"], list)
    assert eval_report["men_tabpfn_followup"]["report_json"] == str(men_tabpfn_report_path)
    men_gate_aware_report_path = Path(result["men_gate_aware_search"]["report_json"])
    assert men_gate_aware_report_path.exists()
    men_gate_aware_report = json.loads(men_gate_aware_report_path.read_text(encoding="utf-8"))
    assert men_gate_aware_report["policy_name"] == "men_gate_aware_search_v1"
    assert men_gate_aware_report["research_decision"] in {
        "promising_gate_aware_candidate",
        "hold_current_reference",
        "insufficient_data",
    }
    assert isinstance(men_gate_aware_report["candidates"], list)
    assert eval_report["men_gate_aware_search"]["report_json"] == str(men_gate_aware_report_path)
    assert eval_report["prediction_policy"]["selected_policy"] in {
        "men_external_prior_policy_v1",
        "blend_candidate_v1",
        "blend_final_recipe_v1",
        "mixed_with_baseline_fallback",
    }
    blend_policy_report_path = Path(result["blend_candidate_policy"]["report_json"])
    assert blend_policy_report_path.exists()
    blend_policy_report = json.loads(blend_policy_report_path.read_text(encoding="utf-8"))
    assert blend_policy_report["policy_name"] == "blend_candidate_policy_v1"
    assert "aggregate" in blend_policy_report
    assert "candidate_ready_genders" in blend_policy_report["aggregate"]
    assert eval_report["blend_candidate_policy"]["report_json"] == str(blend_policy_report_path)
    final_blend_recipe_report_path = Path(result["final_blend_recipe"]["report_json"])
    assert final_blend_recipe_report_path.exists()
    final_blend_recipe_report = json.loads(final_blend_recipe_report_path.read_text(encoding="utf-8"))
    assert final_blend_recipe_report["policy_name"] == "blend_final_recipe_v1"
    assert final_blend_recipe_report["aggregate"]["decision"] == "explicit_final_recipe"
    assert eval_report["final_blend_recipe"]["report_json"] == str(final_blend_recipe_report_path)
    men_policy_report_path = Path(result["men_policy_refinement"]["report_json"])
    assert men_policy_report_path.exists()
    men_policy_report = json.loads(men_policy_report_path.read_text(encoding="utf-8"))
    assert men_policy_report["policy_name"] == "men_regime_policy_research_v1"
    assert men_policy_report["status"] == "passed"
    assert isinstance(men_policy_report["candidates"], list)
    assert eval_report["men_policy_refinement"]["report_json"] == str(men_policy_report_path)
    men_external_report_path = Path(result["men_external_prior_policy"]["report_json"])
    assert men_external_report_path.exists()
    men_external_report = json.loads(men_external_report_path.read_text(encoding="utf-8"))
    assert men_external_report["policy_name"] == "men_external_prior_policy_research_v1"
    assert men_external_report["status"] == "passed"
    assert isinstance(men_external_report["candidates"], list)
    assert eval_report["men_external_prior_policy"]["report_json"] == str(men_external_report_path)
    men_residual_report_path = Path(result["men_residual_correction"]["report_json"])
    assert men_residual_report_path.exists()
    men_residual_report = json.loads(men_residual_report_path.read_text(encoding="utf-8"))
    assert men_residual_report["policy_name"] == "men_residual_correction_research_v1"
    assert men_residual_report["status"] == "passed"
    assert isinstance(men_residual_report["candidates"], list)
    assert eval_report["men_residual_correction"]["report_json"] == str(men_residual_report_path)
    men_regime_report_path = Path(result["men_regime_routing"]["report_json"])
    assert men_regime_report_path.exists()
    men_regime_report = json.loads(men_regime_report_path.read_text(encoding="utf-8"))
    assert men_regime_report["policy_name"] == "men_regime_routing_research_v1"
    assert men_regime_report["status"] == "passed"
    assert isinstance(men_regime_report["candidates"], list)
    assert isinstance(men_regime_report["regime_selection"], dict)
    assert eval_report["men_regime_routing"]["report_json"] == str(men_regime_report_path)
    for gender_key in ("men", "women"):
        eval_weights = eval_report["prediction_policy"]["by_gender"][gender_key].get("blend_weights")
        policy_weights = blend_policy_report["by_gender"][gender_key].get("selected_candidate_weights")
        if eval_report["prediction_policy"]["by_gender"][gender_key]["selected_policy"] in {
            "blend_candidate_v1",
            "men_external_prior_policy_v1",
        } and policy_weights is not None:
            assert eval_weights == policy_weights
        if eval_report["prediction_policy"]["by_gender"][gender_key]["selected_policy"] == "blend_final_recipe_v1":
            assert eval_weights == final_blend_recipe_report["by_gender"][gender_key]["selected_candidate_weights"]


def test_final_blend_recipe_promotes_men_tabpfn_gate_ready_candidate(tmp_path):
    module = _load_module()
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_tabpfn_report_path = run_dir / "men_tabpfn_followup_report.json"
    men_tabpfn_report_path.write_text(
        json.dumps(
            {
                "reference_weights": {"baseline": 0.75, "histgb_benchmark": 0.25},
                "candidates": [
                    {
                        "candidate_id": "tabpfn_raw",
                        "status": "available",
                        "raw_metrics": {
                            "val": {"brier": 0.2148},
                            "test": {"brier": 0.1703},
                        },
                        "raw_local_gate_check_vs_baseline": {"status": "passed"},
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    alternative_model_payload = {
        "by_gender": {
            "men": {
                "selection": {
                    "selected_candidate_id": "baseline_histgb_spline_logistic_blend",
                    "selected_candidate_weights": {
                        "baseline": 0.4,
                        "histgb_benchmark": 0.2,
                        "spline_logistic_benchmark": 0.4,
                    },
                },
                "candidates": [
                    {
                        "candidate_id": "baseline",
                        "status": "available",
                        "metrics": {
                            "test": {
                                "brier": 0.1779,
                                "ece": 0.0366,
                                "wmae": 0.0366,
                                "high_prob_gap": -0.0383,
                            }
                        },
                    },
                    {
                        "candidate_id": "baseline_histgb_spline_logistic_blend",
                        "status": "available",
                        "metrics": {
                            "test": {
                                "brier": 0.1760,
                                "ece": 0.0464,
                                "wmae": 0.0464,
                                "high_prob_gap": -0.0539,
                            }
                        },
                    },
                ],
            },
            "women": {
                "selection": {
                    "selected_candidate_id": "spline_logistic_benchmark",
                    "selected_candidate_weights": {"spline_logistic_benchmark": 1.0},
                },
                "candidates": [],
            },
        }
    }

    result = module._build_final_blend_recipe_report(
        context={"run_id": "unit_final_recipe", "seed": 42, "run_dir": str(run_dir)},
        alternative_model_payload=alternative_model_payload,
        men_tabpfn_followup_payload={"report_json": str(men_tabpfn_report_path)},
    )

    report = json.loads(Path(result["report_json"]).read_text(encoding="utf-8"))
    assert report["by_gender"]["men"]["selected_candidate_id"] == "tabpfn_benchmark"
    assert report["by_gender"]["men"]["selected_candidate_weights"] == {"tabpfn_benchmark": 1.0}
    assert report["by_gender"]["men"]["selection_source"] == "men_tabpfn_followup"
    assert report["by_gender"]["women"]["selected_candidate_id"] == "spline_logistic_benchmark"

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m004_s03", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ensemble_promotion_blocks_when_test_brier_degrades(monkeypatch):
    module = _load_module()

    baseline_split_probabilities = {
        "Val": {
            "y_true": np.asarray([0.0, 1.0], dtype=float),
            "y_prob": np.asarray([0.8, 0.2], dtype=float),
        },
        "Test": {
            "y_true": np.asarray([0.0, 1.0], dtype=float),
            "y_prob": np.asarray([0.1, 0.9], dtype=float),
        },
    }

    feature_df = pd.DataFrame(
        {
            "Split": ["Train", "Train", "Val", "Val", "Test", "Test"],
            "Target": [1, 0, 0, 1, 0, 1],
            "SeedNum_diff": [0.2, -0.2, 0.3, -0.3, 0.4, -0.4],
            "NetRtg_diff": [0.1, -0.1, 0.2, -0.2, 0.3, -0.3],
            "Season": [2022, 2022, 2023, 2023, 2024, 2024],
            "TeamA": [1, 2, 3, 4, 5, 6],
            "TeamB": [7, 8, 9, 10, 11, 12],
        }
    )

    def _stub_train_with_optional_profile(**kwargs):
        del kwargs
        return object(), {
            "feature_snapshot": {
                "feature_columns": ["SeedNum_diff", "NetRtg_diff"],
                "feature_count": 2,
            }
        }

    def _stub_predict_model_split_probabilities(**kwargs):
        del kwargs
        return {
            "Val": {
                "y_true": np.asarray([0.0, 1.0], dtype=float),
                "y_prob": np.asarray([0.4, 0.6], dtype=float),
            },
            "Test": {
                "y_true": np.asarray([0.0, 1.0], dtype=float),
                "y_prob": np.asarray([0.3, 0.7], dtype=float),
            },
        }

    monkeypatch.setattr(module, "_train_with_optional_profile", _stub_train_with_optional_profile)
    monkeypatch.setattr(module, "_predict_model_split_probabilities", _stub_predict_model_split_probabilities)

    payload = module._evaluate_ensemble_candidates_for_gender(
        context={"seed": 42},
        train_module=object(),
        gender_key="men",
        feature_df=feature_df,
        baseline_split_probabilities=baseline_split_probabilities,
        hpo_gender_payload={"best_param_overrides": {"learning_rate": 0.03}},
        hpo_target_profile="quality_v1",
    )

    assert payload["status"] == "passed"
    assert payload["selected_candidate_id"] == "baseline"
    assert payload["selection_signal"] == "hold_baseline"
    assert payload["selection_reason"] == "test_brier_degraded"

    candidate_ids = {row["candidate_id"] for row in payload["candidates"]}
    assert {"baseline", "hpo_best", "ensemble_weighted"}.issubset(candidate_ids)

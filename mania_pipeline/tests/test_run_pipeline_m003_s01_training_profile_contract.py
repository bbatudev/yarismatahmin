import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class DummyModel:
    def predict_proba(self, X):
        import numpy as np

        probs = np.full(len(X), 0.5, dtype=float)
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m003_s01", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_small_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Split": ["Train", "Train", "Val", "Val", "Test", "Test"],
            "Target": [1, 0, 1, 0, 1, 0],
            "SeedNum_diff": [1, -1, 2, -2, 3, -3],
            "NetRtg_diff": [0.3, -0.3, 0.2, -0.2, 0.1, -0.1],
            "Season": [2022, 2022, 2023, 2023, 2024, 2024],
            "TeamA": [1, 2, 3, 4, 5, 6],
            "TeamB": [7, 8, 9, 10, 11, 12],
        }
    )


def test_parse_args_accepts_training_profile_contract():
    module = _load_module()

    args_default = module.parse_args([])
    assert args_default.training_profile == "baseline"

    args_quality = module.parse_args(["--training-profile", "quality_v1"])
    assert args_quality.training_profile == "quality_v1"


def test_stage_train_propagates_training_profile_to_payload(tmp_path, monkeypatch):
    module = _load_module()

    men_df = _build_small_df()
    women_df = _build_small_df()

    class StubTrainModule:
        DATA_DIR = ""
        OUT_DIR = ""

        @staticmethod
        def load_data(gender="M"):
            return men_df if gender == "M" else women_df

        @staticmethod
        def train_baseline(df, gender="M", random_state=42, profile="baseline"):
            del df, random_state
            return DummyModel(), {
                "gender": gender,
                "training_profile": profile,
                "training_params": {"learning_rate": 0.03 if profile == "quality_v1" else 0.05},
                "metrics_by_split": {
                    "Train": {"brier": 0.2, "logloss": 0.6, "auc": 0.7},
                    "Val": {"brier": 0.21, "logloss": 0.61, "auc": 0.69},
                    "Test": {"brier": 0.22, "logloss": 0.62, "auc": 0.68},
                },
                "feature_snapshot": {"feature_columns": ["SeedNum_diff", "NetRtg_diff"], "feature_count": 2},
                "best_iteration": 10,
            }

    monkeypatch.setattr(module, "_load_script_module", lambda filename, module_name: StubTrainModule, raising=False)
    monkeypatch.setattr(module, "PIPELINE_DIR", tmp_path / "pipeline", raising=False)

    context = {
        "seed": 42,
        "run_id": "m003_s01_profile_contract",
        "training_profile": "quality_v1",
        "stage_outputs": {
            "feature": {
                "gates": {
                    "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                    "women": {"pass": True, "blocking_rule": None, "reason": "ok"},
                }
            }
        },
    }

    result = module.stage_train(context)

    assert result["training_profile"] == "quality_v1"
    assert result["genders"]["men"]["training_profile"] == "quality_v1"
    assert result["genders"]["women"]["training_profile"] == "quality_v1"
    assert result["genders"]["men"]["training_params"]["learning_rate"] == 0.03

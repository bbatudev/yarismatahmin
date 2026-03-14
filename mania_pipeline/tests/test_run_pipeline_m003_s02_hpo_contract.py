import importlib.util
import json
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class DummyModel:
    def predict_proba(self, X):
        import numpy as np

        probs = np.full(len(X), 0.5, dtype=float)
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m003_s02", SCRIPT_PATH)
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


def test_parse_args_accepts_hpo_contract_flags():
    module = _load_module()

    args = module.parse_args(["--hpo-trials", "3", "--hpo-target-profile", "quality_v1"])
    assert args.hpo_trials == 3
    assert args.hpo_target_profile == "quality_v1"


def test_stage_train_emits_reproducible_hpo_report_contract(tmp_path, monkeypatch):
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
        def train_baseline(df, gender="M", random_state=42, profile="baseline", param_overrides=None):
            del df, random_state, profile
            overrides = param_overrides or {}
            lr = float(overrides.get("learning_rate", 0.05))
            leaves = int(overrides.get("num_leaves", 31))
            min_child = int(overrides.get("min_child_samples", 20))

            # deterministic synthetic objective: best around lr=0.03, leaves=47, min_child=15
            val_brier = 0.20 + abs(lr - 0.03) * 0.5 + abs(leaves - 47) * 0.0004 + abs(min_child - 15) * 0.0003
            test_brier = val_brier + 0.01
            payload = {
                "gender": gender,
                "training_profile": "quality_v1",
                "training_params": {"learning_rate": lr, "num_leaves": leaves, "min_child_samples": min_child},
                "metrics_by_split": {
                    "Train": {"brier": val_brier - 0.02, "logloss": 0.55, "auc": 0.75},
                    "Val": {"brier": val_brier, "logloss": 0.60, "auc": 0.72},
                    "Test": {"brier": test_brier, "logloss": 0.62, "auc": 0.70},
                },
                "feature_snapshot": {"feature_columns": ["SeedNum_diff", "NetRtg_diff"], "feature_count": 2},
                "best_iteration": 12,
            }
            return DummyModel(), payload

    monkeypatch.setattr(module, "_load_script_module", lambda filename, module_name: StubTrainModule, raising=False)
    monkeypatch.setattr(module, "PIPELINE_DIR", tmp_path / "pipeline", raising=False)

    def _context(run_id: str) -> dict:
        return {
            "seed": 42,
            "run_id": run_id,
            "run_dir": str(tmp_path / "runs" / run_id),
            "training_profile": "quality_v1",
            "hpo_trials": 4,
            "hpo_target_profile": "quality_v1",
            "stage_outputs": {
                "feature": {
                    "gates": {
                        "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                        "women": {"pass": True, "blocking_rule": None, "reason": "ok"},
                    }
                }
            },
        }

    result1 = module.stage_train(_context("m003_s02_hpo_1"))
    result2 = module.stage_train(_context("m003_s02_hpo_2"))

    assert result1["hpo"]["status"] == "passed"
    assert result1["hpo"]["trials_executed"] == 4
    report_path = Path(result1["hpo"]["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    men_hpo = report["by_gender"]["men"]
    women_hpo = report["by_gender"]["women"]
    assert len(men_hpo["candidates"]) == 4
    assert len(women_hpo["candidates"]) == 4
    assert men_hpo["best_trial_id"] is not None

    report2 = json.loads(Path(result2["hpo"]["report_json"]).read_text(encoding="utf-8"))
    men_first_1 = report["by_gender"]["men"]["candidates"][0]["param_overrides"]
    men_first_2 = report2["by_gender"]["men"]["candidates"][0]["param_overrides"]
    assert men_first_1 == men_first_2

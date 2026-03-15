import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m004_s02", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_df() -> pd.DataFrame:
    # Original split values are used by the first trial pass; CV folds overwrite Split internally.
    return pd.DataFrame(
        {
            "Split": ["Train", "Train", "Train", "Train", "Val", "Val", "Test", "Test"],
            "Season": [2021, 2021, 2022, 2022, 2023, 2023, 2024, 2024],
            "Target": [1, 0, 1, 0, 1, 0, 1, 0],
            "SeedNum_diff": [1.0, -1.0, 1.2, -1.2, 0.8, -0.8, 0.6, -0.6],
            "NetRtg_diff": [0.3, -0.3, 0.2, -0.2, 0.1, -0.1, 0.05, -0.05],
        }
    )


def test_hpo_selection_prefers_cv_objective_over_single_val_brier():
    module = _load_module()
    df = _build_df()

    class StubTrainModule:
        @staticmethod
        def train_baseline(df, gender="M", random_state=42, profile="baseline", param_overrides=None):
            del gender, random_state, profile
            overrides = param_overrides or {}
            lr = float(overrides.get("learning_rate", 0.05))

            val_rows = df[df["Split"] == "Val"]
            val_season = int(val_rows["Season"].iloc[0]) if not val_rows.empty else 2023

            if abs(lr - 0.02) < 1e-9:
                # Looks better on the default Val split (2023), worse on CV fold 2022.
                brier_by_season = {2022: 0.40, 2023: 0.19}
            elif abs(lr - 0.07) < 1e-9:
                # Slightly worse on default Val, but more stable across CV folds.
                brier_by_season = {2022: 0.21, 2023: 0.20}
            else:
                brier_by_season = {2022: 0.30, 2023: 0.30}

            val_brier = float(brier_by_season.get(val_season, 0.30))
            payload = {
                "metrics_by_split": {
                    "Train": {"brier": max(0.0, val_brier - 0.03), "logloss": 0.50, "auc": 0.75},
                    "Val": {"brier": val_brier, "logloss": 0.55, "auc": 0.72},
                    "Test": {"brier": val_brier + 0.01, "logloss": 0.57, "auc": 0.70},
                }
            }
            return object(), payload

    result = module._run_hpo_search_for_gender(
        train_module=StubTrainModule,
        df=df,
        gender_key="men",
        seed=42,
        target_profile="quality_v1",
        trial_overrides=[
            {"learning_rate": 0.02},
            {"learning_rate": 0.07},
        ],
    )

    assert result["status"] == "passed"
    # CV objective should pick trial 2 despite trial 1 having lower single-split val brier on 2023.
    assert result["best_trial_id"] == 2
    assert abs(float(result["best_cv_mean_val_brier"]) - 0.205) < 1e-9

    candidates = {item["trial_id"]: item for item in result["candidates"]}
    assert "cv" in candidates[1]
    assert "rows" in candidates[1]["cv"]
    assert candidates[1]["metrics"]["objective_reason"] in {
        "cv_mean_val_brier",
        "val_brier_plus_gap_penalty",
    }

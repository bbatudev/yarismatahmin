import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class FeatureBranchProbModel:
    def __init__(self, feature_columns: list[str], weights: dict[str, float] | None = None, bias: float = 0.0):
        self.feature_columns = list(feature_columns)
        self.weights = dict(weights or {})
        self.bias = float(bias)
        self.feature_importances_ = np.asarray([abs(self.weights.get(col, 1.0)) for col in self.feature_columns], dtype=float)

    def predict_proba(self, X):
        score = np.full(len(X), self.bias, dtype=float)
        for column in self.feature_columns:
            score += np.asarray(X[column], dtype=float) * float(self.weights.get(column, 1.0))
        probs = 1.0 / (1.0 + np.exp(-score))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m005_s04", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_model(path: Path, model: FeatureBranchProbModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(model, handle)
    return path


def _feature_frame(include_massey: bool) -> pd.DataFrame:
    rows = []
    seed_values = [1.3, -1.2, 1.1, -1.0, 0.9, -0.8, 0.7, -0.6, 0.5, -0.4, 0.3, -0.2]
    for idx, seed_diff in enumerate(seed_values, start=1):
        if idx <= 4:
            split = "Train"
            season = 2022
        elif idx <= 8:
            split = "Val"
            season = 2023
        else:
            split = "Test"
            season = 2024
        row = {
            "Season": season,
            "TeamA": idx,
            "TeamB": idx + 100,
            "Target": 1 if seed_diff > 0 else 0,
            "Split": split,
            "SeedNum_diff": seed_diff,
            "NetRtg_diff": seed_diff * 0.9,
            "PythWR_diff": seed_diff * 1.2,
            "Luck_diff": seed_diff * 0.7,
            "StyleClash_eFG_BlkPct_diff": seed_diff * 0.5,
            "SeedPythMispricing_diff": seed_diff * 0.6,
            "SeedNetRtgMispricing_diff": seed_diff * 0.4,
            "Round_Num": 1 if idx % 2 else 2,
        }
        if include_massey:
            row.update(
                {
                    "MasseyRankStd_diff": seed_diff * 0.3,
                    "MasseyPctSpread_diff": seed_diff * 0.25,
                    "MasseyOrdinalRange_diff": seed_diff * 0.2,
                    "SeedMasseyMispricing_diff": seed_diff * 0.45,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _write_feature_csv(path: Path, include_massey: bool) -> Path:
    frame = _feature_frame(include_massey=include_massey)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _metrics(base_brier: float) -> dict:
    return {
        "Train": {"brier": base_brier - 0.02, "logloss": 0.50, "auc": 0.77},
        "Val": {"brier": base_brier - 0.01, "logloss": 0.54, "auc": 0.75},
        "Test": {"brier": base_brier, "logloss": 0.58, "auc": 0.73},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_features = _write_feature_csv(data_dir / "processed_features_men.csv", include_massey=True)
    women_features = _write_feature_csv(data_dir / "processed_features_women.csv", include_massey=False)

    men_columns = [c for c in _feature_frame(include_massey=True).columns if c not in ("Season", "TeamA", "TeamB", "Target", "Split")]
    women_columns = [c for c in _feature_frame(include_massey=False).columns if c not in ("Season", "TeamA", "TeamB", "Target", "Split")]
    men_model = FeatureBranchProbModel(
        men_columns,
        weights={col: 0.6 for col in men_columns} | {"PythWR_diff": 1.3, "Luck_diff": 1.0},
        bias=0.0,
    )
    women_model = FeatureBranchProbModel(
        women_columns,
        weights={col: 0.6 for col in women_columns} | {"PythWR_diff": 1.2, "Luck_diff": 0.9},
        bias=0.0,
    )
    men_model_path = _write_model(model_dir / "men.pkl", men_model)
    women_model_path = _write_model(model_dir / "women.pkl", women_model)

    return {
        "run_id": "m005_s04_feature_branch_contract",
        "seed": 42,
        "run_dir": str(run_dir),
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
                    "men": _metrics(0.24),
                    "women": _metrics(0.23),
                },
                "feature_snapshot": {
                    "men": {"feature_columns": men_columns, "feature_count": len(men_columns)},
                    "women": {"feature_columns": women_columns, "feature_count": len(women_columns)},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": men_columns, "feature_count": len(men_columns)},
                        "metrics_by_split": _metrics(0.24),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": women_columns, "feature_count": len(women_columns)},
                        "metrics_by_split": _metrics(0.23),
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


def test_stage_eval_report_emits_feature_branch_research_contract(tmp_path, monkeypatch):
    module = _load_module()
    monkeypatch.setattr(module, "CALIBRATION_POLICY_MIN_VAL_SAMPLES", 2, raising=False)
    monkeypatch.setattr(module, "STACKING_POLICY_MIN_VAL_SAMPLES", 2, raising=False)

    class StubTrainModule:
        DATA_DIR = ""
        OUT_DIR = ""
        DROP_COLUMNS = ("Season", "TeamA", "TeamB", "Target", "Split")

        @staticmethod
        def train_baseline(df, gender="M", random_state=42, profile="baseline", param_overrides=None):
            del random_state, profile, param_overrides
            features = [column for column in df.columns if column not in StubTrainModule.DROP_COLUMNS]
            included = set(features)
            weights = {column: 0.5 for column in features}
            bias = -0.2
            if "PythWR_diff" in included:
                weights["PythWR_diff"] = 1.4
                bias += 0.15
            if "Luck_diff" in included:
                weights["Luck_diff"] = 1.2
                bias += 0.15
            if "MasseyPctSpread_diff" in included:
                weights["MasseyPctSpread_diff"] = 0.4
                bias -= 0.05
            model = FeatureBranchProbModel(features, weights=weights, bias=bias)
            base_brier = 0.22 if gender == "M" else 0.21
            if "PythWR_diff" in included and "Luck_diff" in included:
                base_brier -= 0.02
            elif "PythWR_diff" in included or "Luck_diff" in included:
                base_brier -= 0.01
            payload = {
                "gender": gender,
                "training_profile": "baseline",
                "training_params": {"random_state": 42},
                "metrics_by_split": {
                    "Train": {"brier": base_brier - 0.02, "logloss": 0.50, "auc": 0.78},
                    "Val": {"brier": base_brier - 0.01, "logloss": 0.54, "auc": 0.76},
                    "Test": {"brier": base_brier, "logloss": 0.58, "auc": 0.74},
                },
                "feature_snapshot": {
                    "feature_columns": features,
                    "feature_count": len(features),
                },
                "best_iteration": 10,
            }
            return model, payload

    monkeypatch.setattr(module, "_load_script_module", lambda filename, module_name: StubTrainModule, raising=False)
    monkeypatch.setattr(
        module,
        "_build_ensemble_report",
        lambda **kwargs: {"report_json": str(Path(kwargs["context"]["run_dir"]) / "ensemble_report.json"), "aggregate": {"decision": "hold_baseline"}},
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

    payload = result["feature_branch"]
    report_path = Path(payload["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["policy_name"] == "feature_branch_research_v1"
    assert set(report["by_gender"].keys()) == {"men", "women"}

    men_variants = {variant["variant_id"] for variant in report["by_gender"]["men"]["variants"]}
    women_variants = {variant["variant_id"] for variant in report["by_gender"]["women"]["variants"]}
    assert {"legacy_baseline", "pythwr_only", "luck_only", "pythwr_luck", "style_clash_only", "seed_mispricing_only", "luck_seed_mispricing", "full_feature_package"}.issubset(men_variants)
    assert "massey_spread_only" in men_variants
    assert {"legacy_baseline", "pythwr_only", "luck_only", "pythwr_luck", "style_clash_only", "seed_mispricing_only", "luck_seed_mispricing", "full_feature_package"}.issubset(women_variants)
    assert "massey_spread_only" not in women_variants

    eval_report = json.loads(Path(result["eval_report"]).read_text(encoding="utf-8"))
    assert eval_report["feature_branch"]["report_json"] == str(report_path)

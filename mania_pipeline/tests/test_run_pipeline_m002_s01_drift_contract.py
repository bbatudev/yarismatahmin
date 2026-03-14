import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
CANONICAL_SPLITS = ("Train", "Val", "Test")


class DriftProbModel:
    def __init__(self, feature_name: str, bias: float = 0.0):
        self.feature_name = feature_name
        self.feature_importances_ = np.asarray([5.0, 1.0], dtype=float)
        self.bias = float(bias)

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_name], dtype=float) + self.bias
        probs = 1.0 / (1.0 + np.exp(-values))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m002_s01", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pickled_model(path: Path, *, feature_name: str, bias: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(DriftProbModel(feature_name=feature_name, bias=bias), handle)
    return path


def _write_feature_csv(path: Path, rows: list[tuple[str, int, float, int]]) -> Path:
    frame = pd.DataFrame(rows, columns=["Split", "Target", "NetRtg_diff", "SeedNum_diff"])
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _sample_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.18 + offset, "logloss": 0.52 + offset, "auc": 0.74 + offset},
        "Val": {"brier": 0.20 + offset, "logloss": 0.56 + offset, "auc": 0.70 + offset},
        "Test": {"brier": 0.22 + offset, "logloss": 0.60 + offset, "auc": 0.68 + offset},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_model_path = _write_pickled_model(model_dir / "men.pkl", feature_name="NetRtg_diff", bias=0.15)
    women_model_path = _write_pickled_model(model_dir / "women.pkl", feature_name="NetRtg_diff", bias=-0.1)

    men_features_path = _write_feature_csv(
        data_dir / "processed_features_men.csv",
        rows=[
            ("Train", 1, 2.0, 1),
            ("Train", 0, -1.0, 3),
            ("Val", 1, 0.7, 8),
            ("Val", 0, -0.8, 5),
            ("Test", 1, 1.1, 1),
            ("Test", 0, -0.9, 4),
            ("Test", 1, 0.5, 10),
        ],
    )
    women_features_path = _write_feature_csv(
        data_dir / "processed_features_women.csv",
        rows=[
            ("Train", 1, 1.3, 2),
            ("Train", 0, -1.1, 6),
            ("Val", 1, 0.6, 8),
            ("Val", 0, -0.7, 3),
            ("Test", 1, 0.9, 1),
            ("Test", 0, -0.8, 5),
            ("Test", 0, -0.5, 12),
        ],
    )

    return {
        "run_id": "m002_s01_drift_contract",
        "seed": 42,
        "run_dir": str(run_dir),
        "stage_outputs": {
            "feature": {
                "outputs": {
                    "men_features": str(men_features_path),
                    "women_features": str(women_features_path),
                }
            },
            "train": {
                "models": {
                    "men": str(men_model_path),
                    "women": str(women_model_path),
                },
                "metrics_by_split": {
                    "men": _sample_metrics(0.0),
                    "women": _sample_metrics(0.03),
                },
                "feature_snapshot": {
                    "men": {"feature_columns": ["NetRtg_diff", "SeedNum_diff"], "feature_count": 2},
                    "women": {"feature_columns": ["NetRtg_diff", "SeedNum_diff"], "feature_count": 2},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": ["NetRtg_diff", "SeedNum_diff"], "feature_count": 2},
                        "metrics_by_split": _sample_metrics(0.0),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": ["NetRtg_diff", "SeedNum_diff"], "feature_count": 2},
                        "metrics_by_split": _sample_metrics(0.03),
                    },
                },
            },
        },
    }


def test_drift_helpers_bucket_seed_and_split_summary_contract():
    module = _load_module()

    assert module._seed_regime_from_diff(1) == "close"
    assert module._seed_regime_from_diff(5) == "medium"
    assert module._seed_regime_from_diff(12) == "wide"

    summary = module._build_split_drift_summary(
        y_true=np.asarray([1.0, 0.0], dtype=float),
        y_prob=np.asarray([0.8, 0.2], dtype=float),
    )
    assert {"sample_count", "pred_mean", "actual_rate", "gap", "reason"}.issubset(summary.keys())
    assert summary["sample_count"] == 2


def test_stage_eval_report_emits_drift_regime_contract(tmp_path):
    module = _load_module()
    context = _build_context(tmp_path)

    result = module.stage_eval_report(context)

    drift_payload = result["drift"]
    drift_report_path = Path(drift_payload["report_json"])
    assert drift_report_path.exists()

    drift_report = json.loads(drift_report_path.read_text(encoding="utf-8"))
    assert set(drift_report["by_gender"].keys()) == {"men", "women"}
    for gender_key in ("men", "women"):
        splits = drift_report["by_gender"][gender_key]["splits"]
        assert set(splits.keys()) == set(CANONICAL_SPLITS)
        regimes = drift_report["by_gender"][gender_key]["regimes"]
        assert {"close", "medium", "wide"}.issubset(regimes.keys())

    assert isinstance(drift_report["alerts"], list)

    eval_report_path = Path(result["eval_report"])
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    assert eval_report["drift"]["report_json"] == str(drift_report_path)

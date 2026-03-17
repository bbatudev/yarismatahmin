import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class ErrorProbModel:
    def __init__(self, feature_name: str, bias: float = 0.0):
        self.feature_name = feature_name
        self.bias = float(bias)
        self.feature_importances_ = np.asarray([5.0, 1.0], dtype=float)

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_name], dtype=float) + self.bias
        probs = 1.0 / (1.0 + np.exp(-values))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m005_s02", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pickled_model(path: Path, *, feature_name: str, bias: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(ErrorProbModel(feature_name=feature_name, bias=bias), handle)
    return path


def _write_feature_csv(path: Path, rows: list[tuple]) -> Path:
    frame = pd.DataFrame(
        rows,
        columns=["Split", "Target", "NetRtg_diff", "SeedNum_diff", "Season", "TeamA", "TeamB"],
    )
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
            ("Train", 1, 2.0, 1, 2022, 1, 11),
            ("Train", 0, -1.0, 9, 2022, 2, 12),
            ("Val", 1, 0.1, 2, 2023, 3, 13),
            ("Val", 0, -0.1, 8, 2023, 4, 14),
            ("Test", 1, 0.0, 1, 2024, 5, 15),
            ("Test", 0, 3.0, 10, 2024, 6, 16),
            ("Test", 0, -3.0, 5, 2024, 7, 17),
        ],
    )
    women_features_path = _write_feature_csv(
        data_dir / "processed_features_women.csv",
        rows=[
            ("Train", 1, 1.5, 1, 2022, 21, 31),
            ("Train", 0, -1.2, 7, 2022, 22, 32),
            ("Val", 1, 0.2, 3, 2023, 23, 33),
            ("Val", 0, -0.2, 9, 2023, 24, 34),
            ("Test", 1, 0.0, 2, 2024, 25, 35),
            ("Test", 0, 2.5, 11, 2024, 26, 36),
            ("Test", 1, -2.5, 6, 2024, 27, 37),
        ],
    )

    return {
        "run_id": "m005_s02_error_decomposition_contract",
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


def test_stage_eval_report_emits_error_decomposition_artifact(tmp_path):
    module = _load_module()
    context = _build_context(tmp_path)

    result = module.stage_eval_report(context)

    payload = result["error_decomposition"]
    report_path = Path(payload["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert set(report["by_gender"].keys()) == {"men", "women"}

    men_test = report["by_gender"]["men"]["test"]
    assert "confidence_buckets" in men_test
    assert "close_call_0.45_0.55" in men_test["confidence_buckets"]
    assert "overconfident_misses" in men_test
    assert "seed_gap_buckets" in men_test
    assert "diagnostics" in men_test
    assert men_test["diagnostics"]["min_bucket_samples"] == 10
    assert men_test["diagnostics"]["total_error_count"] >= 0
    assert "highest_error_rate_confidence_bucket" in men_test["diagnostics"]
    assert "worst_seed_gap_bucket_by_brier" in men_test["diagnostics"]
    assert {"close", "medium", "wide"}.issubset(men_test["seed_gap_buckets"].keys())

    eval_report = json.loads(Path(result["eval_report"]).read_text(encoding="utf-8"))
    assert eval_report["error_decomposition"]["report_json"] == str(report_path)

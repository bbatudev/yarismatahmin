import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
CANONICAL_SPLITS = ("Train", "Val", "Test")


class DeterministicProbModel:
    def __init__(self, feature_name: str, bias: float = 0.0):
        self.feature_name = feature_name
        self.bias = float(bias)

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_name], dtype=float)
        logits = values + self.bias
        probs = 1.0 / (1.0 + np.exp(-logits))
        return np.column_stack([1.0 - probs, probs])


def _load_run_pipeline_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_s04_calibration", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pickled_model(path: Path, *, feature_name: str, bias: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(DeterministicProbModel(feature_name=feature_name, bias=bias), handle)
    return path


def _write_feature_csv(path: Path, *, feature_name: str, rows: list[tuple[str, int, float]]) -> Path:
    frame = pd.DataFrame(rows, columns=["Split", "Target", feature_name])
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _sample_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.18 + offset, "logloss": 0.52 + offset, "auc": 0.74 + offset},
        "Val": {"brier": 0.20 + offset, "logloss": 0.56 + offset, "auc": 0.70 + offset},
        "Test": {"brier": 0.22 + offset, "logloss": 0.60 + offset, "auc": 0.68 + offset},
    }


def _build_context(tmp_path: Path, *, women_bias: float = -0.2, men_feature: str = "NetRtg_diff") -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_model_path = _write_pickled_model(model_dir / "men.pkl", feature_name=men_feature, bias=0.15)
    women_model_path = _write_pickled_model(model_dir / "women.pkl", feature_name="SeedNum_diff", bias=women_bias)

    men_features_path = _write_feature_csv(
        data_dir / "processed_features_men.csv",
        feature_name=men_feature,
        rows=[
            ("Train", 1, 2.0),
            ("Train", 1, 1.1),
            ("Train", 0, -1.1),
            ("Val", 1, 0.7),
            ("Val", 0, -0.8),
            ("Test", 1, 0.9),
            ("Test", 0, -0.9),
        ],
    )
    women_features_path = _write_feature_csv(
        data_dir / "processed_features_women.csv",
        feature_name="SeedNum_diff",
        rows=[
            ("Train", 1, 1.4),
            ("Train", 0, -1.0),
            ("Val", 1, 0.6),
            ("Val", 0, -0.5),
            ("Test", 1, 0.8),
            ("Test", 0, -0.7),
        ],
    )

    return {
        "run_id": "s04_calibration_contract",
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
                    "women": _sample_metrics(0.04),
                },
                "feature_snapshot": {
                    "men": {"feature_columns": [men_feature], "feature_count": 1},
                    "women": {"feature_columns": ["SeedNum_diff"], "feature_count": 1},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": [men_feature], "feature_count": 1},
                        "metrics_by_split": _sample_metrics(0.0),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": ["SeedNum_diff"], "feature_count": 1},
                        "metrics_by_split": _sample_metrics(0.04),
                    },
                },
            },
        },
    }


def test_stage_eval_report_emits_calibration_contract_artifacts(tmp_path):
    run_pipeline_module = _load_run_pipeline_module()
    context = _build_context(tmp_path)

    result = run_pipeline_module.stage_eval_report(context)

    eval_report_path = Path(result["eval_report"])
    bins_path = Path(result["calibration"]["bins_csv"])
    calibration_report_path = Path(result["calibration"]["report_json"])

    assert eval_report_path.exists()
    assert bins_path.exists()
    assert calibration_report_path.exists()

    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    calibration_report = json.loads(calibration_report_path.read_text(encoding="utf-8"))
    bins = pd.read_csv(bins_path)

    assert list(bins.columns) == [
        "gender",
        "split",
        "bin_left",
        "bin_right",
        "sample_count",
        "pred_mean",
        "actual_rate",
        "gap",
    ]
    assert set(bins["gender"].unique()) == {"men", "women"}
    assert set(bins["split"].unique()) == set(CANONICAL_SPLITS)

    summary = calibration_report["calibration_summary"]
    assert set(summary.keys()) == {"men", "women"}
    for gender_key in ("men", "women"):
        assert set(summary[gender_key].keys()) == set(CANONICAL_SPLITS)
        for split_label in CANONICAL_SPLITS:
            split_payload = summary[gender_key][split_label]
            assert {"ece", "wmae", "sample_count", "high_prob_band"}.issubset(split_payload.keys())

    assert "calibration" in eval_report
    assert eval_report["calibration"]["bins_csv"].endswith("calibration_bins.csv")
    assert eval_report["calibration"]["report_json"].endswith("calibration_report.json")


def test_stage_eval_report_fails_on_feature_column_mismatch(tmp_path):
    run_pipeline_module = _load_run_pipeline_module()
    context = _build_context(tmp_path, men_feature="KnownFeature")

    context["stage_outputs"]["train"]["genders"]["men"]["feature_snapshot"]["feature_columns"] = ["MissingFeature"]

    with pytest.raises(RuntimeError, match=r"feature column mismatch"):
        run_pipeline_module.stage_eval_report(context)


def test_stage_eval_report_sets_reason_for_empty_high_prob_band(tmp_path):
    run_pipeline_module = _load_run_pipeline_module()
    context = _build_context(tmp_path, women_bias=-8.0)

    result = run_pipeline_module.stage_eval_report(context)

    calibration_report_path = Path(result["calibration"]["report_json"])
    calibration_report = json.loads(calibration_report_path.read_text(encoding="utf-8"))

    women_summary = calibration_report["calibration_summary"]["women"]
    for split_label in CANONICAL_SPLITS:
        high_prob = women_summary[split_label]["high_prob_band"]
        assert high_prob["sample_count"] == 0
        assert high_prob["reason"] == "empty_high_prob_band"

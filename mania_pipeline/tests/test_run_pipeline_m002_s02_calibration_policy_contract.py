import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class PolicyProbModel:
    def __init__(self, feature_name: str, bias: float = 0.0):
        self.feature_name = feature_name
        self.feature_importances_ = np.asarray([7.0, 2.0], dtype=float)
        self.bias = float(bias)

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_name], dtype=float) + self.bias
        probs = 1.0 / (1.0 + np.exp(-values))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m002_s02", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pickled_model(path: Path, *, feature_name: str, bias: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(PolicyProbModel(feature_name=feature_name, bias=bias), handle)
    return path


def _build_rows(split: str, count: int, seed_cycle: list[int], offset: float) -> list[tuple[str, int, float, int]]:
    rows = []
    for idx in range(count):
        x = np.sin(idx / 9.0) + offset
        target = 1 if (x + (0.2 if split == "Test" else 0.0)) > 0 else 0
        seed_diff = seed_cycle[idx % len(seed_cycle)]
        rows.append((split, int(target), float(x), int(seed_diff)))
    return rows


def _write_feature_csv(path: Path, *, offset: float) -> Path:
    rows = []
    rows += _build_rows("Train", 120, [1, 2, 4, 8], offset)
    rows += _build_rows("Val", 120, [1, 3, 5, 7], offset)
    rows += _build_rows("Test", 90, [1, 1, 2, 3, 8], offset)

    frame = pd.DataFrame(rows, columns=["Split", "Target", "NetRtg_diff", "SeedNum_diff"])
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _sample_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.18 + offset, "logloss": 0.52 + offset, "auc": 0.75 + offset},
        "Val": {"brier": 0.20 + offset, "logloss": 0.56 + offset, "auc": 0.71 + offset},
        "Test": {"brier": 0.22 + offset, "logloss": 0.60 + offset, "auc": 0.69 + offset},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_model_path = _write_pickled_model(model_dir / "men.pkl", feature_name="NetRtg_diff", bias=0.12)
    women_model_path = _write_pickled_model(model_dir / "women.pkl", feature_name="NetRtg_diff", bias=-0.08)

    men_features_path = _write_feature_csv(data_dir / "processed_features_men.csv", offset=0.1)
    women_features_path = _write_feature_csv(data_dir / "processed_features_women.csv", offset=-0.1)

    return {
        "run_id": "m002_s02_calibration_policy_contract",
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


def test_calibration_policy_marks_methods_unavailable_when_val_sample_is_small():
    module = _load_module()

    result = module._build_calibration_policy_for_gender(
        gender_key="men",
        val_true=np.asarray([1.0, 0.0, 1.0], dtype=float),
        val_prob=np.asarray([0.8, 0.2, 0.7], dtype=float),
        test_true=np.asarray([1.0, 0.0], dtype=float),
        test_prob=np.asarray([0.75, 0.25], dtype=float),
        regime_summary={"close": {"sample_count": 2}},
        drift_alerts=[],
    )

    assert result["selected_method"] in {"none", "platt", "isotonic"}
    assert result["candidate_methods"]["none"]["status"] == "available"
    assert result["candidate_methods"]["platt"]["status"] == "unavailable"
    assert result["candidate_methods"]["isotonic"]["status"] == "unavailable"


def test_stage_eval_report_emits_calibration_policy_contract(tmp_path):
    module = _load_module()
    context = _build_context(tmp_path)

    result = module.stage_eval_report(context)

    policy_payload = result["calibration_policy"]
    policy_report_path = Path(policy_payload["report_json"])
    assert policy_report_path.exists()

    policy_report = json.loads(policy_report_path.read_text(encoding="utf-8"))
    assert policy_report["policy_name"] == "regime_aware_calibration_v1"
    assert set(policy_report["by_gender"].keys()) == {"men", "women"}

    for gender_key in ("men", "women"):
        entry = policy_report["by_gender"][gender_key]
        assert entry["selected_method"] in {"none", "platt", "isotonic"}
        methods = entry["candidate_methods"]
        assert methods["none"]["status"] == "available"
        assert isinstance(entry["method_order"], list)

    eval_report_path = Path(result["eval_report"])
    eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
    assert eval_report["calibration_policy"]["report_json"] == str(policy_report_path)

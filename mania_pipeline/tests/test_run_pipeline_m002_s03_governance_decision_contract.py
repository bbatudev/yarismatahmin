import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class GovernanceDecisionProbModel:
    def __init__(self, feature_columns: list[str], importance: list[float], bias: float = 0.0):
        self.feature_columns = list(feature_columns)
        self.feature_importances_ = np.asarray(importance, dtype=float)
        self.bias = float(bias)

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_columns].sum(axis=1), dtype=float) + self.bias
        probs = 1.0 / (1.0 + np.exp(-values))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m002_s03", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_model(path: Path, model: GovernanceDecisionProbModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(model, handle)
    return path


def _write_feature_csv(path: Path, rows: list[tuple]) -> Path:
    frame = pd.DataFrame(
        rows,
        columns=["Split", "Target", "SeedNum_diff", "MasseyPct_diff"],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _sample_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.18 + offset, "logloss": 0.52 + offset, "auc": 0.76 - offset},
        "Val": {"brier": 0.20 + offset, "logloss": 0.57 + offset, "auc": 0.72 - offset},
        "Test": {"brier": 0.22 + offset, "logloss": 0.60 + offset, "auc": 0.70 - offset},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    men_features = ["SeedNum_diff", "MasseyPct_diff"]
    women_features = ["SeedNum_diff", "MasseyPct_diff"]

    men_model = GovernanceDecisionProbModel(men_features, [6.0, 0.0], bias=0.1)
    women_model = GovernanceDecisionProbModel(women_features, [4.0, 0.0], bias=-0.1)

    men_model_path = _write_model(model_dir / "men.pkl", men_model)
    women_model_path = _write_model(model_dir / "women.pkl", women_model)

    men_features_path = _write_feature_csv(
        data_dir / "processed_features_men.csv",
        rows=[
            ("Train", 1, 2.0, 1.0),
            ("Train", 0, -1.1, -0.4),
            ("Val", 1, 0.9, 0.2),
            ("Val", 0, -0.8, -0.2),
            ("Test", 1, 1.2, 0.3),
            ("Test", 0, -0.9, -0.3),
        ],
    )
    women_features_path = _write_feature_csv(
        data_dir / "processed_features_women.csv",
        rows=[
            ("Train", 1, 1.4, 0.2),
            ("Train", 0, -1.0, -0.2),
            ("Val", 1, 0.7, 0.1),
            ("Val", 0, -0.5, -0.1),
            ("Test", 1, 0.8, 0.2),
            ("Test", 0, -0.6, -0.1),
        ],
    )

    return {
        "run_id": "m002_s03_governance_decision_contract",
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
                    "men": {"feature_columns": men_features, "feature_count": len(men_features)},
                    "women": {"feature_columns": women_features, "feature_count": len(women_features)},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": men_features, "feature_count": len(men_features)},
                        "metrics_by_split": _sample_metrics(0.0),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": women_features, "feature_count": len(women_features)},
                        "metrics_by_split": _sample_metrics(0.03),
                    },
                },
            },
        },
    }


def test_stage_eval_report_emits_governance_decision_contract(tmp_path):
    module = _load_module()
    context = _build_context(tmp_path)

    result = module.stage_eval_report(context)

    decision_payload = result["governance_decision"]
    decision_report_path = Path(decision_payload["report_json"])
    assert decision_report_path.exists()

    decision_report = json.loads(decision_report_path.read_text(encoding="utf-8"))
    assert set(decision_report["by_gender"].keys()) == {"men", "women"}

    allowed_decisions = {"tighten_features", "apply_calibration_policy", "monitor_drift", "hold_baseline"}
    for gender_key in ("men", "women"):
        payload = decision_report["by_gender"][gender_key]
        assert payload["decision"] in allowed_decisions
        assert isinstance(payload["confidence"], float)
        assert isinstance(payload["reason_codes"], list)
        evidence = payload["evidence_bundle"]
        assert {"ablation", "drift", "calibration_policy"}.issubset(evidence.keys())

    aggregate = decision_report["aggregate"]
    assert aggregate["decision"] in {"review_feature_groups", "enforce_calibration_policy", "monitor_drift", "hold_baseline"}
    assert isinstance(aggregate["reason_codes"], list)

    eval_report = json.loads(Path(result["eval_report"]).read_text(encoding="utf-8"))
    assert eval_report["governance_decision"]["report_json"] == str(decision_report_path)

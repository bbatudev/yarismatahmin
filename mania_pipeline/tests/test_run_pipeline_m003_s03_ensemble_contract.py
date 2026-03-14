import importlib.util
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"


class ContractProbModel:
    def __init__(self, feature_columns: list[str], bias: float = 0.0, importance: list[float] | None = None):
        self.feature_columns = list(feature_columns)
        self.bias = float(bias)
        self.feature_importances_ = np.asarray(
            importance if importance is not None else [1.0 for _ in self.feature_columns],
            dtype=float,
        )

    def predict_proba(self, X):
        values = np.asarray(X[self.feature_columns].sum(axis=1), dtype=float) + self.bias
        probs = 1.0 / (1.0 + np.exp(-values))
        return np.column_stack([1.0 - probs, probs])


def _load_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_m003_s03", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_model(path: Path, model: ContractProbModel) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(model, handle)
    return path


def _write_feature_csv(path: Path) -> Path:
    frame = pd.DataFrame(
        {
            "Split": ["Train", "Train", "Val", "Val", "Test", "Test"],
            "Target": [1, 0, 1, 0, 1, 0],
            "SeedNum_diff": [1.4, -1.3, 1.1, -1.0, 0.9, -0.8],
            "NetRtg_diff": [0.8, -0.7, 0.6, -0.5, 0.4, -0.4],
            "Season": [2022, 2022, 2023, 2023, 2024, 2024],
            "TeamA": [1, 2, 3, 4, 5, 6],
            "TeamB": [7, 8, 9, 10, 11, 12],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return path


def _split_metrics(base_brier: float) -> dict:
    return {
        "Train": {"brier": base_brier - 0.02, "logloss": 0.52, "auc": 0.76},
        "Val": {"brier": base_brier - 0.01, "logloss": 0.56, "auc": 0.74},
        "Test": {"brier": base_brier, "logloss": 0.60, "auc": 0.72},
    }


def _build_context(tmp_path: Path) -> dict:
    run_dir = tmp_path / "run"
    model_dir = tmp_path / "models"
    data_dir = tmp_path / "data"
    run_dir.mkdir(parents=True, exist_ok=True)

    feature_columns = ["SeedNum_diff", "NetRtg_diff"]
    men_model_path = _write_model(model_dir / "men.pkl", ContractProbModel(feature_columns, bias=-0.9, importance=[5.0, 1.0]))
    women_model_path = _write_model(model_dir / "women.pkl", ContractProbModel(feature_columns, bias=-0.8, importance=[4.0, 1.0]))

    men_features_path = _write_feature_csv(data_dir / "processed_features_men.csv")
    women_features_path = _write_feature_csv(data_dir / "processed_features_women.csv")

    hpo_report_path = _write_json(
        run_dir / "hpo_report.json",
        {
            "run_id": "m003_s03_ensemble_contract",
            "status": "passed",
            "config": {"target_profile": "quality_v1"},
            "by_gender": {
                "men": {
                    "status": "passed",
                    "best_trial_id": 2,
                    "best_val_brier": 0.18,
                    "best_test_brier": 0.19,
                    "best_param_overrides": {
                        "learning_rate": 0.03,
                        "num_leaves": 47,
                        "min_child_samples": 15,
                    },
                    "candidates": [],
                },
                "women": {
                    "status": "passed",
                    "best_trial_id": 1,
                    "best_val_brier": 0.17,
                    "best_test_brier": 0.18,
                    "best_param_overrides": {
                        "learning_rate": 0.03,
                        "num_leaves": 47,
                        "min_child_samples": 15,
                    },
                    "candidates": [],
                },
            },
        },
    )

    return {
        "run_id": "m003_s03_ensemble_contract",
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
                    "men": _split_metrics(0.24),
                    "women": _split_metrics(0.23),
                },
                "feature_snapshot": {
                    "men": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                    "women": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                },
                "genders": {
                    "men": {
                        "model_path": str(men_model_path),
                        "feature_snapshot": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                        "metrics_by_split": _split_metrics(0.24),
                    },
                    "women": {
                        "model_path": str(women_model_path),
                        "feature_snapshot": {"feature_columns": feature_columns, "feature_count": len(feature_columns)},
                        "metrics_by_split": _split_metrics(0.23),
                    },
                },
                "hpo": {
                    "status": "passed",
                    "report_json": str(hpo_report_path),
                    "target_profile": "quality_v1",
                    "trials_requested": 2,
                    "trials_executed": 2,
                    "by_gender": {
                        "men": {"status": "passed", "best_trial_id": 2, "best_param_overrides": {"learning_rate": 0.03}},
                        "women": {"status": "passed", "best_trial_id": 1, "best_param_overrides": {"learning_rate": 0.03}},
                    },
                },
            },
        },
    }


def test_stage_eval_report_emits_ensemble_candidate_contract(tmp_path, monkeypatch):
    module = _load_module()

    class StubTrainModule:
        DATA_DIR = ""
        OUT_DIR = ""
        DROP_COLUMNS = ("Season", "TeamA", "TeamB", "Target", "Split")

        @staticmethod
        def train_baseline(df, gender="M", random_state=42, profile="baseline", param_overrides=None):
            del random_state
            features = [
                column
                for column in df.columns
                if column not in StubTrainModule.DROP_COLUMNS
            ]
            bias = 0.9 if isinstance(param_overrides, dict) and param_overrides else -0.6
            model = ContractProbModel(features, bias=bias, importance=[1.0 for _ in features])
            base_brier = 0.20 if gender == "M" else 0.19
            adjust = -0.02 if isinstance(param_overrides, dict) and param_overrides else 0.0
            payload = {
                "gender": gender,
                "training_profile": str(profile),
                "training_params": {"random_state": 42, **(param_overrides or {})},
                "metrics_by_split": {
                    "Train": {"brier": base_brier - 0.02 + adjust, "logloss": 0.50, "auc": 0.77},
                    "Val": {"brier": base_brier - 0.01 + adjust, "logloss": 0.54, "auc": 0.75},
                    "Test": {"brier": base_brier + adjust, "logloss": 0.58, "auc": 0.73},
                },
                "feature_snapshot": {
                    "feature_columns": features,
                    "feature_count": len(features),
                },
                "best_iteration": 12,
            }
            return model, payload

    monkeypatch.setattr(module, "_load_script_module", lambda filename, module_name: StubTrainModule, raising=False)

    context = _build_context(tmp_path)
    result = module.stage_eval_report(context)

    ensemble_payload = result["ensemble"]
    report_path = Path(ensemble_payload["report_json"])
    assert report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert set(report["by_gender"].keys()) == {"men", "women"}

    for gender_key in ("men", "women"):
        payload = report["by_gender"][gender_key]
        candidate_ids = {entry["candidate_id"] for entry in payload["candidates"]}
        assert {"baseline", "hpo_best", "ensemble_weighted"}.issubset(candidate_ids)
        assert payload["selected_candidate_id"] in candidate_ids
        assert payload["selection_signal"] in {"hold_baseline", "promote_non_baseline"}

    assert report["aggregate"]["decision"] in {"hold_baseline", "adopt_non_baseline_candidates"}

    eval_report = json.loads(Path(result["eval_report"]).read_text(encoding="utf-8"))
    assert eval_report["ensemble"]["report_json"] == str(report_path)

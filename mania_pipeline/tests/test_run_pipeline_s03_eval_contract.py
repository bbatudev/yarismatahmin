import importlib.util
import json
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
CANONICAL_STAGES = ("feature", "train", "eval_report", "artifact")


class DummyProbModel:
    def __init__(self, feature_name: str, bias: float = 0.0):
        self.feature_name = feature_name
        self.bias = float(bias)

    def predict_proba(self, X):
        if hasattr(X, "__getitem__"):
            feature_values = np.asarray(X[self.feature_name], dtype=float)
        else:
            feature_values = np.asarray(X, dtype=float)

        logits = feature_values + self.bias
        probs = 1.0 / (1.0 + np.exp(-logits))
        return np.column_stack([1.0 - probs, probs])


def _load_run_pipeline_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_s03_eval", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _invoke_main(module, argv):
    main = getattr(module, "main", None)
    assert callable(main), "run_pipeline.py must expose main(argv=None)"

    try:
        result = main(argv)
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)

    if result is None:
        return 0
    return int(result)


def _latest_run_dir(artifacts_root: Path) -> Path:
    runs = [p for p in artifacts_root.iterdir() if p.is_dir()]
    assert runs, f"no run directories found under {artifacts_root}"
    return max(runs, key=lambda p: p.stat().st_mtime_ns)


def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sample_split_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.20 + offset, "logloss": 0.58 + offset, "auc": 0.72 + offset, "auc_reason": None, "row_count": 10},
        "Val": {"brier": 0.21 + offset, "logloss": 0.60 + offset, "auc": 0.70 + offset, "auc_reason": None, "row_count": 6},
        "Test": {"brier": 0.22 + offset, "logloss": 0.62 + offset, "auc": 0.68 + offset, "auc_reason": None, "row_count": 4},
    }


def _write_feature_inputs(tmp_path: Path) -> tuple[Path, Path]:
    men_path = tmp_path / "processed_features_men.csv"
    women_path = tmp_path / "processed_features_women.csv"

    men_df = pd.DataFrame(
        {
            "Split": ["Train", "Train", "Val", "Val", "Test", "Test"],
            "Target": [1, 1, 1, 0, 1, 0],
            "NetRtg_diff": [2.2, 1.4, 0.7, -0.8, 1.1, -1.3],
        }
    )
    women_df = pd.DataFrame(
        {
            "Split": ["Train", "Train", "Val", "Val", "Test", "Test"],
            "Target": [1, 1, 0, 0, 1, 0],
            "SeedNum_diff": [1.8, 1.2, 0.4, -0.4, 0.9, -0.9],
        }
    )

    men_df.to_csv(men_path, index=False)
    women_df.to_csv(women_path, index=False)
    return men_path, women_path


def _stub_train_module(tmp_path: Path):
    module = types.SimpleNamespace()
    module.DATA_DIR = ""
    module.OUT_DIR = str(tmp_path / "models")

    def _load_data(gender: str):
        return {"gender": gender}

    def _train_baseline(df, gender: str, random_state: int = 42):
        del df, random_state
        if gender == "M":
            payload = {
                "gender": "M",
                "metrics_by_split": _sample_split_metrics(0.0),
                "feature_snapshot": {"feature_columns": ["NetRtg_diff"], "feature_count": 1},
                "best_iteration": 17,
            }
            return DummyProbModel(feature_name="NetRtg_diff", bias=0.2), payload

        payload = {
            "gender": "W",
            "metrics_by_split": _sample_split_metrics(0.05),
            "feature_snapshot": {"feature_columns": ["SeedNum_diff"], "feature_count": 1},
            "best_iteration": 11,
        }
        return DummyProbModel(feature_name="SeedNum_diff", bias=-0.1), payload

    module.load_data = _load_data
    module.train_baseline = _train_baseline
    return module


def test_stage_train_persists_per_gender_payload_contract(tmp_path, monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()
    train_module = _stub_train_module(tmp_path)

    monkeypatch.setattr(run_pipeline_module, "PIPELINE_DIR", tmp_path, raising=False)
    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: train_module,
        raising=False,
    )

    context = {
        "run_id": "s03_unit_train_contract",
        "seed": 42,
        "stage_outputs": {
            "feature": {
                "gates": {
                    "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                    "women": {"pass": True, "blocking_rule": None, "reason": "ok"},
                }
            }
        },
    }

    result = run_pipeline_module.stage_train(context)

    assert set(result["genders"].keys()) == {"men", "women"}
    assert result["genders"]["men"]["metrics_by_split"]["Test"]["brier"] == pytest.approx(0.22)
    assert result["genders"]["women"]["metrics_by_split"]["Test"]["brier"] == pytest.approx(0.27)
    assert result["feature_snapshot"]["men"]["feature_count"] == 1
    assert result["feature_snapshot"]["women"]["feature_count"] == 1

    assert Path(result["models"]["men"]).exists()
    assert Path(result["models"]["women"]).exists()


def test_stage_train_fails_fast_when_feature_gate_is_blocking(monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()

    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: (_ for _ in ()).throw(AssertionError("train module must not load when gate fails")),
        raising=False,
    )

    context = {
        "run_id": "s03_gate_fail",
        "seed": 42,
        "stage_outputs": {
            "feature": {
                "gates": {
                    "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                    "women": {
                        "pass": False,
                        "blocking_rule": "R006_FEATURE_GATE_REQUIRED",
                        "reason": "women gate did not pass",
                    },
                }
            }
        },
    }

    with pytest.raises(RuntimeError, match=r"\[women\] feature gate failed: R006_FEATURE_GATE_REQUIRED"):
        run_pipeline_module.stage_train(context)


def test_stage_eval_report_writes_metrics_table_and_side_by_side_summary(tmp_path, monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()
    train_module = _stub_train_module(tmp_path)

    monkeypatch.setattr(run_pipeline_module, "PIPELINE_DIR", tmp_path, raising=False)
    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: train_module,
        raising=False,
    )

    men_features, women_features = _write_feature_inputs(tmp_path)

    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)

    context = {
        "run_id": "s03_eval_contract",
        "seed": 42,
        "run_dir": str(run_dir),
        "stage_outputs": {
            "feature": {
                "gates": {
                    "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                    "women": {"pass": True, "blocking_rule": None, "reason": "ok"},
                },
                "outputs": {
                    "men_features": str(men_features),
                    "women_features": str(women_features),
                },
            }
        },
    }

    context["stage_outputs"]["train"] = run_pipeline_module.stage_train(context)
    eval_result = run_pipeline_module.stage_eval_report(context)

    report = json.loads(Path(eval_result["eval_report"]).read_text(encoding="utf-8"))
    assert report["metrics_table"], "metrics_table must not be empty"
    assert len(report["metrics_table"]) == 6
    assert {"gender", "split", "brier", "logloss", "auc"}.issubset(report["metrics_table"][0].keys())

    side = report["side_by_side_summary"]
    assert {"men_test_brier", "women_test_brier", "delta_test_brier"}.issubset(side.keys())
    assert side["delta_test_brier"] == pytest.approx(side["men_test_brier"] - side["women_test_brier"])

    assert "calibration" in report
    assert "calibration" in eval_result
    assert Path(report["calibration"]["bins_csv"]).exists()
    assert Path(report["calibration"]["report_json"]).exists()


def test_main_stops_in_train_stage_when_feature_gate_payload_blocks(tmp_path, monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()

    def _feature_stage(_context):
        return {
            "gates": {
                "men": {"pass": True, "blocking_rule": None, "reason": "ok"},
                "women": {
                    "pass": False,
                    "blocking_rule": "R006_FEATURE_GATE_REQUIRED",
                    "reason": "women gate did not pass",
                },
            }
        }

    def _never_called(context):
        del context
        raise AssertionError("stage should not execute after train gate failure")

    monkeypatch.setattr(run_pipeline_module, "CANONICAL_STAGES", CANONICAL_STAGES, raising=False)
    monkeypatch.setattr(
        run_pipeline_module,
        "STAGE_HANDLERS",
        {
            "feature": _feature_stage,
            "train": run_pipeline_module.stage_train,
            "eval_report": _never_called,
            "artifact": _never_called,
        },
        raising=False,
    )
    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: (_ for _ in ()).throw(AssertionError("train module must not load when gate fails")),
        raising=False,
    )

    artifacts_root = tmp_path / "runs"
    exit_code = _invoke_main(
        run_pipeline_module,
        ["--seed", "42", "--run-label", "s03-train-gate-fail", "--artifacts-root", str(artifacts_root)],
    )

    assert exit_code != 0

    run_dir = _latest_run_dir(artifacts_root)
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    events = _read_jsonl(run_dir / "stage_events.jsonl")

    assert metadata["status"] == "failed"
    assert metadata["failed_stage"] == "train"

    assert [(e["stage"], e["status"]) for e in events] == [
        ("feature", "started"),
        ("feature", "succeeded"),
        ("train", "started"),
        ("train", "failed"),
    ]
    assert "R006_FEATURE_GATE_REQUIRED" in events[-1]["error"]["message"]

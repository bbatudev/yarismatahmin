import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


TRAIN_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "03_lgbm_train.py"
CONTRACTS_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "split_leakage_contracts.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader, f"Could not load module spec from {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


train_module = _load_module(TRAIN_SCRIPT_PATH, "lgbm_train_under_test_contract")
contracts_module = _load_module(CONTRACTS_SCRIPT_PATH, "split_contracts_under_test_for_lgbm")


class _StubLGBMClassifier:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.best_iteration_ = 11
        self.feature_importances_ = np.array([], dtype=float)

    def fit(self, X, y, eval_set=None, callbacks=None):
        del y, eval_set, callbacks
        self.feature_importances_ = np.arange(X.shape[1], 0, -1, dtype=float)
        return self

    def predict_proba(self, X):
        logits = X.iloc[:, 0].to_numpy(dtype=float)
        probs = 1.0 / (1.0 + np.exp(-logits))
        probs = np.clip(probs, 1e-6, 1 - 1e-6)
        return np.column_stack([1.0 - probs, probs])


def _install_stub_model(monkeypatch):
    monkeypatch.setattr(train_module.lgb, "LGBMClassifier", _StubLGBMClassifier, raising=True)
    monkeypatch.setattr(train_module.lgb, "early_stopping", lambda **kwargs: None, raising=True)


def _base_df(*, single_class_test=False):
    train_targets = [0, 1, 0, 1, 0, 1]
    val_targets = [0, 1, 0, 1]
    test_targets = [1, 1, 1, 1] if single_class_test else [0, 1, 0, 1]

    split_targets = (
        [("Train", target) for target in train_targets]
        + [("Val", target) for target in val_targets]
        + [("Test", target) for target in test_targets]
    )

    rows = []
    for idx, (split_label, target) in enumerate(split_targets):
        rows.append(
            {
                "Season": 2020 + (idx % 6),
                "TeamA": 1000 + idx,
                "TeamB": 2000 + idx,
                "Target": target,
                "Split": split_label,
                "NetRtg_diff": float((idx - 5) / 3.0),
                "SeedNum_diff": float((-1) ** idx * (idx % 4)),
            }
        )

    return pd.DataFrame(rows)


def test_train_baseline_returns_unified_payload_for_men_and_women(monkeypatch):
    _install_stub_model(monkeypatch)

    df = _base_df(single_class_test=False)
    _, men_payload = train_module.train_baseline(df, "M", random_state=42)
    _, women_payload = train_module.train_baseline(df, "W", random_state=42)

    for expected_gender, payload in (("M", men_payload), ("W", women_payload)):
        assert payload["gender"] == expected_gender
        assert "best_iteration" in payload
        assert isinstance(payload["best_iteration"], int)

        metrics_by_split = payload["metrics_by_split"]
        canonical_labels = set(contracts_module.ALLOWED_SPLIT_LABELS)
        assert canonical_labels.issubset(metrics_by_split.keys())
        assert "Test" in metrics_by_split

        for split_label in canonical_labels:
            split_metrics = metrics_by_split[split_label]
            assert {"brier", "logloss", "auc"}.issubset(split_metrics.keys())
            assert "auc_reason" in split_metrics

        test_metrics = metrics_by_split["Test"]
        assert test_metrics["row_count"] == int((df["Split"] == "Test").sum())

        feature_snapshot = payload["feature_snapshot"]
        expected_features = [col for col in df.columns if col not in train_module.DROP_COLUMNS]
        assert feature_snapshot["feature_columns"] == expected_features
        assert feature_snapshot["feature_count"] == len(expected_features)


def test_train_baseline_marks_auc_reason_when_test_split_is_single_class(monkeypatch):
    _install_stub_model(monkeypatch)

    df = _base_df(single_class_test=True)
    _, payload = train_module.train_baseline(df, "M", random_state=13)

    test_metrics = payload["metrics_by_split"]["Test"]
    assert test_metrics["auc"] is None
    assert test_metrics["auc_reason"] == "single_class_target:1"

    assert test_metrics["brier"] is not None
    assert test_metrics["logloss"] is not None

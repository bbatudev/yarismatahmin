import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "feature_governance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("feature_governance_ablation_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_rows():
    return [
        {"feature": "SeedNum_diff", "group": "seed", "default_action": "keep", "gender": "men"},
        {"feature": "NetRtg_diff", "group": "rating", "default_action": "drop", "gender": "men"},
        {"feature": "WinPct_Last14Days_diff", "group": "form", "default_action": "candidate", "gender": "men"},
        {"feature": "SeedNum_diff", "group": "seed", "default_action": "keep", "gender": "women"},
        {"feature": "TrueMargin_Last21Days_diff", "group": "form", "default_action": "candidate", "gender": "women"},
    ]


def test_select_suspicious_groups_is_deterministic_and_capped():
    module = _load_module()
    rows = _sample_rows()

    first = module.select_suspicious_groups(rows, max_groups=2)
    second = module.select_suspicious_groups(rows, max_groups=2)

    assert first == second
    assert len(first) == 2
    assert first[0] == "form"


def test_compute_ablation_split_deltas_exposes_required_schema_and_reasons():
    module = _load_module()

    baseline_metrics = {
        "Val": {"brier": 0.20, "logloss": 0.60, "auc": 0.70},
        "Test": {"brier": 0.22, "logloss": 0.62, "auc": 0.68},
    }
    ablated_metrics = {
        "Val": {"brier": 0.21, "logloss": 0.61, "auc": 0.69},
        "Test": {"brier": 0.23, "logloss": 0.63, "auc": 0.67},
    }

    baseline_calibration = {
        "Val": {"ece": 0.03, "wmae": 0.03, "reason": None, "high_prob_band": {"gap": 0.05, "reason": None}},
        "Test": {
            "ece": 0.04,
            "wmae": 0.04,
            "reason": None,
            "high_prob_band": {"gap": None, "reason": "empty_high_prob_band"},
        },
    }
    ablated_calibration = {
        "Val": {"ece": 0.05, "wmae": 0.05, "reason": None, "high_prob_band": {"gap": 0.08, "reason": None}},
        "Test": {
            "ece": 0.06,
            "wmae": 0.06,
            "reason": None,
            "high_prob_band": {"gap": None, "reason": "empty_high_prob_band"},
        },
    }

    deltas = module.compute_ablation_split_deltas(
        baseline_metrics_by_split=baseline_metrics,
        ablated_metrics_by_split=ablated_metrics,
        baseline_calibration_by_split=baseline_calibration,
        ablated_calibration_by_split=ablated_calibration,
    )

    assert set(deltas.keys()) == set(module.ABLATION_TARGET_SPLITS)

    val_payload = deltas["Val"]
    assert {"delta_brier", "delta_logloss", "delta_auc", "delta_calibration", "reason"}.issubset(val_payload.keys())
    assert val_payload["delta_brier"] == pytest.approx(0.01)
    assert val_payload["delta_calibration"]["delta_ece"] == pytest.approx(0.02)
    assert val_payload["reason"] is None

    test_payload = deltas["Test"]
    assert test_payload["reason"] == "empty_high_prob_band"


def test_build_ablation_summary_reports_counts_and_skip_domain():
    module = _load_module()

    summary = module.build_ablation_summary(
        selected_groups=["form", "rating", "seed"],
        ablation_groups=[
            {"group": "form", "status": "executed", "reason": None},
            {"group": "rating", "status": "skipped", "reason": "split_empty"},
            {"group": "seed", "status": "skipped", "reason": "unknown_reason"},
        ],
    )

    assert summary["selected_group_count"] == 3
    assert summary["executed_group_count"] == 1
    assert len(summary["skipped_groups"]) == 2
    assert {item["reason"] for item in summary["skipped_groups"]}.issubset(set(module.ABLATION_ALLOWED_SKIP_REASONS))

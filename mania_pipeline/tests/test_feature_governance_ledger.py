import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "feature_governance.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("feature_governance_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_metrics(offset: float) -> dict:
    return {
        "Train": {"brier": 0.19 + offset, "logloss": 0.55 + offset, "auc": 0.74 - offset},
        "Val": {"brier": 0.21 + offset, "logloss": 0.60 + offset, "auc": 0.71 - offset},
        "Test": {"brier": 0.23 + offset, "logloss": 0.64 + offset, "auc": 0.69 - offset},
    }


def _sample_payload() -> tuple[dict, dict]:
    genders_payload = {
        "men": {
            "feature_snapshot": {
                "feature_columns": ["SeedNum_diff", "MasseyPct_diff", "NetRtg_diff"],
                "feature_count": 3,
            },
            "metrics_by_split": _sample_metrics(0.0),
        },
        "women": {
            "feature_snapshot": {
                "feature_columns": ["SeedNum_diff", "NetRtg_diff", "MasseyPct_diff"],
                "feature_count": 3,
            },
            "metrics_by_split": _sample_metrics(0.03),
        },
    }
    model_importances = {
        "men": [9.0, 0.0, 2.0],
        "women": [3.0, 1.0, 0.0],
    }
    return genders_payload, model_importances


def test_build_governance_ledger_rows_enforces_schema_and_value_domain():
    module = _load_module()
    genders_payload, model_importances = _sample_payload()

    rows = module.build_governance_ledger_rows(
        genders_payload=genders_payload,
        model_importances=model_importances,
    )

    assert rows, "ledger rows should not be empty"

    for row in rows:
        assert set(module.LEDGER_REQUIRED_COLUMNS).issubset(row.keys())
        assert row["default_action"] in set(module.DEFAULT_ACTION_DOMAIN)

        evidence = json.loads(row["evidence"])
        assert "metrics_by_split" in evidence
        assert set(evidence["metrics_by_split"].keys()) == {"Train", "Val", "Test"}

    women_rows = [row for row in rows if row["gender"] == "women"]
    assert all(row["feature"] not in module.MEN_ONLY_FEATURES for row in women_rows)


def test_build_governance_ledger_rows_is_deterministic_for_same_input():
    module = _load_module()
    genders_payload, model_importances = _sample_payload()

    first = module.build_governance_ledger_rows(
        genders_payload=genders_payload,
        model_importances=model_importances,
    )
    second = module.build_governance_ledger_rows(
        genders_payload=genders_payload,
        model_importances=model_importances,
    )

    assert first == second


def test_build_governance_summary_returns_domain_counts():
    module = _load_module()
    genders_payload, model_importances = _sample_payload()

    rows = module.build_governance_ledger_rows(
        genders_payload=genders_payload,
        model_importances=model_importances,
    )
    summary = module.build_governance_summary(rows)

    assert summary["row_count"] == len(rows)
    assert set(summary["default_action_counts"].keys()) == set(module.DEFAULT_ACTION_DOMAIN)


def test_infer_feature_group_classifies_m005_s04_features_as_rating():
    module = _load_module()

    assert module.infer_feature_group("PythWR_diff") == "rating"
    assert module.infer_feature_group("Luck_diff") == "rating"
    assert module.infer_feature_group("MasseyPctSpread_diff") == "rating"
    assert module.infer_feature_group("StyleClash_eFG_BlkPct_diff") == "style"
    assert module.infer_feature_group("SeedPythMispricing_diff") == "seed"

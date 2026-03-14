import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "split_leakage_contracts.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("split_leakage_contracts_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contracts = _load_module()


EXPECTED_GATE_KEYS = {"pass", "blocking_rule", "reason", "evidence"}


def _assert_gate_payload_shape(payload):
    assert set(payload.keys()) == EXPECTED_GATE_KEYS
    assert isinstance(payload["pass"], bool)
    assert isinstance(payload["reason"], str) and payload["reason"].strip()
    assert isinstance(payload["evidence"], dict)

    if payload["pass"]:
        assert payload["blocking_rule"] is None
    else:
        assert isinstance(payload["blocking_rule"], str) and payload["blocking_rule"].strip()


def _valid_contract_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Season": [2022, 2023, 2024, 2025],
            "TeamA": [1001, 1001, 1002, 1003],
            "TeamB": [2001, 2002, 2002, 2003],
            "Target": [1, 0, 1, 0],
            "Split": ["Train", "Val", "Test", "Test"],
            "NetRtg_diff": [3.2, -1.1, 2.0, -0.3],
            "SeedNum_diff": [-4, 2, -1, 3],
            "Heavy_Favorite": [0, 0, 0, 0],
            "Is_FirstWeekend": [1, 1, 1, 1],
        }
    )


def test_split_and_leakage_contracts_pass_with_valid_dataframe():
    df = _valid_contract_df()

    split_result = contracts.validate_split_contract(df)
    leakage_result = contracts.validate_leakage_contract(df)

    _assert_gate_payload_shape(split_result)
    _assert_gate_payload_shape(leakage_result)

    assert split_result["pass"] is True
    assert leakage_result["pass"] is True


def test_split_contract_fails_when_season_mapping_is_wrong():
    df = _valid_contract_df()
    df.loc[df["Season"] == 2023, "Split"] = "Train"

    result = contracts.validate_split_contract(df)

    _assert_gate_payload_shape(result)
    assert result["pass"] is False
    assert result["blocking_rule"] == "R002_SPLIT_SEASON_MISMATCH"
    assert result["evidence"]["mismatch_count"] == 1
    assert result["evidence"]["mismatches"][0]["Season"] == 2023


def test_split_contract_fails_on_unknown_split_label():
    df = _valid_contract_df()
    df.loc[df["Season"] == 2024, "Split"] = "History"

    result = contracts.validate_split_contract(df)

    _assert_gate_payload_shape(result)
    assert result["pass"] is False
    assert result["blocking_rule"] == "R002_SPLIT_UNKNOWN_LABEL"
    assert "History" in result["evidence"]["unknown_labels"]


def test_leakage_contract_fails_on_forbidden_column():
    df = _valid_contract_df().copy()
    df["WScore"] = [70, 71, 72, 73]

    result = contracts.validate_leakage_contract(df)

    _assert_gate_payload_shape(result)
    assert result["pass"] is False
    assert result["blocking_rule"] == "R004_LEAKAGE_FORBIDDEN_COLUMNS"
    assert "WScore" in result["evidence"]["forbidden_columns"]

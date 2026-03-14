from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import pandas as pd

GATE_PAYLOAD_FIELDS = ("pass", "blocking_rule", "reason", "evidence")

REQUIRED_SPLIT_COLUMNS = ("Season", "Split")
REQUIRED_LEAKAGE_COLUMNS = ("Season", "TeamA", "TeamB", "Target", "Split")
ALLOWED_SPLIT_LABELS = frozenset({"Train", "Val", "Test"})

FORBIDDEN_LEAKAGE_COLUMNS = frozenset(
    {
        # Raw winner/loser columns (direct outcome leakage)
        "WTeamID",
        "LTeamID",
        "WScore",
        "LScore",
        "WLoc",
        "NumOT",
        "DayNum",
        # Long-format game-level columns (post-game signal)
        "TeamID",
        "OppID",
        "Win",
        "Score",
        "OppScore",
        "TrueMargin",
        "PointDiff",
        # Box-score raw stats
        "FGM",
        "FGA",
        "FGM3",
        "FGA3",
        "FTM",
        "FTA",
        "OR",
        "DR",
        "Ast",
        "TO",
        "Stl",
        "Blk",
        "PF",
        "OppFGM",
        "OppFGA",
        "OppFGM3",
        "OppFGA3",
        "OppFTM",
        "OppFTA",
        "OppOR",
        "OppDR",
        "OppAst",
        "OppTO",
        "OppStl",
        "OppBlk",
        "OppPF",
        # Post-game efficiency features (without matchup differential)
        "Poss",
        "eFG",
        "TOVpct",
        "ORBpct",
        "FTr",
        "OppFTr",
        "OffRtg",
        "DefRtg",
        "NetRtg",
    }
)

ALLOWED_NON_DIFF_FEATURE_COLUMNS = frozenset(
    {
        "Heavy_Favorite",
        "Toss_Up",
        "TeamA_Is_Favorite",
        "TeamA_Is_Underdog",
        "TeamA_Seed_Top4",
        "TeamA_Seed_Mid",
        "TeamA_Seed_Low",
        "TeamA_Is_11_12_vs_5_6",
        "TeamA_Is_5_6_vs_11_12",
        "Round_Num",
        "Is_FirstWeekend",
        "Is_SecondWeekend",
        "Is_FinalWeekend",
    }
)


def _build_gate_result(
    *,
    passed: bool,
    reason: str,
    blocking_rule: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "pass": bool(passed),
        "blocking_rule": blocking_rule,
        "reason": reason,
        "evidence": evidence or {},
    }
    return payload


@lru_cache(maxsize=1)
def _load_assign_split_authority() -> Callable[[int], str]:
    script_path = Path(__file__).with_name("02_feature_engineering.py")
    spec = importlib.util.spec_from_file_location("feature_engineering_authority", script_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load split authority from {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assign_split = getattr(module, "assign_split", None)
    if not callable(assign_split):
        raise RuntimeError("Split authority is missing callable assign_split(season)")
    return assign_split


def _missing_columns(df: pd.DataFrame, required_columns: tuple[str, ...]) -> list[str]:
    return sorted([col for col in required_columns if col not in df.columns])


def validate_split_contract(
    df: pd.DataFrame,
    *,
    assign_split_fn: Callable[[int], str] | None = None,
) -> dict[str, Any]:
    """Validate deterministic season->split mapping contract (R002)."""

    missing_columns = _missing_columns(df, REQUIRED_SPLIT_COLUMNS)
    if missing_columns:
        return _build_gate_result(
            passed=False,
            blocking_rule="R002_SPLIT_REQUIRED_COLUMNS_MISSING",
            reason="Split contract requires Season and Split columns.",
            evidence={"missing_columns": missing_columns},
        )

    actual_split = df["Split"].astype(str)
    unknown_mask = ~actual_split.isin(ALLOWED_SPLIT_LABELS)
    if unknown_mask.any():
        unknown_labels = sorted(actual_split[unknown_mask].drop_duplicates().tolist())
        sample_rows = (
            df.loc[unknown_mask, ["Season", "Split"]]
            .drop_duplicates()
            .sort_values(["Season", "Split"])
            .head(10)
            .to_dict("records")
        )
        return _build_gate_result(
            passed=False,
            blocking_rule="R002_SPLIT_UNKNOWN_LABEL",
            reason="Split column contains labels outside Train/Val/Test contract.",
            evidence={
                "unknown_labels": unknown_labels,
                "unknown_label_count": int(len(unknown_labels)),
                "sample_rows": sample_rows,
            },
        )

    seasons = pd.to_numeric(df["Season"], errors="coerce")
    invalid_season_mask = seasons.isna()
    if invalid_season_mask.any():
        invalid_samples = (
            df.loc[invalid_season_mask, "Season"]
            .astype(str)
            .drop_duplicates()
            .sort_values()
            .head(10)
            .tolist()
        )
        return _build_gate_result(
            passed=False,
            blocking_rule="R002_SPLIT_INVALID_SEASON",
            reason="Season column must be numeric for split authority mapping.",
            evidence={"invalid_season_samples": invalid_samples},
        )

    assigner = assign_split_fn or _load_assign_split_authority()
    expected_split = seasons.astype(int).apply(assigner).astype(str)

    mismatch_mask = actual_split != expected_split
    if mismatch_mask.any():
        mismatch_df = pd.DataFrame(
            {
                "Season": seasons.astype(int),
                "actual_split": actual_split,
                "expected_split": expected_split,
            }
        )
        mismatch_rows = (
            mismatch_df.loc[mismatch_mask]
            .drop_duplicates()
            .sort_values(["Season", "actual_split", "expected_split"])
        )
        return _build_gate_result(
            passed=False,
            blocking_rule="R002_SPLIT_SEASON_MISMATCH",
            reason="Season to split mapping violated walk-forward authority.",
            evidence={
                "mismatch_count": int(len(mismatch_rows)),
                "mismatches": mismatch_rows.head(20).to_dict("records"),
            },
        )

    split_counts = actual_split.value_counts().sort_index().to_dict()
    return _build_gate_result(
        passed=True,
        blocking_rule=None,
        reason="Split contract satisfied.",
        evidence={
            "row_count": int(len(df)),
            "split_counts": split_counts,
            "allowed_labels": sorted(ALLOWED_SPLIT_LABELS),
        },
    )


def validate_leakage_contract(df: pd.DataFrame) -> dict[str, Any]:
    """Validate leakage guardrails for final matchup matrix (R004)."""

    missing_columns = _missing_columns(df, REQUIRED_LEAKAGE_COLUMNS)
    if missing_columns:
        return _build_gate_result(
            passed=False,
            blocking_rule="R004_LEAKAGE_REQUIRED_COLUMNS_MISSING",
            reason="Leakage contract requires canonical model columns.",
            evidence={"missing_columns": missing_columns},
        )

    forbidden_columns = sorted(set(df.columns).intersection(FORBIDDEN_LEAKAGE_COLUMNS))
    if forbidden_columns:
        return _build_gate_result(
            passed=False,
            blocking_rule="R004_LEAKAGE_FORBIDDEN_COLUMNS",
            reason="Leakage contract detected forbidden raw/post-game columns.",
            evidence={
                "forbidden_columns": forbidden_columns,
                "forbidden_column_count": int(len(forbidden_columns)),
            },
        )

    feature_columns = [col for col in df.columns if col not in REQUIRED_LEAKAGE_COLUMNS]
    namespace_violations = sorted(
        [
            col
            for col in feature_columns
            if not (col.endswith("_diff") or col in ALLOWED_NON_DIFF_FEATURE_COLUMNS)
        ]
    )
    if namespace_violations:
        return _build_gate_result(
            passed=False,
            blocking_rule="R004_LEAKAGE_NAMESPACE_VIOLATION",
            reason="Feature namespace contract requires *_diff or explicit allowlist columns.",
            evidence={
                "violating_columns": namespace_violations,
                "violating_column_count": int(len(namespace_violations)),
            },
        )

    return _build_gate_result(
        passed=True,
        blocking_rule=None,
        reason="Leakage contract satisfied.",
        evidence={
            "row_count": int(len(df)),
            "feature_column_count": int(len(feature_columns)),
        },
    )

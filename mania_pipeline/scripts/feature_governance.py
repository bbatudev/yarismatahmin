from __future__ import annotations

import json
import math
from collections import Counter
from typing import Any

DEFAULT_ACTION_DOMAIN = ("keep", "drop", "candidate")
LEDGER_REQUIRED_COLUMNS = ("feature", "group", "default_action", "evidence")

MEN_ONLY_FEATURES = {
    "CoachTenureYears_diff",
    "FTr_diff",
    "MasseyPct_diff",
    "MasseyAvgRank_diff",
    "ProgramAge_diff",
}


def _as_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
    return None


def infer_feature_group(feature_name: str) -> str:
    lowered = feature_name.lower()

    if "seed" in lowered:
        return "seed"
    if "massey" in lowered or lowered.startswith("net"):
        return "rating"
    if any(token in lowered for token in ("efg", "tov", "orb", "ftr", "netrtg", "truemargin", "pace")):
        return "four_factors"
    if any(token in lowered for token in ("winpct", "last7", "last14", "last21", "rolling", "streak")):
        return "form"
    if any(token in lowered for token in ("rusty", "back_to_back", "rest", "fatigue")):
        return "fatigue"
    if any(token in lowered for token in ("conference", "conf", "coach", "program")):
        return "context"
    return "other"


def _normalize_importance_vector(feature_columns: list[str], raw_importance: Any) -> dict[str, float | None]:
    if raw_importance is None:
        return {feature: None for feature in feature_columns}

    if hasattr(raw_importance, "tolist"):
        raw_importance = raw_importance.tolist()

    if not isinstance(raw_importance, (list, tuple)):
        return {feature: None for feature in feature_columns}

    values = list(raw_importance)
    if len(values) != len(feature_columns):
        return {feature: None for feature in feature_columns}

    return {
        feature: _as_float_or_none(values[idx])
        for idx, feature in enumerate(feature_columns)
    }


def _build_rank_map(importance_by_feature: dict[str, float | None]) -> dict[str, int]:
    ranked_features = sorted(
        importance_by_feature.keys(),
        key=lambda feature: (
            -(importance_by_feature[feature] if importance_by_feature[feature] is not None else float("-inf")),
            feature,
        ),
    )
    return {feature: idx for idx, feature in enumerate(ranked_features)}


def _split_metric_snapshot(metrics_by_split: dict[str, Any]) -> dict[str, dict[str, float | None]]:
    snapshot: dict[str, dict[str, float | None]] = {}
    for split_label in ("Train", "Val", "Test"):
        split_metrics = metrics_by_split.get(split_label, {}) if isinstance(metrics_by_split, dict) else {}
        if not isinstance(split_metrics, dict):
            split_metrics = {}
        snapshot[split_label] = {
            "brier": _as_float_or_none(split_metrics.get("brier")),
            "logloss": _as_float_or_none(split_metrics.get("logloss")),
            "auc": _as_float_or_none(split_metrics.get("auc")),
        }
    return snapshot


def derive_default_action(*, importance: float | None, rank: int, feature_count: int) -> str:
    if feature_count <= 0:
        return "candidate"

    if importance is None:
        return "candidate"

    if importance <= 0.0:
        return "drop"

    rank_pct = (rank / max(feature_count - 1, 1)) if feature_count > 1 else 0.0
    if rank_pct >= 0.85:
        return "candidate"

    return "keep"


def _build_evidence(
    *,
    gender_key: str,
    importance: float | None,
    rank: int,
    feature_count: int,
    metrics_by_split: dict[str, Any],
) -> str:
    rank_pct = (rank / max(feature_count - 1, 1)) if feature_count > 1 else 0.0
    payload = {
        "gender": gender_key,
        "importance": {
            "value": importance,
            "rank": int(rank),
            "rank_pct": round(float(rank_pct), 6),
        },
        "metrics_by_split": _split_metric_snapshot(metrics_by_split),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def build_governance_ledger_rows(
    *,
    genders_payload: dict[str, Any],
    model_importances: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    model_importances = model_importances or {}

    for gender_key in ("men", "women"):
        gender_payload = genders_payload.get(gender_key, {}) if isinstance(genders_payload, dict) else {}
        if not isinstance(gender_payload, dict):
            continue

        snapshot = gender_payload.get("feature_snapshot", {})
        feature_columns = snapshot.get("feature_columns") if isinstance(snapshot, dict) else None
        if not isinstance(feature_columns, list) or not feature_columns:
            continue

        metrics_by_split = gender_payload.get("metrics_by_split", {})
        importance_by_feature = _normalize_importance_vector(feature_columns, model_importances.get(gender_key))
        rank_map = _build_rank_map(importance_by_feature)
        feature_count = len(feature_columns)

        for feature_name in sorted(feature_columns):
            if gender_key == "women" and feature_name in MEN_ONLY_FEATURES:
                continue

            importance = importance_by_feature.get(feature_name)
            rank = rank_map.get(feature_name, feature_count - 1)
            default_action = derive_default_action(
                importance=importance,
                rank=rank,
                feature_count=feature_count,
            )

            rows.append(
                {
                    "feature": feature_name,
                    "group": infer_feature_group(feature_name),
                    "default_action": default_action,
                    "evidence": _build_evidence(
                        gender_key=gender_key,
                        importance=importance,
                        rank=rank,
                        feature_count=feature_count,
                        metrics_by_split=metrics_by_split,
                    ),
                    "gender": gender_key,
                }
            )

    rows.sort(key=lambda row: (row.get("gender", ""), row.get("feature", "")))
    return rows


def build_governance_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    action_counter = Counter(row.get("default_action") for row in rows)
    group_counter = Counter(row.get("group") for row in rows)

    default_action_counts = {
        action: int(action_counter.get(action, 0))
        for action in DEFAULT_ACTION_DOMAIN
    }

    return {
        "row_count": int(len(rows)),
        "default_action_counts": default_action_counts,
        "group_counts": {group: int(count) for group, count in sorted(group_counter.items())},
    }

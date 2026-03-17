from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from typing import Any

DEFAULT_ACTION_DOMAIN = ("keep", "drop", "candidate")
LEDGER_REQUIRED_COLUMNS = ("feature", "group", "default_action", "evidence")

MEN_ONLY_FEATURES = {
    "CoachTenureYears_diff",
    "FTr_diff",
    "MasseyPct_diff",
    "MasseyAvgRank_diff",
    "MasseyRankStd_diff",
    "MasseyPctSpread_diff",
    "MasseyOrdinalRange_diff",
    "ProgramAge_diff",
}

ABLATION_TARGET_SPLITS = ("Val", "Test")
DEFAULT_MAX_ABLATION_GROUPS = 3
ABLATION_ALLOWED_SKIP_REASONS = (
    "group_missing",
    "no_gender_features",
    "split_empty",
    "empty_high_prob_band",
)


def _as_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
    return None


def _delta_or_none(*, current: Any, baseline: Any) -> float | None:
    current_value = _as_float_or_none(current)
    baseline_value = _as_float_or_none(baseline)
    if current_value is None or baseline_value is None:
        return None
    return float(current_value - baseline_value)


def infer_feature_group(feature_name: str) -> str:
    lowered = feature_name.lower()

    if "clash" in lowered:
        return "style"
    if "mispricing" in lowered:
        return "seed"
    if "seed" in lowered:
        return "seed"
    if "massey" in lowered or lowered.startswith("net") or "pyth" in lowered or "luck" in lowered:
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


def _action_priority(action: Any) -> int:
    if action == "drop":
        return 2
    if action == "candidate":
        return 1
    return 0


def select_suspicious_groups(
    rows: list[dict[str, Any]],
    *,
    max_groups: int = DEFAULT_MAX_ABLATION_GROUPS,
) -> list[str]:
    max_groups = max(1, int(max_groups))
    score_by_group: Counter[str] = Counter()
    size_by_group: Counter[str] = Counter()

    for row in rows:
        group = row.get("group")
        if not isinstance(group, str) or not group:
            continue
        size_by_group[group] += 1
        score_by_group[group] += _action_priority(row.get("default_action"))

    ordered_groups = sorted(
        size_by_group.keys(),
        key=lambda group: (-score_by_group[group], -size_by_group[group], group),
    )

    selected = [group for group in ordered_groups if score_by_group[group] > 0][:max_groups]
    if selected:
        return selected
    return ordered_groups[:max_groups]


def build_group_gender_feature_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    index: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for row in rows:
        group = row.get("group")
        gender = row.get("gender")
        feature = row.get("feature")
        if not isinstance(group, str) or not group:
            continue
        if not isinstance(gender, str) or not gender:
            continue
        if not isinstance(feature, str) or not feature:
            continue
        index[group][gender].add(feature)

    result: dict[str, dict[str, list[str]]] = {}
    for group in sorted(index.keys()):
        result[group] = {}
        for gender in sorted(index[group].keys()):
            result[group][gender] = sorted(index[group][gender])
    return result


def _extract_high_prob_payload(split_payload: Any) -> dict[str, Any]:
    if not isinstance(split_payload, dict):
        return {}
    high_prob = split_payload.get("high_prob_band")
    if not isinstance(high_prob, dict):
        return {}
    return high_prob


def _resolve_split_reason(*, baseline_calibration: Any, ablated_calibration: Any) -> str | None:
    baseline_payload = baseline_calibration if isinstance(baseline_calibration, dict) else {}
    ablated_payload = ablated_calibration if isinstance(ablated_calibration, dict) else {}

    if baseline_payload.get("reason") == "split_empty" or ablated_payload.get("reason") == "split_empty":
        return "split_empty"

    baseline_high = _extract_high_prob_payload(baseline_payload)
    ablated_high = _extract_high_prob_payload(ablated_payload)
    if baseline_high.get("reason") == "empty_high_prob_band" or ablated_high.get("reason") == "empty_high_prob_band":
        return "empty_high_prob_band"

    return None


def compute_ablation_split_deltas(
    *,
    baseline_metrics_by_split: dict[str, Any],
    ablated_metrics_by_split: dict[str, Any],
    baseline_calibration_by_split: dict[str, Any],
    ablated_calibration_by_split: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    deltas: dict[str, dict[str, Any]] = {}

    for split_label in ABLATION_TARGET_SPLITS:
        baseline_metrics = baseline_metrics_by_split.get(split_label, {}) if isinstance(baseline_metrics_by_split, dict) else {}
        ablated_metrics = ablated_metrics_by_split.get(split_label, {}) if isinstance(ablated_metrics_by_split, dict) else {}
        baseline_calibration = (
            baseline_calibration_by_split.get(split_label, {}) if isinstance(baseline_calibration_by_split, dict) else {}
        )
        ablated_calibration = (
            ablated_calibration_by_split.get(split_label, {}) if isinstance(ablated_calibration_by_split, dict) else {}
        )

        baseline_high = _extract_high_prob_payload(baseline_calibration)
        ablated_high = _extract_high_prob_payload(ablated_calibration)

        split_reason = _resolve_split_reason(
            baseline_calibration=baseline_calibration,
            ablated_calibration=ablated_calibration,
        )

        deltas[split_label] = {
            "delta_brier": _delta_or_none(
                current=ablated_metrics.get("brier"),
                baseline=baseline_metrics.get("brier"),
            ),
            "delta_logloss": _delta_or_none(
                current=ablated_metrics.get("logloss"),
                baseline=baseline_metrics.get("logloss"),
            ),
            "delta_auc": _delta_or_none(
                current=ablated_metrics.get("auc"),
                baseline=baseline_metrics.get("auc"),
            ),
            "delta_calibration": {
                "delta_ece": _delta_or_none(
                    current=ablated_calibration.get("ece") if isinstance(ablated_calibration, dict) else None,
                    baseline=baseline_calibration.get("ece") if isinstance(baseline_calibration, dict) else None,
                ),
                "delta_wmae": _delta_or_none(
                    current=ablated_calibration.get("wmae") if isinstance(ablated_calibration, dict) else None,
                    baseline=baseline_calibration.get("wmae") if isinstance(baseline_calibration, dict) else None,
                ),
                "delta_high_prob_gap": _delta_or_none(
                    current=ablated_high.get("gap"),
                    baseline=baseline_high.get("gap"),
                ),
                "baseline_high_prob_reason": baseline_high.get("reason"),
                "ablated_high_prob_reason": ablated_high.get("reason"),
            },
            "reason": split_reason,
        }

    return deltas


def normalize_skip_reason(reason: Any) -> str:
    if isinstance(reason, str) and reason in ABLATION_ALLOWED_SKIP_REASONS:
        return reason
    return "no_gender_features"


def build_ablation_summary(
    *,
    selected_groups: list[str],
    ablation_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    executed_group_count = 0
    skipped_groups: list[dict[str, str]] = []

    for group_payload in ablation_groups:
        status = group_payload.get("status")
        group_name = group_payload.get("group")
        if status == "executed":
            executed_group_count += 1
            continue

        skipped_groups.append(
            {
                "group": str(group_name),
                "reason": normalize_skip_reason(group_payload.get("reason")),
            }
        )

    return {
        "selected_group_count": int(len(selected_groups)),
        "executed_group_count": int(executed_group_count),
        "skipped_groups": skipped_groups,
    }

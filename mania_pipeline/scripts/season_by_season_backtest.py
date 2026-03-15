from __future__ import annotations

import argparse
import importlib.util
import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MEN_PATH = SCRIPT_DIR.parent / "artifacts" / "data" / "processed_features_men.csv"
DEFAULT_WOMEN_PATH = SCRIPT_DIR.parent / "artifacts" / "data" / "processed_features_women.csv"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR.parent / "artifacts" / "reports"


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_train_module():
    module_path = SCRIPT_DIR / "03_lgbm_train.py"
    spec = importlib.util.spec_from_file_location("lgbm_train_module", module_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"could not load module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _as_float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        val = float(value)
        if np.isfinite(val):
            return val
    return None


def _prepare_season_frame(df: pd.DataFrame, eval_season: int) -> tuple[pd.DataFrame | None, str | None]:
    frame = df.copy()
    seasons = pd.to_numeric(frame.get("Season"), errors="coerce")
    if seasons.isna().any():
        return None, "season_column_not_numeric"

    seasons = seasons.astype(int)
    train_mask = seasons <= int(eval_season) - 2
    val_mask = seasons == int(eval_season) - 1
    test_mask = seasons == int(eval_season)

    train_rows = int(train_mask.sum())
    val_rows = int(val_mask.sum())
    test_rows = int(test_mask.sum())

    if train_rows <= 0:
        return None, "train_rows_empty"
    if val_rows <= 0:
        return None, "val_rows_empty"
    if test_rows <= 0:
        return None, "test_rows_empty"

    frame.loc[:, "Split"] = "Unused"
    frame.loc[train_mask, "Split"] = "Train"
    frame.loc[val_mask, "Split"] = "Val"
    frame.loc[test_mask, "Split"] = "Test"
    frame = frame[frame["Split"].isin(("Train", "Val", "Test"))].copy()

    return frame, None


def _run_one_season(
    *,
    train_module: Any,
    base_df: pd.DataFrame,
    gender_label: str,
    eval_season: int,
    profile: str,
    seed: int,
    quiet_train: bool,
) -> dict[str, Any]:
    prepared_df, prepare_error = _prepare_season_frame(base_df, eval_season)
    if prepare_error is not None:
        return {
            "season": int(eval_season),
            "status": "skipped",
            "reason": prepare_error,
        }

    train_rows = int((prepared_df["Split"] == "Train").sum())
    val_rows = int((prepared_df["Split"] == "Val").sum())
    test_rows = int((prepared_df["Split"] == "Test").sum())

    random_state = int(seed) + int(eval_season)

    try:
        if quiet_train:
            log_buffer = io.StringIO()
            with redirect_stdout(log_buffer):
                _, payload = train_module.train_baseline(
                    prepared_df,
                    gender=gender_label,
                    random_state=random_state,
                    profile=profile,
                )
        else:
            _, payload = train_module.train_baseline(
                prepared_df,
                gender=gender_label,
                random_state=random_state,
                profile=profile,
            )

        metrics_by_split = payload.get("metrics_by_split", {}) if isinstance(payload, dict) else {}
        test_metrics = metrics_by_split.get("Test", {}) if isinstance(metrics_by_split, dict) else {}
        val_metrics = metrics_by_split.get("Val", {}) if isinstance(metrics_by_split, dict) else {}

        return {
            "season": int(eval_season),
            "status": "passed",
            "reason": None,
            "row_counts": {
                "train": train_rows,
                "val": val_rows,
                "test": test_rows,
            },
            "metrics": {
                "val_brier": _as_float_or_none(val_metrics.get("brier")),
                "test_brier": _as_float_or_none(test_metrics.get("brier")),
                "test_logloss": _as_float_or_none(test_metrics.get("logloss")),
                "test_auc": _as_float_or_none(test_metrics.get("auc")),
            },
        }
    except Exception as exc:
        return {
            "season": int(eval_season),
            "status": "failed",
            "reason": f"{exc.__class__.__name__}:{exc}",
            "row_counts": {
                "train": train_rows,
                "val": val_rows,
                "test": test_rows,
            },
        }


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed_rows = [r for r in rows if r.get("status") == "passed"]
    test_briers = [
        float(r.get("metrics", {}).get("test_brier"))
        for r in passed_rows
        if isinstance(r.get("metrics", {}).get("test_brier"), (int, float))
    ]
    if not test_briers:
        return {
            "season_count": len(rows),
            "passed_count": len(passed_rows),
            "mean_test_brier": None,
            "median_test_brier": None,
            "best_season": None,
            "worst_season": None,
        }

    best_row = min(
        (r for r in passed_rows if isinstance(r.get("metrics", {}).get("test_brier"), (int, float))),
        key=lambda r: float(r.get("metrics", {}).get("test_brier")),
    )
    worst_row = max(
        (r for r in passed_rows if isinstance(r.get("metrics", {}).get("test_brier"), (int, float))),
        key=lambda r: float(r.get("metrics", {}).get("test_brier")),
    )

    return {
        "season_count": len(rows),
        "passed_count": len(passed_rows),
        "mean_test_brier": float(np.mean(test_briers)),
        "median_test_brier": float(np.median(test_briers)),
        "best_season": {
            "season": int(best_row["season"]),
            "test_brier": float(best_row["metrics"]["test_brier"]),
        },
        "worst_season": {
            "season": int(worst_row["season"]),
            "test_brier": float(worst_row["metrics"]["test_brier"]),
        },
    }


def _flatten_for_csv(by_gender: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for gender_key, payload in by_gender.items():
        season_rows = payload.get("rows", []) if isinstance(payload, dict) else []
        for row in season_rows:
            metrics = row.get("metrics", {}) if isinstance(row, dict) else {}
            counts = row.get("row_counts", {}) if isinstance(row, dict) else {}
            rows.append(
                {
                    "gender": gender_key,
                    "season": row.get("season"),
                    "status": row.get("status"),
                    "reason": row.get("reason"),
                    "train_rows": counts.get("train"),
                    "val_rows": counts.get("val"),
                    "test_rows": counts.get("test"),
                    "val_brier": metrics.get("val_brier"),
                    "test_brier": metrics.get("test_brier"),
                    "test_logloss": metrics.get("test_logloss"),
                    "test_auc": metrics.get("test_auc"),
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run season-by-season walk-forward backtest for men and women."
    )
    parser.add_argument("--men-path", type=Path, default=DEFAULT_MEN_PATH)
    parser.add_argument("--women-path", type=Path, default=DEFAULT_WOMEN_PATH)
    parser.add_argument("--profile", type=str, default="quality_v1", choices=("baseline", "quality_v1"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start-season", type=int, default=2018)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--quiet-train", action="store_true", default=False)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-csv", type=Path, default=None)
    args = parser.parse_args()

    if not args.men_path.exists() or not args.women_path.exists():
        raise FileNotFoundError(
            f"feature files not found: men={args.men_path.exists()} women={args.women_path.exists()}"
        )

    train_module = _load_train_module()
    men_df = pd.read_csv(args.men_path)
    women_df = pd.read_csv(args.women_path)

    output_slug = _now_slug()
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_json = args.output_json or (DEFAULT_OUTPUT_DIR / f"season_backtest_{output_slug}.json")
    output_csv = args.output_csv or (DEFAULT_OUTPUT_DIR / f"season_backtest_{output_slug}.csv")

    by_gender: dict[str, Any] = {}
    for gender_key, gender_label, df in (
        ("men", "M", men_df),
        ("women", "W", women_df),
    ):
        available_seasons = sorted(int(s) for s in pd.to_numeric(df["Season"], errors="coerce").dropna().astype(int).unique())
        target_seasons = [s for s in available_seasons if args.start_season <= s <= args.end_season]

        rows = []
        print(f"[{gender_key}] target seasons: {target_seasons}")
        for season in target_seasons:
            print(f"[{gender_key}] season {season} ...", end=" ", flush=True)
            row = _run_one_season(
                train_module=train_module,
                base_df=df,
                gender_label=gender_label,
                eval_season=season,
                profile=args.profile,
                seed=args.seed,
                quiet_train=args.quiet_train,
            )
            rows.append(row)
            print(row.get("status"))

        by_gender[gender_key] = {
            "rows": rows,
            "summary": _summarize_rows(rows),
        }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "config": {
            "men_path": str(args.men_path),
            "women_path": str(args.women_path),
            "profile": args.profile,
            "seed": int(args.seed),
            "start_season": int(args.start_season),
            "end_season": int(args.end_season),
        },
        "by_gender": by_gender,
    }

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_frame = _flatten_for_csv(by_gender)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    csv_frame.to_csv(output_csv, index=False)

    print("\n=== season-by-season backtest complete ===")
    print(f"json: {output_json}")
    print(f"csv : {output_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

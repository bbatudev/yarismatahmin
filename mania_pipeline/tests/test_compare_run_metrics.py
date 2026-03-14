import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "compare_run_metrics.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("compare_run_metrics_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_metadata(path: Path, *, run_id: str, men_brier: float, women_brier: float, men_auc: float, women_auc: float):
    payload = {
        "run_id": run_id,
        "stage_outputs": {
            "train": {
                "metrics_by_split": {
                    "men": {"Test": {"brier": men_brier, "logloss": 0.50, "auc": men_auc}},
                    "women": {"Test": {"brier": women_brier, "logloss": 0.45, "auc": women_auc}},
                }
            },
            "eval_report": {
                "ensemble": {
                    "aggregate": {
                        "decision": "hold_baseline",
                    }
                }
            },
            "artifact": {
                "readiness": {
                    "status": "ready",
                }
            },
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_comparison_computes_metric_deltas(tmp_path):
    module = _load_module()

    baseline = tmp_path / "baseline" / "run_metadata.json"
    candidate = tmp_path / "candidate" / "run_metadata.json"

    _write_metadata(baseline, run_id="baseline_1", men_brier=0.20, women_brier=0.18, men_auc=0.75, women_auc=0.80)
    _write_metadata(candidate, run_id="candidate_1", men_brier=0.19, women_brier=0.19, men_auc=0.76, women_auc=0.79)

    payload = module.build_comparison(
        baseline_metadata=json.loads(baseline.read_text(encoding="utf-8")),
        candidate_metadata=json.loads(candidate.read_text(encoding="utf-8")),
    )

    assert payload["baseline_run_id"] == "baseline_1"
    assert payload["candidate_run_id"] == "candidate_1"
    assert payload["by_gender"]["men"]["delta"]["brier"] == pytest.approx(-0.01)
    assert payload["by_gender"]["women"]["delta"]["brier"] == pytest.approx(0.01)
    assert payload["aux"]["candidate"]["readiness_status"] == "ready"


def test_main_writes_output_json_when_requested(tmp_path):
    module = _load_module()

    baseline_run = tmp_path / "baseline_run"
    candidate_run = tmp_path / "candidate_run"
    _write_metadata(baseline_run / "run_metadata.json", run_id="b", men_brier=0.2, women_brier=0.2, men_auc=0.7, women_auc=0.7)
    _write_metadata(candidate_run / "run_metadata.json", run_id="c", men_brier=0.19, women_brier=0.21, men_auc=0.71, women_auc=0.69)

    out = tmp_path / "comparison.json"
    exit_code = module.main(
        [
            "--baseline-run",
            str(baseline_run),
            "--candidate-run",
            str(candidate_run),
            "--output-json",
            str(out),
        ]
    )

    assert exit_code == 0
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["candidate_run_id"] == "c"

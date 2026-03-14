import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
MODULE_AVAILABLE = SCRIPT_PATH.exists()
CANONICAL_STAGES = ("feature", "train", "eval_report", "artifact")
REQUIRED_EVENT_FIELDS = {"stage", "status", "started_at", "finished_at", "duration_ms", "error"}



def _load_run_pipeline_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_cli", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def run_pipeline_module():
    if not MODULE_AVAILABLE:
        pytest.skip(f"Missing canonical orchestrator script: {SCRIPT_PATH}. Implement it in T02.")
    return _load_run_pipeline_module()



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



def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]



def _latest_run_dir(artifacts_root: Path) -> Path:
    runs = [p for p in artifacts_root.iterdir() if p.is_dir()]
    assert runs, f"no run directories found under {artifacts_root}"
    return max(runs, key=lambda p: p.stat().st_mtime_ns)



def _assert_iso8601(value: str, *, field_name: str):
    assert isinstance(value, str) and value.strip(), f"{field_name} must be a non-empty string"
    datetime.fromisoformat(value.replace("Z", "+00:00"))



def _assert_event_contract(events):
    assert events, "stage_events.jsonl must contain at least one event"
    for event in events:
        assert isinstance(event, dict), "each stage event must be a JSON object"

        missing = REQUIRED_EVENT_FIELDS - set(event.keys())
        assert not missing, f"event missing required fields: {sorted(missing)}"

        assert event["stage"] in CANONICAL_STAGES, f"unexpected stage: {event['stage']}"
        assert event["status"] in {"started", "succeeded", "failed"}, (
            f"unexpected status: {event['status']}"
        )

        _assert_iso8601(event["started_at"], field_name="started_at")

        if event["status"] == "started":
            assert event["finished_at"] in (None, ""), (
                "started events should not have finished_at"
            )
            assert event["duration_ms"] in (None, 0), "started event duration must be null/0"
            assert event["error"] is None, "started event error must be null"
        else:
            _assert_iso8601(event["finished_at"], field_name="finished_at")
            assert isinstance(event["duration_ms"], (int, float)), "duration_ms must be numeric"
            assert event["duration_ms"] >= 0, "duration_ms must be non-negative"

            if event["status"] == "succeeded":
                assert event["error"] is None, "succeeded event error must be null"
            else:
                assert event["error"] is not None, "failed event must include error payload"



def _install_stubbed_stages(module, monkeypatch, failing_stage=None):
    handlers = {}
    seen = []

    for stage in CANONICAL_STAGES:
        if stage == failing_stage:

            def _fail(context, stage_name=stage):
                seen.append(stage_name)
                raise RuntimeError(f"forced failure at {stage_name}")

            handlers[stage] = _fail
        else:

            def _ok(context, stage_name=stage):
                seen.append(stage_name)
                if stage_name == "train":
                    return {
                        "models": {"men": "models/men.pkl", "women": "models/women.pkl"},
                        "metrics_by_split": {
                            "men": {
                                "Train": {"brier": 0.20, "logloss": 0.58, "auc": 0.72},
                                "Val": {"brier": 0.21, "logloss": 0.60, "auc": 0.70},
                                "Test": {"brier": 0.22, "logloss": 0.62, "auc": 0.68},
                            },
                            "women": {
                                "Train": {"brier": 0.24, "logloss": 0.63, "auc": 0.66},
                                "Val": {"brier": 0.25, "logloss": 0.65, "auc": 0.64},
                                "Test": {"brier": 0.26, "logloss": 0.67, "auc": 0.62},
                            },
                        },
                        "feature_snapshot": {
                            "men": {"feature_columns": ["NetRtg_diff"], "feature_count": 1},
                            "women": {"feature_columns": ["SeedNum_diff"], "feature_count": 1},
                        },
                        "best_iteration": {"men": 11, "women": 9},
                    }
                return {"stage": stage_name}

            handlers[stage] = _ok

    monkeypatch.setattr(module, "CANONICAL_STAGES", CANONICAL_STAGES, raising=False)
    monkeypatch.setattr(module, "STAGE_HANDLERS", handlers, raising=False)
    return seen



def test_run_pipeline_script_exists_for_cli_contract_testing():
    assert MODULE_AVAILABLE, (
        f"Missing canonical orchestrator script: {SCRIPT_PATH}. "
        "Implement it in T02."
    )



def test_cli_writes_started_and_succeeded_events_with_contract_fields(tmp_path, monkeypatch, run_pipeline_module):
    seen = _install_stubbed_stages(run_pipeline_module, monkeypatch)

    artifacts_root = tmp_path / "runs"
    exit_code = _invoke_main(
        run_pipeline_module,
        ["--seed", "17", "--run-label", "pytest-success", "--artifacts-root", str(artifacts_root)],
    )

    assert exit_code == 0
    assert seen == list(CANONICAL_STAGES), "stages should execute in canonical order"

    run_dir = _latest_run_dir(artifacts_root)
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["seed"] == 17, "CLI seed must propagate into run metadata"

    train_payload = metadata["stage_outputs"]["train"]
    assert {"metrics_by_split", "feature_snapshot", "models"}.issubset(train_payload.keys())
    assert train_payload["metrics_by_split"]["men"]["Test"]["brier"] == pytest.approx(0.22)
    assert train_payload["metrics_by_split"]["women"]["Test"]["brier"] == pytest.approx(0.26)

    events = _read_jsonl(run_dir / "stage_events.jsonl")
    _assert_event_contract(events)

    assert [(e["stage"], e["status"]) for e in events] == [
        ("feature", "started"),
        ("feature", "succeeded"),
        ("train", "started"),
        ("train", "succeeded"),
        ("eval_report", "started"),
        ("eval_report", "succeeded"),
        ("artifact", "started"),
        ("artifact", "succeeded"),
    ]



def test_cli_writes_failed_event_with_error_payload_and_stops_pipeline(tmp_path, monkeypatch, run_pipeline_module):
    seen = _install_stubbed_stages(run_pipeline_module, monkeypatch, failing_stage="train")

    artifacts_root = tmp_path / "runs"
    exit_code = _invoke_main(
        run_pipeline_module,
        ["--seed", "23", "--run-label", "pytest-fail", "--artifacts-root", str(artifacts_root)],
    )

    assert exit_code != 0, "pipeline should return non-zero on stage failure"
    assert seen == ["feature", "train"], "pipeline should stop after the first failing stage"

    run_dir = _latest_run_dir(artifacts_root)
    events = _read_jsonl(run_dir / "stage_events.jsonl")
    _assert_event_contract(events)

    assert [(e["stage"], e["status"]) for e in events] == [
        ("feature", "started"),
        ("feature", "succeeded"),
        ("train", "started"),
        ("train", "failed"),
    ]

    failed_event = events[-1]
    assert "forced failure at train" in json.dumps(failed_event["error"], ensure_ascii=False)

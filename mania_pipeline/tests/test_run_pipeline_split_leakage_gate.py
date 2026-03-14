import importlib.util
import json
import types
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
CANONICAL_STAGES = ("feature", "train", "eval_report", "artifact")


def _load_run_pipeline_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test_split_gate", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _gate_payload(*, passed: bool, blocking_rule: str | None, reason: str):
    return {
        "pass": passed,
        "blocking_rule": blocking_rule,
        "reason": reason,
        "evidence": {},
    }


def _valid_feature_df(split_label: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Season": [2023],
            "TeamA": [1001],
            "TeamB": [2001],
            "Target": [1],
            "Split": [split_label],
            "NetRtg_diff": [1.5],
            "SeedNum_diff": [-2],
            "Heavy_Favorite": [0],
            "Is_FirstWeekend": [1],
        }
    )


def _stub_feature_module(tmp_path: Path):
    module = types.SimpleNamespace()
    module.DATA_DIR = ""
    module.OUT_DIR = str(tmp_path / "feature_data")

    def _run_pipeline(gender: str):
        del gender
        return _valid_feature_df("Val")

    module.run_pipeline = _run_pipeline
    return module


def _install_stubbed_non_feature_handlers(run_pipeline_module, monkeypatch):
    seen = []

    def _ok(stage_name):
        def _inner(context):
            del context
            seen.append(stage_name)
            return {"stage": stage_name}

        return _inner

    handlers = {
        "feature": run_pipeline_module.stage_feature,
        "train": _ok("train"),
        "eval_report": _ok("eval_report"),
        "artifact": _ok("artifact"),
    }
    monkeypatch.setattr(run_pipeline_module, "CANONICAL_STAGES", CANONICAL_STAGES, raising=False)
    monkeypatch.setattr(run_pipeline_module, "STAGE_HANDLERS", handlers, raising=False)
    return seen


def test_cli_feature_stage_fails_fast_with_blocking_rule(tmp_path, monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()
    feature_module = _stub_feature_module(tmp_path)

    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: feature_module,
        raising=False,
    )
    monkeypatch.setattr(
        run_pipeline_module,
        "validate_split_contract",
        lambda df: _gate_payload(passed=True, blocking_rule=None, reason="split ok"),
        raising=False,
    )
    monkeypatch.setattr(
        run_pipeline_module,
        "validate_leakage_contract",
        lambda df: _gate_payload(
            passed=False,
            blocking_rule="R004_LEAKAGE_FORBIDDEN_COLUMNS",
            reason="forbidden columns detected",
        ),
        raising=False,
    )

    _install_stubbed_non_feature_handlers(run_pipeline_module, monkeypatch)

    artifacts_root = tmp_path / "runs"
    exit_code = _invoke_main(
        run_pipeline_module,
        ["--seed", "42", "--run-label", "gate-fail", "--artifacts-root", str(artifacts_root)],
    )

    assert exit_code != 0, "pipeline should return non-zero when feature gate fails"

    run_dir = _latest_run_dir(artifacts_root)
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    events = _read_jsonl(run_dir / "stage_events.jsonl")

    assert metadata["status"] == "failed"
    assert metadata["failed_stage"] == "feature"

    assert [(e["stage"], e["status"]) for e in events] == [
        ("feature", "started"),
        ("feature", "failed"),
    ]
    assert "R004_LEAKAGE_FORBIDDEN_COLUMNS" in events[-1]["error"]["message"]


def test_cli_feature_stage_persists_gender_gate_payloads_on_pass(tmp_path, monkeypatch):
    run_pipeline_module = _load_run_pipeline_module()
    feature_module = _stub_feature_module(tmp_path)

    monkeypatch.setattr(
        run_pipeline_module,
        "_load_script_module",
        lambda filename, module_name: feature_module,
        raising=False,
    )
    monkeypatch.setattr(
        run_pipeline_module,
        "validate_split_contract",
        lambda df: _gate_payload(passed=True, blocking_rule=None, reason="split ok"),
        raising=False,
    )
    monkeypatch.setattr(
        run_pipeline_module,
        "validate_leakage_contract",
        lambda df: _gate_payload(passed=True, blocking_rule=None, reason="leakage ok"),
        raising=False,
    )

    seen = _install_stubbed_non_feature_handlers(run_pipeline_module, monkeypatch)

    artifacts_root = tmp_path / "runs"
    exit_code = _invoke_main(
        run_pipeline_module,
        ["--seed", "42", "--run-label", "gate-pass", "--artifacts-root", str(artifacts_root)],
    )

    assert exit_code == 0
    assert seen == ["train", "eval_report", "artifact"]

    run_dir = _latest_run_dir(artifacts_root)
    metadata = json.loads((run_dir / "run_metadata.json").read_text(encoding="utf-8"))
    events = _read_jsonl(run_dir / "stage_events.jsonl")

    gates = metadata["stage_outputs"]["feature"]["gates"]
    assert gates["men"]["pass"] is True
    assert gates["women"]["pass"] is True

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

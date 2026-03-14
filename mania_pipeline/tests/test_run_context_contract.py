import importlib.util
import re
from datetime import datetime
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_pipeline.py"
MODULE_AVAILABLE = SCRIPT_PATH.exists()
REQUIRED_CONTEXT_FIELDS = {"run_id", "seed", "git_commit", "started_at", "command", "cwd"}



def _load_run_pipeline_module():
    spec = importlib.util.spec_from_file_location("run_pipeline_under_test", SCRIPT_PATH)
    assert spec and spec.loader, f"Could not load module spec from {SCRIPT_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def run_pipeline_module():
    if not MODULE_AVAILABLE:
        pytest.skip(f"Missing canonical orchestrator script: {SCRIPT_PATH}. Implement it in T02.")
    return _load_run_pipeline_module()



def _assert_iso8601(value: str, *, field_name: str):
    assert isinstance(value, str) and value.strip(), f"{field_name} must be a non-empty string"
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        pytest.fail(f"{field_name} must be ISO-8601 compatible, got: {value!r} ({exc})")



def _assert_run_context_contract(context: dict):
    assert isinstance(context, dict), "run context must be a dict"

    missing = REQUIRED_CONTEXT_FIELDS - set(context.keys())
    assert not missing, f"run context missing required fields: {sorted(missing)}"

    run_id = context["run_id"]
    assert isinstance(run_id, str) and run_id.strip(), "run_id must be a non-empty string"
    assert re.match(r"^[A-Za-z0-9_.:-]+$", run_id), "run_id should be filesystem-safe"

    seed = context["seed"]
    assert isinstance(seed, int), f"seed must be int, got {type(seed).__name__}"

    git_commit = context["git_commit"]
    assert isinstance(git_commit, str) and git_commit.strip(), "git_commit must be non-empty string"

    _assert_iso8601(context["started_at"], field_name="started_at")

    command = context["command"]
    assert isinstance(command, str) and command.strip(), "command must be a non-empty string"

    cwd = context["cwd"]
    assert isinstance(cwd, str) and cwd.strip(), "cwd must be a non-empty string"



def test_run_pipeline_script_exists_for_contract_testing():
    assert MODULE_AVAILABLE, (
        f"Missing canonical orchestrator script: {SCRIPT_PATH}. "
        "Implement it in T02."
    )



def test_build_run_context_contract_and_seed_propagation(run_pipeline_module):
    build_run_context = getattr(run_pipeline_module, "build_run_context", None)
    assert callable(build_run_context), (
        "run_pipeline.py must expose build_run_context(seed=...) for contract tests"
    )

    context = build_run_context(seed=42)
    _assert_run_context_contract(context)
    assert context["seed"] == 42, "seed should be carried into run context unchanged"


@pytest.mark.parametrize("missing_key", sorted(REQUIRED_CONTEXT_FIELDS))
def test_run_context_contract_fails_when_required_field_is_missing(run_pipeline_module, missing_key: str):
    build_run_context = getattr(run_pipeline_module, "build_run_context", None)
    assert callable(build_run_context), (
        "run_pipeline.py must expose build_run_context(seed=...) for contract tests"
    )

    context = build_run_context(seed=7)
    _assert_run_context_contract(context)

    broken = dict(context)
    broken.pop(missing_key)

    with pytest.raises(AssertionError, match=missing_key):
        _assert_run_context_contract(broken)

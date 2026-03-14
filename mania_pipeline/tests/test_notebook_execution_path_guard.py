import json
import re
from pathlib import Path


NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "scripts" / "03_model_training.ipynb"

# R003/R019 guardrail: notebook must stay analysis-only and must not reintroduce
# independent training or model persistence primitives.
FORBIDDEN_PATTERNS = {
    "lgbm_classifier_constructor": re.compile(r"\b(?:lgb\.)?LGBMClassifier\s*\(", re.IGNORECASE),
    "lgbm_regressor_constructor": re.compile(r"\b(?:lgb\.)?LGBMRegressor\s*\(", re.IGNORECASE),
    "generic_fit_call": re.compile(r"\.\s*fit\s*\(", re.IGNORECASE),
    "joblib_dump": re.compile(r"\bjoblib\.dump\s*\(", re.IGNORECASE),
    "pickle_dump": re.compile(r"\bpickle\.dump\s*\(", re.IGNORECASE),
    "lightgbm_train": re.compile(r"\blgb\.train\s*\(", re.IGNORECASE),
}


def _load_notebook_cells() -> list[dict]:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    return notebook.get("cells", [])


def _as_source_text(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def test_notebook_has_script_first_authority_note():
    cells = _load_notebook_cells()
    markdown_text = "\n".join(_as_source_text(cell) for cell in cells if cell.get("cell_type") == "markdown")

    assert "Script-first authority" in markdown_text
    assert "canonical artifact analysis/reporting only" in markdown_text
    assert "run_pipeline.py" in markdown_text
    assert "03_lgbm_train.py" in markdown_text


def test_notebook_code_cells_do_not_contain_training_or_persistence_primitives():
    cells = _load_notebook_cells()
    violations: list[str] = []

    for idx, cell in enumerate(cells):
        if cell.get("cell_type") != "code":
            continue

        source_text = _as_source_text(cell)
        source_lines = source_text.splitlines()

        for pattern_name, pattern in FORBIDDEN_PATTERNS.items():
            match = pattern.search(source_text)
            if not match:
                continue

            line_number = source_text.count("\n", 0, match.start()) + 1
            line_text = source_lines[line_number - 1].strip() if source_lines else ""
            violations.append(
                f"cell[{idx}] pattern={pattern_name} line={line_number} code={line_text!r}"
            )

    assert not violations, (
        "Notebook must remain canonical artifact analysis/reporting only. "
        "Forbidden training/persistence primitives detected:\n"
        + "\n".join(violations)
    )

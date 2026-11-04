from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = REPO_ROOT / "specs" / "000-general-system" / "spec.md"
REPORTING = REPO_ROOT / "src" / "cg_01" / "reporting.py"
CONSTITUTION = REPO_ROOT / ".specify" / "memory" / "constitution.md"
INTERPRETATIONS = REPO_ROOT / ".specify" / "memory" / "interpretations.json"
QUESTIONS = REPO_ROOT / ".specify" / "memory" / "open_questions.json"
AGENTS = REPO_ROOT / "AGENTS.md"
README = REPO_ROOT / "README.md"


def test_pending_codes_are_synchronized_between_spec_and_reporting() -> None:
    spec_codes = set(re.findall(r"\| (PD-\d{2}) \|", SPEC.read_text(encoding="utf-8")))
    reporting_codes = set(
        re.findall(r'\("(PD-\d{2})"', REPORTING.read_text(encoding="utf-8"))
    )
    assert spec_codes
    assert spec_codes == reporting_codes


def test_constitution_includes_data_markdown_and_audit_principles() -> None:
    text = CONSTITUTION.read_text(encoding="utf-8")
    for code in ("PR-13", "PR-14", "PR-15", "PR-16", "PR-17", "PR-18"):
        assert code in text
    assert "Markdown" in text
    assert "notebook" in text.lower()
    assert "interpretaciones confirmadas" in text.lower()


def test_spec_and_plan_define_f1_2_scope() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    plan = (REPO_ROOT / "specs" / "000-general-system" / "plan.md").read_text(encoding="utf-8")
    tasks = (REPO_ROOT / "specs" / "000-general-system" / "tasks.md").read_text(encoding="utf-8")
    for code in ("FR-14", "FR-15", "FR-16", "FR-17", "FR-18"):
        assert code in spec
    assert "F1.2" in spec
    assert "Markdown" in plan
    assert "F1.2" in tasks


def test_operational_memory_is_valid_and_has_no_duplicate_ids() -> None:
    interpretations = json.loads(INTERPRETATIONS.read_text(encoding="utf-8"))
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    items = interpretations["items"]
    pending = questions["questions"]
    assert len({item["id"] for item in items}) == len(items)
    assert len({item["id"] for item in pending}) == len(pending)
    assert items
    for item in items:
        assert {"id", "concept", "status", "decision", "evidence", "scope", "affects"} <= set(item)
    for question in pending:
        assert {
            "id",
            "priority",
            "concept",
            "status",
            "evidence",
            "contradiction",
            "verified",
            "options",
            "needed",
            "affects",
        } <= set(question)
        assert question["status"] == "open"
        assert question["options"]
    assert all(item["status"] in {"confirmed", "provisional", "inference", "hypothesis", "accepted_exception", "pending", "rejected"} for item in items)


def test_agents_and_readme_keep_the_working_rules_visible() -> None:
    agents = AGENTS.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    assert "data/` es de solo lectura" in agents
    assert "interpretations.json" in agents
    assert "open_questions.json" in agents
    assert "Monte Carlo" in agents
    assert "outputs/markdown" in readme
    assert "01_revision_matrices.ipynb" in readme
    assert "uv run python -m cg_01" in readme


def test_simplified_modules_do_not_keep_obsolete_sources_module() -> None:
    assert not (REPO_ROOT / "src" / "cg_01" / "sources.py").exists()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO_ROOT / "src" / "cg_01").glob("*.py")
    )
    assert "cg_01.sources" not in source_text
    assert "ratio_tolerance_pct" not in source_text
    assert "def dump_json" not in source_text

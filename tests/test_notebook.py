from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "notebooks" / "01_revision_matrices.ipynb"


@pytest.mark.skipif(
    importlib.util.find_spec("nbformat") is None or importlib.util.find_spec("nbclient") is None,
    reason="nbformat/nbclient no instalados",
)
def test_revision_notebook_executes_without_errors() -> None:
    import nbformat
    from nbclient import NotebookClient

    notebook = nbformat.read(NOTEBOOK, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(REPO_ROOT)}},
    )
    client.execute()
    assert any(cell.cell_type == "code" for cell in notebook.cells)
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            assert output.get("output_type") != "error", output

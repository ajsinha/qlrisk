"""Execute every python example in the user guides (and pricers.md), so docs never drift from code."""

import pathlib
import re

import pytest

DOCS = pathlib.Path(__file__).resolve().parents[1] / "docs"
FILES = sorted((DOCS / "guides").rglob("*.md")) + [DOCS / "market_risk" / "pricers.md"]
BLOCK = re.compile(r"```python\n(.*?)```", re.S)


@pytest.mark.parametrize("path", [f for f in FILES if BLOCK.search(f.read_text())],
                         ids=lambda p: str(p.relative_to(DOCS)))
def test_doc_examples_run(path, capsys):
    namespace = {"__name__": "__doc_example__"}
    for i, code in enumerate(BLOCK.findall(path.read_text())):
        try:
            exec(compile(code, f"{path.name}[block {i}]", "exec"), namespace)
        except Exception as exc:
            pytest.fail(f"{path.name} block {i} failed: {type(exc).__name__}: {exc}\n{code}")

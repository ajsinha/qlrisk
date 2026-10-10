"""Execute the python examples in the README, user guides, product pages and selected docs, so docs never drift from code."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BLOCK = re.compile(r"```python\n(.*?)```", re.S)

FULL = ([ROOT / "README.md"] + sorted((DOCS / "guides").rglob("*.md"))
        + [DOCS / "market_risk" / "pricers.md", DOCS / "market_risk" / "README.md"])
# Product pages: the first example is generated from the code by scripts/gen_product_docs.py
FIRST_ONLY = [p for p in sorted((DOCS / "products").rglob("*.md")) if p.parent != DOCS / "products"]


def _run(path, blocks):
    namespace = {"__name__": "__doc_example__"}
    for i, code in enumerate(blocks):
        try:
            exec(compile(code, f"{path.name}[block {i}]", "exec"), namespace)
        except Exception as exc:
            pytest.fail(f"{path.name} block {i} failed: {type(exc).__name__}: {exc}\n{code}")


@pytest.mark.parametrize("path", [f for f in FULL if BLOCK.search(f.read_text())], ids=lambda p: str(p.relative_to(ROOT)))
def test_doc_examples_run(path, capsys):
    _run(path, BLOCK.findall(path.read_text()))


@pytest.mark.parametrize("path", FIRST_ONLY, ids=lambda p: str(p.relative_to(ROOT)))
def test_product_page_example_runs(path, capsys):
    _run(path, BLOCK.findall(path.read_text())[:1])

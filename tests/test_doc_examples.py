"""
Execute every ```python block in README.md and docs/ so documentation never drifts from code.

Conventions: ```python blocks are runnable examples (executed here, top to bottom, one namespace per page);
```py blocks are illustrative listings / design sketches and are not executed.
"""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLOCK = re.compile(r"```python\n(.*?)```", re.S)
PAGES = [ROOT / "README.md"] + sorted((ROOT / "docs").rglob("*.md"))


@pytest.mark.parametrize("path", [p for p in PAGES if BLOCK.search(p.read_text())],
                         ids=lambda p: str(p.relative_to(ROOT)))
def test_doc_examples_run(path, capsys):
    namespace = {"__name__": "__doc_example__"}
    for i, code in enumerate(BLOCK.findall(path.read_text())):
        try:
            exec(compile(code, f"{path.name}[block {i}]", "exec"), namespace)
        except Exception as exc:
            pytest.fail(f"{path.relative_to(ROOT)} block {i} failed: {type(exc).__name__}: {exc}\n{code}")

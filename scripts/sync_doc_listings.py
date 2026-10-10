#!/usr/bin/env python3
"""
Keep class listings in the reference docs identical to the code.

Any ```python block in docs/ (outside guides/) that only declares classes (dataclass result / input
listings) is replaced by the real source of those classes, looked up across the qlrisk package, with
the imports needed to run it. Unknown classes are left untouched.

    python scripts/sync_doc_listings.py
"""

import dataclasses
import enum
import importlib
import inspect
import pathlib
import pkgutil
import re

import qlrisk

ROOT = pathlib.Path(__file__).resolve().parents[1]
HEADER = ("from dataclasses import dataclass, field\n"
          "from typing import Any, Dict, List, Optional, Tuple\n\n")


def class_index():
    index = {}
    for mod in pkgutil.walk_packages(qlrisk.__path__, "qlrisk."):
        try:
            m = importlib.import_module(mod.name)
        except Exception:
            continue
        for name, obj in vars(m).items():
            if inspect.isclass(obj) and obj.__module__ == m.__name__:
                index.setdefault(name, obj)
    return index


def _type_name(tp) -> str:
    return getattr(tp, "__name__", str(tp)).replace("typing.", "")


def _default(f) -> str:
    if f.default is not dataclasses.MISSING:
        d = f.default
        return getattr(d, "name", None) and f"{type(d).__name__}.{d.name}" or repr(d)
    if f.default_factory is not dataclasses.MISSING:
        name = getattr(f.default_factory, '__name__', 'factory')
        return "auto-generated" if name == "<lambda>" else f"{name}()"
    return "required"


def _old_descriptions(table_lines):
    out = {}
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[-1]:
            out[cells[0].strip("`")] = cells[-1]
    return out


def regenerate_tables(text: str, index) -> str:
    """Rewrite enum value tables and dataclass attribute tables under '### Name (Enum|Dataclass)' headings."""
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^### (\w+) \((Enum|Dataclass)\)", lines[i])
        cls = index.get(m.group(1)) if m else None
        if not cls:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("### "):
            if lines[j].startswith("|"):
                break
            j += 1
        if j >= len(lines) or not lines[j].startswith("|"):
            i += 1
            continue
        k = j
        while k < len(lines) and lines[k].startswith("|"):
            k += 1
        old = _old_descriptions(lines[j:k])
        if m.group(2) == "Enum" and inspect.isclass(cls) and issubclass(cls, enum.Enum):
            table = ["| Value | Name | Description |", "|-------|------|-------------|"]
            table += [f"| `{e.value}` | `{e.name}` | {old.get(e.name, old.get(str(e.value), ''))} |" for e in cls]
        elif dataclasses.is_dataclass(cls):
            table = ["| Attribute | Type | Default | Description |", "|-----------|------|---------|-------------|"]
            table += [f"| `{f.name}` | {_type_name(f.type)} | {_default(f)} | {old.get(f.name, '')} |"
                      for f in dataclasses.fields(cls)]
        else:
            i += 1
            continue
        lines[j:k] = table
        i = j + len(table)
    return "\n".join(lines)


def main() -> None:
    index = class_index()
    changed = 0
    for page in sorted((ROOT / "docs").rglob("*.md")):
        if "guides" in page.parts:
            continue
        text = page.read_text()

        def replace(match):
            code = match.group(1)
            names = re.findall(r"^class (\w+)", code, re.M)
            body = [l for l in code.splitlines() if l.strip() and not l.lstrip().startswith("#")]
            only_classes = names and all(l.startswith(("@", "class ", " ", "\t")) for l in body)
            if not only_classes or not all(n in index for n in names):
                return match.group(0)
            source = "\n\n".join(inspect.getsource(index[n]).rstrip() for n in names)
            return f"```python\n{HEADER}{source}\n```"

        new = re.sub(r"```python\n(.*?)```", replace, text, flags=re.S)
        new = regenerate_tables(new, index)
        if new != text:
            page.write_text(new)
            changed += 1
    print(f"synced listings in {changed} pages")


if __name__ == "__main__":
    main()

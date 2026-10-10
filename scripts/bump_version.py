#!/usr/bin/env python3
"""
Bump the QLRisk version everywhere.

    python scripts/bump_version.py patch|minor|major|X.Y.Z

Single source of truth: qlrisk/__init__.py (__version__, VERSION). Every tracked text file
has the old version string replaced, except version-history table rows. The README's
"*Unreleased*" history row becomes the new version (bold), and the previous bold row is
un-bolded. config/application.properties and install.sh are synchronised too.
"""

import datetime
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INIT = ROOT / "qlrisk" / "__init__.py"
TEXT = {".py", ".md", ".toml", ".properties", ".sh", ".txt", ".cfg"}
HISTORY_ROW = re.compile(r"^\|\s*(\*\*v|v|\*Unreleased)")


def current() -> str:
    return re.search(r'__version__ = "([^"]+)"', INIT.read_text()).group(1)


def target(old: str, how: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", how):
        return how
    major, minor, patch = map(int, old.split("."))
    return {"major": f"{major + 1}.0.0", "minor": f"{major}.{minor + 1}.0", "patch": f"{major}.{minor}.{patch + 1}"}[how]


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    old = current()
    new = target(old, sys.argv[1])
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    changed = 0
    for rel in files:
        path = ROOT / rel
        if path.suffix not in TEXT or rel.startswith("dist/") or not path.exists():
            continue
        text = path.read_text()
        out = []
        for line in text.splitlines(keepends=True):
            if HISTORY_ROW.match(line):
                out.append(line)
            else:
                out.append(line.replace(old, new).replace(f"({old.replace('.', ', ')})", f"({new.replace('.', ', ')})"))
        new_text = "".join(out)
        if rel == "qlrisk/config/application.properties":
            new_text = re.sub(r"application\.version=.*", f"application.version={new}", new_text)
        if rel == "qlrisk/install.sh":
            new_text = re.sub(r"QLRisk v\d+\.\d+\.\d+", f"QLRisk v{new}", new_text)
        if rel in ("README.md", "qlrisk/README.md"):
            month = datetime.date.today().strftime("%b %Y")
            new_text = re.sub(r"^\| \*\*v(\d+\.\d+\.\d+)\*\* \|", r"| v\1 |", new_text, flags=re.M)
            new_text = re.sub(r"^\| \*Unreleased\* \| [^|]+\|", f"| **v{new}** | {month} |", new_text, flags=re.M)
        if new_text != text:
            path.write_text(new_text)
            changed += 1
    print(f"{old} -> {new} ({changed} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

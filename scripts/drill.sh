#!/usr/bin/env bash
# Drill: test, rebuild the wheel, commit, push develop; with --main also merge to main and tag.
#   scripts/drill.sh "commit message" [--main]
set -euo pipefail
cd "$(dirname "$0")/.."
msg="$1"; to_main="${2:-}"
[ "$(git branch --show-current)" = "develop" ] || { echo "not on develop"; exit 1; }
.venv/bin/python -m pytest -q
find qlrisk tests -name __pycache__ -prune -exec rm -rf {} +
rm -rf build && git rm -q --ignore-unmatch dist/*.whl && rm -f dist/*.whl
uv build --wheel --out-dir dist | tail -1
rm -rf build dist/.gitignore
version=$(.venv/bin/python -c "import re;print(re.search(r'__version__ = \"([^\"]+)\"',open('qlrisk/__init__.py').read()).group(1))")
git add -A
git commit -q -m "$msg

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01UyBENKCXdpfQavK3mH9yXN" || echo "nothing to commit"
git push -q origin develop
if [ "$to_main" = "--main" ]; then
  git checkout -q main && git pull -q --ff-only
  git merge -q --no-ff develop -m "Merge develop: v$version

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01UyBENKCXdpfQavK3mH9yXN"
  git push -q origin main
  if ! git rev-parse -q --verify "refs/tags/v$version" >/dev/null; then
    git tag -a "v$version" -m "QLRisk v$version" && git push -q origin "v$version"
  fi
  git checkout -q develop
fi
echo "drilled v$version ($(git log --oneline -1))"

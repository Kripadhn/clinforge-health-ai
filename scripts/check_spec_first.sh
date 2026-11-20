#!/usr/bin/env bash
# Spec-first check: SPEC.md must exist and be committed no later than the first implementation commit.
set -euo pipefail
[ -f SPEC.md ] || { echo "SPEC.md missing"; exit 1; }
if git rev-parse --git-dir >/dev/null 2>&1; then
  spec=$(git log --diff-filter=A --format=%ct -- SPEC.md | tail -1)
  impl=$(git log --diff-filter=A --format=%ct -- agent mcp-server mock-ehr-api | tail -1)
  [ -z "${spec:-}" ] && { echo "SPEC.md not committed"; exit 1; }
  [ -z "${impl:-}" ] || [ "$spec" -le "$impl" ] || { echo "SPEC.md was committed after implementation"; exit 1; }
fi
echo "spec-first ok"

#!/usr/bin/env bash
set -uo pipefail
OUT="docs/STATUS_REPORT.md"
mkdir -p "$(dirname "$OUT")"

# helpers
header() { echo -e "# Project Status Report\n\nGenerated: $(date -Is)\n"; }
sec() { echo -e "\n**$1**\n"; }
row() { local s="$1"; shift; echo "- **$s**: $*"; }

# env info
PY_VER=$(uv run python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "n/a")
UV_VER=$(uv --version 2>/dev/null | head -n1 || echo "n/a")

VALIDATE_STATUS="OK"; VALIDATE_OUT=$(uv run python scripts/validate_json.py --strict 2>&1) || VALIDATE_STATUS="FAIL"
FMT_STATUS="OK"; FMT_OUT=$(uv run ruff format --check . 2>&1) || FMT_STATUS="FAIL"
LINT_STATUS="OK"; LINT_OUT=$(uv run ruff check . 2>&1) || LINT_STATUS="FAIL"
SUPPRESS_STATUS="OK"; SUPPRESS_OUT=$(bash scripts/ci/forbid_suppress.sh 2>&1) || SUPPRESS_STATUS="FAIL"
MYPY_STATUS="OK"; MYPY_OUT=$(uv run mypy scripts/rules scripts/build_pipeline.py dashboard/api --strict --ignore-missing-imports 2>&1) || MYPY_STATUS="FAIL"

export TEST_DB_STATEMENT_TIMEOUT_MS=${TEST_DB_STATEMENT_TIMEOUT_MS:-2000}
PYTEST_STATUS="OK"; PYTEST_OUT=$(uv run pytest -q 2>&1) || PYTEST_STATUS="FAIL"

COVXML_STATUS="OK"; COVXML_OUT=$(make cov-xml 2>&1) || COVXML_STATUS="FAIL"
RATCHET_STATUS="OK"; RATCHET_OUT=$(make ratchet 2>&1) || RATCHET_STATUS="FAIL"

HEALTH_PRESENT="$(rg -n "/healthz/(live|startup)" -S dashboard/app.py >/dev/null 2>&1 && echo yes || echo no)"

{
  header
  sec "Environment"
  row "Python" "$PY_VER"
  row "uv" "$UV_VER"

  sec "Checks"
  row "JSON validate" "$VALIDATE_STATUS"
  row "Format check" "$FMT_STATUS"
  row "Lint" "$LINT_STATUS"
  row "Suppress guard" "$SUPPRESS_STATUS"
  row "Typecheck (mypy)" "$MYPY_STATUS"
  row "Tests (pytest)" "$PYTEST_STATUS"
  row "Coverage XML" "$COVXML_STATUS"
  row "Coverage ratchet" "$RATCHET_STATUS"

  sec "Health Endpoints"
  row "Defined" "$HEALTH_PRESENT"

  sec "Summaries"
  echo "- Validate: ${VALIDATE_OUT%%$'\n'*}"
  echo "- Format: ${FMT_OUT%%$'\n'*}"
  echo "- Lint: ${LINT_OUT%%$'\n'*}"
  echo "- Suppress: ${SUPPRESS_OUT%%$'\n'*}"
  echo "- Mypy: ${MYPY_OUT%%$'\n'*}"
  echo "- Pytest: $(echo "$PYTEST_OUT" | tail -n 3 | tr '\n' ' ' | sed 's/  */ /g')"
  echo "- Ratchet: $(echo "$RATCHET_OUT" | tail -n 3 | tr '\n' ' ' | sed 's/  */ /g')"

  sec "Remaining Failing Checks"
  FAILS=()
  [[ "$VALIDATE_STATUS" != OK ]] && FAILS+=("JSON validate")
  [[ "$FMT_STATUS" != OK ]] && FAILS+=("Format check")
  [[ "$LINT_STATUS" != OK ]] && FAILS+=("Lint")
  [[ "$SUPPRESS_STATUS" != OK ]] && FAILS+=("Suppress guard")
  [[ "$MYPY_STATUS" != OK ]] && FAILS+=("Typecheck")
  [[ "$PYTEST_STATUS" != OK ]] && FAILS+=("Tests")
  [[ "$COVXML_STATUS" != OK ]] && FAILS+=("Coverage XML")
  [[ "$RATCHET_STATUS" != OK ]] && FAILS+=("Coverage ratchet")
  if [[ ${#FAILS[@]} -eq 0 ]]; then
    echo "- None — all checks passed."
  else
    for f in "${FAILS[@]}"; do echo "- $f"; done
  fi

  sec "Artifacts"
  row "Report" "docs/STATUS_REPORT.md"
  row "Coverage XML" "build/coverage.xml (if generated)"
} > "$OUT"

echo "Wrote $OUT"

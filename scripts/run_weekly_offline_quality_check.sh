#!/usr/bin/env bash
# V4.3.2 — Weekly offline quality check. Chạy deterministic test suite + static
# quality checks (manifest/registry/untracked). KHÔNG API/network/submission.
set -euo pipefail
if [[ -n "${ANTHROPIC_API_KEY:-}" || -n "${OPENAI_API_KEY:-}" ]]; then
  echo "OFFLINE VIOLATION: API key set — abort." >&2; exit 2
fi
export MRAQ_OFFLINE_CI=1 USE_MOCK_SOURCES=true
PY="${PYTHON:-python3}"
RES="${RESULTS_DIR:-results}"; mkdir -p "$RES"

echo "== [1] deterministic offline test suite =="
"$PY" -m pytest -q -p no:cacheprovider --junit-xml="$RES/weekly_junit.xml" \
  | tee "$RES/weekly_test_run.txt"
TEST_RC=${PIPESTATUS[0]}

echo "== [2] static quality (manifest/registry/untracked) =="
"$PY" -m research_automation.automation_cli weekly-quality | tee "$RES/weekly_quality.json"
Q_RC=${PIPESTATUS[0]}

echo "== [3] dashboard data regen =="
"$PY" -m research_automation.automation_cli dashboard \
  --out "$RES/research_studio_dashboard.html" --test-status "$([[ $TEST_RC -eq 0 ]] && echo PASS || echo FAIL)" \
  | tee "$RES/weekly_dashboard.txt"

RC=$(( TEST_RC != 0 ? TEST_RC : Q_RC ))
echo "WEEKLY_QUALITY_EXIT=$RC"
exit "$RC"

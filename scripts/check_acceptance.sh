#!/usr/bin/env bash
# End-to-end acceptance check for AC1-AC5. Uses a temporary TASKS_FILE, never the real one.
set -u
cd "$(dirname "$0")/.."
export TASKS_FILE="$(mktemp -d)/tasks.json"
run() { python -m tasktracker "$@"; }
pass=0; fail=0
check() { if [ "$2" = "0" ]; then echo "PASS $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }

out=$(run add "Write report" --priority low)
grep -q '"title": "Write report"' "$TASKS_FILE" && [ "$out" = "Added task 1: Write report" ]; check AC1 $?

run add "Fix bug" --priority high --due 2020-01-01 >/dev/null
run add "Plan trip" --priority medium --due 2999-01-01 >/dev/null
before=$(cat "$TASKS_FILE")
out=$(run done 99); code=$?
[ "$code" = "1" ] && [ "$out" = "Task not found" ] && [ "$before" = "$(cat "$TASKS_FILE")" ] \
  && run done 1 >/dev/null && grep -q '"done": true' "$TASKS_FILE"; check AC2 $?

pending=$(run list --pending)
order=$(run list --sort priority | awk '{print $NF}' | tr '\n' ' ')
! echo "$pending" | grep -q "Write report" && echo "$order" | grep -q "2020-01-01) 2999-01-01) report"; check AC3 $?

over=$(run overdue)
echo "$over" | grep -q "Fix bug" && ! echo "$over" | grep -q "Plan trip"; check AC4 $?

run delete 2 >/dev/null
list=$(run list)
! echo "$list" | grep -q "Fix bug" && echo "$list" | grep -q "^  1 .*Write report" && echo "$list" | grep -q "^  3 .*Plan trip"; check AC5 $?

echo "acceptance: $pass passed, $fail failed"
[ "$fail" = "0" ]

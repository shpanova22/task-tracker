#!/usr/bin/env bash
# Read-only probes: run against the repo, use only temp TASKS_FILE, never modify repo files.
cd /home/claude/task-tracker
t() { export TASKS_FILE="$(mktemp -d)/tasks.json"; }
run() { echo "\$ tasktracker $*"; python -m tasktracker "$@" 2>&1 | tail -4; echo "exit=${PIPESTATUS[0]}"; }

echo "=== R1 duplicate ids after delete ==="; t
run add A; run add B; run add C; run delete 1; run add D; run list
run delete 3; run list

echo "=== R2 corrupted / empty tasks.json ==="; t
printf '' > "$TASKS_FILE"; run list
printf '{"broken": ' > "$TASKS_FILE"; run add X

echo "=== R3 non-atomic save (fault injected during json.dump) ==="; t
run add "important"
python - <<'PY'
import json, os
from tasktracker import tracker
orig = json.dump
def failing_dump(obj, f, **kw):
    f.write('[{"id": 1, "ti')   # partial write, then crash (simulates kill / disk full)
    raise OSError("simulated crash during write")
json.dump = failing_dump
try:
    tracker.add_task("second")
except OSError as e:
    print("crash:", e)
json.dump = orig
print("file now:", open(os.environ["TASKS_FILE"]).read())
PY
run list

echo "=== R4 invalid due date accepted ==="; t
run add "bad date" --due 01.12.2026; run add "nonsense" --due tomorrow; run overdue

echo "=== R5 unknown priority accepted ==="; t
run add "typo prio" --priority hihg; run list

echo "=== R6 README commands ==="
grep -n "tracker.py\|requirements.txt" README.md; ls requirements.txt tracker.py 2>&1

echo "=== R7 unpinned / missing dev deps ==="
cat requirements-dev.txt; grep -c "ruff\|mypy\|build" requirements-dev.txt; ruff --version

echo "=== R8 TASKS_FILE path traversal ==="
grep -n "environ" tasktracker/storage.py

echo "=== R9 insecure deserialization claim ==="
grep -n "json.load\|pickle\|eval\|yaml" tasktracker/*.py

echo "=== R10 default data path inside working dir ==="
grep -n "DEFAULT_FILE" tasktracker/storage.py; grep -n "tasks.json" .gitignore

echo "=== R12 mypy skips untyped functions ==="
mypy --no-incremental --cache-dir=/dev/null --check-untyped-defs tasktracker 2>&1 | tail -3
mypy --no-incremental --cache-dir=/dev/null --disallow-untyped-defs tasktracker 2>&1 | tail -2

echo "=== R13 local-time date.today ==="
ruff check --no-cache --select DTZ . 2>&1 | grep -E "DTZ|-->"

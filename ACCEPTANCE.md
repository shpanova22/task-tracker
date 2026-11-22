# Acceptance Criteria

These must remain true after every change. They are checked end-to-end through the CLI by
`scripts/check_acceptance.sh` (each line prints PASS/FAIL) and partially by `pytest`.

| ID  | Criterion |
|-----|-----------|
| AC1 | `add "<title>"` creates a pending task, prints `Added task <id>: <title>`, and the task is persisted to the JSON file (`TASKS_FILE`). |
| AC2 | `done <id>` marks an existing task as done. For an unknown id it prints `Task not found`, exits with code 1, and does not change the file. |
| AC3 | `list --pending` hides done tasks; `list --sort priority` orders tasks high → medium → low. |
| AC4 | `overdue` shows only tasks that are not done and whose due date is before today. |
| AC5 | `delete <id>` removes only that task; the remaining tasks keep their ids and data. |

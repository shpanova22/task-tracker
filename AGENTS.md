# AGENTS.md — instructions for coding agents

## Purpose
`tasktracker` is a small Python 3.10+ command-line task tracker. Tasks are stored in one JSON
file (path from the `TASKS_FILE` environment variable, default `./tasks.json`). It is a course
project: no network access, no users, no secrets.

## Architecture
| Path | Role |
|------|------|
| `tasktracker/__main__.py` | Entry point for `python -m tasktracker` |
| `tasktracker/cli.py` | argparse commands and output formatting only |
| `tasktracker/tracker.py` | Business logic: add / done / delete / list / overdue |
| `tasktracker/storage.py` | Reading and writing the JSON file |
| `tests/` | pytest unit tests |
| `scripts/check_acceptance.sh` | End-to-end checks for `ACCEPTANCE.md` (AC1–AC5) |

Keep the layering: `cli` → `tracker` → `storage`. Business rules never print; the CLI never
touches the file directly.

## Setup
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

## Safe commands (may run without asking)
- `python -m pytest -q`
- `ruff check .`
- `mypy tasktracker`
- `python -m build --outdir /tmp/dist`
- `bash scripts/check_acceptance.sh` (uses a temporary `TASKS_FILE`)
- `python -m tasktracker <command>` **only** with `TASKS_FILE` pointing to a temp file
- read-only git: `git status`, `git diff`, `git log`

## Coding conventions
- Standard library only at runtime. Type hints on new or changed functions.
- Small functions; no printing outside `cli.py`.
- Keep the JSON format backward compatible (`id`, `title`, `priority`, `due`, `done`).
- Commit messages: imperative, one change per commit.

## Test expectations
- Every bug fix comes with a test that fails before the fix and passes after it.
- Before handing work back: pytest, ruff, mypy and `scripts/check_acceptance.sh` must all exit 0.
  Report the exact commands and pass/fail totals. Never claim a check passed if it was not run.

## Forbidden actions
- Do not read, create or commit secrets, tokens, `.env` files or real personal data.
- Do not deploy, publish to PyPI, or push to any remote.
- No destructive commands: `rm -rf`, `git reset --hard`, `git push --force`, rewriting history,
  deleting or overwriting the user's real `tasks.json`.
- Do not add, remove or upgrade dependencies, or edit `pyproject.toml` / requirements files,
  without explicit human approval.
- Do not disable, skip or delete tests to make a check pass.

## Review gates
- All diffs are reviewed by a human before commit.
- Changes to storage format, dependencies or this file need explicit approval.
- In "review" or "read-only" tasks, do not modify any file — only report findings with evidence
  (file path, line, command output) and label each one confirmed / plausible / unsupported.

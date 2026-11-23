---
title: "Software Engineering — Assignment #05"
subtitle: "AI-assisted repository customization, agent readiness and software risk governance"
---

**Student:** [Surname Name], ID [Student ID]  
**Date:** 22 November 2026  
**AI assistant used:** Claude (model Claude Opus 5.5), claude.ai  
**Repository:** https://github.com/[YOUR_LOGIN]/task-tracker (full git history and tags). Commit references: baseline `aea8006` (tag `baseline`), agent instructions `57240e6`, refactoring `889164f` (tag `refactor`), final `f1b3deb` (tag `final`).

All command outputs quoted below are real output captured in the repository folder `docs/assignment05/evidence/`. Tests that were not executed are listed explicitly.

---

## 0. Scenario and starting point

**Project.** A small command-line task tracker in Python 3 (standard library only). Tasks are stored in one JSON file whose path comes from the `TASKS_FILE` environment variable (default `./tasks.json`). It contains no secrets and no personal data.

**Baseline preserved.** Commit `aea8006`, tag `baseline`.

**Run / test / build commands (recorded at baseline):**

| Purpose | Command |
|---|---|
| Run | `python -m tasktracker add "Buy milk" --priority high --due 2026-12-01` |
| Unit tests | `python -m pytest -v` |
| Lint | `ruff check .` (ruff 0.16.9) |
| Type check | `mypy tasktracker` (mypy 2.3.1) |
| Build | `python -m build --outdir /tmp/dist` |
| Acceptance | `bash scripts/check_acceptance.sh` (added in commit `57240e6`) |

**Acceptance criteria (`ACCEPTANCE.md`)** — must stay true after every change:

| ID | Criterion |
|---|---|
| AC1 | `add "<title>"` creates a pending task, prints `Added task <id>: <title>` and persists it to `TASKS_FILE`. |
| AC2 | `done <id>` marks a task done; an unknown id prints `Task not found`, exits 1 and leaves the file unchanged. |
| AC3 | `list --pending` hides done tasks; `list --sort priority` orders high → medium → low. |
| AC4 | `overdue` shows only tasks that are not done and whose due date is before today. |
| AC5 | `delete <id>` removes only that task; the remaining tasks keep their ids and data. |

---

## Task 01 — Baseline and context

### Repository map

| Element | Path | Notes |
|---|---|---|
| Entry points | `tasktracker/__main__.py` (`python -m tasktracker`), console script `tasktracker` in `pyproject.toml` | |
| CLI layer | `tasktracker/cli.py` (72 lines) | argparse, output formatting |
| Business logic | `tasktracker/tracker.py` (67 lines) | add / done / delete / list / overdue |
| Storage | `tasktracker/storage.py` (22 lines) | JSON load/save |
| Tests | `tests/test_tracker.py` (6 tests) | pytest, `tmp_path` |
| Dependencies | runtime: none; dev: `requirements-dev.txt` = `pytest` (unpinned) | |
| Build | `pyproject.toml`, setuptools backend | |
| Docs | `README.md` | |

### Baseline checks (commit `aea8006`)

| Command | Actual result |
|---|---|
| `python -m pytest -v` | **6 passed** in 0.03 s, exit 0 |
| `ruff check .` | **Found 1 error** — `DTZ011 datetime.date.today() used` at `tasktracker/tracker.py:63`, exit 1 |
| `mypy tasktracker` | `Success: no issues found in 5 source files`, exit 0 |
| `python -m build` | `Successfully built tasktracker-0.1.0.tar.gz and tasktracker-0.1.0-py3-none-any.whl`, exit 0 |
| `python tracker.py list` (from README) | `can't open file '.../tracker.py': [Errno 2]`, exit 2 |
| `pip install -r requirements.txt` (from README) | `Could not open requirements file`, exit 1 |
| `bash scripts/check_acceptance.sh` | 5 passed, 0 failed |

### Weaknesses found (with evidence)

1. **README is wrong.** It documents `python tracker.py ...` and `requirements.txt`; neither file exists (both commands fail, see table above).
2. **Lint gate fails at baseline** (`DTZ011`), and the linter is not listed in `requirements-dev.txt`, so the result depends on whichever ruff version is installed.
3. **Dev dependencies are unpinned** — `requirements-dev.txt` contains only `pytest`, no versions; ruff, mypy and build are missing.
4. **Duplicated conditionals** — the priority → rank/mark mapping is written twice as `if/elif` chains (`tracker.py` `list_tasks`, `cli.py` `format_task`).
5. **mypy success is weak evidence** — functions have no annotations, so mypy skips their bodies; with `--disallow-untyped-defs` it reports 10 errors.
6. **No input validation** — any string is accepted as a priority or due date (`storage`/`tracker` have no checks).

### Facts vs assumptions

- **Observed facts:** everything in the tables above (commands were actually run; output saved in `docs/assignment05/evidence/baseline_*.txt`).
- **Assumptions:** the project runs on Python ≥ 3.10 (declared in `pyproject.toml`, only 3.13 was actually tested); single user, single process.
- **Unverified AI suggestions** were not treated as facts — they were turned into candidate findings and checked in Task 04.

---

## Task 02 — Agent instructions

A root-level **`AGENTS.md`** was created (commit `57240e6`). It documents:

- **Purpose** and **architecture** (layering `cli → tracker → storage`, business logic never prints);
- **Setup** (venv, `requirements-dev.txt`, `pip install -e .`);
- **Safe commands** that may run without asking: pytest, ruff, mypy, build to `/tmp`, the acceptance script, the CLI only with a temporary `TASKS_FILE`, read-only git;
- **Coding conventions** (stdlib only, type hints on changed code, backward-compatible JSON format);
- **Test expectations** (every fix comes with a failing-then-passing test; report exact commands; never claim a check that was not run);
- **Forbidden actions:** no secrets / `.env` / personal data; no deployment, PyPI publishing or pushing; no destructive commands (`rm -rf`, `git reset --hard`, `push --force`, overwriting the real `tasks.json`); no dependency or `pyproject.toml` changes without approval; never skip or delete tests;
- **Review gates:** human review of every diff; explicit approval for storage-format, dependency or `AGENTS.md` changes; read-only tasks must not modify files.

**Loading disclosure.** The assistant (Claude in the claude.ai chat) does **not** load `AGENTS.md` automatically. Its content was therefore provided explicitly in the conversation, and the assistant was asked to follow it for all later steps.

---

## Task 03 — Focused pattern decision

**Problem.** The same priority knowledge was duplicated in two places:

```python
# tracker.py (baseline)                    # cli.py (baseline)
if t["priority"] == "high":   return 0     if t["priority"] == "high":   mark = "!!!"
elif t["priority"] == "medium": return 1   elif t["priority"] == "medium": mark = "!!"
elif t["priority"] == "low":  return 2     elif t["priority"] == "low":  mark = "!"
else: return 3                             else: mark = "?"
```

Adding a priority (e.g. `critical`) means editing two `if/elif` chains in two modules, plus the `--sort` choices list — easy to forget one.

**Options evaluated.**

| Option | Verdict |
|---|---|
| Full Strategy pattern (a `SortStrategy` class hierarchy) | Rejected — three one-line behaviours do not justify classes; more code than the problem. |
| Adapter | Not applicable — no incompatible interface. |
| **Lightweight Strategy: a table of key functions + one priority table** | **Chosen** — removes the duplication, Pythonic, adding a sort mode or priority = one line. |

**Implementation (one refactoring, commit `889164f`).** New `tasktracker/priority.py` holds `PRIORITIES = {"high": (0, "!!!"), "medium": (1, "!!"), "low": (2, "!")}` with `rank()`/`mark()` helpers. `tracker.py` gets `SORT_KEYS = {"id": ..., "priority": ..., "due": ...}`; `list_tasks` becomes `sorted(tasks, key=SORT_KEYS.get(sort_by, SORT_KEYS["id"]))`. The CLI builds `--sort` choices from `SORT_KEYS`.

**Before / after.** `git diff --stat`: 4 files, +40 / −27. `if/elif` chains on priority: 2 → 0. Places to edit to add a priority: 3 → 1.

**Proof acceptance criteria still hold** (after refactor): pytest **7 passed** (6 old + 1 new test for unknown priority), acceptance script **5 passed, 0 failed**, mypy success. The first ruff run after the refactor showed a **new** `UP035` error introduced by the AI-written import (`typing.Callable`); it was fixed before commit.

---

## Task 04 — Read-only risk review

The assistant was asked to propose risks **without modifying files**. `git status --short` was empty before and after the review; every probe used a temporary `TASKS_FILE` (script `docs/assignment05/probes/probe_all.sh`, output `docs/assignment05/evidence/risk_probes.txt`). 13 candidate findings, 5 categories, were investigated:

| ID | Category | Candidate finding | Classification | Evidence |
|---|---|---|---|---|
| R-01 | Correctness | Ids reused after delete (`len(tasks)+1`) | **Confirmed** | add A,B,C → delete 1 → add D printed `Added task 3: D`; `list` showed two tasks with id 3; `delete 3` then removed **both** C and D |
| R-02 | Correctness | Empty/corrupted `tasks.json` crashes every command | **Confirmed** | empty file → `json.decoder.JSONDecodeError` traceback, exit 1, for `list` and `add` |
| R-03 | Correctness | `save_tasks` writes in place (not atomic) → crash mid-write destroys data | **Confirmed** (fault injection) | patched `json.dump` to write a partial string then raise; file became `[{"id": 1, "ti` and all commands then failed |
| R-04 | Correctness | Due dates not validated; compared as strings | **Confirmed** | `--due 01.12.2026` accepted and shown as overdue; `--due tomorrow` accepted, never overdue |
| R-05 | Correctness | Any priority accepted (typo `hihg`) | **Confirmed** | stored and shown as `?` |
| R-06 | Maintainability | README commands are wrong | **Confirmed** | `README.md:8,14-16`; both files missing |
| R-07 | Dependency | Dev deps unpinned, ruff/mypy/build missing | **Confirmed** | `requirements-dev.txt` = `pytest` only |
| R-08 | Security | Path traversal via `TASKS_FILE` | **Unsupported** | the variable is set by the local user who already owns the shell; no trust boundary is crossed |
| R-09 | Security | Insecure deserialization of the tasks file | **Unsupported** | only `json.load` is used (`storage.py:16`); JSON parsing cannot execute code; no `pickle`/`eval`/`yaml` |
| R-10 | Agent operations | Running the CLI without `TASKS_FILE` writes `./tasks.json` in the working directory — an agent could overwrite real data | **Confirmed** (behaviour) | `storage.py:4,8` `DEFAULT_FILE = "tasks.json"` |
| R-11 | Correctness | Two processes writing at once lose an update | **Plausible / unverified** | read-modify-write without locking in `tracker.py`; not reproduced |
| R-12 | Maintainability | mypy "Success" gives false confidence | **Confirmed** | `--disallow-untyped-defs` → 10 errors in 3 files |
| R-13 | Correctness | `date.today()` uses local time zone | **Confirmed** (lint) | ruff `DTZ011` at `tracker.py:63`; practical impact low |

Summary: **10 confirmed, 1 plausible, 2 unsupported**; categories covered: correctness, maintainability, security, dependency, agent operations.

---

## Task 05 — Risk register

Score = Likelihood (1–3) × Impact (1–3). "Residual" is the score after the mitigation listed (only M1, M2 and the AGENTS.md rule were actually implemented).

| ID | Cause → Event → Consequence | Component | L | I | Score | Mitigation | Owner | Verification plan | Residual |
|---|---|---|---|---|---|---|---|---|---|
| R-01 | id = `len+1` → user deletes then adds → duplicate ids; `done/delete` hit the wrong or several tasks (data loss) | `tracker.add_task` | 3 | 3 | **9** | **M1 (done):** `max(id)+1` | Author | regression tests + probe R-01 | L1×I2 = 2 (only via concurrent writers, R-11) |
| R-02 | file empty/corrupted → any command → traceback, app unusable, risk of being overwritten | `storage.load_tasks`, `cli` | 2 | 3 | **6** | **M2 (done):** `StorageError`, clear stderr message, exit 2, file never overwritten | Author | 5 tests + probe R-02 | L2×I1 = 2 (user must still repair file) |
| R-06 | README wrong → new user/agent runs documented commands → failure, wrong assumptions | `README.md` | 3 | 2 | 6 | Rewrite usage section | Author | run every README command | open |
| R-04 | no validation → bad date typed → wrong overdue list | `cli`, `tracker` | 2 | 2 | 4 | validate with `date.fromisoformat` | Author | unit tests for bad formats | open |
| R-07 | unpinned / missing tools → different versions → non-reproducible lint/test results | `requirements-dev.txt` | 2 | 2 | 4 | pin pytest, ruff, mypy, build | Author (needs approval per AGENTS.md) | fresh venv install + checks | open |
| R-10 | default path in CWD → agent runs CLI in repo → real data overwritten | `storage.get_path` | 2 | 2 | 4 | AGENTS.md rule: CLI only with temp `TASKS_FILE` (done, documentation only) | Author | review agent transcripts | L1×I2 = 2 |
| R-03 | in-place write → crash during save → data file destroyed | `storage.save_tasks` | 1 | 3 | 3 | write to temp file + `os.replace` | Author | fault-injection test | open (M2 now reports it clearly instead of crashing) |
| R-05 | free-text priority → typo → task sorted last silently | `cli` | 2 | 1 | 2 | argparse `choices` | Author | CLI test | open |
| R-11 | no locking → two processes → lost update | `tracker`, `storage` | 1 | 2 | 2 | file lock (out of scope for single-user CLI) | Author | — | accepted |
| R-12 | untyped code → mypy skips it → false confidence | whole package | 2 | 1 | 2 | add annotations, enable `--disallow-untyped-defs` | Author | mypy strict run | open |
| R-13 | local time → wrong "today" near midnight in another TZ | `tracker.overdue_tasks` | 1 | 1 | 1 | decide policy; fix or configure ruff rule | Author | ruff clean | open |
| R-08 | — | `storage` | — | — | — | none (unsupported) | — | — | — |
| R-09 | — | `storage` | — | — | — | none (unsupported) | — | — | — |

**Top two confirmed risks for corrective action:** **R-01 (score 9)** and **R-02 (score 6)**. R-02 and R-06 both score 6; R-02 was ranked higher because its impact is 3 (data/availability) versus 2 (documentation).

---

## Task 06 — Agent-readiness audit (final version `f1b3deb`)

| Criterion | Status | Evidence |
|---|---|---|
| Readable structure | ✅ | 3 small modules + priority table, clear layering |
| README accuracy | ❌ | documented commands fail (R-06) |
| Reproducible setup | ⚠️ | `pyproject.toml` builds; `requirements-dev.txt` incomplete |
| Pinned dependencies | ❌ | nothing pinned (R-07) |
| Tests | ✅ | 14 unit tests + 5 acceptance checks, all pass |
| Lint / type checks | ⚠️ | ruff 1 known error (DTZ011); mypy passes but code mostly untyped (R-12) |
| Build | ✅ | sdist + wheel build succeeds |
| Logging | ⚠️ | no logging; errors now go to stderr with exit code 2 (M2) |
| Security safeguards | ✅ | no secrets, no network, no unsafe deserialization; `.gitignore` excludes `tasks.json` |
| AGENTS.md — permissions & safe commands | ✅ | explicit list |
| AGENTS.md — prohibited actions | ✅ | secrets, deploy, destructive commands, dependency changes, skipping tests |
| AGENTS.md — review gates | ✅ | human review of every diff, approval for format/deps |
| CI | ❌ | no automated pipeline |

**Readiness level: 2 — Documented.** It is above Level 1 because the agent instructions, safe/forbidden actions, review gates, acceptance criteria and a reproducible test + acceptance script exist and pass. It is **not Level 3 (Agent-ready)** because of missing evidence: (1) README is inaccurate, (2) dependencies are not pinned and the dev toolchain is incomplete, (3) the lint gate is not green, (4) no CI runs the checks automatically, (5) no strict type checking.

---

## Task 07 — Mitigation and verification

### M1 — RISK-01 duplicate ids

- **Diff** (`tasktracker/tracker.py`, 1 line): `"id": len(tasks) + 1` → `"id": max((t["id"] for t in tasks), default=0) + 1`.
- **AI diff review:** checked the empty list case (`default=0` → first id 1), that existing files with gaps still work, and that ids are never renumbered (AC5).
- **Tests added:** `test_ids_unique_after_delete`, `test_delete_after_readd_removes_only_one_task`.

### M2 — RISK-02 corrupted file crash

- **Diff:** `storage.py` adds `StorageError`; invalid JSON or a non-list document raises it with the path and reason; `cli.main` catches it, prints `Error: ...` to stderr and returns **exit code 2**. Nothing is written, so a damaged file is never overwritten.
- **AI diff review:** confirmed that `load_tasks` is always called before `save_tasks` (so no write can happen after a failed load); checked a missing file still means "no tasks" (AC1 unchanged).
- **Tests added:** `test_corrupted_file_raises_storage_error` (3 cases: empty, truncated, not JSON), `test_cli_reports_corrupted_file_and_keeps_it`, `test_non_list_json_is_rejected`.

### Before / after evidence

| Check | Baseline `aea8006` | New tests before fix | Final `f1b3deb` |
|---|---|---|---|
| pytest | 6 passed | `tests/test_mitigations.py`: **7 failed** (e.g. `assert 3 == 4`, `no attribute 'StorageError'`) | **14 passed, 0 failed** |
| Acceptance script | 5/5 PASS | — | **5/5 PASS** |
| ruff | 1 error (DTZ011) | — | 1 error (DTZ011, unchanged, known) |
| mypy | success | — | success (strict mode: 11 errors, see limitations) |
| build | success | — | success |
| Probe R-01 | `delete 3` removed C and D | — | new task gets id 4; `delete 3` removes only C |
| Probe R-02 | traceback, exit 1 | — | `Error: tasks file '...' is corrupted (invalid JSON: Expecting value, line 1). Fix or move it; it was not modified.`, exit 2 |

**Tests not executed:** Python 3.10–3.12 (only 3.13.18 tested); Windows/macOS; concurrent-process scenario (R-11); a fresh-venv install from `requirements-dev.txt`.

### Updated scores and limitations

R-01: 9 → 2. R-02: 6 → 2. Trade-offs and limits: M2 makes the app refuse to run until the user repairs the file — safer than a crash or silent overwrite, but there is no automatic recovery/backup. R-03 (non-atomic write) can still *create* a corrupted file; M2 only makes that visible. The new `_run` helper in `cli.py` is untyped, so strict-mypy errors went from 10 to 11.

---

## Task 08 — Background agent safeguards (hypothetical design)

**Task:** "Fix R-04: validate `--due` as an ISO date (YYYY-MM-DD) and reject invalid values with a clear message and exit 2."

| Safeguard | Definition |
|---|---|
| Isolation | `git worktree add ../tt-agent-r04 -b agent/r04-due-validation final` — separate directory and branch; main branch untouched |
| Data isolation | `TASKS_FILE` always set to a temp directory; no access to the real `tasks.json` |
| Allowed files | `tasktracker/cli.py`, `tasktracker/tracker.py`, `tests/test_validation.py` (new) |
| Allowed commands | the "safe commands" in AGENTS.md only: pytest, ruff, mypy, acceptance script, `git diff/status/add/commit` on its branch |
| Time / size limits | 30 minutes wall time, max 40 tool calls, diff ≤ 150 lines; stop and report if exceeded |
| Prohibited | network access, `pip install`/dependency changes, editing `pyproject.toml`, `AGENTS.md`, `storage.py` or existing tests, `push`, `merge`, `reset --hard`, deleting files outside the worktree |
| Required artifacts | (1) change summary, (2) full diff, (3) pytest + acceptance + ruff + mypy logs with pass/fail totals, (4) build result, (5) risk notes: what could break, what was not tested |
| Human review | I read the diff and logs, rerun the checks myself in the worktree, and only then merge with `git merge --no-ff`; no deployment step exists |
| Failure handling | if any check fails or limits are hit, the agent stops and returns the artifacts with status FAILED; nothing is merged |
| Rollback | before merge: `git worktree remove ../tt-agent-r04 && git branch -D agent/r04-due-validation`; after merge: `git revert -m 1 <merge-commit>` and rerun all checks |

---

## Task 09 — Release decision

**Decision: CONDITIONAL GO** for version `f1b3deb` (tag `final`).

- **Test evidence:** 14/14 unit tests pass, 5/5 acceptance criteria pass, build succeeds, mypy passes. The only failing check is ruff `DTZ011` (R-13, score 1).
- **Risk register:** the two highest confirmed risks (R-01 = 9, R-02 = 6) are mitigated and verified (residual 2 each). No open risk scores above 6; no security finding was confirmed.
- **Readiness:** Level 2 — documented and tested, but not fully reproducible.

Not **GO**, because known limitations remain. Not **NO-GO**, because no serious data-loss or crash risk remains unmitigated and all critical checks pass. Conditions, each with an owner:

| Condition | Control | Owner | Deadline |
|---|---|---|---|
| R-06 README fixed | every README command executed successfully | Author | before tagging a release |
| R-07 dev dependencies pinned (pytest, ruff, mypy, build) | fresh venv install + all checks green | Author (approval per AGENTS.md) | before tagging a release |
| R-13 lint gate | fix `date.today()` usage or document an ignore | Author | before tagging a release |
| R-03 atomic save | fault-injection test | Author | next iteration |
| Users told: single-process use only (R-11) | note in README | Author | with README fix |

---

## Task 10 — AI reflection

*(≈ 265 words)*

I used Claude (Claude Opus 5.5) in the claude.ai chat. It received the assignment PDF, the full repository files, my acceptance criteria and, because the chat does not load it automatically, the text of AGENTS.md. Since I did not have a suitable project, the starting repository itself was also produced with the assistant and frozen as a baseline commit before any audit work.

The most useful suggestion was the duplicate-id risk (R-01). It looked minor in theory, but the reproduction showed that after deleting one task, `delete 3` removed two tasks at once. That turned an abstract "maybe a bug" into the top risk with a score of 9, and gave me a ready regression test.

The weakest suggestions were the two security findings. "Insecure deserialization" ignored that `json.load` cannot execute code, and "path traversal through TASKS_FILE" ignored that the local user already controls the variable. I classified both as unsupported. The assistant also introduced a new lint error (UP035) in its own refactoring, which ruff caught before the commit.

I personally checked every finding by running the probe script, read each diff line by line, and compared baseline and final outputs. Tests changed my decisions twice: the seven new tests failed first, which proved they really cover the bugs, and the green acceptance script let me accept the refactoring.

AGENTS.md clearly improved the process: the review stayed read-only, all CLI runs used a temporary file, and no dependency was changed without asking. Next time I would add CI and pinned tool versions first, so that "it passes" means the same thing on every machine.

---

## Appendix A — AI-use record

| Date | Tool / model | Prompt summary | Output used | Problems found | Changes made by me | Verification |
|---|---|---|---|---|---|---|
| 22.11.2026 | Claude Opus 5.5 (claude.ai) | Explain Assignment #05 from the PDF | task breakdown | — | — | compared with PDF |
| 22.11.2026 | same | Create a small Python task-tracker project with tests to use as the baseline | initial repository (commit `aea8006`) | README commands wrong, unpinned deps (kept as found weaknesses) | none before baseline | pytest, ruff, mypy, build run |
| 22.11.2026 | same | Write AGENTS.md, acceptance criteria and an acceptance script | `AGENTS.md`, `ACCEPTANCE.md`, `scripts/check_acceptance.sh` | AGENTS.md not auto-loaded — pasted manually | reviewed rules | acceptance script 5/5 on baseline |
| 22.11.2026 | same | Remove duplicated priority conditionals with at most one pattern | `priority.py`, `SORT_KEYS` | introduced ruff UP035 | import fixed | pytest 7/7, acceptance 5/5 |
| 22.11.2026 | same | Read-only risk review, do not modify files | 13 candidates | 2 unsupported security claims | classified, scored | probe script, `git status` clean |
| 22.11.2026 | same | Mitigate R-01 and R-02 with tests | 2 diffs + 7 tests | strict-mypy count +1 | diffs reviewed before commit | tests failed before, 14/14 after; probes |

## Appendix B — Evidence files

All files are in the repository under `docs/assignment05/` (commit after tag `final`; code is unchanged by that commit):

`evidence/baseline_{pytest,ruff,mypy,build,readme_cmds,acceptance}.txt`, `evidence/after_refactor_checks.txt`, `evidence/refactor.diff`, `evidence/risk_probes.txt`, `evidence/mitigation_tests_before.txt`, `evidence/m1.diff`, `evidence/m2.diff`, `evidence/final_{pytest,acceptance,ruff,mypy,build,probes}.txt`, `probes/probe_all.sh`, `evidence/repo_tree.txt`.

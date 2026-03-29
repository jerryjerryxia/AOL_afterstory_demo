---
name: preflight
description: QA preflight check — runs orphaned-file scan, lint, full test suite, and traceback check before playtesting handoff
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

# /preflight — Pre-Playtest QA Check

Run all phases **sequentially**. If lint fails, skip the test suite (fail fast).

## Phase 1: Orphaned .rpyc Check

Use Glob to find all `.rpyc` files under `game/`, then check each has a matching `.rpy`. Report orphans as warnings.

```
Glob: game/**/*.rpyc
Glob: game/**/*.rpy
```

Compare the two lists. Any `.rpyc` without a corresponding `.rpy` is orphaned. List them.

## Phase 2: Kill Zombie Ren'Py Processes

Kill any lingering Ren'Py processes that could lock files or interfere with lint/tests.

```bash
taskkill //F //IM "renpy.exe" 2>/dev/null || true
```

Ignore errors (no process found is fine).

## Phase 3: Ren'Py Lint

Run static analysis on the project. This is the gate — if lint has errors, skip the test suite.

```bash
"X:\RenPy\renpy-8.5.0-sdk\renpy.exe" "X:\GameDev\AOL_afterstory_demo" lint 2>&1
```

- **Pass**: output contains no lines with `Error` severity
- **Fail**: report errors and **skip Phase 4** (fail fast)

Parse the lint summary line (e.g., "The game contains N lint errors.") to determine pass/fail.

## Phase 4: Ren'Py Test Suite

Only run if lint passed. Execute the full test suite with a 120-second timeout.

```bash
"X:\RenPy\renpy-8.5.0-sdk\renpy.exe" "X:\GameDev\AOL_afterstory_demo" test --timeout 120 2>&1
```

All tests must pass. Report individual test results if available in output.

## Phase 5: Post-Test Cleanup

Kill any Ren'Py processes spawned by the test runner.

```bash
taskkill //F //IM "renpy.exe" 2>/dev/null || true
```

## Phase 6: Traceback Check

Read `traceback.txt` in the project root. If it exists and has content, report its contents as a warning.

```
Read: X:\GameDev\AOL_afterstory_demo\traceback.txt
```

If the file doesn't exist or is empty, report as clean.

## Phase 7: Summary Report

Print a summary table:

```
## Preflight Results

| Phase | Status |
|-------|--------|
| Orphaned .rpyc | ✅ Clean / ⚠️ N orphaned |
| Kill zombies | ✅ Done |
| Ren'Py Lint | ✅ Pass / ❌ Errors |
| Test Suite | ✅ All pass / ❌ Failures / ⏭️ Skipped |
| Post-cleanup | ✅ Done |
| Traceback | ✅ Clean / ⚠️ Has content |

**Verdict: 🟢 READY FOR PLAYTESTING** or **🔴 ISSUES FOUND**
```

The verdict is **READY** only if lint passed AND tests passed (or were not skipped) AND no orphaned .rpyc files AND traceback is clean. Warnings (orphaned files, traceback content) downgrade to **ISSUES FOUND**.

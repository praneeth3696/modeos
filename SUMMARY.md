# ModeOS — Portfolio Readiness Summary

Branch `chore/portfolio-readiness` off `main` @ `55637fe`. Full audit and rationale in
[IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md).

## What changed and why

| Commit | Change | Why |
|---|---|---|
| `fix(cli)` | Top-level `--mock` is honoured for every subcommand | `modeos --mock mode gaming` silently ran against **real** brightness/volume and killed real processes, because each sub-parser's `--mock` default overwrote the parent flag |
| `fix(state)` | `force_mock` threaded through `save_state` / `restore_state` / `revert_system` | `modeos revert --mock` wrote to real hardware; mocked sessions recorded real hardware state for later revert |
| `chore` | Untracked `__pycache__/*.pyc`, `data/last_state.json`, `data/installed_apps.json` | Build artefacts and a snapshot of the author's installed apps were committed |
| `test` | `tests/conftest.py` sandboxes XDG dirs; guard test | Running tests wrote logs/state into the developer's real home directory |
| `ci` | GitHub Actions: pytest on Python 3.9–3.13 with `MODEOS_MOCK=1` | No CI existed |
| `docs` | README clone URL and test command | Clone URL pointed at a non-existent repo |

Every fix was preceded by a test that failed against the old code.

## Test results

| | Before | After |
|---|---|---|
| Tests | 25 passed | **33 passed** (+3 subtests) |
| New regression tests | — | 3 CLI flag, 4 state/mock propagation, 1 sandbox guard |

Run locally on Python 3.12: `python -m pytest` → `33 passed, 3 subtests passed`.
CI results for 3.9–3.13 are on the pull request.

## Deferred — needs your input

1. **Protected-process matching** — substring matching (`"sh" in name`) over-protects; changing it
   changes which processes are killed. Recommendation: exact names plus an explicit prefix list.
2. **Legacy root shims and `scripts/*.sh`** — duplicated / unused, but removing them breaks the
   documented `python3 main.py` compatibility.
3. **`cpu_limit`** — advertised but only logged. Implement via cgroups or remove from docs.
4. **LICENSE** — `pyproject.toml` says MIT but there is no licence file.
5. **Metadata** — `authors = "ModeOS Team"`, `requires-python >= 3.8` (EOL).

Details and options for each are in IMPROVEMENT_PLAN.md.

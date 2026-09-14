# ModeOS — Improvement Plan

Audit date: 2026-09-14 · Base: `main` @ `55637fe` · Branch: `chore/portfolio-readiness`

Ranking: **Impact** High / Medium / Low · **Effort** S (< 1h) / M (half day) / L (days)

## Audit snapshot

| Area | State |
|---|---|
| History | 4 commits, single author, no secrets found (gitleaks, full history) |
| Dependencies | `PyYAML`, `psutil` — `pip-audit`: no known vulnerabilities. No lockfile (library; acceptable) |
| Tests | 25 tests, all passing; 62% line coverage (`scanner.py` 19%, `display.py` 44%) |
| CI/CD | None |
| Packaging | `pyproject.toml` with console script; Dockerfile + compose sandbox |

## Findings

### Correctness / safety
1. **Top-level `--mock` is silently ignored when a subcommand follows it.** `modeos --mock mode gaming`
   parses `mock=False` because the sub-parser's own `--mock` default overwrites the parent value. A user
   who asked for simulated backends gets **real** brightness/volume changes and real process termination.
   Verified by patching `apply_mode` and inspecting `force_mock`.
2. **`revert --mock` ignores `--mock`.** `revert_system(force_mock=...)` never passes the flag to
   `restore_state`, which only consults `MODEOS_MOCK`. Likewise `apply_mode --mock` records the *real*
   hardware state via `save_state`, so a later revert restores values the mock session never touched.
3. `is_system_protected` uses substring matching (`"sh" in name`), so any process whose name contains
   `sh`, `i3`, `init`, `login`… is treated as protected and silently skipped by block rules.
4. `cpu_limit` is advertised as a "CPU scheduling budget" but only logs a message.
5. `load_mode_config` accepts path separators in the mode name (`../x`). Local CLI only — low risk.

### Repository hygiene
6. Committed build artefacts and machine state: `__pycache__/*.pyc`, `utils/__pycache__/*.pyc`,
   `data/last_state.json` (already in `.gitignore`), `data/installed_apps.json` (a snapshot of the
   author's installed apps).
7. README clone URL points to `github.com/modeos/modeos` (does not exist).
8. No `LICENSE` file although `pyproject.toml` declares MIT.

### Code quality
9. Seven root-level "legacy shim" modules (`app_scanner.py`, `logger.py`, `mode_controller.py`,
   `process_manager.py`, `resource_manager.py`, `state_manager.py`, `utils/system_control.py`) duplicate
   the package's public surface.
10. `scripts/*.sh` are not referenced by any Python code (superseded by `modeos/backends`).
11. Tests write logs/state into the real `~/.local/state/modeos` of whoever runs them.

### CI/CD
12. No automated test run on push/PR.

## Plan

| # | Change | Impact | Effort | Decision |
|---|---|---|---|---|
| 1 | Honour top-level `--mock` for every subcommand (+ tests) | High | S | **Implement** |
| 2 | Thread `force_mock` through `save_state` / `restore_state` (+ tests) | High | S | **Implement** |
| 6 | Stop tracking `__pycache__` and runtime state files | Medium | S | **Implement** |
| 12 | GitHub Actions: tests on Python 3.9–3.13 | Medium | S | **Implement** |
| 11 | Isolate test runs from the real XDG dirs | Low | S | **Implement** |
| 7 | Fix README clone URL and test instructions | Low | S | **Implement** |
| 3 | Exact-match protected process names | Medium | S | Deferred |
| 9 | Remove legacy shim modules | Low | S | Deferred |
| 10 | Remove unused shell scripts | Low | S | Deferred |
| 4 | Implement or de-advertise `cpu_limit` | Low | M | Deferred |
| 8 | Add a LICENSE | Medium | S | Deferred |
| 5 | Reject path separators in mode names | Low | S | Deferred (low value) |

## Deferred — needs your input

- **Protected-process matching (#3).** Switching to exact names changes *which processes get killed*
  under `block_apps` / `kill_all_except_allow`. Options: (a) exact match on the process name;
  (b) exact match plus an explicit prefix list (`xdg-desktop-portal*`, `pipewire*`); (c) keep substring
  matching but drop the 2-character entries (`sh`, `i3`). (b) is my recommendation.
- **Legacy shims (#9) and `scripts/*.sh` (#10).** The README promises `python3 main.py` backward
  compatibility. Removing the shims is a breaking change for anyone importing `process_manager` etc.
  Options: delete; keep but emit `DeprecationWarning`; move under `legacy/`.
- **`cpu_limit` (#4).** Either implement (cgroups v2 `cpu.max` via a user systemd scope) or remove it
  from the schema/README so the feature list stays honest.
- **LICENSE (#8).** `pyproject.toml` says MIT; adding the file is a licensing decision only you can make.
- **Metadata.** `authors = "ModeOS Team"` and `requires-python >= 3.8` (EOL). Suggest your name and `>=3.9`.

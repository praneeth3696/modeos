"""
ModeOS Safe Process Manager
Handles graceful termination (SIGTERM -> SIGKILL), process priority tracking,
whitelist filtering, and 100% dry-run safety.
"""

import os
import signal
import time
from typing import Dict, List, Optional, Set, Tuple
import psutil
from modeos.logger import get_logger

log = get_logger()

# Essential system, desktop, and session processes that must never be terminated
SYSTEM_EXCEPTIONS: Set[str] = {
    # Core system & init
    "systemd", "init", "kthreadd", "dbus-daemon", "dconf-service",
    # Display servers & compositors
    "xorg", "xwayland", "wayland", "gnome-shell", "mutter", "plasma", "kwin",
    "sway", "hyprland", "wayfire", "weston", "i3", "bspwm",
    # Audio & hardware daemons
    "pulseaudio", "pipewire", "pipewire-pulse", "wireplumber", "upowerd",
    # Desktop portals & settings
    "xdg-desktop-portal", "xdg-desktop-portal-gtk", "xdg-desktop-portal-gnome", "gcr-prompter",
    # Shells & terminal multiplexers
    "bash", "zsh", "fish", "sh", "tmux", "screen", "login",
    # Remote access & agents
    "ssh", "sshd", "ssh-agent", "gpg-agent", "systemd-resolved",
    # ModeOS process itself
    "modeos", "main.py", "python", "python3"
}

def resolve_app_name(app_name: str, installed_apps: Dict[str, str]) -> str:
    """Resolves an app alias to an executable name."""
    clean = app_name.strip().lower()
    return installed_apps.get(clean, clean)

def get_running_user_processes() -> List[psutil.Process]:
    """Returns all running processes owned by current user."""
    try:
        current_uid = psutil.Process().uids().real
    except Exception:
        current_uid = os.geteuid() if hasattr(os, "geteuid") else None

    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'uids', 'nice']):
        try:
            if current_uid is not None:
                p_uid = proc.info.get('uids')
                if p_uid and p_uid.real != current_uid:
                    continue
            procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return procs

def matches_app(proc: psutil.Process, target_exec: str) -> bool:
    """Checks if a process matches target executable or name."""
    target = target_exec.strip().lower()
    try:
        # Check process comm name
        name = (proc.info.get('name') or proc.name() or "").lower()
        if name == target or name.startswith(target[:14]): # 15-char Linux limit
            return True

        # Check full executable path basename
        try:
            exe = proc.exe()
            if exe and os.path.basename(exe).lower() == target:
                return True
        except (psutil.AccessDenied, psutil.NoSuchProcess, Exception):
            pass

        # Check cmdline tokens
        cmdline = proc.info.get('cmdline') or []
        for arg in cmdline[:3]:
            base = os.path.basename(arg).lower()
            if base == target:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False

def is_system_protected(proc: psutil.Process) -> bool:
    """Determines if a process is a critical system service."""
    try:
        name = (proc.info.get('name') or proc.name() or "").lower()
        for exc in SYSTEM_EXCEPTIONS:
            if exc in name:
                return True
    except Exception:
        pass
    return False

def terminate_process_list(procs_to_kill: List[psutil.Process], dry_run: bool = False) -> List[Tuple[int, str]]:
    """
    Terminates processes gracefully using SIGTERM, waiting up to 2 seconds,
    then escalating to SIGKILL only if necessary.
    Returns list of (pid, name) terminated.
    """
    if not procs_to_kill:
        return []

    killed = []
    if dry_run:
        for p in procs_to_kill:
            try:
                name = p.info.get('name') or p.name()
                killed.append((p.pid, name))
                log.info(f"[DRY-RUN] Would terminate: {name} (PID: {p.pid})")
            except Exception:
                pass
        return killed

    # Phase 1: SIGTERM
    alive = []
    for p in procs_to_kill:
        try:
            name = p.info.get('name') or p.name()
            p.terminate()
            alive.append(p)
            killed.append((p.pid, name))
            log.info(f"Sent SIGTERM to: {name} (PID: {p.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            log.debug(f"Could not terminate PID {p.pid}: {e}")

    if not alive:
        return killed

    # Wait up to 2.0s for processes to exit cleanly
    gone, surviving = psutil.wait_procs(alive, timeout=2.0)

    # Phase 2: SIGKILL for stubborn processes
    for p in surviving:
        try:
            name = p.info.get('name') or p.name()
            p.kill()
            log.warning(f"Sent SIGKILL to unresponsive process: {name} (PID: {p.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return killed

def kill_apps(app_list: List[str], installed_apps: Dict[str, str], dry_run: bool = False) -> List[Tuple[int, str]]:
    """Kills running instances of applications in the target list."""
    if not app_list:
        return []

    targets = [resolve_app_name(a, installed_apps) for a in app_list]
    user_procs = get_running_user_processes()
    procs_to_kill = []

    for proc in user_procs:
        if is_system_protected(proc):
            continue
        for target in targets:
            if matches_app(proc, target):
                procs_to_kill.append(proc)
                break

    if not procs_to_kill:
        log.info("No blocked applications are currently running.")
        return []

    return terminate_process_list(procs_to_kill, dry_run=dry_run)

def kill_all_except(allow_list: List[str], installed_apps: Dict[str, str], dry_run: bool = False) -> List[Tuple[int, str]]:
    """Kills all user graphical applications except those in allow_list."""
    log.info("Evaluating processes for focus isolation...")
    allowed_targets = set(resolve_app_name(a, installed_apps) for a in allow_list)
    known_app_names = set(installed_apps.values()) | set(installed_apps.keys())

    user_procs = get_running_user_processes()
    procs_to_kill = []

    for proc in user_procs:
        if is_system_protected(proc):
            continue

        # Check if process is explicitly allowed
        is_allowed = any(matches_app(proc, target) for target in allowed_targets)
        if is_allowed:
            continue

        # To be safe, only kill if it's a known desktop application
        try:
            name = (proc.info.get('name') or proc.name() or "").lower()
            if name in known_app_names:
                procs_to_kill.append(proc)
        except Exception:
            pass

    if not procs_to_kill:
        log.info("No non-whitelisted applications found running.")
        return []

    return terminate_process_list(procs_to_kill, dry_run=dry_run)

def adjust_priorities(
    priority_dict: Dict[str, int],
    installed_apps: Dict[str, str],
    dry_run: bool = False
) -> Dict[int, int]:
    """
    Adjusts process nice values.
    Returns a dictionary mapping {PID: original_nice} for rollback/revert.
    """
    if not priority_dict:
        return {}

    modified_pids = {}
    user_procs = get_running_user_processes()

    for app, target_nice in priority_dict.items():
        exec_name = resolve_app_name(app, installed_apps)
        matched = False

        for proc in user_procs:
            if matches_app(proc, exec_name):
                matched = True
                try:
                    original_nice = proc.nice()
                    p_name = proc.info.get('name') or proc.name()

                    if original_nice == target_nice:
                        continue

                    if dry_run:
                        log.info(f"[DRY-RUN] Would adjust priority for {p_name} (PID: {proc.pid}) from {original_nice} to {target_nice}")
                        modified_pids[proc.pid] = original_nice
                        continue

                    # Attempt setting nice value
                    proc.nice(target_nice)
                    modified_pids[proc.pid] = original_nice
                    log.info(f"Adjusted priority for {p_name} (PID: {proc.pid}): {original_nice} -> {target_nice}")
                except psutil.AccessDenied:
                    if target_nice < 0:
                        log.warning(
                            f"Permission denied boosting priority for {proc.name()} (PID: {proc.pid}) to {target_nice}. "
                            "Negative nice values require root or CAP_SYS_NICE."
                        )
                    else:
                        log.warning(f"Permission denied adjusting priority for PID {proc.pid}")
                except Exception as e:
                    log.error(f"Failed to adjust priority for PID {proc.pid}: {e}")

        if not matched:
            log.debug(f"Target app '{app}' ({exec_name}) is not currently running.")

    return modified_pids

def restore_process_priorities(pid_priorities: Dict[int, int], dry_run: bool = False) -> int:
    """Restores recorded processes back to their pre-mode nice values."""
    if not pid_priorities:
        return 0

    restored = 0
    for pid_str, orig_nice in pid_priorities.items():
        try:
            pid = int(pid_str)
            if not psutil.pid_exists(pid):
                continue
            proc = psutil.Process(pid)
            cur_nice = proc.nice()
            if cur_nice == orig_nice:
                continue

            if dry_run:
                log.info(f"[DRY-RUN] Would restore priority for PID {pid} to {orig_nice}")
                restored += 1
                continue

            proc.nice(orig_nice)
            restored += 1
            log.info(f"Restored priority for {proc.name()} (PID: {pid}) to {orig_nice}")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            log.debug(f"Could not restore PID {pid_str}: {e}")
        except Exception:
            pass

    return restored

def reset_all_priorities(dry_run: bool = False) -> int:
    """Resets all non-zero user processes back to nice 0."""
    log.info("Resetting process priorities to 0...")
    user_procs = get_running_user_processes()
    reset_count = 0

    for proc in user_procs:
        try:
            cur_nice = proc.nice()
            if cur_nice != 0:
                p_name = proc.info.get('name') or proc.name()
                if dry_run:
                    log.info(f"[DRY-RUN] Would reset priority for {p_name} (PID: {proc.pid}) to 0")
                    reset_count += 1
                    continue
                proc.nice(0)
                reset_count += 1
                log.info(f"Reset priority for {p_name} (PID: {proc.pid}) to 0")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception:
            pass

    return reset_count

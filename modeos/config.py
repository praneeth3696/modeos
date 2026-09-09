"""
ModeOS Configuration and Path Management
Follows XDG Base Directory specifications with safe fallbacks.
"""

import os
from pathlib import Path

def get_xdg_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        p = Path(base) / "modeos"
    else:
        p = Path.home() / ".config" / "modeos"
    return p

def get_xdg_state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME")
    if base:
        p = Path(base) / "modeos"
    else:
        p = Path.home() / ".local" / "state" / "modeos"
    return p

def get_xdg_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        p = Path(base) / "modeos"
    else:
        p = Path.home() / ".cache" / "modeos"
    return p

# Project root (where this code lives or installed package)
PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent

def get_mode_search_dirs():
    """Returns search paths for mode YAML definitions in order of priority."""
    dirs = [
        get_xdg_config_dir() / "modes",
        REPO_ROOT / "modes",
        PACKAGE_ROOT / "modes"
    ]
    return [d for d in dirs if d.exists()]

def get_default_modes_dir() -> Path:
    """Returns the primary directory to look up or store modes."""
    local_modes = REPO_ROOT / "modes"
    if local_modes.exists():
        return local_modes
    xdg_modes = get_xdg_config_dir() / "modes"
    xdg_modes.mkdir(parents=True, exist_ok=True)
    return xdg_modes

def get_state_file() -> Path:
    """Returns the path to the state persistence file."""
    state_dir = get_xdg_state_dir()
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "last_state.json"
    except (PermissionError, OSError):
        # Fallback to local data dir if accessible, or tmp
        local_data = REPO_ROOT / "data"
        if local_data.exists() and os.access(local_data, os.W_OK):
            return local_data / "last_state.json"
        return Path("/tmp") / "modeos_last_state.json"

def get_app_cache_file() -> Path:
    """Returns path to cached installed apps database."""
    cache_dir = get_xdg_cache_dir()
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "installed_apps.json"
    except (PermissionError, OSError):
        local_data = REPO_ROOT / "data"
        if local_data.exists() and os.access(local_data, os.W_OK):
            return local_data / "installed_apps.json"
        return Path("/tmp") / "modeos_installed_apps.json"

def get_log_file() -> Path:
    """Returns path to ModeOS rotating log file."""
    state_dir = get_xdg_state_dir()
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "modeos.log"
    except (PermissionError, OSError):
        local_logs = REPO_ROOT / "logs"
        if local_logs.exists() and os.access(local_logs, os.W_OK):
            return local_logs / "modeos.log"
        return Path("/tmp") / "modeos.log"

def is_mock_mode() -> bool:
    """Returns true if environment variable MODEOS_MOCK is set."""
    return os.environ.get("MODEOS_MOCK", "0").lower() in ("1", "true", "yes")

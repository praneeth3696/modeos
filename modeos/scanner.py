"""
ModeOS FreeDesktop Application Scanner
Indexes desktop applications across system, user, Flatpak, and Snap directories.
Extracts executable names and FreeDesktop categories.
"""

import glob
import json
import os
import re
import shlex
import shutil
from typing import Dict, List, Set, Tuple
from modeos.config import get_app_cache_file
from modeos.logger import get_logger

log = get_logger()

DESKTOP_DIRS = [
    "/usr/share/applications",
    "/usr/local/share/applications",
    os.path.expanduser("~/.local/share/applications"),
    "/var/lib/flatpak/exports/share/applications",
    os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
    "/var/lib/snapd/desktop/applications",
    "/snap/bin"
]

COMMON_CLI_FALLBACKS = [
    'code', 'nvim', 'vim', 'nano', 'tmux', 'terminal', 'gnome-terminal',
    'konsole', 'alacritty', 'kitty', 'wezterm', 'foot', 'chrome',
    'google-chrome', 'chromium', 'firefox', 'brave', 'edge', 'microsoft-edge',
    'discord', 'spotify', 'slack', 'vlc', 'mpv', 'steam', 'obs', 'obsidian'
]

def clean_exec_string(exec_str: str) -> str:
    """Extracts the base executable name from a .desktop Exec line."""
    try:
        tokens = shlex.split(exec_str)
    except Exception:
        tokens = exec_str.split()

    if not tokens:
        return ""

    # Filter out env prefixes like 'env VAR=val'
    idx = 0
    while idx < len(tokens):
        tok = tokens[idx]
        if tok == "env" or "=" in tok:
            idx += 1
            continue
        break

    if idx < len(tokens):
        raw_cmd = tokens[idx]
    else:
        raw_cmd = tokens[0]

    # Strip arguments like %U, %f, -flags
    raw_cmd = re.sub(r'%[a-zA-Z]', '', raw_cmd).strip()
    return os.path.basename(raw_cmd).lower()

def scan_apps(verbose: bool = True) -> Dict[str, str]:
    """Scans for installed desktop applications and saves index to cache."""
    if verbose:
        log.info("Scanning for installed applications...")

    app_map: Dict[str, str] = {}
    categories_map: Dict[str, List[str]] = {}

    for directory in DESKTOP_DIRS:
        if not os.path.isdir(directory):
            continue

        desktop_files = glob.glob(os.path.join(directory, "*.desktop"))
        for df in desktop_files:
            try:
                with open(df, 'r', encoding='utf-8', errors='ignore') as f:
                    in_main_section = False
                    name = None
                    exec_cmd = None
                    no_display = False
                    categories: List[str] = []

                    for line in f:
                        line = line.strip()
                        if line == "[Desktop Entry]":
                            in_main_section = True
                            continue
                        elif line.startswith("[") and in_main_section:
                            # Sub-action section reached, stop parsing main entry
                            break

                        if not in_main_section:
                            continue

                        if line.startswith("Name=") and not name:
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Exec=") and not exec_cmd:
                            exec_cmd = line.split("=", 1)[1].strip()
                        elif line.startswith("NoDisplay="):
                            val = line.split("=", 1)[1].strip().lower()
                            if val == "true":
                                no_display = True
                        elif line.startswith("Categories="):
                            cats = line.split("=", 1)[1].strip().split(";")
                            categories = [c.strip() for c in cats if c.strip()]

                    if no_display or not name or not exec_cmd:
                        continue

                    base_exec = clean_exec_string(exec_cmd)
                    if not base_exec or base_exec in ("false", "true"):
                        continue

                    norm_name = name.lower()
                    app_map[norm_name] = base_exec
                    app_map[base_exec] = base_exec

                    # Store categories if found
                    if categories:
                        categories_map[base_exec] = categories
            except Exception:
                pass

    # CLI tools scan
    for tool in COMMON_CLI_FALLBACKS:
        if shutil.which(tool):
            app_map[tool] = tool

    cache_file = get_app_cache_file()
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(app_map, f, indent=2)
        if verbose:
            log.info(f"Indexed {len(app_map)} application references.")
            log.info(f"Saved to {cache_file}")
    except Exception as e:
        log.error(f"Failed to cache app index: {e}")

    return app_map

def get_installed_apps() -> Dict[str, str]:
    """Loads indexed apps from cache or performs a new scan if absent."""
    cache_file = get_app_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # If cache not present, scan now
    return scan_apps(verbose=False)

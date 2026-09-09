"""
ModeOS Core Engine
Orchestrates hardware backends, process management, state tracking, and mode switching.
"""

import os
from typing import Dict, List, Optional, Tuple
import psutil
import yaml
from modeos.backends import get_audio_backend, get_display_backend, get_nightlight_backend
from modeos.config import get_mode_search_dirs, is_mock_mode
from modeos.logger import get_logger, BOLD, RESET
from modeos.models import ModeConfig
from modeos.process import (
    adjust_priorities,
    kill_all_except,
    kill_apps,
    reset_all_priorities
)
from modeos.scanner import get_installed_apps
from modeos.state import restore_state, save_state

log = get_logger()

def load_mode_config(mode_name: str) -> Optional[ModeConfig]:
    """Loads a mode configuration from search directories."""
    clean_name = mode_name.replace(".yaml", "").strip()
    for search_dir in get_mode_search_dirs():
        mode_file = search_dir / f"{clean_name}.yaml"
        if mode_file.exists():
            try:
                with open(mode_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        return ModeConfig.from_dict(clean_name, data)
            except Exception as e:
                log.error(f"Error parsing {mode_file}: {e}")
                return None
    log.error(f"Mode '{clean_name}' not found in configuration directories.")
    return None

def list_available_modes() -> List[ModeConfig]:
    """Returns all discoverable mode configurations."""
    modes = {}
    for search_dir in reversed(get_mode_search_dirs()):
        if not search_dir.exists():
            continue
        for file in sorted(search_dir.glob("*.yaml")):
            name = file.stem
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        modes[name] = ModeConfig.from_dict(name, data)
            except Exception:
                pass
    return list(modes.values())

def get_system_stats() -> Dict[str, float]:
    """Returns quick CPU and memory telemetry without artificial delays."""
    try:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None) # non-blocking instant sample
        return {
            "cpu_percent": cpu,
            "memory_percent": mem.percent,
            "memory_used_mb": mem.used / (1024 * 1024),
            "memory_total_mb": mem.total / (1024 * 1024)
        }
    except Exception:
        return {}

def print_stats_comparison(before: Dict[str, float], after: Dict[str, float]):
    """Prints a comparison of system telemetry before and after mode switch."""
    if not before or not after:
        return
    log.info("\n--- System Telemetry Comparison ---")
    log.info(f"CPU Usage:    {before.get('cpu_percent', 0.0):.1f}% -> {after.get('cpu_percent', 0.0):.1f}%")
    log.info(f"Memory Usage: {before.get('memory_percent', 0.0):.1f}% -> {after.get('memory_percent', 0.0):.1f}%")
    log.info("-----------------------------------\n")

def apply_mode(mode_name: str, dry_run: bool = False, force_mock: bool = False) -> bool:
    """Orchestrates applying a specified mode."""
    config = load_mode_config(mode_name)
    if not config:
        return False

    prefix = "[DRY-RUN] " if dry_run else ""
    log.info(f"{prefix}[MODE] {config.name.upper()}")

    warnings = config.validate()
    for w in warnings:
        log.warning(w)

    mock = force_mock or is_mock_mode()
    audio = get_audio_backend(force_mock=mock)
    display = get_display_backend(force_mock=mock)
    nightlight = get_nightlight_backend(force_mock=mock)

    stats_before = get_system_stats()
    installed_apps = get_installed_apps()

    # Pre-flight state save before making modifications
    if not dry_run:
        save_state(active_mode=config.name)

    # 1. Hardware Settings
    if config.brightness is not None:
        display.set_brightness(config.brightness, dry_run=dry_run)

    if config.volume is not None:
        audio.set_volume(config.volume, dry_run=dry_run)

    if config.night_light is not None:
        nightlight.set_night_light(config.night_light, dry_run=dry_run)

    # 2. Process Management (100% dry-run aware)
    terminated = []
    if config.kill_all_except_allow:
        terminated = kill_all_except(config.allow_apps, installed_apps, dry_run=dry_run)
    elif config.block_apps:
        terminated = kill_apps(config.block_apps, installed_apps, dry_run=dry_run)

    # 3. Priority Adjustments
    priority_dict = {}
    priority_dict.update(config.boost_apps)
    priority_dict.update(config.reduce_apps)

    modified_priorities = {}
    if priority_dict:
        modified_priorities = adjust_priorities(priority_dict, installed_apps, dry_run=dry_run)

    # If state was saved, update it with modified priorities for revert
    if not dry_run and (modified_priorities or terminated):
        save_state(
            active_mode=config.name,
            modified_priorities=modified_priorities,
            terminated_apps=terminated
        )

    # 4. CPU Throttling notification
    if config.cpu_limit is not None:
        log.info(f"Target CPU scheduling budget: {config.cpu_limit}%")

    stats_after = get_system_stats()
    print_stats_comparison(stats_before, stats_after)

    log.info(f"[✔] MODE {config.name.upper()} APPLIED")
    return True

def reset_system(dry_run: bool = False, force_mock: bool = False) -> bool:
    """Resets hardware to defaults and normalizes all process priorities to 0."""
    prefix = "[DRY-RUN] " if dry_run else ""
    log.info(f"=== {prefix}Resetting System to Default State ===")

    mock = force_mock or is_mock_mode()
    audio = get_audio_backend(force_mock=mock)
    display = get_display_backend(force_mock=mock)
    nightlight = get_nightlight_backend(force_mock=mock)

    display.set_brightness(100, dry_run=dry_run)
    audio.set_volume(100, dry_run=dry_run)
    nightlight.set_night_light(False, dry_run=dry_run)

    reset_all_priorities(dry_run=dry_run)

    log.info(f"=== {prefix}System Reset Successfully ===")
    return True

def revert_system(dry_run: bool = False, force_mock: bool = False) -> bool:
    """Reverts to pre-mode state including hardware and process priorities."""
    return restore_state(dry_run=dry_run)

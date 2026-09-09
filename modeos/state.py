"""
ModeOS State and Session Persistence Manager
Safely preserves pre-mode hardware settings and altered process priorities for instant rollback.
"""

from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Optional
from modeos.backends import get_audio_backend, get_display_backend, get_nightlight_backend
from modeos.config import get_state_file, is_mock_mode
from modeos.logger import get_logger
from modeos.process import restore_process_priorities

log = get_logger()

def capture_current_state(
    active_mode: Optional[str] = None,
    modified_priorities: Optional[Dict[int, int]] = None,
    terminated_apps: Optional[list] = None
) -> Dict[str, Any]:
    """Captures the current hardware and process states."""
    mock = is_mock_mode()
    audio = get_audio_backend(force_mock=mock)
    display = get_display_backend(force_mock=mock)
    nightlight = get_nightlight_backend(force_mock=mock)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_mode": active_mode,
        "volume": audio.get_volume(),
        "brightness": display.get_brightness(),
        "night_light": nightlight.get_night_light(),
        "modified_priorities": {str(k): v for k, v in (modified_priorities or {}).items()},
        "terminated_apps": terminated_apps or []
    }

def save_state(
    active_mode: Optional[str] = None,
    modified_priorities: Optional[Dict[int, int]] = None,
    terminated_apps: Optional[list] = None
) -> bool:
    """Saves current state to state file."""
    state_file = get_state_file()
    state = capture_current_state(active_mode, modified_priorities, terminated_apps)

    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        log.debug(f"State saved to {state_file}")
        return True
    except Exception as e:
        log.warning(f"Could not save state to {state_file}: {e}")
        return False

def load_last_state() -> Optional[Dict[str, Any]]:
    """Loads the last saved state from disk."""
    state_file = get_state_file()
    if not state_file.exists():
        return None
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Failed to read state file: {e}")
        return None

def restore_state(dry_run: bool = False) -> bool:
    """Restores the system state from the last saved state file."""
    state = load_last_state()
    if not state:
        log.warning("No previous state found. Cannot revert.")
        return False

    prefix = "[DRY-RUN] " if dry_run else ""
    log.info(f"{prefix}Reverting system state to pre-mode configuration...")

    mock = is_mock_mode()
    audio = get_audio_backend(force_mock=mock)
    display = get_display_backend(force_mock=mock)
    nightlight = get_nightlight_backend(force_mock=mock)

    # 1. Restore Volume
    vol = state.get("volume")
    if vol is not None:
        audio.set_volume(vol, dry_run=dry_run)

    # 2. Restore Brightness
    br = state.get("brightness")
    if br is not None:
        display.set_brightness(br, dry_run=dry_run)

    # 3. Restore Night Light
    nl = state.get("night_light")
    if nl is not None:
        nightlight.set_night_light(nl, dry_run=dry_run)

    # 4. Restore Process Priorities
    priors = state.get("modified_priorities", {})
    if priors:
        count = restore_process_priorities(priors, dry_run=dry_run)
        log.info(f"{prefix}Restored {count} process priority changes.")

    log.info(f"[✔] System state successfully reverted")
    return True

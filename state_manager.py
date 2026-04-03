import json
import os
from logger import get_logger
from utils.system_control import get_volume, get_brightness, get_night_light, set_volume, set_brightness, set_night_light

log = get_logger()
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "last_state.json")

def _fix_permissions(path):
    """Attempts to fix file permissions so it's writeable by the current user."""
    try:
        if os.geteuid() != 0 and os.path.exists(path):
            stat_info = os.stat(path)
            if stat_info.st_uid == 0:
                log.warning("[WARN] Running without sudo after previous sudo run. This may cause permission conflicts.")
                
            if not os.access(path, os.W_OK):
                log.warning(f"[WARN] Permission issue detected. Attempting fix on {path}...")
                os.chmod(path, 0o666)
                log.info("[OK] Ownership/permissions corrected")
    except Exception as e:
        log.warning(f"[WARN] Failed to change permissions on {path}: {e}")

def save_state():
    """Saves the current system state."""
    log.info("Saving current system state...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    _fix_permissions(STATE_FILE)
    
    state = {
        "volume": get_volume(),
        "brightness": get_brightness(),
        "night_light": get_night_light()
    }
    
    target_file = STATE_FILE
    success = False
    
    for attempt in range(2):
        try:
            with open(target_file, "w") as f:
                json.dump(state, f, indent=4)
            log.info(f"State saved correctly: {state}")
            success = True
            break
        except PermissionError:
            log.warning(f"[WARN] Permission denied writing to {target_file}. Attempting to fix...")
            _fix_permissions(target_file)
        except Exception as e:
            log.warning(f"[WARN] Failed to save state on attempt {attempt+1}: {e}")
            
    if not success:
        # Fallback to temp file
        import tempfile
        tmp_file = os.path.join(tempfile.gettempdir(), "modeos_last_state.json")
        log.warning(f"[WARN] Could not write to {STATE_FILE}. Falling back to {tmp_file}")
        try:
            with open(tmp_file, "w") as f:
                json.dump(state, f, indent=4)
            log.info(f"State saved to fallback: {tmp_file}")
        except Exception as e:
            log.error(f"[ERROR] Extremely fatal: could not save state anywhere. Mode will continue. Error: {e}")

def restore_state(dry_run=False):
    """Restores the system state from the last saved file."""
    log.info("Restoring previous system state...")
    target_file = STATE_FILE
    if not os.path.exists(target_file):
        import tempfile
        target_file = os.path.join(tempfile.gettempdir(), "modeos_last_state.json")
        
    if not os.path.exists(target_file):
        log.warning("No previous state found. Cannot revert.")
        return False
        
    try:
        with open(target_file, "r") as f:
            state = json.load(f)
    except Exception as e:
        log.warning(f"Failed to read state file: {e}")
        return False
        
    # Validation step: verify keys are present and somewhat sensible
    if not isinstance(state, dict):
        log.warning("State file is corrupted. Cannot revert.")
        return False

    # Execute restore commands securely using system_control
    if "volume" in state and state["volume"] is not None:
        set_volume(state["volume"], dry_run)
            
    if "brightness" in state and state["brightness"] is not None:
        set_brightness(state["brightness"], dry_run)
            
    if "night_light" in state and state["night_light"] is not None:
        set_night_light(state["night_light"], dry_run)

    log.info("System restored successfully")
    return True

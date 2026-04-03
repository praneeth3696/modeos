import os
import subprocess
import time
from logger import get_logger

log = get_logger()
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")

def _run_sh(script_name, arg, dry_run=False):
    """Runs a shell script with robustness."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log.error(f"[{script_name}] Script not found at {script_path}")
        return False
        
    cmd = [script_path, str(arg)]
    if dry_run:
        log.info(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.warning(f"[{script_name}] failed with stderr: {result.stderr.strip() if result.stderr else result.stdout.strip()}")
            return False
        else:
            return True
    except Exception as e:
        log.error(f"[{script_name}] Exception during execution: {e}")
        return False

# ----- GETTERS ----- #

def get_volume():
    """Gets current volume percentage utilizing pactl or amixer."""
    try:
        result = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
        if result.returncode == 0 and "%" in result.stdout:
            return int(result.stdout.split("%")[0].split("/")[-1].strip())
    except FileNotFoundError:
        pass

    try:
        result = subprocess.run(["amixer", "sget", "Master"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "[" in line and "%]" in line:
                    return int(line.split("[")[1].split("%]")[0])
    except FileNotFoundError:
        pass
    return None

def get_brightness():
    """Gets brightness percentage utilizing brightnessctl."""
    try:
        result = subprocess.run(["brightnessctl", "get"], capture_output=True, text=True)
        result_max = subprocess.run(["brightnessctl", "max"], capture_output=True, text=True)
        if result.returncode == 0 and result_max.returncode == 0:
            current = float(result.stdout.strip())
            maximum = float(result_max.stdout.strip())
            return int((current / maximum) * 100)
    except FileNotFoundError:
        pass
    # Basic fallback missing for simple implementation, relying on brightnessctl 
    return None

def get_night_light():
    """Checks if redshift is running."""
    try:
        result = subprocess.run(["pgrep", "redshift"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

# ----- SETTERS ----- #

def set_volume(target_percent, dry_run=False):
    log.info(f"[INFO] Setting volume -> {target_percent}%")
    if _run_sh("volume.sh", target_percent, dry_run):
        if dry_run:
            return True
        # Verify
        time.sleep(0.5)
        current = get_volume()
        if current is not None and abs(current - int(target_percent)) <= 10: # Increased tolerance
            log.info(f"[OK] Volume verified at {current}%")
            return True
        else:
            log.warning(f"[WARN] Volume unverified (Expected: {target_percent}%, Got: {current}%). Retrying once...")
            _run_sh("volume.sh", target_percent, dry_run)
            time.sleep(0.5)
            current = get_volume()
            if current is not None and abs(current - int(target_percent)) <= 10:
                log.info(f"[OK] Volume verified on retry at {current}%")
                return True
            else:
                log.error(f"[ERROR] Failed to set volume after retry.")
                return False
    else:
        log.error(f"[ERROR] Volume script failed completely.")
    return False

def set_brightness(target_percent, dry_run=False):
    log.info(f"[INFO] Setting brightness -> {target_percent}%")
    if _run_sh("brightness.sh", target_percent, dry_run):
        if dry_run:
            return True
        time.sleep(0.5)
        current = get_brightness()
        # if xrandr is used instead of brightnessctl, reading back the % natively via brightnessctl might fail
        # that's acceptable in fallback
        if current is not None and abs(current - int(target_percent)) <= 10:
            log.info(f"[OK] Brightness verified at {current}%")
            return True
        elif current is None:
            log.info(f"[WARN] Set brightness but unable to read back current level (fallback likely used)")
            return True
        else:
            log.warning(f"[WARN] Brightness unverified (Expected: {target_percent}%, Got: {current}%). Retrying once...")
            _run_sh("brightness.sh", target_percent, dry_run)
            time.sleep(0.5)
            current = get_brightness()
            if current is not None and abs(current - int(target_percent)) <= 10:
                log.info(f"[OK] Brightness verified on retry at {current}%")
                return True
            else:
                log.error(f"[ERROR] Failed to set brightness after retry.")
                return False
    else:
        log.error(f"[ERROR] Brightness script failed completely.")
    return False

def set_night_light(state_bool, dry_run=False):
    import shutil
    if not shutil.which("redshift"):
        log.warning("[WARN] Night light not supported on this system (redshift missing)")
        return False

    val = "true" if state_bool else "false"
    text_val = "ON" if state_bool else "OFF"
    log.info(f"[INFO] Setting night light -> {text_val}")
    if _run_sh("nightlight.sh", val, dry_run):
        if dry_run:
            return True
        time.sleep(1.0) # wait for redshift to startup / exit
        current = get_night_light()
        if current == state_bool:
            log.info(f"[OK] Night light verified ({text_val})")
            return True
        else:
            log.warning(f"[WARN] Night light unverified (Expected: {state_bool}, Got: {current}). Retrying once...")
            _run_sh("nightlight.sh", val, dry_run)
            time.sleep(1.0)
            current = get_night_light()
            if current == state_bool:
                log.info(f"[OK] Night light verified on retry ({text_val})")
                return True
            else:
                log.error(f"[ERROR] Failed to set night light after retry.")
                return False
    else:
        log.error(f"[ERROR] Night light script failed completely.")
    return False

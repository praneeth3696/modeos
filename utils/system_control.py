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
    """Checks if night light is enabled via gsettings."""
    try:
        res = subprocess.run(["gsettings", "get", "org.gnome.settings-daemon.plugins.color", "night-light-enabled"], capture_output=True, text=True)
        return "true" in res.stdout.lower()
    except Exception:
        return False

# ----- SETTERS ----- #

def set_volume(target_percent, dry_run=False):
    if os.geteuid() == 0:
        log.warning("[WARN] Running as root may break audio control")

    if dry_run:
        log.info(f"[DRY-RUN] Will set volume to {target_percent}%")
        return True
        
    try:
        res = subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_percent}%"], capture_output=True, text=True)
        if res.returncode == 0:
            target = int(target_percent)
            time.sleep(0.5)
            current = get_volume()
            if current is not None and abs(current - target) <= 10:
                log.info(f"[✔] Volume -> {current}%")
                return True
        log.error("[ERROR] Volume control failed")
        return False
    except Exception as e:
        log.error(f"[ERROR] Volume control failed: {e}")
        return False

def set_brightness(target_percent, dry_run=False):
    requested = int(target_percent)
    target = max(20, requested)
    if requested < 20: 
        log.info("[INFO] Adjusted brightness target due to hardware limits")
        
    if _run_sh("brightness.sh", target, dry_run):
        if dry_run: return True
        time.sleep(0.5)
        current = get_brightness()
        if current is not None and abs(current - target) <= 30:
            log.info(f"[✔] Brightness -> {target}%")
            return True
        elif current is None:
            log.info(f"[✔] Brightness -> {target}% (unverified)")
            return True
        else:
            log.error("[ERROR] Brightness control failed")
            return False
    else:
        log.error("[ERROR] Brightness control failed")
    return False

def set_night_light(state_bool, dry_run=False):
    val = "true" if state_bool else "false"
    text_val = "ON" if state_bool else "OFF"
    
    if dry_run:
        log.info(f"[DRY-RUN] Will set night light to {text_val}")
        return True
        
    try:
        res = subprocess.run(["gsettings", "set", "org.gnome.settings-daemon.plugins.color", "night-light-enabled", val], capture_output=True, text=True)
        if res.returncode == 0:
            log.info(f"[✔] Night light -> {text_val}")
            return True
        else:
            log.warning("[WARN] Night light not supported")
            return False
    except Exception:
        log.warning("[WARN] Night light not supported")
        return False

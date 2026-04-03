import os
import json
import subprocess
import glob
from logger import get_logger

log = get_logger()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
APP_DATA_FILE = os.path.join(DATA_DIR, "installed_apps.json")

def scan_apps():
    """Scans for installed apps and saves them to a JSON file."""
    log.info("Scanning for installed applications...")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    apps = {}

    # Scan .desktop files
    desktop_files = glob.glob("/usr/share/applications/*.desktop")
    for df in desktop_files:
        try:
            with open(df, 'r', encoding='utf-8') as f:
                content = f.read()
                name = None
                exec_cmd = None
                for line in content.split('\n'):
                    if line.startswith("Name=") and not name:
                        name = line.split("=", 1)[1].strip()
                    elif line.startswith("Exec=") and not exec_cmd:
                        exec_cmd = line.split("=", 1)[1].strip().split(' ')[0]
                
                if name and exec_cmd:
                    # extract basename of exec command
                    exec_base = os.path.basename(exec_cmd)
                    # normalize name to lower case
                    normalized_name = name.lower()
                    apps[normalized_name] = exec_base
                    apps[exec_base] = exec_base # Also allow referencing by executable name
        except Exception as e:
            pass
            
    # Optional: We could also scan 'which' for common things, but it's slow to iterate all PATH.
    # Let's add some common known executables just in case they lack a .desktop file
    common_cli_apps = ['code', 'terminal', 'gnome-terminal', 'konsole', 'chrome', 'google-chrome', 'discord', 'spotify', 'vlc']
    for app in common_cli_apps:
        try:
            res = subprocess.run(["which", app], capture_output=True, text=True)
            if res.returncode == 0:
                apps[app] = app
        except Exception:
            pass

    try:
        with open(APP_DATA_FILE, 'w') as f:
            json.dump(apps, f, indent=4)
        log.info(f"Successfully scanned {len(apps)} application references.")
        log.info(f"Saved to {APP_DATA_FILE}")
    except Exception as e:
        log.error(f"Failed to save app data: {e}")

def get_installed_apps():
    """Returns the dictionary of installed apps."""
    if not os.path.exists(APP_DATA_FILE):
        log.warning("App data not found. Running scan...")
        scan_apps()
        
    try:
        with open(APP_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Failed to read app data: {e}")
        return {}

if __name__ == "__main__":
    scan_apps()

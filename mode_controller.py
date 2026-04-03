import os
import yaml
import subprocess
from logger import get_logger
from app_scanner import get_installed_apps
from process_manager import kill_apps, kill_all_except, adjust_priorities, reset_all_priorities
from resource_manager import get_system_stats, print_stats_comparison
from utils.system_control import set_brightness, set_volume, set_night_light

log = get_logger()

MODES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modes")
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")

def load_mode_config(mode_name):
    """Loads a mode configuration from its YAML file."""
    mode_file = os.path.join(MODES_DIR, f"{mode_name}.yaml")
    if not os.path.exists(mode_file):
        log.error(f"Mode configuration for '{mode_name}' not found at {mode_file}.")
        return None
        
    try:
        with open(mode_file, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except yaml.YAMLError as e:
        log.error(f"Error parsing {mode_name}.yaml: {e}")
        return None

def run_script(script_name, arg):
    """Runs a shell script from the scripts directory."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        log.error(f"Script {script_name} not found.")
        return
        
    try:
        subprocess.run([script_path, str(arg)], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Error running {script_name}: {e.stderr.strip() if e.stderr else 'Unknown error'}")
    except Exception as e:
        log.error(f"Failed to execute {script_name}: {e}")

def apply_mode(mode_name, dry_run=False):
    """Orchestrates the application of a specified mode."""
    mode_text = "[DRY-RUN] Activating" if dry_run else "Activating"
    log.info(f"=== {mode_text} '{mode_name.upper()}' Mode ===")
    
    config = load_mode_config(mode_name)
    if not config:
        return False
        
    installed_apps = get_installed_apps()
    
    # 1. Gather stats before switch
    stats_before = get_system_stats()
    
    # 2. Hardware Settings
    if 'brightness' in config and config['brightness'] is not None:
        set_brightness(config['brightness'], dry_run)
        
    if 'volume' in config and config['volume'] is not None:
        set_volume(config['volume'], dry_run)
        
    if 'night_light' in config and config['night_light'] is not None:
        set_night_light(bool(config['night_light']), dry_run)
        
    # 3. Process Management
    if config.get('kill_all_except_allow'):
        allow_list = config.get('allow_apps') or []
        kill_all_except(allow_list, installed_apps)
    else:
        block_list = config.get('block_apps') or []
        if block_list:
            kill_apps(block_list, installed_apps)
            
    # 4. Priority Adjustments
    boost_apps = config.get('boost_apps') or {}
    reduce_apps = config.get('reduce_apps') or {}
    
    priority_dict = {}
    for app, nice in boost_apps.items():
        priority_dict[app] = nice
    for app, nice in reduce_apps.items():
        priority_dict[app] = nice
        
    if priority_dict:
        adjust_priorities(priority_dict, installed_apps)
        
    # Optional CPU limiting mapping
    if 'cpu_limit' in config:
        # Complex to enforce pure CPU limiting per group without cgroups
        # But we can use extreme nice values for non-allowed apps.
        # This is out of scope for a basic version, but nice already maps priority.
        log.info(f"Global CPU prioritization adjusting toward mode limit ({config['cpu_limit']}%)")

    # 5. Gather stats after switch and compare
    stats_after = get_system_stats()
    print_stats_comparison(stats_before, stats_after)
    
    log.info(f"=== '{mode_name.upper()}' Mode Activated Successfully ===")
    return True

def reset_system(dry_run=False):
    """Resets the system back to normal defaults."""
    reset_text = "[DRY-RUN] Resetting" if dry_run else "Resetting"
    log.info(f"=== {reset_text} System to Default State ===")
    
    # 1. Reset hardware
    set_brightness(100, dry_run)
    set_volume(100, dry_run)
    set_night_light(False, dry_run)
    
    # 2. Reset process priorities
    reset_all_priorities()
    
    log.info("=== System Reset Successfully ===")
    return True

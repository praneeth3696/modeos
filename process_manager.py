import psutil
from logger import get_logger

log = get_logger()

def get_running_processes_by_name():
    """Returns a dictionary of process names mapped to a list of process objects."""
    processes = {}
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name']
            if name:
                name = name.lower()
                if name not in processes:
                    processes[name] = []
                processes[name].append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def resolve_app_name(app_name, installed_apps):
    """Tries to resolve an app alias to an executable name."""
    app_name_lower = app_name.lower()
    return installed_apps.get(app_name_lower, app_name_lower)

def kill_apps(app_list, installed_apps):
    """Kills all processes matching the applications in the list."""
    if not app_list:
        return

    running_procs = get_running_processes_by_name()
    for app in app_list:
        exec_name = resolve_app_name(app, installed_apps)
        if exec_name in running_procs:
            for proc in running_procs[exec_name]:
                try:
                    proc.kill()
                    log.info(f"Killed process: {proc.info['name']} (PID: {proc.pid})")
                except Exception as e:
                    log.error(f"Failed to kill {proc.info['name']}: {e}")
        else:
            log.info(f"Target app '{app}' (exec: '{exec_name}') is not currently running.")

def kill_all_except(allow_list, installed_apps):
    """Kills all user apps except those in the allow_list."""
    log.info("Killing all user processes except allowed ones...")
    # This is a very dangerous function. We must be extremely careful to only kill user processes 
    # that look like GUI/desktop applications, rather than system services.
    # A safe approach is to only check processes associated with the current user and not system critical.
    
    allowed_execs = set(resolve_app_name(app, installed_apps) for app in allow_list)
    # Add vital system/desktop environment processes to a safe exception list
    system_exceptions = {
        'systemd', 'xorg', 'wayland', 'gnome-shell', 'plasma', 'kwin', 'bash', 'zsh', 'python', 'ssh',
        'dbus-daemon', 'pulseaudio', 'pipewire', 'wireplumber', 'modeos', 'main.py'
    }
    
    current_uid = psutil.Process().uids().real
    
    for proc in psutil.process_iter(['pid', 'name', 'uids']):
        try:
            # Only kill processes owned by the current user
            if proc.info['uids'] and proc.info['uids'].real == current_uid:
                name = proc.info['name']
                if not name:
                    continue
                name_lower = name.lower()
                
                # Check if it's in the allowed list or system exceptions
                if name_lower not in allowed_execs and not any(ext in name_lower for ext in system_exceptions):
                    # We should be very careful here. Let's only kill if we see it in our installed_apps DB
                    # to avoid killing random user daemon processes
                    if name_lower in installed_apps.values() or name_lower in installed_apps.keys():
                        proc.kill()
                        log.info(f"Killed non-whitelisted process: {name} (PID: {proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def adjust_priorities(priority_dict, installed_apps):
    """Adjusts process priorities via nice values. Negative is higher priority."""
    if not priority_dict:
        return
        
    running_procs = get_running_processes_by_name()
    for app, nice_val in priority_dict.items():
        exec_name = resolve_app_name(app, installed_apps)
        if exec_name in running_procs:
            for proc in running_procs[exec_name]:
                try:
                    # nice_val should be an int between -20 and 19
                    # Note: negative nice values usually require sudo
                    proc.nice(int(nice_val))
                    log.info(f"Adjusted priority for {proc.info['name']} (PID: {proc.pid}) to {nice_val}")
                except psutil.AccessDenied:
                    log.error(f"Permission denied adjusting priority for {proc.info['name']}. Try running with sudo.")
                except Exception as e:
                    log.error(f"Failed to adjust priority for {proc.info['name']}: {e}")
        else:
            log.info(f"Target app '{app}' (exec: '{exec_name}') is not currently running to adjust priority.")

def reset_all_priorities():
    """Resets the priority of all user processes to 0."""
    log.info("Resetting all user process priorities to 0...")
    current_uid = psutil.Process().uids().real
    for proc in psutil.process_iter(['pid', 'name', 'uids', 'nice']):
        try:
            if proc.info['uids'] and proc.info['uids'].real == current_uid:
                if proc.info.get('nice', 0) != 0:
                    proc.nice(0)
                    log.info(f"Reset priority for {proc.info['name']} (PID: {proc.pid}) to 0")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

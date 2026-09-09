"""
ModeOS Subsystem Diagnostics & Doctor
Inspects Linux audio, display, desktop environment, and process capabilities.
"""

import os
import platform
import shutil
import sys
from typing import List, Tuple
from modeos.backends import get_audio_backend, get_display_backend, get_nightlight_backend
from modeos.config import get_mode_search_dirs
from modeos.logger import get_logger, BOLD, GREEN, RED, YELLOW, CYAN, RESET

log = get_logger()

def check_dependencies() -> bool:
    """Runs a structured health check on system backends."""
    print(f"\n{BOLD}=== ModeOS System Diagnostics ==={RESET}\n")

    # 1. Environment & Desktop
    os_name = platform.system()
    release = platform.release()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
    session_type = os.environ.get("XDG_SESSION_TYPE", "Unknown")
    print(f"{CYAN}OS & Environment:{RESET}")
    print(f"  System:       {os_name} {release}")
    print(f"  Desktop:      {desktop}")
    print(f"  Session Type: {session_type}")
    try:
        uid = os.geteuid()
        print(f"  User UID:     {uid} {'(Running as root)' if uid == 0 else '(Standard user)'}")
    except Exception:
        pass

    # 2. Audio Providers
    print(f"\n{CYAN}Audio Control Providers:{RESET}")
    audio_tools = [
        ("wpctl", "WirePlumber / PipeWire"),
        ("pactl", "PulseAudio / PipeWire-Pulse"),
        ("amixer", "ALSA Audio")
    ]
    for tool, desc in audio_tools:
        found = shutil.which(tool) is not None
        badge = f"{GREEN}[OK]{RESET}" if found else f"{YELLOW}[MISSING]{RESET}"
        print(f"  {badge} {tool:<10} ({desc})")

    active_audio = get_audio_backend()
    print(f"  -> Active Audio Provider: {BOLD}{active_audio.name}{RESET}")

    # 3. Brightness Providers
    print(f"\n{CYAN}Display Brightness Providers:{RESET}")
    sysfs_nodes = []
    if os.path.exists("/sys/class/backlight"):
        sysfs_nodes = os.listdir("/sys/class/backlight")
    sysfs_status = f"{GREEN}[OK]{RESET} ({', '.join(sysfs_nodes)})" if sysfs_nodes else f"{YELLOW}[NONE]{RESET}"
    print(f"  {sysfs_status:<10} /sys/class/backlight nodes")

    display_tools = [
        ("brightnessctl", "Systemd backlight controller"),
        ("xrandr", "X11 software gamma controller"),
        ("ddcutil", "DDC/CI External monitor controller")
    ]
    for tool, desc in display_tools:
        found = shutil.which(tool) is not None
        badge = f"{GREEN}[OK]{RESET}" if found else f"{YELLOW}[MISSING]{RESET}"
        print(f"  {badge} {tool:<14} ({desc})")

    active_display = get_display_backend()
    print(f"  -> Active Display Provider: {BOLD}{active_display.name}{RESET}")

    # 4. Night Light Providers
    print(f"\n{CYAN}Night Light / Blue Light Filter Providers:{RESET}")
    nl_tools = [
        ("gsettings", "GNOME Night Light"),
        ("qdbus", "KDE Plasma Color Correct"),
        ("gammastep", "Wayland Color Temperature"),
        ("redshift", "X11 Color Temperature")
    ]
    for tool, desc in nl_tools:
        found = shutil.which(tool) is not None
        badge = f"{GREEN}[OK]{RESET}" if found else f"{YELLOW}[MISSING]{RESET}"
        print(f"  {badge} {tool:<12} ({desc})")

    active_nl = get_nightlight_backend()
    print(f"  -> Active Night Light Provider: {BOLD}{active_nl.name}{RESET}")

    # 5. Config directories
    print(f"\n{CYAN}Configuration & State Directories:{RESET}")
    dirs = get_mode_search_dirs()
    for d in dirs:
        print(f"  Found mode directory: {d}")

    print(f"\n{BOLD}=== Diagnostics Complete ==={RESET}\n")
    return True

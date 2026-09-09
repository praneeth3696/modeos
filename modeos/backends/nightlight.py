"""
Night Light / Color Temperature Backend Providers for ModeOS
Supports GNOME GSettings, KDE Plasma D-Bus, Gammastep/Wlsunset (Wayland), Redshift (X11), and Mock.
"""

import os
import shutil
import subprocess
from typing import Optional
from modeos.backends.base import NightLightBackend
from modeos.logger import get_logger

log = get_logger()

class GnomeNightLightBackend(NightLightBackend):
    """GNOME Desktop GSettings Night Light Provider."""
    SCHEMA = "org.gnome.settings-daemon.plugins.color"
    KEY = "night-light-enabled"

    @property
    def name(self) -> str:
        return "GNOME Night Light (GSettings)"

    def is_available(self) -> bool:
        if shutil.which("gsettings") is None:
            return False
        try:
            res = subprocess.run(["gsettings", "list-schemas"], capture_output=True, text=True)
            return self.SCHEMA in res.stdout
        except Exception:
            return False

    def get_night_light(self) -> Optional[bool]:
        try:
            res = subprocess.run(["gsettings", "get", self.SCHEMA, self.KEY], capture_output=True, text=True)
            if res.returncode == 0:
                return "true" in res.stdout.lower()
        except Exception as e:
            log.debug(f"GNOME night light read error: {e}")
        return None

    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        val = "true" if enable else "false"
        label = "ON" if enable else "OFF"
        if dry_run:
            log.info(f"[DRY-RUN] Would execute: gsettings set {self.SCHEMA} {self.KEY} {val}")
            return True
        try:
            res = subprocess.run(["gsettings", "set", self.SCHEMA, self.KEY, val], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            log.error(f"GNOME night light error: {e}")
            return False


class KdeNightLightBackend(NightLightBackend):
    """KDE Plasma Night Color Provider via D-Bus."""
    @property
    def name(self) -> str:
        return "KDE Plasma Night Color (D-Bus)"

    def is_available(self) -> bool:
        if shutil.which("qdbus") is None:
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        return "kde" in desktop or "plasma" in desktop

    def get_night_light(self) -> Optional[bool]:
        try:
            res = subprocess.run(
                ["qdbus", "org.kde.KWin", "/ColorCorrect", "org.kde.kwin.ColorCorrect.nightColorConfig"],
                capture_output=True, text=True
            )
            if res.returncode == 0:
                return "Active: true" in res.stdout or "Running: true" in res.stdout
        except Exception as e:
            log.debug(f"KDE night color read error: {e}")
        return None

    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        val = "true" if enable else "false"
        if dry_run:
            log.info(f"[DRY-RUN] Would set KDE Night Color to {val}")
            return True
        try:
            res = subprocess.run(
                ["qdbus", "org.kde.KWin", "/ColorCorrect", "org.kde.kwin.ColorCorrect.setNightColorConfig", val],
                capture_output=True, text=True
            )
            return res.returncode == 0
        except Exception as e:
            log.error(f"KDE night color error: {e}")
            return False


class GammastepBackend(NightLightBackend):
    """Gammastep / Wlsunset provider for Wayland compositors (Sway, Hyprland, etc.)."""
    @property
    def name(self) -> str:
        return "Gammastep (Wayland)"

    def is_available(self) -> bool:
        return shutil.which("gammastep") is not None

    def get_night_light(self) -> Optional[bool]:
        # Gammastep runs as a daemon process when active
        try:
            res = subprocess.run(["pgrep", "-x", "gammastep"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return None

    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        label = "ON (3500K)" if enable else "OFF"
        if dry_run:
            log.info(f"[DRY-RUN] Would set Gammastep night light to {label}")
            return True
        try:
            subprocess.run(["pkill", "-x", "gammastep"], capture_output=True)
            if enable:
                subprocess.Popen(["gammastep", "-O", "3500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            log.error(f"Gammastep error: {e}")
            return False


class RedshiftBackend(NightLightBackend):
    """Redshift provider for X11 environments."""
    @property
    def name(self) -> str:
        return "Redshift (X11)"

    def is_available(self) -> bool:
        return shutil.which("redshift") is not None and bool(os.environ.get("DISPLAY"))

    def get_night_light(self) -> Optional[bool]:
        try:
            res = subprocess.run(["pgrep", "-x", "redshift"], capture_output=True)
            return res.returncode == 0
        except Exception:
            return None

    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        label = "ON (3500K)" if enable else "OFF"
        if dry_run:
            log.info(f"[DRY-RUN] Would execute: redshift {'-O 3500' if enable else '-x'}")
            return True
        try:
            subprocess.run(["redshift", "-x"], capture_output=True)
            subprocess.run(["pkill", "-x", "redshift"], capture_output=True)
            if enable:
                subprocess.Popen(["redshift", "-O", "3500"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            log.error(f"Redshift error: {e}")
            return False


class MockNightLightBackend(NightLightBackend):
    """Simulated in-memory night light backend for testing and cross-platform environments."""
    def __init__(self, initial_state: bool = False):
        self._state = initial_state

    @property
    def name(self) -> str:
        return "Mock Night Light Simulator"

    def is_available(self) -> bool:
        return True

    def get_night_light(self) -> Optional[bool]:
        return self._state

    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        label = "ON" if enable else "OFF"
        if dry_run:
            log.info(f"[DRY-RUN] [MOCK NIGHT LIGHT] Would set night light to {label}")
            return True
        self._state = enable
        log.info(f"[MOCK NIGHT LIGHT] Night light set to {label}")
        return True


def get_nightlight_backend(force_mock: bool = False) -> NightLightBackend:
    if force_mock:
        return MockNightLightBackend()

    gnome = GnomeNightLightBackend()
    if gnome.is_available():
        return gnome

    kde = KdeNightLightBackend()
    if kde.is_available():
        return kde

    gammastep = GammastepBackend()
    if gammastep.is_available():
        return gammastep

    redshift = RedshiftBackend()
    if redshift.is_available():
        return redshift

    return MockNightLightBackend()

"""
Display / Brightness Backend Providers for ModeOS
Supports direct Linux sysfs backlight, brightnessctl, xrandr, and Mock.
"""

import glob
import os
import shutil
import subprocess
from typing import Optional
from modeos.backends.base import DisplayBackend
from modeos.logger import get_logger

log = get_logger()

class SysfsBacklightBackend(DisplayBackend):
    """Direct Linux sysfs backlight controller (/sys/class/backlight)."""
    @property
    def name(self) -> str:
        return "Linux Sysfs Backlight (/sys/class/backlight)"

    def _get_device_paths(self):
        devices = glob.glob("/sys/class/backlight/*")
        return devices

    def is_available(self) -> bool:
        return len(self._get_device_paths()) > 0

    def get_brightness(self) -> Optional[int]:
        devices = self._get_device_paths()
        if not devices:
            return None
        dev = devices[0]
        try:
            with open(os.path.join(dev, "brightness"), "r") as f:
                cur = float(f.read().strip())
            with open(os.path.join(dev, "max_brightness"), "r") as f:
                max_b = float(f.read().strip())
            if max_b > 0:
                return int(round((cur / max_b) * 100))
        except Exception as e:
            log.debug(f"Sysfs backlight read failed: {e}")
        return None

    def set_brightness(self, target_percent: int, dry_run: bool = False) -> bool:
        devices = self._get_device_paths()
        if not devices:
            return False
        dev = devices[0]
        target_percent = max(5, min(100, int(target_percent)))

        if dry_run:
            log.info(f"[DRY-RUN] Would set backlight to {target_percent}% via {dev}")
            return True

        try:
            with open(os.path.join(dev, "max_brightness"), "r") as f:
                max_b = float(f.read().strip())
            target_raw = int(round((target_percent / 100.0) * max_b))
            with open(os.path.join(dev, "brightness"), "w") as f:
                f.write(str(target_raw))
            return True
        except PermissionError:
            # Writing to sysfs directly usually requires root or udev backlight group
            log.debug(f"Permission denied writing directly to {dev}/brightness, will fall back")
            return False
        except Exception as e:
            log.debug(f"Sysfs write failed: {e}")
            return False


class BrightnessctlBackend(DisplayBackend):
    """Standard systemd brightnessctl controller."""
    @property
    def name(self) -> str:
        return "brightnessctl"

    def is_available(self) -> bool:
        return shutil.which("brightnessctl") is not None

    def get_brightness(self) -> Optional[int]:
        try:
            cur_res = subprocess.run(["brightnessctl", "get"], capture_output=True, text=True)
            max_res = subprocess.run(["brightnessctl", "max"], capture_output=True, text=True)
            if cur_res.returncode == 0 and max_res.returncode == 0:
                cur = float(cur_res.stdout.strip())
                max_b = float(max_res.stdout.strip())
                if max_b > 0:
                    return int(round((cur / max_b) * 100))
        except Exception as e:
            log.debug(f"brightnessctl read failed: {e}")
        return None

    def set_brightness(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(5, min(100, int(target_percent)))
        if dry_run:
            log.info(f"[DRY-RUN] Would execute: brightnessctl set {target_percent}%")
            return True
        try:
            res = subprocess.run(["brightnessctl", "set", f"{target_percent}%"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            log.error(f"brightnessctl failed: {e}")
            return False


class XrandrBackend(DisplayBackend):
    """X11 xrandr software gamma fallback."""
    @property
    def name(self) -> str:
        return "xrandr (X11)"

    def is_available(self) -> bool:
        return shutil.which("xrandr") is not None and bool(os.environ.get("DISPLAY"))

    def get_brightness(self) -> Optional[int]:
        try:
            res = subprocess.run(["xrandr", "--verbose"], capture_output=True, text=True)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "Brightness:" in line:
                        val = float(line.split(":")[1].strip())
                        return int(round(val * 100))
        except Exception as e:
            log.debug(f"xrandr read failed: {e}")
        return None

    def set_brightness(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(10, min(100, int(target_percent)))
        decimal_val = f"{target_percent / 100.0:.2f}"
        if dry_run:
            log.info(f"[DRY-RUN] Would execute: xrandr --output <connected> --brightness {decimal_val}")
            return True
        try:
            res = subprocess.run(["xrandr"], capture_output=True, text=True)
            if res.returncode != 0:
                return False
            success = False
            for line in res.stdout.splitlines():
                if " connected" in line:
                    disp = line.split()[0]
                    sub = subprocess.run(["xrandr", "--output", disp, "--brightness", decimal_val], capture_output=True, text=True)
                    if sub.returncode == 0:
                        success = True
            return success
        except Exception as e:
            log.error(f"xrandr error: {e}")
            return False


class MockDisplayBackend(DisplayBackend):
    """Simulated in-memory display backend for testing and cross-platform environments."""
    def __init__(self, initial_brightness: int = 80):
        self._brightness = initial_brightness

    @property
    def name(self) -> str:
        return "Mock Display Simulator"

    def is_available(self) -> bool:
        return True

    def get_brightness(self) -> Optional[int]:
        return self._brightness

    def set_brightness(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(0, min(100, int(target_percent)))
        if dry_run:
            log.info(f"[DRY-RUN] [MOCK DISPLAY] Would set brightness to {target_percent}%")
            return True
        self._brightness = target_percent
        log.info(f"[MOCK DISPLAY] Brightness set to {target_percent}%")
        return True


def get_display_backend(force_mock: bool = False) -> DisplayBackend:
    if force_mock:
        return MockDisplayBackend()

    # If brightnessctl is available, it handles permissions safely via udev/systemd
    bctl = BrightnessctlBackend()
    if bctl.is_available():
        return bctl

    sysfs = SysfsBacklightBackend()
    if sysfs.is_available():
        return sysfs

    xrandr = XrandrBackend()
    if xrandr.is_available():
        return xrandr

    return MockDisplayBackend()

"""
Audio Backend Providers for ModeOS
Supports WirePlumber (PipeWire), PulseAudio, ALSA, and Mock.
"""

import shutil
import subprocess
from typing import Optional
from modeos.backends.base import AudioBackend
from modeos.logger import get_logger

log = get_logger()

class WirePlumberBackend(AudioBackend):
    """Modern PipeWire / WirePlumber backend using wpctl."""
    @property
    def name(self) -> str:
        return "WirePlumber (PipeWire)"

    def is_available(self) -> bool:
        return shutil.which("wpctl") is not None

    def get_volume(self) -> Optional[int]:
        try:
            res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True)
            if res.returncode == 0:
                # Output format: "Volume: 0.50" or "Volume: 0.50 [MUTED]"
                parts = res.stdout.strip().split()
                if len(parts) >= 2 and parts[0] == "Volume:":
                    vol_float = float(parts[1])
                    return int(round(vol_float * 100))
        except Exception as e:
            log.debug(f"WirePlumber get_volume failed: {e}")
        return None

    def set_volume(self, target_percent: int, dry_run: bool = False) -> bool:
        decimal_val = max(0.0, min(1.0, target_percent / 100.0))
        if dry_run:
            log.info(f"[DRY-RUN] Would set WirePlumber volume to {target_percent}% (wpctl set-volume @DEFAULT_AUDIO_SINK@ {decimal_val:.2f})")
            return True
        try:
            res = subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{decimal_val:.2f}"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            log.error(f"wpctl error: {e}")
            return False


class PulseAudioBackend(AudioBackend):
    """PulseAudio / PipeWire-Pulse backend using pactl."""
    @property
    def name(self) -> str:
        return "PulseAudio (pactl)"

    def is_available(self) -> bool:
        return shutil.which("pactl") is not None

    def get_volume(self) -> Optional[int]:
        try:
            res = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True)
            if res.returncode == 0 and "%" in res.stdout:
                # Example: Volume: front-left: 32768 /  50% / -18.06 dB ...
                for part in res.stdout.split():
                    if part.endswith("%"):
                        clean_num = part.replace("%", "").strip()
                        if clean_num.isdigit():
                            return int(clean_num)
        except Exception as e:
            log.debug(f"PulseAudio get_volume failed: {e}")
        return None

    def set_volume(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(0, min(100, int(target_percent)))
        if dry_run:
            log.info(f"[DRY-RUN] Would set PulseAudio volume to {target_percent}% (pactl set-sink-volume @DEFAULT_SINK@ {target_percent}%)")
            return True
        try:
            res = subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{target_percent}%"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            log.error(f"pactl error: {e}")
            return False


class AlsaBackend(AudioBackend):
    """Direct ALSA backend using amixer."""
    @property
    def name(self) -> str:
        return "ALSA (amixer)"

    def is_available(self) -> bool:
        return shutil.which("amixer") is not None

    def get_volume(self) -> Optional[int]:
        try:
            res = subprocess.run(["amixer", "sget", "Master"], capture_output=True, text=True)
            if res.returncode == 0:
                for line in res.stdout.split("\n"):
                    if "[" in line and "%]" in line:
                        pct = line.split("[")[1].split("%]")[0]
                        if pct.isdigit():
                            return int(pct)
        except Exception as e:
            log.debug(f"amixer get_volume failed: {e}")
        return None

    def set_volume(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(0, min(100, int(target_percent)))
        if dry_run:
            log.info(f"[DRY-RUN] Would set ALSA volume to {target_percent}% (amixer sset Master {target_percent}%)")
            return True
        try:
            res = subprocess.run(["amixer", "sset", "Master", f"{target_percent}%"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception as e:
            log.error(f"amixer error: {e}")
            return False


class MockAudioBackend(AudioBackend):
    """Simulated in-memory audio backend for testing and cross-platform environments."""
    def __init__(self, initial_volume: int = 50):
        self._volume = initial_volume

    @property
    def name(self) -> str:
        return "Mock Audio Simulator"

    def is_available(self) -> bool:
        return True

    def get_volume(self) -> Optional[int]:
        return self._volume

    def set_volume(self, target_percent: int, dry_run: bool = False) -> bool:
        target_percent = max(0, min(100, int(target_percent)))
        if dry_run:
            log.info(f"[DRY-RUN] [MOCK AUDIO] Would set volume to {target_percent}%")
            return True
        self._volume = target_percent
        log.info(f"[MOCK AUDIO] Volume set to {target_percent}%")
        return True


def get_audio_backend(force_mock: bool = False) -> AudioBackend:
    if force_mock:
        return MockAudioBackend()

    # Prefer PipeWire / WirePlumber first on modern Linux
    wp = WirePlumberBackend()
    if wp.is_available():
        return wp

    pulse = PulseAudioBackend()
    if pulse.is_available():
        return pulse

    alsa = AlsaBackend()
    if alsa.is_available():
        return alsa

    # Fallback to mock if no audio utility is present
    return MockAudioBackend()

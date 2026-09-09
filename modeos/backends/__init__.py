"""
ModeOS Hardware Backend Package
Provides factory functions for audio, display, and night light providers.
"""

from modeos.backends.base import AudioBackend, DisplayBackend, NightLightBackend
from modeos.backends.audio import get_audio_backend, MockAudioBackend
from modeos.backends.display import get_display_backend, MockDisplayBackend
from modeos.backends.nightlight import get_nightlight_backend, MockNightLightBackend

__all__ = [
    "AudioBackend",
    "DisplayBackend",
    "NightLightBackend",
    "get_audio_backend",
    "get_display_backend",
    "get_nightlight_backend",
    "MockAudioBackend",
    "MockDisplayBackend",
    "MockNightLightBackend"
]

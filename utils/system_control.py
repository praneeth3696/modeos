"""
Legacy utils.system_control compatibility shim for ModeOS
"""

from modeos.backends import get_audio_backend, get_display_backend, get_nightlight_backend

def get_volume():
    return get_audio_backend().get_volume()

def set_volume(target_percent, dry_run=False):
    return get_audio_backend().set_volume(target_percent, dry_run=dry_run)

def get_brightness():
    return get_display_backend().get_brightness()

def set_brightness(target_percent, dry_run=False):
    return get_display_backend().set_brightness(target_percent, dry_run=dry_run)

def get_night_light():
    return get_nightlight_backend().get_night_light()

def set_night_light(state_bool, dry_run=False):
    return get_nightlight_backend().set_night_light(state_bool, dry_run=dry_run)

__all__ = [
    "get_volume", "set_volume",
    "get_brightness", "set_brightness",
    "get_night_light", "set_night_light"
]

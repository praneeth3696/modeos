"""
Legacy mode_controller compatibility shim for ModeOS
"""

from modeos.core import apply_mode, load_mode_config, reset_system
from modeos.logger import get_logger

log = get_logger()

__all__ = ["apply_mode", "load_mode_config", "reset_system"]

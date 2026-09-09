"""
Legacy process_manager compatibility shim for ModeOS
"""

from modeos.process import (
    adjust_priorities,
    kill_all_except,
    kill_apps,
    reset_all_priorities,
    resolve_app_name,
)

__all__ = [
    "adjust_priorities",
    "kill_all_except",
    "kill_apps",
    "reset_all_priorities",
    "resolve_app_name"
]

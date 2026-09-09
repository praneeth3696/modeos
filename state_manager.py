"""
Legacy state_manager compatibility shim for ModeOS
"""

from modeos.state import restore_state, save_state

__all__ = ["save_state", "restore_state"]

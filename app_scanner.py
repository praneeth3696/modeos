"""
Legacy app_scanner compatibility shim for ModeOS
"""

from modeos.scanner import get_installed_apps, scan_apps

__all__ = ["get_installed_apps", "scan_apps"]

if __name__ == "__main__":
    scan_apps()

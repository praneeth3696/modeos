"""
Abstract Base Classes for ModeOS Hardware Backends
"""

from abc import ABC, abstractmethod
from typing import Optional

class AudioBackend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the audio provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the required system tools or services exist."""
        pass

    @abstractmethod
    def get_volume(self) -> Optional[int]:
        """Returns current volume percentage (0-100) or None."""
        pass

    @abstractmethod
    def set_volume(self, target_percent: int, dry_run: bool = False) -> bool:
        """Sets system volume to target percentage (0-100)."""
        pass


class DisplayBackend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the brightness provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the required system tools or hardware interfaces exist."""
        pass

    @abstractmethod
    def get_brightness(self) -> Optional[int]:
        """Returns current brightness percentage (0-100) or None."""
        pass

    @abstractmethod
    def set_brightness(self, target_percent: int, dry_run: bool = False) -> bool:
        """Sets display brightness percentage (0-100)."""
        pass


class NightLightBackend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the night light / color temperature provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the required system tools or services exist."""
        pass

    @abstractmethod
    def get_night_light(self) -> Optional[bool]:
        """Returns True if night light is currently active, False if inactive, None if unknown."""
        pass

    @abstractmethod
    def set_night_light(self, enable: bool, dry_run: bool = False) -> bool:
        """Enables or disables night light / blue light filter."""
        pass

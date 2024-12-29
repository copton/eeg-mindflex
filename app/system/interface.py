import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class OsOperations(ABC):
    """Abstract base class for OS-specific operations."""

    def prevent_sleep(self) -> None:
        """Prevents the system from entering sleep mode."""
        try:
            self._prevent_sleep()
        except Exception as e:
            logger.error(f"Failed to prevent sleep: {e}")
        logger.debug("Sleep prevention enabled")

    def restore_sleep(self) -> None:
        """Restores the system's default sleep behavior."""
        try:
            self._restore_sleep()
        except Exception as e:
            logger.error(f"Failed to restore sleep: {e}")
        logger.debug("Sleep prevention disabled")

    def set_volume(self, volume: float) -> None:
        """Sets the system volume level.

        Args:
            volume: Float that will be clipped between 0.0 and 1.0 representing volume level
        """
        volume = max(0.0, min(1.0, volume))
        try:
            self._set_volume(volume)
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
        logger.debug(f"Volume set to {volume}")

    @abstractmethod
    def _restore_sleep(self) -> None:
        """Restores the system's default sleep behavior."""

    @abstractmethod
    def _prevent_sleep(self) -> None:
        """Internal method to prevent the system from entering sleep mode."""

    @abstractmethod
    def _set_volume(self, volume: float) -> None:
        pass


def create_os_operations() -> Optional[OsOperations]:
    """Factory function that creates the appropriate OsOperations object based
    on the current OS.

    Returns:
        OsOperations: An instance of the OS-specific operations class.
    """
    import platform

    system = platform.system().lower()

    if system == "windows":
        from .windows import WindowsOperations

        return WindowsOperations()
    elif system == "darwin":
        from .macos import MacOperations

        return MacOperations()
    elif system == "linux":
        from .linux import LinuxOperations

        return LinuxOperations()
    else:
        return None

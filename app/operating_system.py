from abc import ABC, abstractmethod
import logging
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

    @abstractmethod
    def _restore_sleep(self) -> None:
        """Restores the system's default sleep behavior."""
        pass

    @abstractmethod
    def _prevent_sleep(self) -> None:
        """Internal method to prevent the system from entering sleep mode."""
        pass


class _WindowsOperations(OsOperations):
    def __init__(self):
        self._previous_state: Optional[int] = None

    def _prevent_sleep(self) -> None:
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        self._previous_state = ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )
        logger.debug("Sleep prevention enabled on Windows")

    def restore_sleep(self) -> None:
        if self._previous_state is not None:
            import ctypes

            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            logger.debug("Sleep prevention disabled on Windows")


class _MacOperations(OsOperations):
    def __init__(self):
        self._caffeinate_process = None

    def _prevent_sleep(self) -> None:
        import subprocess

        self._caffeinate_process = subprocess.Popen(["caffeinate", "-d"])
        logger.debug("Sleep prevention enabled on macOS")

    def _restore_sleep(self) -> None:
        if self._caffeinate_process:
            self._caffeinate_process.terminate()
            self._caffeinate_process = None
            logger.debug("Sleep prevention disabled on macOS")


class _LinuxOperations(OsOperations):
    def _prevent_sleep(self) -> None:
        import subprocess

        subprocess.run(
            [
                "systemctl",
                "mask",
                "sleep.target",
                "suspend.target",
                "hibernate.target",
                "hybrid-sleep.target",
            ]
        )
        logger.debug("Sleep prevention enabled on Linux")

    def _restore_sleep(self) -> None:
        import subprocess

        subprocess.run(
            [
                "systemctl",
                "unmask",
                "sleep.target",
                "suspend.target",
                "hibernate.target",
                "hybrid-sleep.target",
            ]
        )
        logger.debug("Sleep prevention disabled on Linux")


def create_os_operations() -> Optional[OsOperations]:
    """Factory function that creates the appropriate OsOperations object based
    on the current OS.

    Returns:
        OsOperations: An instance of the OS-specific operations class.
    """
    import platform

    system = platform.system().lower()

    if system == "windows":
        return _WindowsOperations()
    elif system == "darwin":
        return _MacOperations()
    elif system == "linux":
        return _LinuxOperations()
    else:
        return None


class PreventSleep:
    """Context manager that prevents system sleep while active."""

    def __init__(self, os_operations: OsOperations):
        self.os_operations = os_operations

    def __enter__(self):
        self.os_operations.prevent_sleep()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.os_operations.restore_sleep()
        return False  # Re-raise any exceptions

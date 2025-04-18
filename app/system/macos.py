import logging
import subprocess

from .interface import OsOperations

logger = logging.getLogger(__name__)


class MacOperations(OsOperations):
    def __init__(self) -> None:
        self._caffeinate_process: subprocess.Popen | None = None

    def _prevent_sleep(self) -> None:
        self._caffeinate_process = subprocess.Popen(["caffeinate", "-d"])
        logger.debug("Sleep prevention enabled on macOS")

    def _restore_sleep(self) -> None:
        if self._caffeinate_process:
            self._caffeinate_process.terminate()
            self._caffeinate_process = None
            logger.debug("Sleep prevention disabled on macOS")

    def _set_volume(self, volume: float) -> None:
        import subprocess

        # Convert 0-1 float to 0-100 integer
        vol = int(volume * 100)
        subprocess.run(["osascript", "-e", f"set volume output volume {vol}"])
        logger.debug(f"Volume set to {volume} on macOS")

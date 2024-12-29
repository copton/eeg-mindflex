import logging
import subprocess

from .interface import OsOperations

logger = logging.getLogger(__name__)


class LinuxOperations(OsOperations):
    def _prevent_sleep(self) -> None:
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

    def _set_volume(self, volume: float) -> None:
        vol = int(volume * 100)
        subprocess.run(["amixer", "sset", "Master", f"{vol}%"])
        logger.debug(f"Volume set to {volume} on Linux")

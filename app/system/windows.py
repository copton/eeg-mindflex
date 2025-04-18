import logging

from .interface import OsOperations

logger = logging.getLogger(__name__)


class WindowsOperations(OsOperations):
    def __init__(self) -> None:
        self._previous_state: int | None = None

    def _prevent_sleep(self) -> None:
        import ctypes

        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        self._previous_state = ctypes.windll.kernel32.SetThreadExecutionState(  # type: ignore
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED
        )
        logger.debug("Sleep prevention enabled on Windows")

    def _restore_sleep(self) -> None:
        if self._previous_state is not None:
            import ctypes

            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)  # type: ignore
            logger.debug("Sleep prevention disabled on Windows")

    def _set_volume(self, volume: float) -> None:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL  # type: ignore
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
        volume_interface.SetMasterVolumeLevelScalar(volume, None)
        logger.debug(f"Volume set to {volume} on Windows")

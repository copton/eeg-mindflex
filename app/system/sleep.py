from .interface import OsOperations


class PreventSleep:
    """Context manager that prevents system sleep while active."""

    def __init__(self, activate: bool, os_operations: OsOperations):
        self.activate = activate
        self.os_operations = os_operations

    def __enter__(self):
        if self.activate:
            self.os_operations.prevent_sleep()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.activate:
            self.os_operations.restore_sleep()
        return False  # Re-raise any exceptions

import sys
from unittest.mock import MagicMock

def pytest_configure(config):
    """
    Hook executed before test collection.
    Used here to globally mock UI libraries that are not needed for most
    backend and integration tests, preventing ModuleNotFoundError in
    headless environments like CI/CD.
    """
    # A standard MagicMock is sufficient. It will create mocks for any accessed
    # attributes on the fly. The previous custom class caused a RecursionError.
    mock_pyqt = MagicMock()

    # The key to preventing `TypeError: metaclass conflict` when a class in the
    # tested code inherits from a PyQt class (like QObject) is to ensure that
    # the mocked base class is a real, inheritable class. `object` is perfect.
    mock_pyqt.QObject = object

    # Assign the same mock instance to all PyQt5 modules. This ensures that
    # `from PyQt5.QtCore import QObject` and `from PyQt5.QtWidgets import QWidget`
    # all resolve to the same mocked namespace.
    sys.modules['PyQt5'] = mock_pyqt
    sys.modules['PyQt5.QtCore'] = mock_pyqt
    sys.modules['PyQt5.QtWidgets'] = mock_pyqt
    sys.modules['PyQt5.QtGui'] = mock_pyqt
    sys.modules['PyQt5.QtPrintSupport'] = mock_pyqt
    sys.modules['PyQt5.QtChart'] = mock_pyqt

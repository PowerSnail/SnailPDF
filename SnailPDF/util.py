from PySide2 import QtGui
import contextlib
from typing import List, Dict, Optional, Any, Generator, ContextManager


@contextlib.contextmanager
def q_painter(device: QtGui.QPaintDevice) -> ContextManager[QtGui.QPainter]:
    painter = QtGui.QPainter()
    painter.begin(device)
    yield painter
    painter.end()
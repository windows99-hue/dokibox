# -*- coding: utf-8 -*-
"""dokibox.cmdbox -- top-left gray panel"""
import sys
import ctypes
from PySide6.QtCore import Qt, QEventLoop
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget
from dokibox._base import _get_app, _get_dpi_scale

CMD_COLOR = "#888888"
WIDTH_RATIO = 2.7
HEIGHT_RATIO = 3.5

DWMWA_BORDER_COLOR = 34
DWMWA_SHADOW_OPACITY = 33


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cxTopHeight", ctypes.c_int),
        ("cxBottomHeight", ctypes.c_int),
    ]


def _remove_dwm_frame(hwnd):
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))


def _remove_window_shadow(hwnd):
    zero_val = ctypes.c_uint(0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SHADOW_OPACITY,
        ctypes.byref(zero_val),
        ctypes.sizeof(zero_val),
    )


class _CmdPanel(QWidget):

    def __init__(self, pinned=True):
        _get_app()
        super().__init__(None)
        self._pinned = pinned

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        sw = self.screen().size().width()
        sh = self.screen().size().height()
        w = int(sw / WIDTH_RATIO)
        h = int(sh / HEIGHT_RATIO)
        self.setWindowOpacity(0.4)
        self.setGeometry(0, 0, w, h)
        self.setFixedSize(w, h)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            _remove_dwm_frame(hwnd)
            _remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
            self.deleteLater()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(CMD_COLOR))
        painter.end()


def cmdbox(pinned=True):
    """Show a gray borderless panel in the top-left corner of the screen.

    Width  = screen width  / 2.7
    Height = screen height / 3.5

    Press ESC to close.

    Args:
        pinned: keep the window always on top (default True).
    """
    panel = _CmdPanel(pinned=pinned)
    panel.show()
    panel.raise_()
    panel.activateWindow()
    loop = QEventLoop()
    panel.destroyed.connect(loop.quit)
    loop.exec()

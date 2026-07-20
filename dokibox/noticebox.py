# -*- coding: utf-8 -*-
"""dokibox.noticebox -- top-left notice/toast notification"""
import sys
import ctypes
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QEventLoop
from PySide6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QLinearGradient, QBrush, QPen,
)
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from dokibox._base import _get_app, _get_dpi_scale

NOTICE_HEIGHT = 60
NOTICE_WIDTH_RATIO = 0.35
FONT_SIZE = 16
TEXT_COLOR = "#555555"
FADE_DURATION = 300
TOP_MARGIN = 60
LEFT_PADDING = 16

DWMWA_BORDER_COLOR = 34
DWMWA_SHADOW_OPACITY = 33


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth",     ctypes.c_int),
        ("cxRightWidth",    ctypes.c_int),
        ("cxTopHeight",     ctypes.c_int),
        ("cxBottomHeight",  ctypes.c_int),
    ]


def _remove_dwm_frame(hwnd):
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))


def _remove_window_shadow(hwnd):
    zero_val = ctypes.c_uint(0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd, DWMWA_SHADOW_OPACITY,
        ctypes.byref(zero_val), ctypes.sizeof(zero_val),
    )


class _NoticeWidget(QWidget):

    def __init__(self, msg, last, x, y, w):
        _get_app()
        super().__init__(None)
        self._msg = msg
        h = NOTICE_HEIGHT

        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(x, y, w, h)
        self.setFixedSize(w, h)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._fade_out)
        self._close_timer.start(int(last * 1000))

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(FADE_DURATION)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.InQuad)
        self._anim.finished.connect(self._close)
        self._anim.start()

    def _close(self):
        self.hide()
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            _remove_dwm_frame(hwnd)
            _remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        gradient = QLinearGradient(w * 0.30, 0, w, 0)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 240))
        gradient.setColorAt(0.45, QColor(255, 255, 255, 240))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, 0, w, h)

        font = QFont("Microsoft YaHei", int(FONT_SIZE / _get_dpi_scale()))
        painter.setFont(font)
        painter.setPen(QColor(TEXT_COLOR))
        fm = QFontMetrics(font)
        tx = int(LEFT_PADDING / _get_dpi_scale())
        ty = int((h + fm.ascent()) // 2 - 1)
        painter.drawText(tx, ty, self._msg)

        painter.end()


_notices = []


def notice(msg="", last=3):
    screen = _get_app().primaryScreen()
    sw = screen.size().width()
    dpi_s = 1.0 / _get_dpi_scale()
    w = int(sw * NOTICE_WIDTH_RATIO)
    h = NOTICE_HEIGHT
    x = 0
    y = TOP_MARGIN + len(_notices) * (h + 4)
    widget = _NoticeWidget(msg, last, x, y, w)
    _notices.append(widget)
    widget.show()
    widget.raise_()

    loop = QEventLoop()
    widget.destroyed.connect(loop.quit)
    loop.exec()

    _cleanup(widget)
    return widget


def _cleanup(obj):
    try:
        _notices.remove(obj)
    except ValueError:
        pass

# -*- coding: utf-8 -*-
"""dokibox internal base class -- window / gradient border / stroked text / dragging"""
import sys
import math
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QEventLoop, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics


BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"


def _get_dpi_scale():
    try:
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            return screen.devicePixelRatio()
    except Exception:
        pass
    return 1.0


_app_instance = None


def _get_app():
    global _app_instance
    if _app_instance is not None:
        return _app_instance
    existing = QApplication.instance()
    if existing is not None:
        _app_instance = existing
        return _app_instance
    _app_instance = QApplication(sys.argv)
    return _app_instance


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class _DokiBase(QWidget):
    """Dialog base class. Subclasses implement _calc_size / _draw_content / _on_click."""

    BORDER_W = 12

    def __init__(self, msg, title="", pinned=True):
        _get_app()
        super().__init__(None)
        self.result = None
        self._msg = msg
        self._pinned = pinned
        self._drag_pos = QPoint()
        self._drag_start = QPoint()
        self._click_pos = QPoint()
        self._dpi_s = 1.0 / _get_dpi_scale()

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setMouseTracking(True)

        self.w, self.h = self._calc_size(msg)
        sw = self.screen().size().width()
        sh = self.screen().size().height()
        x = (sw - self.w) // 2
        y = (sh - self.h) // 2
        self.setGeometry(x, y, self.w, self.h)
        self.setFixedSize(self.w, self.h)

    def _calc_size(self, msg):
        raise NotImplementedError

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BODY_COLOR))
        self._draw_gradient_border(painter)
        self._draw_content(painter)
        painter.end()

    def _draw_content(self, painter):
        raise NotImplementedError

    def _on_click_local(self, event):
        pass

    def _draw_gradient_border(self, painter):
        br, bg, bb = _hex_to_rgb(BORDER_COLOR)
        er, eg, eb = _hex_to_rgb(BODY_COLOR)
        bw = max(self.BORDER_W, 8)
        for i in range(bw):
            t = (i / max(bw - 1, 1)) ** 3
            r = int(br + (er - br) * t)
            g = int(bg + (eg - bg) * t)
            b = int(bb + (eb - bb) * t)
            painter.setPen(QPen(QColor(r, g, b), 1))
            painter.drawRect(i, i, self.w - i * 2, self.h - i * 2)

    def _draw_stroked_text(self, painter, x, y, text, font, fill_color, stroke_color, stroke_w):
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        th = fm.height()
        text_x = int(x - tw // 2)
        text_y = int(y + fm.ascent() - th // 2)
        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = int(stroke_w * math.cos(angle))
            dy = int(stroke_w * math.sin(angle))
            painter.setPen(QColor(stroke_color))
            painter.drawText(text_x + dx, text_y + dy, text)
        painter.setPen(QColor(fill_color))
        painter.drawText(text_x, text_y, text)

    def _draw_stroked_text_left(self, painter, x, y, text, font, fill_color, stroke_color, stroke_w):
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_y = int(y + fm.ascent() - fm.height() // 2)
        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = int(stroke_w * math.cos(angle))
            dy = int(stroke_w * math.sin(angle))
            painter.setPen(QColor(stroke_color))
            painter.drawText(int(x) + dx, text_y + dy, text)
        painter.setPen(QColor(fill_color))
        painter.drawText(int(x), text_y, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._click_pos = event.globalPosition().toPoint()
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_start = self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self._drag_start + delta)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            delta = (event.globalPosition().toPoint() - self._click_pos).manhattanLength()
            if delta < 5:
                self._on_click_local(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done(False)

    def _done(self, value):
        self.result = value
        self.hide()
        self.deleteLater()

    @classmethod
    def run(cls, *args, **kwargs):
        dialog = cls(*args, **kwargs)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        loop = QEventLoop()
        dialog.destroyed.connect(loop.quit)
        loop.exec()
        return dialog.result

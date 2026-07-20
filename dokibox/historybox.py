# -*- coding: utf-8 -*-
"""dokibox.historybox -- history display window with dotted background"""
import math
import sys
import ctypes
from PySide6.QtCore import Qt, QEventLoop, QPointF, QTimer, QElapsedTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import QWidget
from dokibox._base import _get_app
from dokibox._widgets import draw_stroked_text_left


DOT_COLOR = "#FFEEF8"
DOT_GAP_X = 160
DOT_GAP_Y = 45
DOT_SPEED_X = 42.0
DOT_SPEED_Y = 42.0


class _HistoryBox(QWidget):

    def __init__(self, data, pinned=True):
        _get_app()
        super().__init__(None)
        self.result = None
        self._data = data

        if sys.platform == "win32":
            ctypes.windll.winmm.timeBeginPeriod(1)

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setMouseTracking(True)
        self._drag_pos = None

        sw = self.screen().size().width()
        sh = self.screen().size().height()
        w = int(sw * 0.5)
        h = int(w * 9 / 16)
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.setGeometry(x, y, w, h)
        self.setFixedSize(w, h)

        self._offset_x = 0.0
        self._offset_y = 0.0
        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _grid_params(self):
        h = self.height()
        dr = h / 17
        step_x = int(dr * 2 + DOT_GAP_X)
        row_h = int(dr * 2 + DOT_GAP_Y)
        return dr, step_x, row_h

    def _tick(self):
        dt = self._elapsed.restart() / 1000.0
        self._offset_x += DOT_SPEED_X * dt
        self._offset_y += DOT_SPEED_Y * dt
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(DOT_COLOR)))

        w = self.width()
        h = self.height()
        dr, step_x, row_h = self._grid_params()
        m = dr * 3

        first_row = math.floor((self._offset_y - dr - m) / row_h)
        last_row = math.ceil((self._offset_y + h + m - dr) / row_h)

        for r in range(first_row, last_row + 1):
            row_offset = step_x // 2 if r % 2 == 1 else 0
            y = dr + r * row_h - self._offset_y

            first_col = math.floor((self._offset_x - dr - row_offset - m) / step_x)
            last_col = math.ceil((self._offset_x + w + m - dr - row_offset) / step_x)

            for c in range(first_col, last_col + 1):
                x = dr + row_offset + c * step_x - self._offset_x
                painter.drawEllipse(QPointF(x, y), dr, dr)

        self._draw_left_curtain(painter, w, h)

        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        draw_stroked_text_left(painter, int(w / 20), int(h / 15), "历史",
                               title_font, "#ffffff", "#BD539D", 3)
        draw_stroked_text_left(painter, int(w / 20), int(h - h / 10), "返回游戏",
                               title_font, "#ffffff", "#BD539D", 3)

        painter.end()

    def _draw_left_curtain(self, painter, w, h):
        top_x = w * 0.12
        bot_x = w * 0.12
        bulge = w * 0.3

        def draw_shape(tx, tb, bu, color):
            path = QPainterPath()
            path.moveTo(0, -h * 0.2)
            path.lineTo(tx, -h * 0.2)
            path.cubicTo(bu, h * (-0.15), bu, h * 1.15, tb, h * 1.2)
            path.lineTo(0, h * 1.2)
            path.closeSubpath()
            painter.setBrush(QColor(color))
            painter.drawPath(path)

        draw_shape(top_x, bot_x, bulge, "#FFBDE1")
        draw_shape(top_x - w * 0.03, bot_x - w * 0.03, bulge - w * 0.03, "#FEE6F4")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_start = self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self._drag_start + delta)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done()

    def _done(self):
        self._timer.stop()
        self.result = None
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


def historybox(data="", pinned=True):
    return _HistoryBox.run(data, pinned=pinned)

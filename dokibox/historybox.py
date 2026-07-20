# -*- coding: utf-8 -*-
"""dokibox.historybox -- history display window with dotted background"""
from PySide6.QtCore import Qt, QEventLoop, QPointF, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QWidget
from dokibox._base import _get_app


DOT_COLOR = "#FFEEF8"
DOT_GAP_X = 160
DOT_GAP_Y = 45
DOT_SPEED_X = 1.40
DOT_SPEED_Y = 1.40


class _HistoryBox(QWidget):

    def __init__(self, data, pinned=True):
        _get_app()
        super().__init__(None)
        self.result = None
        self._data = data

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

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def _grid_params(self):
        h = self.height()
        dr = h / 17
        step_x = int(dr * 2 + DOT_GAP_X)
        row_h = int(dr * 2 + DOT_GAP_Y)
        return dr, step_x, row_h

    def _tick(self):
        self._offset_x += DOT_SPEED_X
        self._offset_y += DOT_SPEED_Y
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

        first_row = int((self._offset_y - dr - m) / row_h) - 1
        last_row = int((self._offset_y + h + m - dr) / row_h) + 1

        for r in range(first_row, last_row + 1):
            row_offset = step_x // 2 if r % 2 == 1 else 0
            y = dr + r * row_h - self._offset_y

            first_col = int((self._offset_x - dr - row_offset - m) / step_x) - 1
            last_col = int((self._offset_x + w + m - dr - row_offset) / step_x) + 1

            for c in range(first_col, last_col + 1):
                x = dr + row_offset + c * step_x - self._offset_x
                painter.drawEllipse(QPointF(x, y), dr, dr)

        painter.end()

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

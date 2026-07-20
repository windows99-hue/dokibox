# -*- coding: utf-8 -*-
"""dokibox.historybox -- history display window with dotted background"""
from PySide6.QtCore import Qt, QEventLoop, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtWidgets import QWidget
from dokibox._base import _get_app


DOT_COLOR = "#FFEEF8"
DOT_GAP_X = 160
DOT_GAP_Y = 45


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

        self._dots = self._generate_dots()

    def _generate_dots(self):
        w = self.width()
        h = self.height()

        dr = h / 17
        step_x = int(dr * 2 + DOT_GAP_X)
        row_h = int(dr * 2 + DOT_GAP_Y)

        dots = []
        row = 0
        y = dr
        while y < h + row_h:
            offset_x = step_x // 2 if row % 2 == 1 else 0
            x = max(0, offset_x)
            while x < w + step_x:
                dots.append((x, y))
                x += step_x
            y += row_h
            row += 1
        return dots

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(DOT_COLOR)))

        h = self.height()
        dr = h / 14
        for x, y in self._dots:
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

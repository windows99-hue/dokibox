# -*- coding: utf-8 -*-
"""dokibox.historybox -- history display window with dotted background"""
import math
import sys
import ctypes
from PySide6.QtCore import Qt, QEventLoop, QPointF, QTimer, QElapsedTimer
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPainterPath, QFont, QFontMetrics,
)
from PySide6.QtWidgets import QWidget, QScrollBar
from dokibox._base import _get_app
from dokibox._widgets import draw_stroked_text_left


class _StrokedTextArea(QWidget):

    def __init__(self, parent, records, font, bold_font, fill_color, stroke_color, stroke_w):
        super().__init__(parent)
        self._records = records
        self._font = font
        self._bold_font = bold_font
        self._fill = fill_color
        self._stroke = stroke_color
        self._stroke_w = stroke_w
        self._lines = []
        self._line_h = 0
        self._scroll = 0
        self.setMouseTracking(True)

    def set_geometry(self, x, y, w, h):
        self.setGeometry(x, y, w, h)
        self._wrap_lines(w - 8)

    def _wrap_lines(self, area_w):
        fm = QFontMetrics(self._font)
        bm = QFontMetrics(self._bold_font)
        self._line_h = max(fm.lineSpacing(), bm.lineSpacing())
        self._lines = []

        for idx, (name, msg) in enumerate(self._records):
            if idx > 0:
                self._lines.append([])

            prefix = f"{name}："
            prefix_w = bm.horizontalAdvance(prefix)

            raw_lines = msg.split('\n')
            for li, raw_line in enumerate(raw_lines):
                if li == 0:
                    if not raw_line:
                        self._lines.append([(prefix, True)])
                        continue
                    avail = area_w - prefix_w
                    if avail <= 0:
                        self._lines.append([(prefix, True)])
                        avail = area_w
                    current = ''
                    for ch in raw_line:
                        if fm.horizontalAdvance(current + ch) <= avail:
                            current += ch
                        else:
                            segs = [(prefix, True)] if avail == area_w - prefix_w else []
                            if current:
                                segs.append((current, False))
                            self._lines.append(segs)
                            current = ch
                            avail = area_w
                    segs = [(prefix, True)] if avail == area_w - prefix_w else []
                    if current:
                        segs.append((current, False))
                    if segs:
                        self._lines.append(segs)
                else:
                    if not raw_line:
                        self._lines.append([])
                        continue
                    current = ''
                    for ch in raw_line:
                        if fm.horizontalAdvance(current + ch) <= area_w:
                            current += ch
                        else:
                            self._lines.append([(current, False)])
                            current = ch
                    if current:
                        self._lines.append([(current, False)])

        total_h = len(self._lines) * self._line_h
        self.setFixedHeight(total_h)

    def scroll_to(self, value):
        self._scroll = value
        self.update()

    def line_height(self):
        return self._line_h

    def total_lines(self):
        return len(self._lines)

    def paintEvent(self, event):
        if not self._lines:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        start_line = self._scroll // self._line_h
        end_line = min(len(self._lines),
                       (self._scroll + self.parent().height()) // self._line_h + 2)

        for i in range(start_line, end_line):
            y = i * self._line_h - self._scroll + self._line_h // 2
            segments = self._lines[i]
            if not segments:
                continue
            x = 8
            for text, is_bold in segments:
                font = self._bold_font if is_bold else self._font
                draw_stroked_text_left(painter, int(x), int(y), text,
                                       font, self._fill, self._stroke, self._stroke_w)
                fm = QFontMetrics(font)
                x += fm.horizontalAdvance(text)

        painter.end()

DOT_COLOR = "#FFEEF8"
DOT_GAP_X = 160
DOT_GAP_Y = 45
DOT_SPEED_X = 42.0
DOT_SPEED_Y = 42.0

SBAR_QSS = """
QScrollBar:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent, stop:0.44 transparent,
        stop:0.45 #000000, stop:0.55 #000000,
        stop:0.56 transparent, stop:1 transparent);
    width: %(sbw)dpx;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #ffffff;
    border: 1px solid #000000;
    border-radius: 0px;
    min-height: 60px;
}
QScrollBar::handle:vertical:hover {
    background: #D5D3CE;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""

TEXT_PAD_LEFT = 50
TEXT_PAD_TOP = 20
TEXT_PAD_RIGHT = 30
TEXT_PAD_BOT = 20
TEXT_FONT_SIZE = 18
SBAR_W = 20


class _HistoryBox(QWidget):

    def __init__(self, records, pinned=True):
        _get_app()
        super().__init__(None)
        self.result = None
        self._records = records

        if sys.platform == "win32":
            ctypes.windll.winmm.timeBeginPeriod(1)

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        self.setMouseTracking(True)
        self._drag_pos = None
        self._hover_return = False
        self._return_rect = None

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

        self._setup_text()

    def _setup_text(self):
        w = self.width()
        h = self.height()

        tx = int(w * 0.28)
        ty = int(h * 0.14)
        tw = int(w - w * 0.28 - TEXT_PAD_RIGHT)
        th = int(h * 0.72)

        text_font = QFont("Microsoft YaHei", TEXT_FONT_SIZE)
        bold_font = QFont("Microsoft YaHei", TEXT_FONT_SIZE, QFont.Bold)
        self._text = _StrokedTextArea(self, self._records, text_font, bold_font,
                                      "#ffffff", "#000000", 2)

        self._setup_scrollbar(tx, ty, tw, th)

    def _setup_scrollbar(self, tx, ty, tw, th):
        sb_w = SBAR_W
        self._sbar = QScrollBar(Qt.Vertical, self)
        self._sbar.setStyleSheet(SBAR_QSS % {"sbw": sb_w, "bg": "#E4E2DD"})
        self._sbar.setGeometry(tx + tw - sb_w, ty, sb_w, th)
        self._sbar.valueChanged.connect(self._text.scroll_to)

        self._text.set_geometry(tx, ty, tw - sb_w - 8, th)

        self._sync_scroll_range()

    def _sync_scroll_range(self):
        content_h = self._text.total_lines() * self._text.line_height()
        visible_h = self._sbar.height()
        if content_h > visible_h:
            self._sbar.setRange(0, content_h - visible_h)
            self._sbar.setPageStep(visible_h)
            self._sbar.setVisible(True)
            self._sbar.setValue(content_h - visible_h)
        else:
            self._sbar.setRange(0, 0)
            self._sbar.setVisible(False)

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
        fm = QFontMetrics(title_font)

        hx = int(w / 20)
        hy = int(h / 15)
        draw_stroked_text_left(painter, hx, hy, "历史",
                               title_font, "#ffffff", "#BD539D", 3)

        rx = int(w / 20)
        ry = int(h - h / 10)
        return_fill = "#ffd0e8" if self._hover_return else "#ffffff"
        draw_stroked_text_left(painter, rx, ry, "返回游戏",
                               title_font, return_fill, "#BD539D", 3)
        rw = fm.horizontalAdvance("返回游戏")
        th = fm.height()
        self._return_rect = (rx, ry - th // 2, rw + 12, th)

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

    def _check_hover(self, pos):
        ret_hover = False
        if self._return_rect:
            rx, ry, rw, rh = self._return_rect
            if rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh:
                ret_hover = True
        if ret_hover != self._hover_return:
            self._hover_return = ret_hover
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_start = self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self._drag_start + delta)
        self._check_hover(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._return_rect:
            rx, ry, rw, rh = self._return_rect
            pos = event.position().toPoint()
            if rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh:
                self._done()
                return

    def enterEvent(self, event):
        self._check_hover(event.position().toPoint())

    def leaveEvent(self, event):
        if self._hover_return:
            self._hover_return = False
            self.update()

    def wheelEvent(self, event):
        if self._sbar.isVisible():
            delta = event.angleDelta().y()
            self._sbar.setValue(self._sbar.value() - delta)

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
    if not data:
        from dokibox.dialogbox import _history
        records = list(_history)
    elif isinstance(data, str):
        records = [("", data)]
    else:
        records = data
    return _HistoryBox.run(records, pinned=pinned)

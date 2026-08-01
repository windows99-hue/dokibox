# -*- coding: utf-8 -*-
"""dokibox.historybox -- history display window , style like DDLC Menu"""
import math
import sys
import ctypes
from PySide6.QtCore import Qt, QEvent, QEventLoop, QPointF, QRectF, QTimer, QElapsedTimer
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QFontMetrics, QPen, QPixmap,
)
from PySide6.QtWidgets import QWidget, QScrollBar
from dokibox._base import _get_app, _get_dpi_scale


def _render_stroked_label(text, font, fill_color, stroke_color, stroke_w, dpr):
    fm = QFontMetrics(font)
    padding = stroke_w + 2
    logical_w = max(fm.horizontalAdvance(text) + padding * 2, 1)
    logical_h = max(fm.height() + padding * 2, 1)

    pixmap = QPixmap(
        max(int(math.ceil(logical_w * dpr)), 1),
        max(int(math.ceil(logical_h * dpr)), 1),
    )
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.transparent)

    path = QPainterPath()
    path.addText(padding, padding + fm.ascent(), font, text)
    pen = QPen(QColor(stroke_color))
    pen.setWidthF(stroke_w * 2)
    pen.setJoinStyle(Qt.RoundJoin)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawPath(path)
    painter.fillPath(path, QColor(fill_color))
    painter.end()
    return pixmap, padding, fm


class _StrokedTextArea(QWidget):

    def __init__(self, parent, records, font, bold_font, fill_color, stroke_color, stroke_w):
        super().__init__(parent)
        self._records = records
        self._font = font
        self._bold_font = bold_font
        self._fill = fill_color
        self._stroke = stroke_color
        self._stroke_w = stroke_w
        self._font_metrics = QFontMetrics(font)
        self._bold_metrics = QFontMetrics(bold_font)
        self._stroke_color = QColor(stroke_color)
        self._fill_color = QColor(fill_color)
        self._stroke_offsets = tuple(dict.fromkeys(
            (
                int(stroke_w * math.cos(2 * math.pi * step / 24)),
                int(stroke_w * math.sin(2 * math.pi * step / 24)),
            )
            for step in range(24)
        ))
        self._lines = []
        self._line_h = 0
        self._scroll = 0
        self.setMouseTracking(True)

    def set_geometry(self, x, y, w, h):
        self.setGeometry(x, y, w, h)
        self._wrap_lines(w - 8)

    def _wrap_lines(self, area_w):
        fm = self._font_metrics
        bm = self._bold_metrics
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
                fm = self._bold_metrics if is_bold else self._font_metrics
                baseline = int(y + fm.ascent() - fm.height() // 2)
                painter.setFont(font)
                painter.setPen(self._stroke_color)
                for dx, dy in self._stroke_offsets:
                    painter.drawText(int(x) + dx, baseline + dy, text)
                painter.setPen(self._fill_color)
                painter.drawText(int(x), baseline, text)
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
        self._timer_resolution_active = False

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

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
        self._setup_background_cache()
        self._setup_label_cache()

        self._offset_x = 0.0
        self._offset_y = 0.0
        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)

        self._setup_text()

    def _new_cache_pixmap(self, logical_w, logical_h):
        dpr = self.devicePixelRatioF()
        pixmap = QPixmap(
            max(int(round(logical_w * dpr)), 1),
            max(int(round(logical_h * dpr)), 1),
        )
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(Qt.transparent)
        return pixmap

    def _setup_background_cache(self):
        dr, step_x, row_h = self._grid_params()
        tile_w = max(step_x, 1)
        tile_h = max(row_h * 2, 1)
        self._dot_tile = self._new_cache_pixmap(tile_w, tile_h)
        self._dot_tile_w = self._dot_tile.width() / self._dot_tile.devicePixelRatio()
        self._dot_tile_h = self._dot_tile.height() / self._dot_tile.devicePixelRatio()

        tile_painter = QPainter(self._dot_tile)
        tile_painter.setRenderHint(QPainter.Antialiasing)
        tile_painter.setPen(Qt.NoPen)
        tile_painter.setBrush(QColor(DOT_COLOR))
        tile_painter.drawEllipse(QPointF(dr, dr), dr, dr)
        tile_painter.drawEllipse(
            QPointF(dr + step_x // 2, dr + row_h), dr, dr)
        tile_painter.end()

        self._curtain_cache = self._new_cache_pixmap(self.width(), self.height())
        curtain_painter = QPainter(self._curtain_cache)
        curtain_painter.setRenderHint(QPainter.Antialiasing)
        curtain_painter.setPen(Qt.NoPen)
        self._draw_left_curtain(curtain_painter, self.width(), self.height())
        curtain_painter.end()

    def _setup_label_cache(self):
        s = 1.0 / _get_dpi_scale()
        title_fs = max(12, int(18 * s))
        self._title_font = QFont("Microsoft YaHei", title_fs, QFont.Bold)
        dpr = self.devicePixelRatioF()

        self._history_label, self._label_padding, self._title_fm = _render_stroked_label(
            "历史", self._title_font, "#ffffff", "#BD539D", 3, dpr)
        self._return_label, _, _ = _render_stroked_label(
            "返回游戏", self._title_font, "#ffffff", "#BD539D", 3, dpr)
        self._return_label_hover, _, _ = _render_stroked_label(
            "返回游戏", self._title_font, "#ffd0e8", "#BD539D", 3, dpr)

        rx = int(self.width() / 20)
        ry = int(self.height() - self.height() / 10)
        rw = self._title_fm.horizontalAdvance("返回游戏")
        th = self._title_fm.height()
        self._return_rect = (rx, ry - th // 2, rw + 12, th)

    def _setup_text(self):
        w = self.width()
        h = self.height()

        tx = int(w * 0.28)
        ty = int(h * 0.14)
        tw = int(w - w * 0.28 - TEXT_PAD_RIGHT)
        th = int(h * 0.72)

        s = 1.0 / _get_dpi_scale()
        fs = max(12, int(TEXT_FONT_SIZE * s))
        text_font = QFont("Microsoft YaHei", fs)
        bold_font = QFont("Microsoft YaHei", fs, QFont.Bold)
        self._text = _StrokedTextArea(self, self._records, text_font, bold_font,
                                      "#ffffff", "#000000", 2)

        self._setup_scrollbar(tx, ty, tw, th)

    def _setup_scrollbar(self, tx, ty, tw, th):
        s = 1.0 / _get_dpi_scale()
        sb_w = max(8, int(SBAR_W * s))
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

    def _begin_timer_resolution(self):
        if sys.platform != "win32" or self._timer_resolution_active:
            return
        try:
            if ctypes.windll.winmm.timeBeginPeriod(1) == 0:
                self._timer_resolution_active = True
        except Exception:
            pass

    def _end_timer_resolution(self):
        if not self._timer_resolution_active:
            return
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass
        finally:
            self._timer_resolution_active = False

    def _start_animation(self):
        self._begin_timer_resolution()
        self._elapsed.restart()
        if not self._timer.isActive():
            self._timer.start(16)

    def _stop_animation(self):
        self._timer.stop()
        self._end_timer_resolution()

    def _tick(self):
        dt = self._elapsed.restart() / 1000.0
        self._offset_x = (self._offset_x + DOT_SPEED_X * dt) % self._dot_tile_w
        self._offset_y = (self._offset_y + DOT_SPEED_Y * dt) % self._dot_tile_h
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

        w = self.width()
        h = self.height()
        painter.drawTiledPixmap(
            QRectF(self.rect()), self._dot_tile,
            QPointF(self._offset_x, self._offset_y),
        )
        painter.drawPixmap(0, 0, self._curtain_cache)

        hx = int(w / 20)
        hy = int(h / 15)
        label_top = hy - self._title_fm.height() // 2 - self._label_padding
        painter.drawPixmap(hx - self._label_padding, label_top, self._history_label)

        rx = int(w / 20)
        ry = int(h - h / 10)
        return_label = self._return_label_hover if self._hover_return else self._return_label
        return_top = ry - self._title_fm.height() // 2 - self._label_padding
        painter.drawPixmap(rx - self._label_padding, return_top, return_label)

        painter.end()

    def showEvent(self, event):
        super().showEvent(event)
        self._start_animation()

    def hideEvent(self, event):
        self._stop_animation()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_animation()
        super().closeEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self._stop_animation()
            elif self.isVisible():
                self._start_animation()
        super().changeEvent(event)

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
        self._stop_animation()
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


def _normalize_history_records(data):
    items = [data] if isinstance(data, dict) else data
    records = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name", "")
            msg = item.get("msg", "")
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            name, msg = item
        else:
            raise TypeError(
                "history records must be dictionaries or two-item lists/tuples")
        records.append((
            "" if name is None else str(name),
            "" if msg is None else str(msg),
        ))
    return records


def historybox(data="", pinned=True):
    """DDLC-menu-style history viewer showing past dialog records.

    Args:
        data:   history records. Can be:
                - empty str (default): reads from internal dialogbox history.
                - str: treated as a single message with no speaker name.
                - list of (name, msg) tuples or dicts with "name"/"msg" keys.
        pinned: keep the window always on top (default True).

    Returns:
        None

    Usage:
        import dokibox
        dokibox.historybox()                       # show all dialog history
        dokibox.historybox("Hello world!")          # single plain message
        dokibox.historybox([("Alice", "Hi"), ("Bob", "Hey")])  # custom records
    """
    if not data:
        from dokibox.dialogbox import _history
        records = list(_history)
    elif isinstance(data, str):
        records = [("", data)]
    else:
        records = _normalize_history_records(data)
    return _HistoryBox.run(records, pinned=pinned)

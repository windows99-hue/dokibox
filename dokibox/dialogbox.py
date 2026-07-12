# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC-style bottom dialog (rounded corners, gradient opacity, white stroke)"""
import math
import sys
import ctypes
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QEventLoop, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QLinearGradient,
)
from PySide6.QtWidgets import QWidget, QApplication
from dokibox._base import _get_app, _get_dpi_scale


BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#FFDEEF"
FADE_TO = "#FFFFFF"
CORNER_RADIUS = 18
INSET = 3

DOT_RADIUS = 13
DOT_GAP_X = 35
DOT_GAP_Y = 6
DOT_COLOR = "#FB94C1"

DWMWA_BORDER_COLOR = 34
# 新增：窗口阴影透明度属性ID
DWMWA_SHADOW_OPACITY = 33


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _blend(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 * t + r2 * (1 - t))
    g = int(g1 * t + g2 * (1 - t))
    b = int(b1 * t + b2 * (1 - t))
    return QColor(r, g, b)

class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cxTopHeight", ctypes.c_int),
        ("cxBottomHeight", ctypes.c_int),
    ]

def remove_dwm_frame(hwnd):
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

# 新增函数：关闭指定窗口阴影
def remove_window_shadow(hwnd):
    zero_val = ctypes.c_uint(0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SHADOW_OPACITY,
        ctypes.byref(zero_val),
        ctypes.sizeof(zero_val)
    )

_box = None


class _DialogBox(QWidget):

    dismissed = Signal()

    def __init__(self, msg, w, h, name=None, typewriter=True, chardelay=50,
                 bold=False, pinned=True, fdst=False, overflow_mode="wrap",
                 font_family=None, font_size=None, transparent=True, glare=True):
        global _box

        if overflow_mode not in ("wrap", "overflow", "hide"):
            raise ValueError(
                f"overflow_mode must be 'wrap', 'overflow', or 'hide', got {overflow_mode!r}"
            )
        _get_app()
        super().__init__(None)

        self._overflow_mode = overflow_mode
        self.w = w
        self.h = h
        self._name = name
        self._typewriter = typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._fdst = fdst
        self._pinned = pinned
        self._typing = False
        self._typing_done = False
        self._after_timer = None
        self._transparent = transparent
        self._glare = glare

        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size or 20

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        self._body_fs = max(12, int(self._font_size * s))
        self._name_fs = max(12, int(self._font_size * s))
        self._line_h = int(44 * s)
        self._pad_top = int(40 * s)
        self._pad_x = int(40 * s)
        self._name_pad_val = int(28 * s)
        self._dot_radius = int(DOT_RADIUS * s)
        self._dot_gap_x = int(DOT_GAP_X * s)
        self._dot_gap_y = int(DOT_GAP_Y * s)
        self._corner_radius = max(8, int(CORNER_RADIUS * s))
        self._inset = max(2, int(INSET * s))
        sw_raw = 4 if bold else 1
        self._stroke_w = max(1, int(sw_raw * s))
        self._triangle_s = int(16 * s)
        self.r = self._corner_radius
        self.r = self._corner_radius

        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_pad = self._name_pad_val
        name_h = fm.lineSpacing() + name_pad
        if name:
            tw = fm.horizontalAdvance(name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

        cv_h = h + name_h + int(30 * s)
        cv_h += self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = w
        if self._overflow_mode == "overflow" and msg:
            f_body = QFont(self._font_family, self._body_fs, QFont.Bold)
            fm = QFontMetrics(f_body)
            max_line_w = max(fm.horizontalAdvance(line) for line in msg.split('\n'))
            needed_w = int(max_line_w + int(80 * s))
            if needed_w > canvas_w:
                canvas_w = needed_w
        canvas_w += self._inset * 2
        self._canvas_w = canvas_w
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        if self._overflow_mode == "overflow":
            x = (sw - w) // 2 - self._dialog_left
        dialog_screen_y = sh - h - 60
        win_y = dialog_screen_y - self._dialog_top

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        self._init_typewriter_state(msg)
        self.show()

        _box = self

        QApplication.processEvents()
        self.raise_()
        self.activateWindow()

    def _update_content(self, msg, typewriter, chardelay, bold, overflow_mode, name=None,
                        font_family=None, font_size=None, transparent=None, glare=None):
        if self._after_timer:
            try:
                self._after_timer.stop()
            except Exception:
                pass
            self._after_timer.deleteLater()
            self._after_timer = None

        self._overflow_mode = overflow_mode
        self._typewriter = typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._typing = False
        self._typing_done = False
        if transparent is not None:
            self._transparent = transparent
        if glare is not None:
            self._glare = glare

        self._name = name

        if font_family is not None:
            self._font_family = font_family
        else:
            self._font_family = "Microsoft YaHei"
        if font_size is not None:
            self._font_size = font_size
        else:
            self._font_size = 20
        self._body_fs = self._font_size
        self._name_fs = self._font_size

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        name_pad = int(28 * s)

        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_h = fm.lineSpacing() + name_pad
        if self._name:
            tw = fm.horizontalAdvance(self._name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

        cv_h = self.h + name_h + int(30 * s)
        cv_h += self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = self.w
        if self._overflow_mode == "overflow" and msg:
            f_body = QFont(self._font_family, self._body_fs, QFont.Bold)
            fm = QFontMetrics(f_body)
            max_line_w = max(fm.horizontalAdvance(line) for line in msg.split('\n'))
            needed_w = int(max_line_w + int(80 * s))
            if needed_w > canvas_w:
                canvas_w = needed_w
        canvas_w += self._inset * 2
        self._canvas_w = canvas_w
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - self.w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        if self._overflow_mode == "overflow":
            x = (sw - self.w) // 2 - self._dialog_left
        dialog_screen_y = sh - self.h - 60
        win_y = dialog_screen_y - self._dialog_top

        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        self._init_typewriter_state(msg)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            remove_dwm_frame(hwnd)
            remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def _init_typewriter_state(self, msg):
        self._full_msg = msg
        if self._typewriter and msg:
            self._typing = True
            self._typing_done = False
            self._cur_line = 0
            self._cur_char = 0
            font = QFont(self._font_family, self._body_fs, QFont.Bold)
            lines = self._process_lines(msg, font, self._text_area_width())
            self._typewriter_lines = lines
            self._typewriter_font = font
            self._typewriter_positions = self._layout_text_positions(lines)
            self._start_typewriter_timer()
        else:
            self._typing = False
            self._typing_done = True

    def _start_typewriter_timer(self):
        self._after_timer = QTimer(self)
        self._after_timer.setSingleShot(True)
        self._after_timer.timeout.connect(self._type_tick)
        self._after_timer.start(self._chardelay)

    def _type_tick(self):
        if self._cur_line >= len(self._typewriter_lines):
            self._typing = False
            self._typing_done = True
            self._after_timer = None
            return

        full_text = self._typewriter_lines[self._cur_line]
        self._cur_char += 1
        if self._cur_char > len(full_text):
            self._cur_line += 1
            self._cur_char = 0
            self._type_tick()
            return

        self.update()
        self._after_timer = QTimer(self)
        self._after_timer.setSingleShot(True)
        self._after_timer.timeout.connect(self._type_tick)
        self._after_timer.start(self._chardelay)

    def _finish_typewriter(self):
        if self._after_timer:
            try:
                self._after_timer.stop()
            except Exception:
                pass
            self._after_timer.deleteLater()
            self._after_timer = None
        self._typing = False
        self._typing_done = True
        self._cur_line = len(self._typewriter_lines)
        self._cur_char = 0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        r = self.r
        w = self.w
        top = self._dialog_top
        h = self.h
        dl = self._dialog_left

        if self._name:
            self._draw_name_tag_bg(painter)
            self._draw_name_text(painter, dl)

        dialog_rect = QRectF(dl, top, w, h)
        path = QPainterPath()
        path.addRoundedRect(dialog_rect, r, r)
        painter.setClipPath(path)

        self._draw_fill(painter, dl, top, w, h)
        self._draw_dots(painter, dl, top, w, h)
        if self._glare:
            self._draw_glare(painter, dl, top, w, h)
        painter.setClipping(False)

        self._draw_outline(painter, dl, top, w, h, r)
        self._draw_text(painter, dl, top)
        self._draw_triangle(painter, dl, top, w, h)

        painter.end()

    def _draw_name_tag_bg(self, painter):
        tx = self.r + 10 + self._dialog_left
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        tr = self._tag_r

        tag_path = QPainterPath()
        tag_path.addRoundedRect(QRectF(tx, ty, tw, th), tr, tr)
        painter.fillPath(tag_path, QColor("#ffffff"))

        grad_top = ty + th * 0.75
        grad_h = th * 0.25
        steps = 12
        for i in range(steps):
            t_bot = i / max(steps - 1, 1)
            t_top = min((i + 1) / max(steps - 1, 1), 1.0)
            opacity = (t_bot + t_top) / 2
            color = _blend("#000000", "#ffffff", opacity)

            y1 = int(grad_top + grad_h * t_bot)
            y2 = int(grad_top + grad_h * t_top)
            region = QPainterPath()
            region.addRect(QRectF(tx, y1, tw, y2 - y1))
            clipped = tag_path.intersected(region)
            painter.fillPath(clipped, color)

    def _draw_name_text(self, painter, dl):
        tx = self.r + 10 + dl
        ty = self._tag_top - 5
        tw = self._tag_w
        th = self._tag_h
        cx = tx + tw // 2
        cy = ty + th // 2
        font = QFont(self._font_family, self._name_fs, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw_text = fm.horizontalAdvance(self._name)
        text_x = int(cx - tw_text // 2)
        text_y = int(cy + fm.ascent() - fm.height() // 2)

        dpi = _get_dpi_scale()
        name_stroke = max(1, int(2 / dpi))
        for step in range(48):
            angle = 2 * math.pi * step / 48
            dx = int(math.cos(angle) * name_stroke)
            dy = int(math.sin(angle) * name_stroke)
            painter.setPen(QColor("#BD539D"))
            painter.drawText(text_x + dx, text_y + dy, self._name)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(text_x, text_y, self._name)

    def _draw_fill(self, painter, dl, top, w, h):
        if self._transparent:
            gradient = QLinearGradient(0, top + h * 0.333, 0, top + h)
            c_top = QColor(BODY_COLOR)
            c_bot = QColor(BODY_COLOR)
            c_bot.setAlpha(int(255 * 0.65))
            gradient.setColorAt(0, c_top)
            gradient.setColorAt(1, c_bot)
        else:
            gradient = QLinearGradient(0, top, 0, top + h)
            gradient.setColorAt(0, _blend(BODY_COLOR, FADE_TO, 1.0))
            gradient.setColorAt(1, _blend(BODY_COLOR, FADE_TO, 0.5))
        painter.setBrush(gradient)
        painter.drawRect(QRectF(dl, top, w, h))

    def _draw_glare(self, painter, dl, top, w, h):
        rx = w / 2 + 30
        ry = h * 0.40
        cx = dl + w / 2
        cy = top + h

        gradient = QLinearGradient(0, cy - ry, 0, cy)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 100))
        gradient.setColorAt(0.4, QColor(255, 255, 255, 60))
        gradient.setColorAt(0.7, QColor(255, 255, 255, 15))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        path = QPainterPath()
        path.moveTo(dl, cy)
        path.arcTo(QRectF(cx - rx, cy - ry, rx * 2, ry * 2), 180, -180)

        painter.setBrush(gradient)
        painter.drawPath(path)

    def _draw_dots(self, painter, dl, top, w, h):
        painter.save()
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)

        dr = self._dot_radius
        gap_x = self._dot_gap_x
        gap_y = self._dot_gap_y
        step_x = int(dr * 2 + gap_x)
        row_h = int(dr * 2 + gap_y)

        row = 0
        y = top + dr
        while y < top + h + row_h:
            t = max(0, min(1, (y - top) / h))

            offset_x = (step_x // 2) if row % 2 == 1 else 0
            x = dl + max(0, offset_x)
            while x < dl + w + step_x:
                if self._transparent:
                    color = QColor(DOT_COLOR)
                else:
                    opacity = 1.0 - 0.5 * t
                    color = _blend(DOT_COLOR, FADE_TO, opacity)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), dr, dr)
                x += step_x
            y += row_h
            row += 1

        painter.restore()

    def _draw_outline(self, painter, dl, top, w, h, r):
        color = QColor(BORDER_COLOR)
        pen = QPen(color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(dl, top, w, h), r, r)

    def _draw_triangle(self, painter, dl, top, w, h):
        s = self._triangle_s
        tri_h = s * math.sqrt(3) / 2
        tip_x = dl + w - self._pad_x
        tip_y = top + h - self._pad_top
        path = QPainterPath()
        path.moveTo(tip_x, tip_y)
        path.lineTo(tip_x - tri_h, tip_y - s / 2)
        path.lineTo(tip_x - tri_h, tip_y + s / 2)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, QColor("#ffffff"))

    def _text_area_width(self):
        return self.w - self._pad_x * 2

    def _wrap_line(self, text, font, max_w):
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= max_w:
            return [text]
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if fm.horizontalAdvance(test) <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines

    def _truncate_line(self, text, font, max_w):
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= max_w:
            return text
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if fm.horizontalAdvance(text[:mid]) <= max_w:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo]

    def _process_lines(self, text, font, max_w):
        if self._overflow_mode == "overflow":
            return text.split('\n')
        raw_lines = text.split('\n')
        if self._overflow_mode == "wrap":
            result = []
            for line in raw_lines:
                result.extend(self._wrap_line(line, font, max_w))
            return result
        if self._overflow_mode == "hide":
            return [self._truncate_line(line, font, max_w) for line in raw_lines]
        return raw_lines

    def _layout_text_positions(self, lines):
        line_h = self._line_h
        pad_top = self._pad_top
        pad_x = self._pad_x
        top = self._dialog_top
        pos = []
        for j, line in enumerate(lines):
            y = top + pad_top + line_h // 2 + j * line_h
            pos.append((pad_x, y, line))
        return pos

    def _draw_text(self, painter, dl, top):
        msg = self._full_msg
        if not msg:
            return
        font = QFont(self._font_family, self._body_fs, QFont.Bold)

        if self._typewriter and self._typing:
            positions = self._typewriter_positions
            for j, (px, py, full_text) in enumerate(positions):
                if j < self._cur_line:
                    shown = full_text
                elif j == self._cur_line:
                    shown = full_text[:self._cur_char]
                else:
                    shown = ""
                if shown:
                    self._draw_stroked_text_left(painter, dl + px, py, shown, font)
        elif not self._typing and self._typing_done:
            lines = self._process_lines(msg, font, self._text_area_width())
            positions = self._layout_text_positions(lines)
            for px, py, line in positions:
                self._draw_stroked_text_left(painter, dl + px, py, line, font)

    def _draw_stroked_text_left(self, painter, x, y, text, font):
        sw = 4 if self._bold else 1
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_y = int(y + fm.ascent() - fm.height() // 2)
        for step in range(48):
            angle = 2 * math.pi * step / 24
            dx = int(math.cos(angle) * sw)
            dy = int(math.sin(angle) * sw)
            painter.setPen(QColor("#000000"))
            painter.drawText(int(x) + dx, text_y + dy, text)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(int(x), text_y, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done()

    def _on_click(self):
        if self._typewriter and self._typing:
            self._finish_typewriter()
        else:
            self._done()

    def _done(self):
        self.dismissed.emit()


def _destroy_box():
    global _box
    if _box is not None:
        if _box._after_timer:
            try:
                _box._after_timer.stop()
            except Exception:
                pass
            _box._after_timer.deleteLater()
            _box._after_timer = None
        try:
            _box.hide()
            _box.deleteLater()
        except Exception:
            pass
        _box = None


def dialogbox(msg: str = "", w: Optional[int] = None, h: Optional[int] = None,
              name: Optional[str] = None, typewriter: bool = True,
              chardelay: int = 50, bold: bool = False, pinned: bool = True,
              fdst: bool = False, overflow_mode: str = "wrap",
              font_family: str = None, font_size: int = None,
              transparent: bool = True, glare: bool = True) -> None:
    """DDLC-style bottom rounded dialog. Click anywhere or press Esc to dismiss.

    Args:
        msg:           body text to display (supports \\n for multiple lines).
        w:             width in pixels. Defaults to 70% of screen width if None.
        h:             height in pixels. Defaults to 220 (DPI-scaled) if None.
        name:          character name shown in a white rounded tag above the dialog.
        typewriter:    animate text character-by-character (default True).
        chardelay:     delay in ms per character in typewriter mode (default 50).
        bold:          use a thicker black stroke outline for body text (default False).
        pinned:        keep the window always on top of other windows (default True).
        fdst:          If True, destroys the window when dismissed. Use this for the final line of a dialogue scene or story branch to ensure the window closes completely. (default: False)
        overflow_mode: how to handle text exceeding the dialog width:
                       'wrap'    – wrap text to the next line (default).
                       'overflow' – expand the window so text can render past the dialog boundary.
                       'hide'    – clip text at the boundary.
        transparent:   apply alpha gradient from top to bottom, making the body see-through (default True).
        glare:         draw a white semicircular highlight at the bottom of the dialog (default True).

    Usage:
        dokibox.dialogbox("Hello!")
        dokibox.dialogbox("Hello!", name="Sayori", bold=True)
    """
    global _box

    _get_app()
    sw = QApplication.primaryScreen().size().width()
    if w is None:
        w = min(int(sw * 0.7), 1200)
    if h is None:
        h = int(220 / _get_dpi_scale())

    if _box is not None:
        try:
            if _box.w == w and _box.h == h:
                _box._update_content(msg, typewriter, chardelay, bold, overflow_mode, name,
                                     font_family=font_family, font_size=font_size,
                                     transparent=transparent, glare=glare)
            else:
                _destroy_box()
        except Exception:
            _destroy_box()

    if _box is None:
        _box = _DialogBox(msg, w, h, name, typewriter, chardelay, bold, pinned=pinned,
                          fdst=fdst, overflow_mode=overflow_mode,
                          font_family=font_family, font_size=font_size,
                          transparent=transparent, glare=glare)

    _dialogbox_loop = QEventLoop()
    _box.dismissed.connect(_dialogbox_loop.quit, Qt.SingleShotConnection)
    _dialogbox_loop.exec()

    if fdst:
        _destroy_box()
# -*- coding: utf-8 -*-
"""dokibox.enterbox -- DDLC-style input dialog with text entry"""
import math
from typing import Optional, Union
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import QToolTip, QLineEdit
from dokibox._base import _DokiBase, _get_app, _hex_to_rgb, BODY_COLOR
from dokibox._widgets import text_wrap, draw_stroked_button

MSG_COLOR = "#000000"
BTN_STROKE_COLOR = "#BD539D"
BTN_FILL_COLOR = "#ffffff"
BTN_HOVER_COLOR = "#ffd0e8"
INPUT_BORDER = "#FFBBE3"
INPUT_BG = "#FEE6F4"
CURSOR_COLOR = "#CF80B5"
INPUT_STROKE = "#000000"
INPUT_FILL = "#ffffff"
INPUT_STROKE_W = 2

PAD_X = 53
PAD_TOP = 55
PAD_BOT = 50
BTN_STROKE_W = 6
MSG_FONT_SIZE = 22
BTN_FONT_SIZE = 26
INPUT_HEIGHT = 50
INPUT_GAP = 25
INPUT_BTN_GAP = 28


class _CustomLineEdit(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cursor_visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_cursor)
        self._blink_timer.start(530)
        self._base_x = 0
        self.textChanged.connect(self.update)
        self.cursorPositionChanged.connect(self.update)
        self.selectionChanged.connect(self.update)

    def _toggle_cursor(self):
        if self.hasFocus():
            self._cursor_visible = not self._cursor_visible
            self.update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._cursor_visible = True
        if not self._blink_timer.isActive():
            self._blink_timer.start()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._blink_timer.stop()
        self._cursor_visible = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_x = event.pos().x() - self._base_x
            fm = QFontMetrics(self.font())
            text = self.text()
            accumulated = 0
            for i, ch in enumerate(text):
                char_w = fm.horizontalAdvance(ch)
                if click_x < accumulated + char_w / 2:
                    self.setCursorPosition(i)
                    return
                accumulated += char_w
            self.setCursorPosition(len(text))
            return
        super().mousePressEvent(event)

    def _draw_stroked(self, painter, x, y, text):
        _draw_text_stroked_local(painter, int(x), y, text, INPUT_STROKE, INPUT_FILL, INPUT_STROKE_W)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        fm = QFontMetrics(self.font())
        text = self.text()
        body_h = fm.ascent() + fm.descent()
        down_shift = 2
        text_y = rect.top() + (rect.height() - body_h) // 2 + fm.ascent() + down_shift

        p.fillRect(rect, QColor(INPUT_BG))

        cursor_pos = self.cursorPosition()
        text_width = fm.horizontalAdvance(text)
        visible_width = rect.width() - 16
        cursor_rel_x = fm.horizontalAdvance(text[:cursor_pos])

        if text_width <= visible_width:
            self._base_x = 8 + (visible_width - text_width) / 2
        else:
            scroll = max(0, min(cursor_rel_x - visible_width, text_width - visible_width))
            self._base_x = 8 - scroll

        if self.hasSelectedText():
            sel_start = self.selectionStart()
            sel_end = sel_start + len(self.selectedText())
            before = text[:sel_start]
            sel_text = text[sel_start:sel_end]
            after = text[sel_end:]

            bw = fm.horizontalAdvance(before)
            sw = fm.horizontalAdvance(sel_text)

            if before:
                self._draw_stroked(p, int(self._base_x), text_y, before)
            sel_y = rect.top() + (rect.height() - body_h) // 2
            p.fillRect(int(self._base_x + bw), int(sel_y), int(sw), int(body_h), QColor(BTN_STROKE_COLOR))
            self._draw_stroked(p, int(self._base_x + bw), text_y, sel_text)
            if after:
                self._draw_stroked(p, int(self._base_x + bw + sw), text_y, after)
        else:
            self._draw_stroked(p, int(self._base_x), text_y, text)

        if self.hasFocus() and self._cursor_visible:
            cursor_x = self._base_x + cursor_rel_x
            cursor_h = body_h + 1
            cursor_y = rect.top() + (rect.height() - cursor_h) // 2
            p.setPen(QPen(QColor(CURSOR_COLOR), 2))
            p.drawLine(int(cursor_x), int(cursor_y), int(cursor_x), int(cursor_y + cursor_h))

        p.end()


class _EnterDialog(_DokiBase):

    def __init__(self, msg, default="", tooltip=None, pinned=True,
                 font_family=None, font_size=None, max_length=None):
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size
        if isinstance(tooltip, str):
            self._tooltip = tooltip or None
        else:
            # Keep compatibility with the previous tooltip=True API.
            self._tooltip = "OK" if tooltip else None
        self._btn_ok_hover = False
        self._btn_ok_rect = None
        self._tooltip_shown = False
        self._default = default
        self._max_length = max_length
        super().__init__(msg, pinned=pinned)
        self._setup_input()

    def _setup_input(self):
        input_w = self.w - self._pad_x * 2
        self._input = _CustomLineEdit(self)
        self._input.setText(self._default)
        self._input.setFont(self._msg_font)
        self._input.setGeometry(
            int(self._pad_x), int(self._input_y), int(input_w), int(self._input_h)
        )
        self._input.setStyleSheet("border: none; padding: 0px;")
        if self._max_length is not None:
            self._input.setMaxLength(self._max_length)
        self._input.setFocus()
        self._input.returnPressed.connect(self._on_submit)

    def _on_submit(self):
        self._done(self._input.text())

    def _calc_size(self, msg):
        s = self._dpi_s
        pad_x = int(PAD_X * s)
        pad_top = int(PAD_TOP * s)
        input_gap = int(INPUT_GAP * s)
        input_btn_gap = int(INPUT_BTN_GAP * s)
        pad_bot = int(PAD_BOT * s)
        input_h = max(24, int(INPUT_HEIGHT * s))
        msg_fs = max(12, int((self._font_size or MSG_FONT_SIZE) * s))
        btn_fs = max(12, int((self._font_size or BTN_FONT_SIZE) * s))
        btn_stroke = max(3, int(BTN_STROKE_W * s))

        self._msg_font = QFont(self._font_family, msg_fs, QFont.Bold)
        self._btn_font = QFont(self._font_family, btn_fs, QFont.Bold)

        fm_msg = QFontMetrics(self._msg_font)
        fm_btn = QFontMetrics(self._btn_font)

        screen_w = self.screen().size().width()
        max_msg_w = max(screen_w - pad_x * 2, 200)

        wrapped = text_wrap(msg, self._msg_font, max_msg_w)
        self._wrapped_msg = wrapped
        self._msg_line_h = fm_msg.lineSpacing()
        self._msg_total_h = self._msg_line_h * len(wrapped)
        self._btn_line_h = fm_btn.lineSpacing()

        msg_w = max((fm_msg.horizontalAdvance(line) for line in wrapped), default=0)
        w = max(int(msg_w + pad_x * 2), 280)
        w = min(w, screen_w - 24)
        h = max(pad_top + self._msg_total_h + input_gap + input_h
                + input_btn_gap + self._btn_line_h + btn_stroke * 2 + pad_bot, 180)

        self._pad_x = pad_x
        self._pad_top = pad_top
        self._pad_bot = pad_bot
        self._input_h = input_h
        self._input_gap = input_gap
        self._input_btn_gap = input_btn_gap
        self._btn_stroke = btn_stroke
        self._input_w = w - pad_x * 2
        self._input_y = pad_top + self._msg_total_h + input_gap

        return w, h

    def _draw_content(self, painter):
        msg_y = self._pad_top + self._msg_total_h // 2
        self._draw_msg_lines(painter, msg_y)

        btn_y = (self._input_y + self._input_h + self._input_btn_gap
                 + self._btn_line_h // 2)
        self._btn_ok_rect = draw_stroked_button(
            painter, self.w // 2, btn_y, "OK", self._btn_font,
            self._btn_stroke, hover=self._btn_ok_hover)

    def _draw_msg_lines(self, painter, msg_y):
        painter.setFont(self._msg_font)
        fm = QFontMetrics(self._msg_font)
        painter.setPen(QColor(MSG_COLOR))
        for j, line in enumerate(self._wrapped_msg):
            tw = fm.horizontalAdvance(line)
            x = self.w // 2 - tw // 2
            y = (msg_y - self._msg_total_h // 2 + self._msg_line_h // 2
                 + j * self._msg_line_h + fm.ascent() - self._msg_line_h // 2)
            painter.drawText(int(x), int(y), line)

    def _check_hover(self, pos):
        if self._btn_ok_rect:
            rx, ry, rw, rh = self._btn_ok_rect
            return rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh
        return False

    def _on_click_local(self, event):
        if self._check_hover(event.position().toPoint()):
            self._done(self._input.text())

    def enterEvent(self, event):
        hover = self._check_hover(event.position().toPoint())
        if hover != self._btn_ok_hover:
            self._btn_ok_hover = hover
            self.update()

    def leaveEvent(self, event):
        self._btn_ok_hover = False
        self.update()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._btn_ok_rect:
            hover = self._check_hover(event.position().toPoint())
            if hover != self._btn_ok_hover:
                self._btn_ok_hover = hover
                self.update()
        if self._tooltip:
            if self._btn_ok_hover and not self._tooltip_shown:
                self._tooltip_shown = True
                QToolTip.showText(event.globalPosition().toPoint(), self._tooltip, self)
            elif not self._btn_ok_hover:
                self._tooltip_shown = False
                QToolTip.hideText()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done(None)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._done(self._input.text())


def enterbox(msg: str = "", default: str = "",
             tooltip: Optional[Union[str, bool]] = None, pinned: bool = True,
             font_family: str = None, font_size: int = None,
             max_length: int = None) -> Optional[str]:
    """DDLC-style input dialog. Returns the entered text or None if cancelled.

    Args:
        msg:        prompt text to display above the input field.
        default:    default value in the input field.
        tooltip:    custom tooltip text shown while hovering over the OK button.
                    True keeps the legacy behavior and displays "OK".
        pinned:     keep the window always on top of other windows.
        font_family: custom font family name.
        font_size:  base font size (automatically scaled by DPI).
        max_length: maximum number of characters allowed.

    Usage:
        import dokibox
        name = dokibox.enterbox("Enter your name:", max_length=10)
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _EnterDialog.run(msg, default=default, tooltip=tooltip,
                            pinned=pinned, font_family=font_family,
                            font_size=font_size, max_length=max_length)


def _draw_text_stroked_local(painter, text_x, text_y, text, stroke_color, fill_color, stroke_w):
    for step in range(24):
        angle = 2 * math.pi * step / 24
        dx = int(stroke_w * math.cos(angle))
        dy = int(stroke_w * math.sin(angle))
        painter.setPen(QColor(stroke_color))
        painter.drawText(int(text_x) + dx, text_y + dy, text)
    painter.setPen(QColor(fill_color))
    painter.drawText(int(text_x), text_y, text)

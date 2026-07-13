# -*- coding: utf-8 -*-
"""dokibox.msgbox -- DDLC-style message dialog (single OK button)"""
import math
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics
from PySide6.QtWidgets import QToolTip
from dokibox._base import _DokiBase, _get_app, _hex_to_rgb, BODY_COLOR

MSG_COLOR = "#000000"
BTN_STROKE_COLOR = "#BD539D"
BTN_FILL_COLOR = "#ffffff"
BTN_HOVER_COLOR = "#ffd0e8"

PAD_X = 80
PAD_TOP = 50
PAD_BTNS = 30
PAD_BOT = 70
BTN_STROKE_W = 6
MSG_FONT_SIZE = 22
BTN_FONT_SIZE = 26


class _MsgDialog(_DokiBase):

    def __init__(self, msg, title="", tooltip=None, pinned=True,
                 font_family=None, font_size=None):
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size
        self._tooltip = tooltip
        self._btn_ok_hover = False
        self._btn_ok_rect = None
        self._tooltip_shown = False
        super().__init__(msg, title, pinned=pinned)

    def _wrap_lines(self, text, font, max_w):
        raw_lines = text.split('\n')
        wrapped_lines = []
        for line in raw_lines:
            fm = QFontMetrics(font)
            if fm.horizontalAdvance(line) <= max_w:
                wrapped_lines.append(line)
            else:
                current = ""
                for ch in line:
                    test = current + ch
                    if fm.horizontalAdvance(test) <= max_w:
                        current = test
                    else:
                        if current:
                            wrapped_lines.append(current)
                        current = ch
                if current:
                    wrapped_lines.append(current)
        return wrapped_lines

    def _calc_size(self, msg):
        s = self._dpi_s
        pad_x = int(PAD_X * s)
        pad_top = int(PAD_TOP * s)
        pad_btns = int(PAD_BTNS * s)
        pad_bot = int(PAD_BOT * s)
        msg_fs = max(12, int((self._font_size or MSG_FONT_SIZE) * s))
        btn_fs = max(12, int((self._font_size or BTN_FONT_SIZE) * s))
        btn_stroke = max(3, int(BTN_STROKE_W * s))

        self._msg_font = QFont(self._font_family, msg_fs, QFont.Bold)
        self._btn_font = QFont(self._font_family, btn_fs, QFont.Bold)

        fm_msg = QFontMetrics(self._msg_font)
        fm_btn = QFontMetrics(self._btn_font)

        screen_w = self.screen().size().width()
        max_msg_w = max(screen_w - pad_x * 2, 200)

        wrapped = self._wrap_lines(msg, self._msg_font, max_msg_w)
        self._wrapped_msg = wrapped
        self._msg_line_h = fm_msg.lineSpacing()
        self._msg_total_h = self._msg_line_h * len(wrapped)
        self._btn_line_h = fm_btn.lineSpacing()

        msg_w = max(fm_msg.horizontalAdvance(line) for line in wrapped) if wrapped else 0
        w = max(int(msg_w + pad_x * 2), 250)
        w = min(w, screen_w - 24)
        h = max(pad_top + self._msg_total_h + pad_btns
                + self._btn_line_h + btn_stroke * 2 + pad_bot, 150)
        self._btn_stroke = btn_stroke
        self._pad_x = pad_x
        self._pad_top = pad_top
        self._pad_bot = pad_bot
        return w, h

    def _draw_content(self, painter):
        msg_y = self._pad_top + self._msg_total_h // 2
        self._draw_msg_lines(painter, msg_y)

        btn_y = self.h - self._pad_bot - self._btn_line_h // 2
        self._draw_button(painter, self.w // 2, btn_y, "OK", self._btn_ok_hover)

    def _draw_msg_lines(self, painter, msg_y):
        painter.setFont(self._msg_font)
        fm = QFontMetrics(self._msg_font)
        painter.setPen(QColor(MSG_COLOR))
        for j, line in enumerate(self._wrapped_msg):
            tw = fm.horizontalAdvance(line)
            x = self.w // 2 - tw // 2
            y = msg_y - self._msg_total_h // 2 + self._msg_line_h // 2 + j * self._msg_line_h + fm.ascent() - self._msg_line_h // 2
            painter.drawText(int(x), int(y), line)

    def _draw_button(self, painter, x, y, text, hover):
        sw = self._btn_stroke
        painter.setFont(self._btn_font)
        fm = QFontMetrics(self._btn_font)
        tw = fm.horizontalAdvance(text)
        text_x = int(x - tw // 2)
        text_y = int(y + fm.ascent() - fm.height() // 2)

        fill_color = BTN_HOVER_COLOR if hover else BTN_FILL_COLOR
        fill_rgb = _hex_to_rgb(fill_color)
        stroke_rgb = _hex_to_rgb(BTN_STROKE_COLOR)

        for step in range(48):
            angle = 2 * math.pi * step / 36
            dx = int(sw * math.cos(angle))
            dy = int(sw * math.sin(angle))
            painter.setPen(QColor(*stroke_rgb))
            painter.drawText(text_x + dx, text_y + dy, text)

        painter.setPen(QColor(*fill_rgb))
        painter.drawText(text_x, text_y, text)

        br = fm.boundingRect(text)
        self._btn_ok_rect = (
            text_x - 15, text_y + br.top() - 10,
            tw + 30, fm.height() + 20
        )

    def _on_click_local(self, event):
        if self._btn_ok_rect:
            rx, ry, rw, rh = self._btn_ok_rect
            pos = event.position().toPoint()
            if rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh:
                self._done(True)
                return

    def enterEvent(self, event):
        if self._btn_ok_rect:
            pos = event.position().toPoint()
            rx, ry, rw, rh = self._btn_ok_rect
            self._btn_ok_hover = rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh
            self.update()

    def leaveEvent(self, event):
        self._btn_ok_hover = False
        self.update()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if self._btn_ok_rect:
            pos = event.position().toPoint()
            rx, ry, rw, rh = self._btn_ok_rect
            hover = rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh
            if hover != self._btn_ok_hover:
                self._btn_ok_hover = hover
                self.update()
        if self._tooltip:
            if self._btn_ok_hover and not self._tooltip_shown:
                self._tooltip_shown = True
                gp = event.globalPosition().toPoint()
                QToolTip.showText(gp, self._tooltip, self)
            elif not self._btn_ok_hover:
                self._tooltip_shown = False
                QToolTip.hideText()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            self._done(True)


def msgbox(msg: str = "", title: str = "", tooltip: Optional[str] = None,
           pinned: bool = True, font_family: str = None,
           font_size: int = None) -> bool:
    """DDLC-style message dialog (OK button). Returns True.

    Args:
        msg:       message text to display (supports \\n for multiple lines).
        title:     window title (unused in borderless mode).
        tooltip:   tooltip text shown when hovering over the button. Disabled if None or empty.
        pinned:    keep the window always on top of other windows.

    Usage:
        import dokibox
        dokibox.msgbox("Operation completed!")
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _MsgDialog.run(msg, title, tooltip=tooltip, pinned=pinned,
                          font_family=font_family, font_size=font_size)

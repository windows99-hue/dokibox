# -*- coding: utf-8 -*-
"""dokibox.choicebox -- DDLC-style multi-choice dialog (floating windows per option)"""
from typing import Optional, List
from PySide6.QtCore import Qt, QPoint, QEventLoop
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QCursor
from PySide6.QtWidgets import QApplication, QWidget, QToolTip
from dokibox._base import _get_app, _hex_to_rgb, _get_dpi_scale
from dokibox._widgets import text_wrap

BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"
OPT_FILL_COLOR = "#000000"
OPT_HOVER_COLOR = "#999999"

BORDER_W = 12
OPT_FONT_SIZE = 24
OPT_PAD_X = 80
OPT_PAD_Y = 4
OPT_GAP = 40
UNIFIED_MIN_W = 600
MSG_FONT_SIZE = 20
MSG_PAD_Y = 16


class _Panel(QWidget):

    def __init__(self, index, text, pw, opt_fs, opt_pad_y, border_w,
                 on_select, tooltip=None, pinned=True, font_family=None):
        super().__init__(None)
        self.index = index
        self.text = text
        self._on_select = on_select
        self._tooltip = tooltip if isinstance(tooltip, str) and tooltip else None
        self._hover = False
        self._border_w = border_w

        self.pw = int(pw)
        self._opt_font = QFont(font_family or "Microsoft YaHei", opt_fs, QFont.Normal)
        fm = QFontMetrics(self._opt_font)
        self.ph = int(fm.lineSpacing() + opt_pad_y * 2 + border_w * 2)

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setFixedSize(self.pw, self.ph)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BODY_COLOR))
        self._draw_gradient_border(painter)
        self._draw_option(painter)
        painter.end()

    def _draw_gradient_border(self, painter):
        br, bg, bb = _hex_to_rgb(BORDER_COLOR)
        er, eg, eb = _hex_to_rgb(BODY_COLOR)
        bw = max(self._border_w, 6)
        for i in range(bw):
            t = (i / max(bw - 1, 1)) ** 3
            painter.setPen(QPen(QColor(
                int(br + (er - br) * t),
                int(bg + (eg - bg) * t),
                int(bb + (eb - bb) * t),
            ), 1))
            painter.drawRect(i, i, self.pw - i * 2, self.ph - i * 2)

    def _draw_option(self, painter):
        cx = self.pw // 2
        cy = self.ph // 2
        painter.setFont(self._opt_font)
        fm = QFontMetrics(self._opt_font)
        tw = fm.horizontalAdvance(self.text)
        color = OPT_HOVER_COLOR if self._hover else OPT_FILL_COLOR
        painter.setPen(QColor(color))
        text_x = cx - tw // 2
        text_y = cy + fm.ascent() - fm.height() // 2
        painter.drawText(int(text_x), int(text_y), self.text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_select(self.index)

    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mouseMoveEvent(self, event):
        if self._tooltip:
            QToolTip.showText(event.globalPosition().toPoint(), self._tooltip, self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_select(None)

    def set_position(self, x, y):
        self.move(x, y)


class _ChoiceManager:

    def __init__(self, msg, choices, title, tooltip=None, force=None, pinned=True,
                 font_family=None, font_size=None):
        _get_app()
        self.result = None
        self._tooltip = tooltip if isinstance(tooltip, str) and tooltip else None
        self._pinned = pinned
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size

        s = 1.0 / _get_dpi_scale()
        opt_fs = max(12, int((self._font_size or OPT_FONT_SIZE) * s))
        opt_pad_x = int(OPT_PAD_X * s)
        opt_pad_y = int(OPT_PAD_Y * s)
        border_w = int(BORDER_W * s)
        unified_min_w = int(UNIFIED_MIN_W * s)
        opt_gap = int(OPT_GAP * s)

        self._opt_font = QFont("Microsoft YaHei", opt_fs, QFont.Normal)
        fm = QFontMetrics(self._opt_font)
        opt_widths = [fm.horizontalAdvance(c) for c in choices]
        max_opt_w = max(opt_widths) if opt_widths else 0

        unified_w = max(int(max_opt_w + opt_pad_x * 2 + border_w * 2), unified_min_w)
        screen_w = QApplication.primaryScreen().size().width()
        unified_w = min(unified_w, screen_w - border_w * 2)
        self._unified_w = unified_w

        self._opt_gap = opt_gap
        self._border_w = border_w
        self._opt_pad_y = opt_pad_y

        self._panels = []
        for i, choice in enumerate(choices):
            panel = _Panel(i, choice, unified_w, opt_fs, opt_pad_y, border_w,
                          self._on_select, tooltip, pinned=pinned,
                          font_family=self._font_family)
            self._panels.append(panel)

        self._msg_win = None
        if msg.strip():
            self._create_msg_label(msg)

        self._layout(msg)

        for panel in self._panels:
            panel.show()

        if self._msg_win:
            self._msg_win.show()

        if force is not None and 0 <= force < len(choices):
            p = self._panels[force]
            QCursor.setPos(p.mapToGlobal(QPoint(p.width() // 2, p.height() // 2)))

    def _on_select(self, index):
        self.result = index
        for p in self._panels:
            p.close()
            p.deleteLater()
        if self._msg_win:
            self._msg_win.close()
            self._msg_win.deleteLater()

    def _create_msg_label(self, msg):
        s = 1.0 / _get_dpi_scale()
        msg_fs = max(12, int((self._font_size or MSG_FONT_SIZE) * s))
        msg_pad_y = int(MSG_PAD_Y * s)
        f = QFont(self._font_family, msg_fs, QFont.Normal)
        fm = QFontMetrics(f)
        max_lbl_w = max(self._unified_w - int(40 * s), 200)

        wrapped_lines = text_wrap(msg, f, max_lbl_w)

        line_h = fm.lineSpacing()
        total_h = line_h * len(wrapped_lines) + msg_pad_y * 2
        text_w_val = max((fm.horizontalAdvance(line) for line in wrapped_lines), default=0)

        self._msg_win = _MsgLabel(wrapped_lines, f, line_h, msg_pad_y,
                                   max(int(text_w_val + int(40 * s)), self._unified_w),
                                   int(total_h),
                                   self._pinned, self._on_select)
        self._msg_w = self._msg_win.width()
        self._msg_h = self._msg_win.height()

    def _layout(self, msg):
        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()

        if not self._panels:
            return

        gap = self._opt_gap
        total_h = sum(p.ph for p in self._panels) + gap * (len(self._panels) - 1)
        if self._msg_win:
            total_h += self._msg_h + gap

        start_y = (sh - total_h) // 2

        if self._msg_win:
            self._msg_win.move((sw - self._msg_w) // 2, start_y)
            start_y += self._msg_h + gap

        for panel in self._panels:
            panel.set_position((sw - panel.pw) // 2, start_y)
            start_y += panel.ph + gap


class _MsgLabel(QWidget):

    def __init__(self, lines, font, line_h, msg_pad_y, w, h, pinned, on_cancel):
        super().__init__(None)
        self._lines = lines
        self._font = font
        self._line_h = line_h
        self._msg_pad_y = msg_pad_y
        self._on_cancel = on_cancel
        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setFixedSize(w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(BODY_COLOR))
        painter.setPen(QPen(QColor(BORDER_COLOR), 4))
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)
        painter.setFont(self._font)
        painter.setPen(QColor("#000000"))
        fm = QFontMetrics(self._font)
        for j, line in enumerate(self._lines):
            y = self._msg_pad_y + self._line_h // 2 + j * self._line_h + fm.ascent() - self._line_h // 2
            tw = fm.horizontalAdvance(line)
            painter.drawText(int(self.width() // 2 - tw // 2), int(y), line)
        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_cancel(None)


def choicebox(msg: str = "", choices: Optional[List[str]] = None, title: str = "",
              tooltip: Optional[str] = None, force: Optional[int] = None,
              pinned: bool = True, font_family: str = None,
              font_size: int = None) -> Optional[str]:
    """DDLC-style multi-choice dialog. Each option is a floating window.
    Returns the selected text, or None if cancelled.

    Args:
        msg:      prompt text displayed above the options. No label shown if empty.
        choices:  list of option strings to display.
        title:    window title (unused in borderless mode).
        tooltip:  tooltip text shown when hovering over an option. Disabled if None or empty.
        force:    pre-select an option by index (0-based). The mouse warps to its center.
        pinned:   keep the windows always on top of other windows.

    Usage:
        import dokibox
        text = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    if not choices:
        return None
    mgr = _ChoiceManager(msg, choices, title, tooltip, force, pinned=pinned,
                         font_family=font_family, font_size=font_size)

    loop = QEventLoop()
    for p in mgr._panels:
        p.destroyed.connect(lambda obj=None, l=loop: l.quit())
    if mgr._msg_win:
        mgr._msg_win.destroyed.connect(lambda obj=None, l=loop: l.quit())
    loop.exec()

    return choices[mgr.result] if mgr.result is not None else None

# -*- coding: utf-8 -*-
"""dokibox.ynbox -- DDLC-style yes/no dialog"""
import locale
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QToolTip
from dokibox._base import _DokiBase, BODY_COLOR
from dokibox._widgets import text_wrap, draw_stroked_button

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
MIN_GAP = 40

_BTN_TEXTS = {
    'zh': ("是", "否"),
    'en': ("Yes", "No"),
    'ja': ("はい", "いいえ"),
    'ko': ("예", "아니요"),
    'ru': ("Да", "Нет"),
}

_LANG_MAP = {
    0x0804: 'zh', 0x0404: 'zh', 0x0C04: 'zh', 0x1004: 'zh',
    0x0411: 'ja',
    0x0412: 'ko',
    0x0419: 'ru',
}

_LANG_KEYWORDS = {
    'zh': ('zh', 'chinese'),
    'ja': ('ja', 'japanese'),
    'ko': ('ko', 'korean'),
    'ru': ('ru', 'russian'),
}


def get_system_locale():
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            lang_lower = lang.lower()
            if "en" in lang_lower or lang_lower in ("C", "POSIX"):
                return 'en'
            for code, keywords in _LANG_KEYWORDS.items():
                if any(kw in lang_lower for kw in keywords):
                    return code
    except Exception:
        pass
    try:
        import ctypes
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if lang_id in _LANG_MAP:
            return _LANG_MAP[lang_id]
    except Exception:
        pass
    return 'en'


class _YnDialog(_DokiBase):

    def __init__(self, msg, title="", tooltip=None, pinned=True, btn_texts=None,
                 font_family=None, font_size=None):
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size
        self._tooltip = tooltip if isinstance(tooltip, str) and tooltip else None
        if btn_texts is not None:
            self._yes_text, self._no_text = btn_texts
        else:
            self._yes_text, self._no_text = _BTN_TEXTS.get(get_system_locale(), _BTN_TEXTS['en'])
        self._btn_yes_hover = False
        self._btn_no_hover = False
        self._btn_yes_rect = None
        self._btn_no_rect = None
        self._tooltip_pos = None
        super().__init__(msg, title, pinned=pinned)

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

        fm_btn = QFontMetrics(self._btn_font)
        self._yes_w = fm_btn.horizontalAdvance(self._yes_text)
        self._no_w = fm_btn.horizontalAdvance(self._no_text)
        self._side_margin = int(self._yes_w * 1.5)

        min_btn_w = (self.BORDER_W * 2 + self._side_margin * 2
                     + int(self._yes_w) + int(self._no_w) + int(MIN_GAP * s))

        screen_w = self.screen().size().width()
        max_msg_w = max(screen_w - pad_x * 2, min_btn_w - pad_x * 2, 200)

        wrapped = text_wrap(msg, self._msg_font, max_msg_w)
        self._wrapped_msg = wrapped
        fm_msg = QFontMetrics(self._msg_font)
        self._msg_line_h = fm_msg.lineSpacing()
        self._msg_total_h = self._msg_line_h * len(wrapped)
        self._btn_line_h = fm_btn.lineSpacing()

        msg_w = max((fm_msg.horizontalAdvance(line) for line in wrapped), default=0)
        w = max(int(msg_w + pad_x * 2), int(min_btn_w), 300)
        w = min(w, screen_w - self.BORDER_W * 2)
        h = max(pad_top + self._msg_total_h + pad_btns
                + self._btn_line_h + btn_stroke * 2 + pad_bot, 180)
        self._btn_stroke = btn_stroke
        self._pad_x = pad_x
        self._pad_top = pad_top
        self._pad_bot = pad_bot
        return w, h

    def _draw_content(self, painter):
        msg_y = self._pad_top + self._msg_total_h // 2
        self._draw_msg_lines(painter, msg_y)

        btn_y = self.h - self._pad_bot - self._btn_line_h // 2
        btn_yes_x = int(self.BORDER_W + self._side_margin + self._yes_w / 2)
        btn_no_x = int(self.w - self.BORDER_W - self._side_margin - self._no_w / 2)

        self._btn_yes_rect = draw_stroked_button(
            painter, btn_yes_x, btn_y, self._yes_text, self._btn_font,
            self._btn_stroke, hover=self._btn_yes_hover)
        self._btn_no_rect = draw_stroked_button(
            painter, btn_no_x, btn_y, self._no_text, self._btn_font,
            self._btn_stroke, hover=self._btn_no_hover)

    def _draw_msg_lines(self, painter, msg_y):
        painter.setFont(self._msg_font)
        fm = QFontMetrics(self._msg_font)
        painter.setPen(QColor(MSG_COLOR))
        for j, line in enumerate(self._wrapped_msg):
            tw = fm.horizontalAdvance(line)
            x = self.w // 2 - tw // 2
            y = msg_y - self._msg_total_h // 2 + self._msg_line_h // 2 + j * self._msg_line_h + fm.ascent() - self._msg_line_h // 2
            painter.drawText(int(x), int(y), line)

    def _hit_button(self, pos):
        for rect, handler in [
            (self._btn_yes_rect, lambda: self._done(True)),
            (self._btn_no_rect, lambda: self._done(False)),
        ]:
            if rect:
                rx, ry, rw, rh = rect
                if rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh:
                    handler()
                    return True
        return False

    def _on_click_local(self, event):
        self._hit_button(event.position().toPoint())

    def _update_hover(self, pos):
        yes_hover = self._check_rect(pos, self._btn_yes_rect)
        no_hover = self._check_rect(pos, self._btn_no_rect)
        changed = (yes_hover != self._btn_yes_hover or no_hover != self._btn_no_hover)
        self._btn_yes_hover = yes_hover
        self._btn_no_hover = no_hover
        if changed:
            self.update()
        return yes_hover or no_hover

    @staticmethod
    def _check_rect(pos, rect):
        if rect:
            rx, ry, rw, rh = rect
            return rx <= pos.x() <= rx + rw and ry <= pos.y() <= ry + rh
        return False

    def enterEvent(self, event):
        self._update_hover(event.position().toPoint())

    def leaveEvent(self, event):
        self._btn_yes_hover = False
        self._btn_no_hover = False
        self.update()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        hovering = self._update_hover(event.position().toPoint())
        if self._tooltip:
            if hovering:
                gp = event.globalPosition().toPoint()
                if self._tooltip_pos is None:
                    self._tooltip_pos = gp
                    QToolTip.showText(gp, self._tooltip, self)
            else:
                self._tooltip_pos = None
                QToolTip.hideText()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self._done(True)
        elif event.key() == Qt.Key_Escape:
            self._done(False)


def ynbox(msg: str = "", title: str = "", tooltip: Optional[str] = None,
          pinned: bool = True, btn_texts: Optional[Tuple[str, str]] = None,
          font_family: str = None, font_size: int = None) -> bool:
    """DDLC-style yes/no dialog. Returns True(Yes) / False(No)

    Args:
        msg:        message text to display (supports \\n for multiple lines).
        title:      window title (unused in borderless mode).
        tooltip:    tooltip text shown when hovering over buttons. Disabled if None or empty.
        pinned:     keep the window always on top of other windows.
        btn_texts:  (confirm, cancel) tuple. Auto-detected from system language if None.

    Usage:
        import dokibox
        result = dokibox.ynbox("Delete this file?")
        result = dokibox.ynbox("Save?", btn_texts=("Save", "Cancel"))
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _YnDialog.run(msg, title, tooltip=tooltip, pinned=pinned, btn_texts=btn_texts,
                         font_family=font_family, font_size=font_size)

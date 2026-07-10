# -*- coding: utf-8 -*-
"""dokibox.ynbox -- DDLC-style yes/no dialog"""
import tkinter as tk
import tkinter.font as tkfont
import math
import locale
from typing import Optional, Tuple
from dokibox._base import _DokiBase, BODY_COLOR

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


def _get_system_lang():
    try:
        lang, _ = locale.getdefaultlocale()
    except Exception:
        lang = None
    if lang:
        lang = lang.lower()
        if lang.startswith('zh'):
            return 'zh'
        if lang.startswith('ja'):
            return 'ja'
        if lang.startswith('ko'):
            return 'ko'
        if lang.startswith('ru'):
            return 'ru'
    return 'en'


class _YnDialog(_DokiBase):

    def __init__(self, msg, title="", tooltip=False, pinned=True, btn_texts=None):
        self._tooltip = tooltip
        if btn_texts is not None:
            self._yes_text, self._no_text = btn_texts
        else:
            self._yes_text, self._no_text = _BTN_TEXTS.get(_get_system_lang(), _BTN_TEXTS['en'])
        super().__init__(msg, title, pinned=pinned)

    def _calc_size(self, msg):
        f_msg = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="bold")
        f_btn = tkfont.Font(family="Microsoft YaHei", size=BTN_FONT_SIZE, weight="bold")

        self._msg_font = ("Microsoft YaHei", MSG_FONT_SIZE, "bold")
        self._btn_font = ("Microsoft YaHei", BTN_FONT_SIZE, "bold")

        self._yes_w = f_btn.measure(self._yes_text)
        self._no_w = f_btn.measure(self._no_text)
        self._side_margin = int(self._yes_w * 1.5)

        min_btn_w = (self.BORDER_W * 2 + self._side_margin * 2
                     + int(self._yes_w) + int(self._no_w) + MIN_GAP)

        screen_w = self.root.winfo_screenwidth()
        max_msg_w = max(screen_w - PAD_X * 2, min_btn_w - PAD_X * 2, 200)

        raw_lines = msg.split('\n')
        wrapped_lines = []
        for line in raw_lines:
            if f_msg.measure(line) <= max_msg_w:
                wrapped_lines.append(line)
            else:
                current = ""
                for ch in line:
                    test = current + ch
                    if f_msg.measure(test) <= max_msg_w:
                        current = test
                    else:
                        if current:
                            wrapped_lines.append(current)
                        current = ch
                if current:
                    wrapped_lines.append(current)

        self._wrapped_msg = '\n'.join(wrapped_lines)
        self._msg_line_h = f_msg.metrics('linespace')
        self._msg_total_h = self._msg_line_h * len(wrapped_lines)
        self._btn_line_h = f_btn.metrics('linespace')

        msg_w = max(f_msg.measure(line) for line in wrapped_lines)
        w = max(int(msg_w + PAD_X * 2), int(min_btn_w), 300)
        w = min(w, screen_w - self.BORDER_W * 2)
        h = max(PAD_TOP + self._msg_total_h + PAD_BTNS
                + self._btn_line_h + BTN_STROKE_W * 2 + PAD_BOT, 180)
        return w, h

    def _draw_content(self, msg):
        msg_y = PAD_TOP + self._msg_total_h // 2
        self.cv.create_text(
            self.w // 2, msg_y, text=self._wrapped_msg, font=self._msg_font,
            fill=MSG_COLOR, anchor="center"
        )

        btn_y = self.h - PAD_BOT - self._btn_line_h // 2
        btn_yes_x = self.BORDER_W + self._side_margin + self._yes_w / 2
        btn_no_x = self.w - self.BORDER_W - self._side_margin - self._no_w / 2

        self._draw_button(btn_yes_x, btn_y, self._yes_text, "btn_yes")
        self._draw_button(btn_no_x, btn_y, self._no_text, "btn_no")

        self.cv.tag_bind("btn_yes", "<Enter>",
                         lambda e: self._set_hover("btn_yes", True))
        self.cv.tag_bind("btn_yes", "<Leave>",
                         lambda e: self._set_hover("btn_yes", False))
        self.cv.tag_bind("btn_no", "<Enter>",
                         lambda e: self._set_hover("btn_no", True))
        self.cv.tag_bind("btn_no", "<Leave>",
                         lambda e: self._set_hover("btn_no", False))

        if self._tooltip:
            self._add_tooltip("btn_yes", self._yes_text)
            self._add_tooltip("btn_no", self._no_text)

        self.root.bind("<Return>", lambda e: self._done(True))

    def _on_click(self, event):
        items = self.cv.find_overlapping(
            event.x - 15, event.y - 15, event.x + 15, event.y + 15
        )
        for item in items:
            tags = self.cv.gettags(item)
            if "btn_yes" in tags:
                self._done(True)
                return
            if "btn_no" in tags:
                self._done(False)
                return

    def _draw_button(self, x, y, text, tag):
        sw = BTN_STROKE_W
        for step in range(36):
            angle = 2 * math.pi * step / 36
            dx = sw * math.cos(angle)
            dy = sw * math.sin(angle)
            self.cv.create_text(x + dx, y + dy, text=text,
                                font=self._btn_font, fill=BTN_STROKE_COLOR,
                                anchor="center",
                                tags=(tag, tag + "_stroke"))
        self.cv.create_text(x, y, text=text, font=self._btn_font,
                            fill=BTN_FILL_COLOR, anchor="center",
                            tags=(tag, tag + "_fill"))

    def _set_hover(self, tag, hover):
        items = self.cv.find_withtag(tag + "_fill")
        color = BTN_HOVER_COLOR if hover else BTN_FILL_COLOR
        for item in items:
            self.cv.itemconfig(item, fill=color)

    def _add_tooltip(self, tag, text):
        tip = [None]

        def show(event):
            if tip[0]:
                return
            tw = tk.Toplevel(self.root)
            tw.overrideredirect(True)
            tw.attributes('-topmost', True)
            label = tk.Label(tw, text=text, bg=BODY_COLOR, fg='#000000',
                             font=("Microsoft YaHei", 12),
                             relief='solid', bd=1, padx=6, pady=2)
            label.pack()
            x = event.x_root + 15
            y = event.y_root + 15
            tw.geometry(f"+{x}+{y}")
            tip[0] = tw

        def hide(event):
            if tip[0]:
                tip[0].destroy()
                tip[0] = None

        self.cv.tag_bind(tag, "<Enter>", show, add='+')
        self.cv.tag_bind(tag, "<Leave>", hide, add='+')


def ynbox(msg: str = "", title: str = "", tooltip: bool = False, pinned: bool = True, btn_texts: Optional[Tuple[str, str]] = None) -> bool:
    """DDLC-style yes/no dialog. Returns True(Yes) / False(No)

    Args:
        msg:        message text to display (supports \\n for multiple lines).
        title:      window title (unused in borderless mode).
        tooltip:    show a floating tooltip when hovering over buttons.
        pinned:     keep the window always on top of other windows.
        btn_texts:  (confirm, cancel) tuple. Auto-detected from system language if None.

    Usage:
        import dokibox
        result = dokibox.ynbox("Delete this file?")
        result = dokibox.ynbox("Save?", btn_texts=("Save", "Cancel"))
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _YnDialog.show(msg, title, tooltip=tooltip, pinned=pinned, btn_texts=btn_texts)

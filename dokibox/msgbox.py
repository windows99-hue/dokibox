# -*- coding: utf-8 -*-
"""dokibox.msgbox -- DDLC风格消息对话框（单 OK 按钮）"""
import tkinter as tk
import tkinter.font as tkfont
import math
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


class _MsgDialog(_DokiBase):

    def __init__(self, msg, title="", tooltip=False):
        self._tooltip = tooltip
        super().__init__(msg, title)

    def _calc_size(self, msg):
        f_msg = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="bold")
        f_btn = tkfont.Font(family="Microsoft YaHei", size=BTN_FONT_SIZE, weight="bold")

        self._msg_font = ("Microsoft YaHei", MSG_FONT_SIZE, "bold")
        self._btn_font = ("Microsoft YaHei", BTN_FONT_SIZE, "bold")

        lines = msg.split('\n')
        msg_max_w = max(f_msg.measure(line) for line in lines)
        self._msg_line_h = f_msg.metrics('linespace')
        self._msg_total_h = self._msg_line_h * len(lines)
        self._btn_line_h = f_btn.metrics('linespace')

        w = max(int(msg_max_w + PAD_X * 2), 250)
        h = max(PAD_TOP + self._msg_total_h + PAD_BTNS
                + self._btn_line_h + BTN_STROKE_W * 2 + PAD_BOT, 150)
        return w, h

    def _draw_content(self, msg):
        msg_y = PAD_TOP + self._msg_total_h // 2
        self.cv.create_text(
            self.w // 2, msg_y, text=msg, font=self._msg_font,
            fill=MSG_COLOR, anchor="center"
        )

        btn_y = self.h - PAD_BOT - self._btn_line_h // 2
        self._draw_button(self.w // 2, btn_y, "OK", "btn_ok")

        self.cv.tag_bind("btn_ok", "<Enter>",
                         lambda e: self._set_hover("btn_ok", True))
        self.cv.tag_bind("btn_ok", "<Leave>",
                         lambda e: self._set_hover("btn_ok", False))

        if self._tooltip:
            self._add_tooltip("btn_ok", "OK")

        self.root.bind("<Return>", lambda e: self._done(True))
        self.root.bind("<Escape>", lambda e: self._done(True))

    def _on_click(self, event):
        items = self.cv.find_overlapping(
            event.x - 15, event.y - 15, event.x + 15, event.y + 15
        )
        for item in items:
            tags = self.cv.gettags(item)
            if "btn_ok" in tags:
                self._done(True)
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


def msgbox(msg="", title="", tooltip=False):
    """DDLC风格消息对话框（OK按钮），返回 True

    用法:
        import dokibox
        dokibox.msgbox("操作成功！")
    """
    return _MsgDialog.show(msg, title, tooltip=tooltip)

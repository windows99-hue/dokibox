# -*- coding: utf-8 -*-
"""dokibox.ynbox -- DDLC风格 是/否 对话框"""
import tkinter as tk
import tkinter.font as tkfont
from dokibox._base import _DokiBase

MSG_COLOR = "#000000"
BTN_FILL_COLOR = "#000000"
BTN_HOVER_COLOR = "#999999"

PAD_X = 80
PAD_TOP = 50
PAD_BTNS = 30
PAD_BOT = 70
MSG_FONT_SIZE = 22
BTN_FONT_SIZE = 26
MIN_GAP = 40


class _YnDialog(_DokiBase):

    def __init__(self, msg, title="", tooltip=False):
        self._tooltip = tooltip
        super().__init__(msg, title)

    def _calc_size(self, msg):
        f_msg = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="normal")
        f_btn = tkfont.Font(family="Microsoft YaHei", size=BTN_FONT_SIZE, weight="normal")

        self._msg_font = ("Microsoft YaHei", MSG_FONT_SIZE, "normal")
        self._btn_font = ("Microsoft YaHei", BTN_FONT_SIZE, "normal")

        lines = msg.split('\n')
        self._msg_max_w = max(f_msg.measure(line) for line in lines)
        self._msg_line_h = f_msg.metrics('linespace')
        self._msg_total_h = self._msg_line_h * len(lines)
        self._btn_line_h = f_btn.metrics('linespace')

        self._yes_w = f_btn.measure("是")
        self._no_w = f_btn.measure("否")
        self._side_margin = int(self._yes_w * 1.5)

        min_btn_w = (self.BORDER_W * 2 + self._side_margin * 2
                     + int(self._yes_w) + int(self._no_w) + MIN_GAP)
        w = max(int(self._msg_max_w + PAD_X * 2), int(min_btn_w), 300)
        h = max(PAD_TOP + self._msg_total_h + PAD_BTNS
                + self._btn_line_h + PAD_BOT, 180)
        return w, h

    def _draw_content(self, msg):
        msg_y = PAD_TOP + self._msg_total_h // 2
        self.cv.create_text(
            self.w // 2, msg_y, text=msg, font=self._msg_font,
            fill=MSG_COLOR, anchor="center"
        )

        btn_y = self.h - PAD_BOT - self._btn_line_h // 2
        btn_yes_x = self.BORDER_W + self._side_margin + self._yes_w / 2
        btn_no_x = self.w - self.BORDER_W - self._side_margin - self._no_w / 2

        self._draw_button(btn_yes_x, btn_y, "是", "btn_yes")
        self._draw_button(btn_no_x, btn_y, "否", "btn_no")

        self.cv.create_rectangle(0, 0, self.w // 2, self.h,
                                 fill='', outline='', tags='area_yes')
        self.cv.create_rectangle(self.w // 2, 0, self.w, self.h,
                                 fill='', outline='', tags='area_no')

        self.cv.tag_bind("area_yes", "<Enter>",
                         lambda e: self._set_hover("btn_yes", True))
        self.cv.tag_bind("area_yes", "<Leave>",
                         lambda e: self._set_hover("btn_yes", False))
        self.cv.tag_bind("area_no", "<Enter>",
                         lambda e: self._set_hover("btn_no", True))
        self.cv.tag_bind("area_no", "<Leave>",
                         lambda e: self._set_hover("btn_no", False))

        if self._tooltip:
            self._add_tooltip("area_yes", "是")
            self._add_tooltip("area_no", "否")

        self.root.bind("<Return>", lambda e: self._done(True))

    def _on_click(self, event):
        if event.x < self.w // 2:
            self._done(True)
        else:
            self._done(False)

    def _draw_button(self, x, y, text, tag):
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
            label = tk.Label(tw, text=text, bg=self.BODY_COLOR, fg='#000000',
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


def ynbox(msg="", title="", tooltip=False):
    """DDLC风格 是/否 对话框，返回 True(是) / False(否)

    用法:
        import dokibox
        result = dokibox.ynbox("确认删除？")                 # 默认无悬浮提示
        result = dokibox.ynbox("确认删除？", tooltip=True)    # 开启悬浮提示
    """
    return _YnDialog.show(msg, title, tooltip=tooltip)

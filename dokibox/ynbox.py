# -*- coding: utf-8 -*-
"""dokibox.ynbox -- DDLC风格 是/否 对话框"""
import tkinter.font as tkfont
import math
from dokibox._base import _DokiBase


# --- 配色 ---
MSG_COLOR = "#BD539D"
BTN_STROKE_COLOR = "#BD539D"
BTN_FILL_COLOR = "#ffffff"
BTN_HOVER_COLOR = "#ffd0e8"

# --- 布局 ---
PAD_X = 80
PAD_TOP = 50
PAD_BTNS = 30
PAD_BOT = 70
MSG_STROKE_W = 2
BTN_STROKE_W = 6
MSG_FONT_SIZE = 22
BTN_FONT_SIZE = 26
MIN_GAP = 40


class _YnDialog(_DokiBase):

    def _calc_size(self, msg):
        f_msg = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="bold")
        f_btn = tkfont.Font(family="Microsoft YaHei", size=BTN_FONT_SIZE, weight="bold")

        self._msg_font = ("Microsoft YaHei", MSG_FONT_SIZE, "bold")
        self._btn_font = ("Microsoft YaHei", BTN_FONT_SIZE, "bold")

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
                + self._btn_line_h + BTN_STROKE_W * 2 + PAD_BOT, 180)
        return w, h

    def _draw_content(self, msg):
        msg_y = PAD_TOP + self._msg_total_h // 2
        self._draw_stroked_text(
            self.w // 2, msg_y, msg, self._msg_font,
            MSG_COLOR, self.BORDER_COLOR, MSG_STROKE_W
        )

        btn_y = self.h - PAD_BOT - self._btn_line_h // 2
        btn_yes_x = self.BORDER_W + self._side_margin + self._yes_w / 2
        btn_no_x = self.w - self.BORDER_W - self._side_margin - self._no_w / 2

        self._draw_button(btn_yes_x, btn_y, "是", "btn_yes")
        self._draw_button(btn_no_x, btn_y, "否", "btn_no")

        self.cv.tag_bind("btn_yes", "<Enter>",
                         lambda e: self._set_hover("btn_yes", True))
        self.cv.tag_bind("btn_yes", "<Leave>",
                         lambda e: self._set_hover("btn_yes", False))
        self.cv.tag_bind("btn_no", "<Enter>",
                         lambda e: self._set_hover("btn_no", True))
        self.cv.tag_bind("btn_no", "<Leave>",
                         lambda e: self._set_hover("btn_no", False))

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

    # ---------- 按钮绘制 ----------

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


def ynbox(msg="", title=""):
    """DDLC风格 是/否 对话框，返回 True(是) / False(否)

    用法:
        import dokibox
        result = dokibox.ynbox("确认删除？")
    """
    return _YnDialog.show(msg, title)

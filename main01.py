# -*- coding: utf-8 -*-
"""
DDLC风格消息对话框
用法:
    from main01 import DDLC_MsgBox
    result = DDLC_MsgBox.show("确认要退出吗？")
    # 返回 True(是) 或 False(否)
"""
import tkinter as tk
import tkinter.font as tkfont
import math

# --- 颜色定义 ---
BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"
MSG_COLOR = "#BD539D"
BTN_STROKE_COLOR = "#BD539D"
BTN_FILL_COLOR = "#ffffff"
BTN_HOVER_COLOR = "#ffd0e8"

# --- 布局常量 ---
PAD_X = 60
PAD_TOP = 50
PAD_BTNS = 30
PAD_BOT = 35
BTN_GAP = 80
BORDER_W = 12
MSG_STROKE_W = 2
BTN_STROKE_W = 5
MSG_FONT_SIZE = 22
BTN_FONT_SIZE = 28


class DDLC_MsgBox:

    @staticmethod
    def show(msg="", title=""):
        box = _DDLC_Dialog(msg, title)
        box.root.mainloop()
        return box.result


class _DDLC_Dialog:

    def __init__(self, msg, title):
        self.result = None
        self._press_x = 0
        self._press_y = 0
        self._offset_x = 0
        self._offset_y = 0

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        self.msg_font = ("Microsoft YaHei", MSG_FONT_SIZE, "bold")
        self.btn_font = ("Microsoft YaHei", BTN_FONT_SIZE, "bold")

        f_msg = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="bold")
        f_btn = tkfont.Font(family="Microsoft YaHei", size=BTN_FONT_SIZE, weight="bold")

        lines = msg.split('\n')
        msg_max_w = max(f_msg.measure(line) for line in lines)
        msg_line_h = f_msg.metrics('linespace')
        msg_total_h = msg_line_h * len(lines)
        btn_line_h = f_btn.metrics('linespace')

        yes_w = f_btn.measure("是")
        no_w = f_btn.measure("否")
        btn_total_w = yes_w + BTN_GAP + no_w

        content_w = max(msg_max_w, btn_total_w)
        self.w = max(content_w + PAD_X * 2, 350)
        self.h = max(PAD_TOP + msg_total_h + PAD_BTNS + btn_line_h + BTN_STROKE_W * 2 + PAD_BOT, 180)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.w) // 2
        y = (sh - self.h) // 2
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")

        self.cv = tk.Canvas(
            self.root, width=self.w, height=self.h,
            bg=BODY_COLOR, highlightthickness=0
        )
        self.cv.pack()

        self._draw_gradient_border()

        self._draw_stroked_text(
            self.w // 2, PAD_TOP + msg_total_h // 2,
            msg, self.msg_font, MSG_COLOR, BORDER_COLOR, MSG_STROKE_W
        )

        btn_area_start = (self.w - btn_total_w) / 2
        btn_y = self.h - PAD_BOT - btn_line_h // 2
        btn_yes_x = btn_area_start + yes_w / 2
        btn_no_x = btn_area_start + yes_w + BTN_GAP + no_w / 2

        self._draw_button(btn_yes_x, btn_y, "是", "btn_yes")
        self._draw_button(btn_no_x, btn_y, "否", "btn_no")

        self.cv.tag_bind("btn_yes", "<Enter>",
                         lambda e: self._set_btn_hover("btn_yes", True))
        self.cv.tag_bind("btn_yes", "<Leave>",
                         lambda e: self._set_btn_hover("btn_yes", False))
        self.cv.tag_bind("btn_no", "<Enter>",
                         lambda e: self._set_btn_hover("btn_no", True))
        self.cv.tag_bind("btn_no", "<Leave>",
                         lambda e: self._set_btn_hover("btn_no", False))

        self.cv.bind("<ButtonPress-1>", self._on_press)
        self.cv.bind("<B1-Motion>", self._on_motion)
        self.cv.bind("<ButtonRelease-1>", self._on_release)

        self.root.bind("<Escape>", lambda e: self._done(False))
        self.root.bind("<Return>", lambda e: self._done(True))
        self.root.focus_force()

    def _hex_to_rgb(self, hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _draw_gradient_border(self):
        br, bg, bb = self._hex_to_rgb(BORDER_COLOR)
        er, eg, eb = self._hex_to_rgb(BODY_COLOR)
        for i in range(BORDER_W):
            t = i / max(BORDER_W - 1, 1)
            r = int(br + (er - br) * t)
            g = int(bg + (eg - bg) * t)
            b = int(bb + (eb - bb) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.cv.create_rectangle(i, i, self.w - i, self.h - i,
                                     outline=color, width=1)

    def _draw_stroked_text(self, x, y, text, font, fill, stroke, stroke_w):
        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = stroke_w * math.cos(angle)
            dy = stroke_w * math.sin(angle)
            self.cv.create_text(x + dx, y + dy, text=text,
                                font=font, fill=stroke, anchor="center")
        self.cv.create_text(x, y, text=text, font=font,
                            fill=fill, anchor="center")

    def _draw_button(self, x, y, text, tag):
        stroke_w = BTN_STROKE_W
        for step in range(36):
            angle = 2 * math.pi * step / 36
            dx = stroke_w * math.cos(angle)
            dy = stroke_w * math.sin(angle)
            self.cv.create_text(x + dx, y + dy, text=text,
                                font=self.btn_font, fill=BTN_STROKE_COLOR,
                                anchor="center",
                                tags=(tag, tag + "_stroke"))
        self.cv.create_text(x, y, text=text, font=self.btn_font,
                            fill=BTN_FILL_COLOR, anchor="center",
                            tags=(tag, tag + "_fill"))

    def _set_btn_hover(self, tag, hover):
        items = self.cv.find_withtag(tag + "_fill")
        color = BTN_HOVER_COLOR if hover else BTN_FILL_COLOR
        for item in items:
            self.cv.itemconfig(item, fill=color)

    def _on_press(self, event):
        self._press_x = event.x_root
        self._press_y = event.y_root
        self._offset_x = event.x_root - self.root.winfo_x()
        self._offset_y = event.y_root - self.root.winfo_y()

    def _on_motion(self, event):
        new_x = event.x_root - self._offset_x
        new_y = event.y_root - self._offset_y
        self.root.geometry(f"+{new_x}+{new_y}")

    def _on_release(self, event):
        dx = abs(event.x_root - self._press_x)
        dy = abs(event.y_root - self._press_y)
        if dx < 5 and dy < 5:
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

    def _done(self, value):
        self.result = value
        self.root.destroy()


def ask_yes_no(msg="", title=""):
    return DDLC_MsgBox.show(msg, title)


if __name__ == "__main__":
    res = DDLC_MsgBox.show("真的要退出DDLC吗？\n纱世里会伤心的...")
    print("用户选择了:", "是" if res else "否")

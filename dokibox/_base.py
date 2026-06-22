# -*- coding: utf-8 -*-
"""dokibox 内部基类 -- 窗口 / 渐变边框 / 描边文字 / 拖拽"""
import tkinter as tk
import math


# --- 默认配色 ---
BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"


class _DokiBase:
    """对话框基类。子类只需实现 _calc_size / _draw_content / _on_click"""

    BORDER_COLOR = BORDER_COLOR
    BODY_COLOR = BODY_COLOR
    BORDER_W = 12

    def __init__(self, msg, title=""):
        self.result = None
        self._px = 0
        self._py = 0
        self._ox = 0
        self._oy = 0

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)

        self.w, self.h = self._calc_size(msg)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - self.w) // 2
        y = (sh - self.h) // 2
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")

        self.cv = tk.Canvas(
            self.root, width=self.w, height=self.h,
            bg=self.BODY_COLOR, highlightthickness=0
        )
        self.cv.pack()

        self._draw_gradient_border()
        self._draw_content(msg)

        self.root.bind("<Escape>", lambda e: self._done(False))
        self._make_draggable()
        self.root.focus_force()

    # ========== 子类必须实现 ==========

    def _calc_size(self, msg):
        raise NotImplementedError

    def _draw_content(self, msg):
        raise NotImplementedError

    def _on_click(self, event):
        pass

    # ========== 共享绘制工具 ==========

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def _draw_gradient_border(self):
        br, bg, bb = self._hex_to_rgb(self.BORDER_COLOR)
        er, eg, eb = self._hex_to_rgb(self.BODY_COLOR)
        bw = self.BORDER_W
        for i in range(bw):
            t = (i / max(bw - 1, 1)) ** 3
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

    # ========== 拖拽 ==========

    def _make_draggable(self):
        self.cv.bind("<ButtonPress-1>", self._on_press, add='+')
        self.cv.bind("<B1-Motion>", self._on_motion, add='+')
        self.cv.bind("<ButtonRelease-1>", self._on_release, add='+')

    def _on_press(self, event):
        self._px = event.x_root
        self._py = event.y_root
        self._ox = event.x_root - self.root.winfo_x()
        self._oy = event.y_root - self.root.winfo_y()

    def _on_motion(self, event):
        new_x = event.x_root - self._ox
        new_y = event.y_root - self._oy
        self.root.geometry(f"+{new_x}+{new_y}")

    def _on_release(self, event):
        dx = abs(event.x_root - self._px)
        dy = abs(event.y_root - self._py)
        if dx < 5 and dy < 5:
            self._on_click(event)

    # ========== 生命周期 ==========

    def _done(self, value):
        self.result = value
        self.root.destroy()

    @classmethod
    def show(cls, msg="", title=""):
        dialog = cls(msg, title)
        dialog.root.mainloop()
        return dialog.result

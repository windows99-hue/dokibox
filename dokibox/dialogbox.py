# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC风格底部对话框（圆角矩形·渐变不透明度·白色描边）"""
import tkinter as tk
import math

BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#ffffff"
TRANSPARENT_KEY = "#00FF00"
FADE_TO = "#FFFFFF"
CORNER_RADIUS = 30

# --- 圆点装饰 ---
DOT_RADIUS = 8
DOT_GAP_X = 20
DOT_GAP_Y = 2
DOT_COLOR = "#FB94C1"


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _blend(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 * t + r2 * (1 - t))
    g = int(g1 * t + g2 * (1 - t))
    b = int(b1 * t + b2 * (1 - t))
    return f'#{r:02x}{g:02x}{b:02x}'


class _DialogBox:

    def __init__(self, msg, w, h):
        self.root = tk.Tk()
        self.root.withdraw()

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.wm_attributes('-transparentcolor', TRANSPARENT_KEY)

        self.w = w
        self.h = h
        self.r = CORNER_RADIUS

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = sh - h - 60
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.cv = tk.Canvas(self.win, width=w, height=h,
                            bg=TRANSPARENT_KEY, highlightthickness=0)
        self.cv.pack()

        self._draw_fill()
        self._draw_dots()
        self._clip_corners()
        self._draw_outline()
        self._draw_text(msg)

        self.win.bind("<Button-1>", lambda e: self._done())
        self.root.bind("<Escape>", lambda e: self._done())
        self.root.update()

    def _draw_fill(self):
        r = self.r
        steps = 60
        for i in range(steps):
            t_bottom = i / max(steps - 1, 1)
            t_top = (i + 1) / max(steps - 1, 1)
            opacity_top = 1.0 - 0.5 * t_bottom
            opacity_bot = 1.0 - 0.5 * t_top
            opacity = (opacity_top + opacity_bot) / 2

            color = _blend(BODY_COLOR, FADE_TO, opacity)

            y1 = int(self.h * t_bottom)
            y2 = int(self.h * t_top)

            inner_left = 0
            inner_right = self.w
            if y1 < r:
                dy1 = r - y1
                inner_left = r - int(math.sqrt(max(r * r - dy1 * dy1, 0)))
                inner_right = self.w - inner_left
            if y2 < r:
                dy2 = r - y2
                inner_left = max(inner_left, r - int(math.sqrt(max(r * r - dy2 * dy2, 0))))
                inner_right = min(inner_right, self.w - (r - int(math.sqrt(max(r * r - dy2 * dy2, 0)))))

            if y1 > self.h - r:
                dy1 = y1 - (self.h - r)
                inner_left = r - int(math.sqrt(max(r * r - dy1 * dy1, 0)))
                inner_right = self.w - inner_left
            if y2 > self.h - r:
                dy2 = y2 - (self.h - r)
                inner_left = max(inner_left, r - int(math.sqrt(max(r * r - dy2 * dy2, 0))))
                inner_right = min(inner_right, self.w - (r - int(math.sqrt(max(r * r - dy2 * dy2, 0)))))

            x1 = max(0, inner_left)
            x2 = min(self.w, inner_right)
            self.cv.create_rectangle(int(x1), int(y1), int(x2), int(y2),
                                     fill=color, outline='')

    def _draw_dots(self):
        dr = DOT_RADIUS
        gap_x = DOT_GAP_X
        gap_y = DOT_GAP_Y
        step = int(dr * 2 + gap_x)
        row_h = int(dr * 2 + gap_y)

        row = 0
        y = -dr
        while y < self.h + dr:
            t = max(0, min(1, y / self.h))
            opacity = 1.0 - 0.5 * t
            color = _blend(DOT_COLOR, FADE_TO, opacity)

            offset_x = (step // 2) if row % 2 == 1 else 0
            x = -dr + offset_x
            while x < self.w + dr:
                d = 2 * dr
                self.cv.create_oval(x - dr, y - dr, x + dr, y + dr,
                                    fill=color, outline='')
                x += step
            y += row_h
            row += 1

    def _clip_corners(self):
        r = self.r
        w = self.w
        h = self.h
        fill = TRANSPARENT_KEY
        for y in range(0, r):
            dy = r - y
            wx = r - int(math.sqrt(max(r * r - dy * dy, 0)))
            if wx > 0:
                self.cv.create_rectangle(0, y, wx, y + 1, fill=fill, outline='')
                self.cv.create_rectangle(w - wx, y, w, y + 1, fill=fill, outline='')
        for y in range(h - r, h):
            dy = y - (h - r)
            wx = r - int(math.sqrt(max(r * r - dy * dy, 0)))
            if wx > 0:
                self.cv.create_rectangle(0, y, wx, y + 1, fill=fill, outline='')
                self.cv.create_rectangle(w - wx, y, w, y + 1, fill=fill, outline='')

    def _draw_outline(self):
        r = self.r
        w = self.w
        h = self.h
        color = BORDER_COLOR

        self.cv.create_arc(0, 0, r * 2, r * 2,
                           start=90, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(w - r * 2, 0, w, r * 2,
                           start=0, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(0, h - r * 2, r * 2, h,
                           start=180, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(w - r * 2, h - r * 2, w, h,
                           start=270, extent=90, style=tk.ARC, outline=color, width=3)

        self.cv.create_line(r, 1, w - r, 1, fill=color, width=3)
        self.cv.create_line(r, h - 1, w - r, h - 1, fill=color, width=3)
        self.cv.create_line(1, r, 1, h - r, fill=color, width=3)
        self.cv.create_line(w - 1, r, w - 1, h - r, fill=color, width=3)

    def _draw_text(self, msg):
        if not msg:
            return
        font = ("Microsoft YaHei", 20, "bold")
        lines = msg.split('\n')
        line_h = 30
        pad_x = self.r + 20
        pad_top = 20

        for j, line in enumerate(lines):
            y = pad_top + line_h // 2 + j * line_h
            self._draw_stroked(pad_x, y, line, font)

    def _draw_stroked(self, x, y, text, font):
        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = math.cos(angle)
            dy = math.sin(angle)
            self.cv.create_text(x + dx, y + dy, text=text, font=font,
                                fill="#000000", anchor="w")
        self.cv.create_text(x, y, text=text, font=font,
                            fill="#ffffff", anchor="w")

    def _done(self):
        self.win.destroy()
        self.root.quit()


def dialogbox(msg="", w=900, h=180):
    """DDLC风格底部圆角对话框。点击任意位置或按 Esc 关闭。

    用法:
        dokibox.dialogbox("你好，世界！")
        dokibox.dialogbox("第二句话", w=900, h=200)
    """
    box = _DialogBox(msg, w, h)
    box.root.mainloop()
    try:
        box.root.destroy()
    except tk.TclError:
        pass

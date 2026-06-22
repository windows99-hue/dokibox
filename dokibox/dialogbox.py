# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC风格底部对话框（圆角矩形·渐变不透明度·白色描边）"""
import tkinter as tk
import tkinter.font as tkfont
import math

BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#ffffff"
TRANSPARENT_KEY = "#00FF00"
FADE_TO = "#FFFFFF"
CORNER_RADIUS = 18

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

    def __init__(self, msg, w, h, name=None):
        self.root = tk.Tk()
        self.root.withdraw()

        self.w = w
        self.h = h
        self.r = CORNER_RADIUS
        self._name = name

        f_name = tkfont.Font(family="Microsoft YaHei", size=16, weight="bold")
        name_h = 0
        if name:
            tw = f_name.measure(name)
            name_pad = 22
            name_h = f_name.metrics('linespace') + name_pad
            self._tag_w = int(tw + name_pad * 2)
            self._tag_h = name_h
            self._tag_top = 10
            self._tag_r = 10
        else:
            self._tag_w = 0

        cv_h = h + name_h + 20 if name else h
        self._cv_h = cv_h
        self._dialog_top = name_h + 20 if name else 0

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.wm_attributes('-transparentcolor', TRANSPARENT_KEY)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = sh - cv_h - 60 + self._dialog_top
        self.win.geometry(f"{w}x{cv_h}+{x}+{y}")

        self.cv = tk.Canvas(self.win, width=w, height=cv_h,
                            bg=TRANSPARENT_KEY, highlightthickness=0)
        self.cv.pack()

        if self._name:
            self._draw_name_tag_bg()
        self._draw_fill()
        self._draw_dots()
        self._clip_corners()
        if self._name:
            self._draw_name_shadow()
        self._draw_outline()
        if self._name:
            self._draw_name_text()
        self._draw_text(msg)

        self.win.bind("<Button-1>", lambda e: self._done())
        self.root.bind("<Escape>", lambda e: self._done())
        self.root.update()

    def _draw_name_tag_bg(self):
        tx = self.r + 10
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        tr = self._tag_r

        self.cv.create_rectangle(tx + tr, ty, tx + tw - tr, ty + th,
                                 fill="#ffffff", outline='')
        self.cv.create_rectangle(tx, ty + tr, tx + tw, ty + th - tr,
                                 fill="#ffffff", outline='')
        self.cv.create_arc(tx, ty, tx + tr * 2, ty + tr * 2,
                           start=90, extent=90, style=tk.PIESLICE, fill="#ffffff", outline='')
        self.cv.create_arc(tx + tw - tr * 2, ty, tx + tw, ty + tr * 2,
                           start=0, extent=90, style=tk.PIESLICE, fill="#ffffff", outline='')
        self.cv.create_arc(tx, ty + th - tr * 2, tx + tr * 2, ty + th,
                           start=180, extent=90, style=tk.PIESLICE, fill="#ffffff", outline='')
        self.cv.create_arc(tx + tw - tr * 2, ty + th - tr * 2, tx + tw, ty + th,
                           start=270, extent=90, style=tk.PIESLICE, fill="#ffffff", outline='')

    def _draw_name_shadow(self):
        tx = self.r + 10
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        for d in range(4):
            alpha = 0.15 - d * 0.03
            color = _blend("#000000", TRANSPARENT_KEY, max(alpha, 0))
            self.cv.create_line(tx + 1, ty + th + d, tx + tw - 1, ty + th + d,
                                fill=color, width=1)

    def _draw_name_text(self):
        tx = self.r + 10
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        cx = tx + tw // 2
        cy = ty + th // 2
        font = ("Microsoft YaHei", 16, "bold")

        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = math.cos(angle) * 1.5
            dy = math.sin(angle) * 1.5
            self.cv.create_text(cx + dx, cy + dy, text=self._name, font=font,
                                fill="#BD539D", anchor="center")
        self.cv.create_text(cx, cy, text=self._name, font=font,
                            fill="#ffffff", anchor="center")

    def _draw_fill(self):
        r = self.r
        top = self._dialog_top
        steps = 60
        for i in range(steps):
            t_bottom = i / max(steps - 1, 1)
            t_top = (i + 1) / max(steps - 1, 1)
            opacity_top = 1.0 - 0.5 * t_bottom
            opacity_bot = 1.0 - 0.5 * t_top
            opacity = (opacity_top + opacity_bot) / 2

            color = _blend(BODY_COLOR, FADE_TO, opacity)

            y1 = int(self.h * t_bottom) + top
            y2 = int(self.h * t_top) + top

            inner_left = 0
            inner_right = self.w
            ly1 = y1 - top
            ly2 = y2 - top
            if ly1 < r:
                dy1 = r - ly1
                inner_left = r - int(math.sqrt(max(r * r - dy1 * dy1, 0)))
                inner_right = self.w - inner_left
            if ly2 < r:
                dy2 = r - ly2
                inner_left = max(inner_left, r - int(math.sqrt(max(r * r - dy2 * dy2, 0))))
                inner_right = min(inner_right, self.w - (r - int(math.sqrt(max(r * r - dy2 * dy2, 0)))))

            if ly1 > self.h - r:
                dy1 = ly1 - (self.h - r)
                inner_left = r - int(math.sqrt(max(r * r - dy1 * dy1, 0)))
                inner_right = self.w - inner_left
            if ly2 > self.h - r:
                dy2 = ly2 - (self.h - r)
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
        top = self._dialog_top
        step = int(dr * 2 + gap_x)
        row_h = int(dr * 2 + gap_y)

        row = 0
        y = top + dr
        while y < top + self.h + dr:
            t = max(0, min(1, (y - top) / self.h))
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
        top = self._dialog_top
        key = TRANSPARENT_KEY
        for y in range(top, top + r + 2):
            dy = max(0, r - (y - top))
            wx = r - int(math.sqrt(max(r * r - dy * dy, 0)))
            if wx > 0:
                self.cv.create_rectangle(0, y, wx + 1, y + 1, fill=key, outline='')
                self.cv.create_rectangle(w - wx - 1, y, w, y + 1, fill=key, outline='')
        for y in range(top + self.h - r - 2, top + self.h):
            dy = max(0, y - (top + self.h - r))
            wx = r - int(math.sqrt(max(r * r - dy * dy, 0)))
            if wx > 0:
                self.cv.create_rectangle(0, y, wx + 1, y + 1, fill=key, outline='')
                self.cv.create_rectangle(w - wx - 1, y, w, y + 1, fill=key, outline='')

    def _draw_outline(self):
        r = self.r
        w = self.w
        top = self._dialog_top
        h = self.h
        color = BORDER_COLOR

        self.cv.create_arc(0, top, r * 2, top + r * 2,
                           start=90, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(w - r * 2, top, w, top + r * 2,
                           start=0, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(0, top + h - r * 2, r * 2, top + h,
                           start=180, extent=90, style=tk.ARC, outline=color, width=3)
        self.cv.create_arc(w - r * 2, top + h - r * 2, w, top + h,
                           start=270, extent=90, style=tk.ARC, outline=color, width=3)

        self.cv.create_line(r, top + 1, w - r, top + 1, fill=color, width=3)
        self.cv.create_line(r, top + h - 1, w - r, top + h - 1, fill=color, width=3)
        self.cv.create_line(1, top + r, 1, top + h - r, fill=color, width=3)
        self.cv.create_line(w - 1, top + r, w - 1, top + h - r, fill=color, width=3)

    def _draw_text(self, msg):
        if not msg:
            return
        top = self._dialog_top
        font = ("Microsoft YaHei", 20, "bold")
        lines = msg.split('\n')
        line_h = 30
        pad_top = 15
        pad_x = self.r + 20
        if self._name:
            pad_x += self._tag_w + 15

        for j, line in enumerate(lines):
            y = top + pad_top + line_h // 2 + j * line_h
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


def dialogbox(msg="", w=None, h=180, name=None):
    """DDLC风格底部圆角对话框。点击任意位置或按 Esc 关闭。

    用法:
        dokibox.dialogbox("你好！")
        dokibox.dialogbox("你好！", name="纱世里")
    """
    if w is None:
        root = tk.Tk()
        root.withdraw()
        w = int(root.winfo_screenwidth() * 0.6)
        root.destroy()
    box = _DialogBox(msg, w, h, name)
    box.root.mainloop()
    try:
        box.root.destroy()
    except tk.TclError:
        pass

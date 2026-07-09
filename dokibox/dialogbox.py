# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC-style bottom dialog (rounded corners, gradient opacity, white stroke)"""
import tkinter as tk
import tkinter.font as tkfont
import math
from typing import Optional

BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#ffffff"
TRANSPARENT_KEY = "#00FF00"
FADE_TO = "#FFFFFF"
CORNER_RADIUS = 18

# --- dot pattern decoration ---
DOT_RADIUS = 13
DOT_GAP_X = 35
DOT_GAP_Y = 6
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


_box = None


class _DialogBox:

    def __init__(self, msg, w, h, name=None, typewriter=True, chardelay=50, bold=False, pinned=True, fdst=False, overflow_mode="overflow"):
        global _box

        if overflow_mode not in ("wrap", "overflow", "hide"):
            raise ValueError(f"overflow_mode must be 'wrap', 'overflow', or 'hide', got {overflow_mode!r}")
        self._overflow_mode = overflow_mode

        self.w = w
        self.h = h
        self.r = CORNER_RADIUS
        self._name = name
        self._typewriter = typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._fdst = fdst
        self._pinned = pinned
        self._typing = False
        self._typing_done = False
        self._after_id = None

        if _box is not None:
            self.root = _box.root
            self.win = _box.win
            self.cv = _box.cv

            if _box._after_id:
                _box.root.after_cancel(_box._after_id)

            self.cv.delete("all")
        else:
            self.root = tk.Tk()
            self.root.withdraw()

            self.win = tk.Toplevel(self.root)
            self.win.overrideredirect(True)
            self.win.wm_attributes('-transparentcolor', TRANSPARENT_KEY)

            self.cv = tk.Canvas(self.win, bg=TRANSPARENT_KEY, highlightthickness=0)
            self.cv.pack()

        f_name = tkfont.Font(family="Microsoft YaHei", size=20, weight="bold")
        name_h = 0
        if name:
            tw = f_name.measure(name)
            name_pad = 28
            name_h = f_name.metrics('linespace') + name_pad
            self._tag_w = int(tw + name_pad * 2) + 80
            self._tag_h = name_h
            self._tag_top = 30
            self._tag_r = 12
        else:
            self._tag_w = 0

        cv_h = h + name_h + 24 if name else h
        self._cv_h = cv_h
        self._dialog_top = name_h + 20 if name else 0

        canvas_w = w
        if self._overflow_mode == "overflow" and msg:
            f_body = tkfont.Font(family="Microsoft YaHei", size=20, weight="bold")
            max_line_w = max(f_body.measure(line) for line in msg.split('\n'))
            needed_w = int(max_line_w + 80)
            if needed_w > canvas_w:
                canvas_w = needed_w

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        dialog_screen_y = sh - h - 60
        win_y = dialog_screen_y - self._dialog_top
        self.win.geometry(f"{canvas_w}x{cv_h}+{x}+{win_y}")
        self.cv.config(width=canvas_w, height=cv_h)

        self.win.attributes('-topmost', pinned)

        if self._name:
            self._draw_name_tag_bg()
        self._draw_fill()
        self._draw_dots()
        self._clip_corners()
        self._draw_outline()
        if self._name:
            self._draw_name_text()
        self._draw_text(msg)
        self._draw_triangle()

        self.win.bind("<Button-1>", lambda e: self._on_click())
        self.root.bind("<Escape>", lambda e: self._done())
        self.root.update()

        _box = self

    def _on_click(self):
        if self._typewriter and self._typing:
            self._finish_typewriter()
        else:
            self._done()

    def _draw_name_tag_bg(self):
        tx = self.r + 10
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        tr = self._tag_r

        # white fill
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

        # bottom 25% gradient: white -> black
        grad_top = ty + th * 0.75
        grad_h = int(th * 0.25)
        steps = 12
        for i in range(steps):
            t_bot = i / max(steps - 1, 1)
            t_top = min((i + 1) / max(steps - 1, 1), 1.0)
            opacity = (t_bot + t_top) / 2
            color = _blend("#000000", "#ffffff", opacity)

            y1 = int(grad_top + grad_h * t_bot)
            y2 = int(grad_top + grad_h * t_top)
            self.cv.create_rectangle(int(tx), int(y1), int(tx + tw), int(y2),
                                     fill=color, outline='')

    def _draw_name_text(self):
        tx = self.r + 10
        ty = self._tag_top - 5
        tw = self._tag_w
        th = self._tag_h
        cx = tx + tw // 2
        cy = ty + th // 2
        font = ("Microsoft YaHei", 20, "bold")

        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = math.cos(angle) * 2
            dy = math.sin(angle) * 2
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
            t_top = min((i + 1) / max(steps - 1, 1), 1.0)
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

    def _text_area_width(self):
        return self.w - 80

    def _wrap_line(self, text, font, max_w):
        f = tkfont.Font(font=font)
        if f.measure(text) <= max_w:
            return [text]
        lines = []
        current = ""
        for ch in text:
            test = current + ch
            if f.measure(test) <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines

    def _truncate_line(self, text, font, max_w):
        f = tkfont.Font(font=font)
        if f.measure(text) <= max_w:
            return text
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if f.measure(text[:mid]) <= max_w:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo]

    def _process_lines(self, text, font, max_w):
        if self._overflow_mode == "overflow":
            return text.split('\n')
        raw_lines = text.split('\n')
        if self._overflow_mode == "wrap":
            result = []
            for line in raw_lines:
                result.extend(self._wrap_line(line, font, max_w))
            return result
        if self._overflow_mode == "hide":
            return [self._truncate_line(line, font, max_w) for line in raw_lines]

    def _draw_text(self, msg):
        if not msg:
            return
        top = self._dialog_top
        font = ("Microsoft YaHei", 20, "bold")
        line_h = 44
        pad_top = 40
        pad_x = 40

        lines = self._process_lines(msg, font, self._text_area_width())

        pos = []
        for j, line in enumerate(lines):
            y = top + pad_top + line_h // 2 + j * line_h
            pos.append((pad_x, y, line))

        if self._typewriter:
            self._start_typewriter(pos, font)
        else:
            for px, py, line in pos:
                self._draw_stroked(px, py, line, font)

    def _start_typewriter(self, positions, font):
        self._typing = True
        self._typing_done = False
        self._lines = []
        self._pos = positions
        self._font = font
        self._cur_line = 0
        self._cur_char = 0

        self._line_data = []
        sw = 4 if self._bold else 1
        for px, py, full_text in positions:
            stroke_ids = []
            for step in range(24):
                angle = 2 * math.pi * step / 24
                dx = math.cos(angle) * sw
                dy = math.sin(angle) * sw
                sid = self.cv.create_text(px + dx, py + dy, text="",
                                          font=font, fill="#000000", anchor="w")
                stroke_ids.append(sid)
            fid = self.cv.create_text(px, py, text="",
                                      font=font, fill="#ffffff", anchor="w")
            self._line_data.append((stroke_ids, fid, full_text))

        self._type_tick()

    def _type_tick(self):
        if self._cur_line >= len(self._line_data):
            self._typing = False
            self._typing_done = True
            self._after_id = None
            return

        stroke_ids, fid, full_text = self._line_data[self._cur_line]
        self._cur_char += 1
        if self._cur_char > len(full_text):
            self._cur_line += 1
            self._cur_char = 0
            self._type_tick()
            return

        current = full_text[:self._cur_char]
        for sid in stroke_ids:
            self.cv.itemconfig(sid, text=current)
        self.cv.itemconfig(fid, text=current)

        self._after_id = self.root.after(self._chardelay, self._type_tick)

    def _draw_triangle(self):
        s = 16
        h = s * math.sqrt(3) / 2
        tip_x = self.w - 28
        tip_y = self._dialog_top + self.h - 24
        self.cv.create_polygon(
            tip_x, tip_y,
            tip_x - h, tip_y - s / 2,
            tip_x - h, tip_y + s / 2,
            fill="#ffffff", outline=""
        )

    def _finish_typewriter(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        for stroke_ids, fid, full_text in self._line_data:
            for sid in stroke_ids:
                self.cv.itemconfig(sid, text=full_text)
            self.cv.itemconfig(fid, text=full_text)
        self._typing = False
        self._typing_done = True

    def _draw_stroked(self, x, y, text, font):
        sw = 4 if self._bold else 1
        for step in range(24):
            angle = 2 * math.pi * step / 24
            dx = math.cos(angle) * sw
            dy = math.sin(angle) * sw
            self.cv.create_text(x + dx, y + dy, text=text, font=font,
                                fill="#000000", anchor="w")
        self.cv.create_text(x, y, text=text, font=font,
                            fill="#ffffff", anchor="w")

    def _done(self):
        if self._fdst:
            _destroy_box()
        else:
            self.root.quit()


def _destroy_box():
    global _box
    if _box is not None:
        if _box._after_id:
            _box.root.after_cancel(_box._after_id)
        _box.root.destroy()
        _box = None


def dialogbox(msg: str = "", w: Optional[int] = None, h: int = 220, name: Optional[str] = None, typewriter: bool = True, chardelay: int = 50, bold: bool = False, pinned: bool = True, fdst: bool = False, overflow_mode: str = "wrap") -> None:
    """DDLC-style bottom rounded dialog. Click anywhere or press Esc to dismiss.

    Args:
        msg:           body text to display (supports \\n for multiple lines).
        w:             width in pixels. Defaults to 70% of screen width if None.
        h:             height in pixels (default 220).
        name:          character name shown in a white rounded tag above the dialog.
        typewriter:    animate text character-by-character (default True).
        chardelay:     delay in ms per character in typewriter mode (default 50).
        bold:          use a thicker black stroke outline for body text (default False).
        pinned:        keep the window always on top of other windows (default True).
        fdst:          destroy window after the user dismisses it (default False, keeps window for reuse).
        overflow_mode: how to handle text exceeding the dialog width:
                       'wrap'    – wrap text to the next line.
                       'overflow' – expand the window so text can render past the dialog boundary (default).
                       'hide'    – clip text at the boundary.

    Usage:
        dokibox.dialogbox("Hello!")
        dokibox.dialogbox("Hello!", name="Sayori", bold=True)
    """
    global _box
    if w is None:
        if _box is not None:
            w = int(_box.root.winfo_screenwidth() * 0.7)
        else:
            root = tk.Tk()
            root.withdraw()
            w = int(root.winfo_screenwidth() * 0.7)
            root.destroy()
    box = _DialogBox(msg, w, h, name, typewriter, chardelay, bold, pinned=pinned, fdst=fdst, overflow_mode=overflow_mode)
    box.root.mainloop()

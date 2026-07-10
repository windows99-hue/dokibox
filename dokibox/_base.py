# -*- coding: utf-8 -*-
"""dokibox internal base class -- window / gradient border / stroked text / dragging"""
import tkinter as tk
import math

# enable per-monitor DPI awareness for correct scaling on high-DPI displays
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


# --- default colors ---
BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"

# --- shared Tk root (NEVER destroyed, for Python 3.9 compat) ---
_root_instance = None


def _get_root():
    global _root_instance
    if _root_instance is None:
        _root_instance = tk.Tk()
        _root_instance.withdraw()
    return _root_instance


class _DokiBase:
    """Dialog base class. Subclasses only need to implement _calc_size / _draw_content / _on_click"""

    BORDER_W = 12

    def __init__(self, msg, title="", pinned=True):
        self.result = None
        self._px = 0
        self._py = 0
        self._ox = 0
        self._oy = 0

        self.root = tk.Toplevel(_get_root())
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', pinned)

        self.w, self.h = self._calc_size(msg)
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
        self._draw_content(msg)

        self.root.bind("<Escape>", lambda e: self._done(False))
        self._make_draggable()
        self.root.focus_force()

    # ========== subclass must implement ==========

    def _calc_size(self, msg):
        raise NotImplementedError

    def _draw_content(self, msg):
        raise NotImplementedError

    def _on_click(self, event):
        pass

    # ========== shared drawing utilities ==========

    @staticmethod
    def _hex_to_rgb(hex_color):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def _draw_gradient_border(self):
        br, bg, bb = self._hex_to_rgb(BORDER_COLOR)
        er, eg, eb = self._hex_to_rgb(BODY_COLOR)
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

    # ========== dragging ==========

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

    # ========== lifecycle ==========

    def _done(self, value):
        self.result = value
        try:
            self.root.destroy()
            _get_root().quit()
        except tk.TclError:
            pass

    @classmethod
    def show(cls, *args, **kwargs):
        dialog = cls(*args, **kwargs)
        _get_root().mainloop()
        return dialog.result

# -*- coding: utf-8 -*-
"""dokibox.choicebox -- DDLC-style multi-choice dialog (floating windows per option)"""
import tkinter as tk
import tkinter.font as tkfont
from typing import Optional, List
from dokibox._base import _get_root

BORDER_COLOR = "#FFBBE3"
BODY_COLOR = "#FEE6F4"
OPT_FILL_COLOR = "#000000"
OPT_HOVER_COLOR = "#999999"

BORDER_W = 12
OPT_FONT_SIZE = 24
OPT_PAD_X = 80
OPT_PAD_Y = 4
OPT_GAP = 40
UNIFIED_MIN_W = 600
MSG_FONT_SIZE = 20
MSG_PAD_Y = 16


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class _Panel:

    def __init__(self, master, text, index, pw, on_select, tooltip=False, pinned=True):
        self.index = index
        self.text = text
        self._on_select = on_select
        self._tooltip = tooltip

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', pinned)

        f_opt = tkfont.Font(family="Microsoft YaHei", size=OPT_FONT_SIZE, weight="normal")
        th = f_opt.metrics('linespace')
        self._font = ("Microsoft YaHei", OPT_FONT_SIZE, "normal")

        self.pw = int(pw)
        self.ph = int(th + OPT_PAD_Y * 2 + BORDER_W * 2)

        self.win.geometry(f"{self.pw}x{self.ph}")

        self.cv = tk.Canvas(self.win, width=self.pw, height=self.ph,
                            bg=BODY_COLOR, highlightthickness=0)
        self.cv.pack()

        self._draw_gradient_border()
        self._draw_option(text)

        self.cv.bind("<Enter>", lambda e: self._set_hover(True))
        self.cv.bind("<Leave>", lambda e: self._set_hover(False))
        self.cv.bind("<Button-1>", lambda e: self._on_select(self.index))

        if self._tooltip:
            self._add_tooltip()

    def _add_tooltip(self):
        tip = [None]

        def show(event):
            if tip[0]:
                return
            tw = tk.Toplevel(self.win)
            tw.overrideredirect(True)
            tw.attributes('-topmost', True)
            label = tk.Label(tw, text=self.text, bg=BODY_COLOR, fg='#000000',
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

        self.cv.bind("<Enter>", show, add='+')
        self.cv.bind("<Leave>", hide, add='+')

    def _draw_gradient_border(self):
        br, bg, bb = _hex_to_rgb(BORDER_COLOR)
        er, eg, eb = _hex_to_rgb(BODY_COLOR)
        bw = BORDER_W
        for i in range(bw):
            t = (i / max(bw - 1, 1)) ** 3
            r = int(br + (er - br) * t)
            g = int(bg + (eg - bg) * t)
            b = int(bb + (eb - bb) * t)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.cv.create_rectangle(i, i, self.pw - i, self.ph - i,
                                     outline=color, width=1)

    def _draw_option(self, text):
        cx = self.pw // 2
        cy = self.ph // 2
        self.cv.create_text(cx, cy, text=text, font=self._font,
                            fill=OPT_FILL_COLOR, anchor="center",
                            tags=("opt", "opt_fill"))

    def _set_hover(self, hover):
        items = self.cv.find_withtag("opt_fill")
        color = OPT_HOVER_COLOR if hover else OPT_FILL_COLOR
        for item in items:
            self.cv.itemconfig(item, fill=color)

    def set_position(self, x, y):
        self.win.geometry(f"+{x}+{y}")

    def destroy(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass


class _ChoiceManager:

    def __init__(self, msg, choices, title, tooltip=False, force=None, pinned=True):
        self.result = None
        self._tooltip = tooltip
        self._force = force
        self._pinned = pinned
        self.root = _get_root()

        f_opt = tkfont.Font(family="Microsoft YaHei", size=OPT_FONT_SIZE, weight="normal")
        opt_widths = [f_opt.measure(c) for c in choices]
        max_opt_w = max(opt_widths) if opt_widths else 0
        unified_w = max(int(max_opt_w + OPT_PAD_X * 2 + BORDER_W * 2), UNIFIED_MIN_W)
        screen_w = self.root.winfo_screenwidth()
        unified_w = min(unified_w, screen_w - BORDER_W * 2)
        self._unified_w = unified_w

        self._panels = []
        for i, choice in enumerate(choices):
            panel = _Panel(self.root, choice, i, unified_w, self._on_select, self._tooltip, pinned=pinned)
            self._panels.append(panel)

        if msg.strip():
            self._create_msg_label(msg)

        self._layout(msg)

        if force is not None and 0 <= force < len(choices):
            self._force_index = force
            p = self._panels[force]
            cx = p.win.winfo_x() + p.pw // 2
            cy = p.win.winfo_y() + p.ph // 2
            self.root.after(50, lambda: p.win.event_generate(
                '<Motion>', warp=True, x=p.pw // 2, y=p.ph // 2))

    def _on_select(self, index):
        self.result = index
        for p in self._panels:
            p.destroy()
        if hasattr(self, '_msg_win'):
            try:
                self._msg_win.destroy()
            except tk.TclError:
                pass
        try:
            _get_root().quit()
        except tk.TclError:
            pass

    def _create_msg_label(self, msg):
        f = tkfont.Font(family="Microsoft YaHei", size=MSG_FONT_SIZE, weight="normal")
        max_lbl_w = max(self._unified_w - 40, 200)

        raw_lines = msg.split('\n')
        wrapped_lines = []
        for line in raw_lines:
            if f.measure(line) <= max_lbl_w:
                wrapped_lines.append(line)
            else:
                current = ""
                for ch in line:
                    test = current + ch
                    if f.measure(test) <= max_lbl_w:
                        current = test
                    else:
                        if current:
                            wrapped_lines.append(current)
                        current = ch
                if current:
                    wrapped_lines.append(current)

        line_h = f.metrics('linespace')
        total_h = line_h * len(wrapped_lines) + MSG_PAD_Y * 2
        text_w = max(f.measure(line) for line in wrapped_lines)

        lbl = tk.Toplevel(self.root)
        lbl.overrideredirect(True)
        lbl.attributes('-topmost', self._pinned)
        self._msg_win = lbl
        self._msg_w = max(int(text_w + 40), self._unified_w)
        self._msg_h = int(total_h)
        lbl.geometry(f"{self._msg_w}x{self._msg_h}")

        cv = tk.Canvas(lbl, width=self._msg_w, height=self._msg_h,
                       bg=BODY_COLOR, highlightthickness=0)
        cv.pack()
        cv.create_rectangle(0, 0, self._msg_w, self._msg_h,
                            outline=BORDER_COLOR, width=4)
        for j, line in enumerate(wrapped_lines):
            y = MSG_PAD_Y + line_h // 2 + j * line_h
            cv.create_text(self._msg_w // 2, y, text=line,
                           font=("Microsoft YaHei", MSG_FONT_SIZE, "normal"),
                           fill="#000000", anchor="center")

    def _layout(self, msg):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        if not self._panels:
            return

        total_h = sum(p.ph for p in self._panels) + OPT_GAP * (len(self._panels) - 1)
        if hasattr(self, '_msg_win'):
            total_h += self._msg_h + OPT_GAP

        start_y = (sh - total_h) // 2

        if hasattr(self, '_msg_win'):
            msg_x = (sw - self._msg_w) // 2
            self._msg_win.geometry(f"+{msg_x}+{start_y}")
            start_y += self._msg_h + OPT_GAP

        for panel in self._panels:
            px = (sw - panel.pw) // 2
            panel.set_position(px, start_y)
            start_y += panel.ph + OPT_GAP


def choicebox(msg: str = "", choices: Optional[List[str]] = None, title: str = "", tooltip: bool = False, force: Optional[int] = None, pinned: bool = True) -> Optional[str]:
    """DDLC-style multi-choice dialog. Each option is a floating window. Returns the selected text, or None if cancelled.

    Args:
        msg:      prompt text displayed above the options. No label shown if empty.
        choices:  list of option strings to display.
        title:    window title (unused in borderless mode).
        tooltip:  show a floating tooltip when hovering over an option.
        force:    pre-select an option by index (0-based). The mouse warps to its center.
        pinned:   keep the windows always on top of other windows.

    Usage:
        import dokibox
        text = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    if not choices:
        return None
    mgr = _ChoiceManager(msg, choices, title, tooltip, force, pinned=pinned)
    _get_root().mainloop()
    return choices[mgr.result] if mgr.result is not None else None

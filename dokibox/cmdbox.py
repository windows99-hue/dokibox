# -*- coding: utf-8 -*-
"""dokibox.cmdbox -- top-left command panel"""
import sys
import ctypes
import subprocess
import io
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QFontMetrics, QTextOption,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QPlainTextEdit,
)

BG_COLOR = "#888888"
TEXT_COLOR = "#ffffff"
FONT_FAMILY = "Consolas"
FONT_SIZE = 16

WIDTH_RATIO = 2.7

DWMWA_BORDER_COLOR = 34
DWMWA_SHADOW_OPACITY = 33


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cxTopHeight", ctypes.c_int),
        ("cxBottomHeight", ctypes.c_int),
    ]


def _remove_dwm_frame(hwnd):
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))


def _remove_window_shadow(hwnd):
    zero_val = ctypes.c_uint(0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd, DWMWA_SHADOW_OPACITY, ctypes.byref(zero_val), ctypes.sizeof(zero_val),
    )


def _wrap_text(text, fm, max_w):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if fm.horizontalAdvance(test) <= max_w:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines if lines else [""]


class _CmdContent(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._panel = None
        self._full_text = ""
        self._visible_count = 0
        self._cursor_visible = True

        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._type_next_char)

        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._toggle_cursor)
        self._cursor_timer.start(500)

        self._font = QFont(FONT_FAMILY, FONT_SIZE)
        self._fm = QFontMetrics(self._font)

    def set_panel(self, panel):
        self._panel = panel

    def set_text(self, text: str):
        self._full_text = text
        self._visible_count = 0
        if text:
            self._typing_timer.start(25)
        else:
            self._typing_timer.stop()
        self._update_geometry()

    def _type_next_char(self):
        if self._visible_count < len(self._full_text):
            self._visible_count += 1
            self._update_geometry()
            self.update()
        else:
            self._typing_timer.stop()

    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    def _wrapped_lines(self):
        max_w = self.width() - 20
        if max_w <= 0:
            max_w = 200
        visible = self._full_text[:self._visible_count]
        prefix_w = self._fm.horizontalAdvance("> ")
        return _wrap_text(visible, self._fm, max(max_w - prefix_w, 40))

    def _line_count(self):
        return max(len(self._wrapped_lines()), 1)

    def sizeHint(self):
        self._fm = QFontMetrics(self._font)
        lh = self._fm.lineSpacing()
        n = self._line_count()
        return QSize(self._fm.horizontalAdvance("> ") + 200, n * lh + 20)

    def minimumSizeHint(self):
        self._fm = QFontMetrics(self._font)
        lh = self._fm.lineSpacing()
        return QSize(self._fm.horizontalAdvance("> ") + 100, lh + 20)

    def _update_geometry(self):
        self.updateGeometry()
        if self._panel:
            self._panel._resize_window()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        painter.setFont(self._font)
        painter.setPen(QColor(TEXT_COLOR))

        self._fm = QFontMetrics(self._font)
        lh = self._fm.lineSpacing()
        base_x = 8
        base_y = 6 + self._fm.ascent()
        prefix_w = self._fm.horizontalAdvance("> ")

        lines = self._wrapped_lines()
        if not lines:
            lines = [""]

        for i, line in enumerate(lines):
            y = int(base_y + i * lh)
            if i == 0:
                painter.drawText(base_x, y, ">")
                painter.drawText(int(base_x + prefix_w), y, line)
            else:
                painter.drawText(base_x, y, line)

        if self._cursor_visible:
            last_line = lines[-1] if lines else ""
            if len(lines) == 1:
                cw = self._fm.horizontalAdvance("> " + last_line)
            else:
                cw = self._fm.horizontalAdvance(last_line)
            cx = 8 + cw + 2
            cy = base_y + (len(lines) - 1) * lh
            painter.drawText(int(cx), int(cy), "_")

        painter.end()


class _CmdPanel(QWidget):

    def __init__(self, pinned=True):
        import dokibox._base as _b
        _b._get_app()
        super().__init__(None)
        self._pinned = pinned
        self._screen = self.screen()
        self._screen_w = self._screen.size().width()
        self._screen_h = self._screen.size().height()

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowOpacity(0.4)

        self._font = QFont(FONT_FAMILY, FONT_SIZE)
        self._fm = QFontMetrics(self._font)
        self._line_h = self._fm.lineSpacing()

        self._cmd_content = _CmdContent()
        self._cmd_content.set_panel(self)

        self._cmd_scroll = QScrollArea()
        self._cmd_scroll.setWidget(self._cmd_content)
        self._cmd_scroll.setWidgetResizable(True)
        self._cmd_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cmd_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._cmd_scroll.setFrameShape(QScrollArea.NoFrame)
        self._cmd_scroll.setStyleSheet(
            "QScrollArea { background: %s; border: none; }"
            "QScrollBar:vertical { background: #555; width: 6px; }"
            "QScrollBar::handle:vertical { background: #aaa; min-height: 16px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }" % BG_COLOR
        )

        self._result_edit = QPlainTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setFrameStyle(0)
        self._result_edit.setFont(self._font)
        self._result_edit.setStyleSheet(
            "QPlainTextEdit { background: %s; color: %s; border: none; padding: 6px 10px; }"
            "QScrollBar:vertical { background: #555; width: 6px; }"
            "QScrollBar::handle:vertical { background: #aaa; min-height: 16px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }" % (BG_COLOR, TEXT_COLOR)
        )
        self._result_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._result_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._result_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._result_edit.document().setDocumentMargin(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._cmd_scroll, 1)
        layout.addWidget(self._result_edit, 2)

        panel_w = int(self._screen_w / WIDTH_RATIO)
        self.setGeometry(0, 0, panel_w, 100)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            _remove_dwm_frame(hwnd)
            _remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass
        self._resize_window()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done()

    def _done(self):
        self.hide()
        self.deleteLater()
        import dokibox.cmdbox as _m
        _m._cmd_panel = None

    def set_cmd(self, text: str):
        self._cmd_content.set_text(text)

    def set_result(self, text: str):
        self._result_edit.setPlainText(text)
        self._resize_window()

    def append_result(self, text: str):
        if text:
            self._result_edit.appendPlainText(text)
        self._resize_window()

    def _resize_window(self):
        panel_w = int(self._screen_w / WIDTH_RATIO)
        max_cmd_h = int(self._screen_h / 3)
        max_result_h = int(self._screen_h * 2 / 3)

        cmd_lines = self._cmd_content._line_count()

        result_lines = 0
        result_max_w = panel_w - 20
        raw_lines = self._result_edit.toPlainText().split('\n')
        for line in raw_lines:
            result_lines += max(len(_wrap_text(line, self._fm, result_max_w)), 1)
        result_lines = max(result_lines, 1)

        cmd_h = min(cmd_lines * self._line_h + 20, max_cmd_h)
        result_h = min(result_lines * self._line_h + 20, max_result_h)
        total_h = max(cmd_h + result_h, 80)

        self.resize(panel_w, total_h)


_cmd_panel = None


def cmdbox(cmd="", result="", runcmd=False, language="python", append=True):
    """Show a gray semi-transparent command panel at top-left corner.

    Parameters:
        cmd:      command string to display (typewriter animation).
        result:   pre-set result text (used as-is unless runcmd=True).
        runcmd:   if True, actually execute cmd and use real output as result.
        language: "python" / "cmd" / "powershell" -- what to run cmd as.
        append:   if True, append result to previous output; False clears first.
    """
    global _cmd_panel
    if _cmd_panel is None:
        _cmd_panel = _CmdPanel()
        _cmd_panel.show()

    actual_result = result
    if runcmd and cmd:
        try:
            if language == "python":
                buf = io.StringIO()
                old_stdout, old_stderr = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = buf, buf
                try:
                    exec(compile(cmd, "<cmdbox>", "exec"))
                finally:
                    sys.stdout, sys.stderr = old_stdout, old_stderr
                actual_result = buf.getvalue()
            elif language == "cmd":
                r = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30,
                )
                actual_result = r.stdout
                if r.stderr:
                    actual_result += r.stderr
            elif language == "powershell":
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd],
                    capture_output=True, text=True, timeout=30,
                )
                actual_result = r.stdout
                if r.stderr:
                    actual_result += r.stderr
        except Exception as e:
            actual_result = str(e)

    _cmd_panel.set_cmd(cmd)

    if append:
        _cmd_panel.append_result(actual_result)
    else:
        _cmd_panel.set_result(actual_result)

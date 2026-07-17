# -*- coding: utf-8 -*-
"""dokibox.cmdbox -- top-left command panel"""
import sys
import ctypes
import subprocess
import io
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QEventLoop
from PySide6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QTextOption, QTextCursor,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QPlainTextEdit,
)

BG_COLOR = "#888888"
BG_ALPHA = 0.4
TEXT_COLOR = "#ffffff"
FONT_FAMILY = "Consolas"
FONT_SIZE = 20

WIDTH_RATIO = 2.7
HEIGHT_RATIO = 3.5

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
        if ch == '\n':
            lines.append(current)
            current = ""
            continue
        test = current + ch
        if fm.horizontalAdvance(test) <= max_w:
            current = test
        else:
            lines.append(current)
            current = ch
    lines.append(current)
    return lines if lines else [""]


class _CmdContent(QWidget):

    typing_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
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

    def set_text(self, text: str):
        self._full_text = text
        self._visible_count = 0
        if text:
            self._typing_timer.start(50)
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
            self.typing_finished.emit()

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

    def paintEvent(self, event):
        painter = QPainter(self)
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
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.StrongFocus)

        self._font = QFont(FONT_FAMILY, FONT_SIZE)

        self._pending_result_text = ""
        self._current_loop = None

        self._cmd_content = _CmdContent()
        self._cmd_content.typing_finished.connect(self._on_typing_finished)

        self._cmd_scroll = QScrollArea()
        self._cmd_scroll.setWidget(self._cmd_content)
        self._cmd_scroll.setWidgetResizable(True)
        self._cmd_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._cmd_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._cmd_scroll.setFrameShape(QScrollArea.NoFrame)
        self._cmd_scroll.viewport().setStyleSheet("background: transparent;")
        self._cmd_scroll.viewport().setAutoFillBackground(False)
        self._cmd_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { background: #555; width: 6px; }"
            "QScrollBar::handle:vertical { background: #aaa; min-height: 16px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )

        self._result_edit = QPlainTextEdit()
        self._result_edit.setReadOnly(True)
        self._result_edit.setFrameStyle(0)
        self._result_edit.setFont(self._font)
        self._result_edit.setStyleSheet(
            "QPlainTextEdit { background: transparent; color: %s; border: none; padding: 6px 10px; }"
            "QScrollBar:vertical { background: #555; width: 6px; }"
            "QScrollBar::handle:vertical { background: #aaa; min-height: 16px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }" % TEXT_COLOR
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
        panel_h = int(self._screen_h / HEIGHT_RATIO)
        self.setGeometry(0, 0, panel_w, panel_h)
        self.setFixedSize(panel_w, panel_h)

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

    def paintEvent(self, event):
        painter = QPainter(self)
        r, g, b = 136, 136, 136
        painter.fillRect(self.rect(), QColor(r, g, b, int(255 * BG_ALPHA)))
        painter.end()

    def _on_typing_finished(self):
        if self._pending_result_text:
            self._append_zero_spaced(self._pending_result_text)
            self._pending_result_text = ""
            self._scroll_result_to_bottom()
        if self._current_loop and self._current_loop.isRunning():
            self._current_loop.quit()

    def _append_zero_spaced(self, text):
        self._result_edit.moveCursor(QTextCursor.End)
        cur = self._result_edit.textCursor()
        fmt = cur.blockFormat()
        fmt.setTopMargin(0)
        fmt.setBottomMargin(0)
        cur.setBlockFormat(fmt)
        if cur.block().text():
            cur.insertBlock(fmt)
        cur.insertText(text)
        self._result_edit.setTextCursor(cur)

    def _scroll_result_to_bottom(self):
        cursor = self._result_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._result_edit.setTextCursor(cursor)
        self._result_edit.ensureCursorVisible()


_cmd_panel = None


def cmdbox(cmd="", result="", runcmd=False, language="python", clear=False):
    """Show a gray semi-transparent command panel at top-left corner.

    Parameters:
        cmd:      command string to display (typewriter animation).
        result:   pre-set result text (used as-is unless runcmd=True).
        runcmd:   if True, actually execute cmd and use real output as result.
        language: "python" / "cmd" / "powershell" -- what to run cmd as.
        clear:    if True, clear all previous results before showing.
    """
    global _cmd_panel
    if _cmd_panel is None:
        _cmd_panel = _CmdPanel()
        _cmd_panel.show()
        _cmd_panel.raise_()
        _cmd_panel.activateWindow()
        _cmd_panel.setFocus()

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

    if clear:
        _cmd_panel._result_edit.clear()

    _cmd_panel._cmd_content.set_text(cmd)
    _cmd_panel._pending_result_text = actual_result
    if not cmd:
        _cmd_panel._on_typing_finished()

    loop = QEventLoop()
    _cmd_panel._current_loop = loop
    _cmd_panel.destroyed.connect(loop.quit)
    loop.exec()


def closecmdbox(delay=0):
    """Close and destroy the cmdbox panel if it exists.

    Args:
        delay: wait this many milliseconds before closing (default 0).
    """
    global _cmd_panel
    if _cmd_panel is not None:
        if delay > 0:
            loop = QEventLoop()
            QTimer.singleShot(delay, loop.quit)
            loop.exec()
        panel = _cmd_panel
        _cmd_panel = None
        panel.hide()
        panel.deleteLater()
        loop = QEventLoop()
        panel.destroyed.connect(loop.quit)
        loop.exec()

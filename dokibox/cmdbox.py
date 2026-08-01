# -*- coding: utf-8 -*-
"""dokibox.cmdbox -- top-left command panel"""
import sys
import ctypes
import subprocess
import io
import threading
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QEventLoop
from PySide6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QTextOption, QTextCursor,
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QPlainTextEdit,
)
from dokibox._base import _get_app, _get_dpi_scale

BG_COLOR = "#333333"
BG_ALPHA = 0.75
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

    def set_text(self, text: str, chardelay=50):
        self._full_text = text
        self._visible_count = 0
        if text:
            self._typing_timer.start(chardelay)
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
        max_w = max(self.width() - 20, 200 if self.width() <= 20 else 40)
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
        indent_x = base_x + prefix_w

        lines = self._wrapped_lines() or [""]

        for i, line in enumerate(lines):
            y = int(base_y + i * lh)
            if i == 0:
                painter.drawText(base_x, y, ">")
                painter.drawText(int(indent_x), y, line)
            else:
                painter.drawText(int(indent_x), y, line)

        if self._cursor_visible:
            last_line = lines[-1]
            if len(lines) == 1:
                cw = self._fm.horizontalAdvance("> " + last_line)
                cx = base_x + cw + 2
            else:
                cw = self._fm.horizontalAdvance(last_line)
                cx = indent_x + cw + 2
            cy = base_y + (len(lines) - 1) * lh
            painter.drawText(int(cx), int(cy), "_")

        painter.end()


class _CmdPanel(QWidget):

    command_finished = Signal(object)

    def __init__(self, pinned=True):
        _get_app()
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

        self._pending_result = ""
        self._pending_command = None
        self._current_loop = None
        self._command_thread = None
        self.command_finished.connect(self._on_command_finished)

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
            "QPlainTextEdit { background: transparent; color: %s; border: none; padding: 6px 0px; }"
            "QScrollBar:vertical { background: #555; width: 6px; }"
            "QScrollBar::handle:vertical { background: #aaa; min-height: 16px; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }" % TEXT_COLOR
        )
        self._result_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._result_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._result_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self._result_edit.document().setDocumentMargin(0)
        self._result_edit.setViewportMargins(
            8 + QFontMetrics(self._font).horizontalAdvance("> "), 0, 0, 0)

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
        color = QColor(BG_COLOR)
        color.setAlpha(int(255 * BG_ALPHA))
        painter.fillRect(self.rect(), color)
        painter.end()

    def _apply_font(self, family, size):
        font = QFont(family, size)
        self._cmd_content._font = font
        self._cmd_content._fm = QFontMetrics(font)
        self._result_edit.setFont(font)
        indent = 8 + QFontMetrics(font).horizontalAdvance("> ")
        self._result_edit.setViewportMargins(indent, 0, 0, 0)
        self._cmd_content.update()

    def _on_typing_finished(self):
        if self._pending_command is not None:
            cmd, language = self._pending_command
            self._pending_command = None
            self._start_command(cmd, language)
            return

        pending = self._pending_result
        if callable(pending):
            try:
                pending = pending()
            except Exception as e:
                pending = str(e)
        if pending:
            self._append_zero_spaced(pending)
            self._scroll_result_to_bottom()
        self._pending_result = ""
        if self._current_loop and self._current_loop.isRunning():
            self._current_loop.quit()

    def _start_command(self, cmd, language):
        def run_command():
            try:
                result = _execute_command(cmd, language)
            except BaseException as exc:
                result = str(exc) or type(exc).__name__
            self.command_finished.emit(result)

        self._command_thread = threading.Thread(target=run_command, daemon=True)
        self._command_thread.start()

    def _on_command_finished(self, result):
        self._command_thread = None
        self._pending_result = result
        self._on_typing_finished()

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


def _execute_command(cmd, language):
    """Execute cmd in the given language and return the result string."""
    if language == "python":
        buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf, buf
        try:
            exec(compile(cmd, "<cmdbox>", "exec"))
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return buf.getvalue()
    elif language == "cmd":
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        result = r.stdout
        if r.stderr:
            result += r.stderr
        return result
    elif language == "powershell":
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=30,
        )
        result = r.stdout
        if r.stderr:
            result += r.stderr
        return result
    return ""


def cmdbox(cmd="", result="", runcmd=False, language="python", clear=False,
           font_family=None, font_size=None, chardelay=50):
    """Show a gray semi-transparent command panel at top-left corner.

    Parameters:
        cmd:         command string to display (typewriter animation).
        result:      result text or callable (if callable, invoked after typing).
        runcmd:      if True, actually execute cmd and use real output as result.
        language:    "python" / "cmd" / "powershell" -- what to run cmd as.
        clear:       if True, clear all previous results before showing.
        font_family: font family name (default Consolas).
        font_size:   font size in points (default 16).
        chardelay:   delay in ms between each character in typewriter (default 50).
    """
    global _cmd_panel
    if _cmd_panel is None:
        _cmd_panel = _CmdPanel()
        _cmd_panel.show()
        _cmd_panel.raise_()
        _cmd_panel.activateWindow()
        _cmd_panel.setFocus()

    if clear:
        _cmd_panel._result_edit.clear()

    ff = font_family or FONT_FAMILY
    dpi_s = 1.0 / _get_dpi_scale()
    fs = int((font_size or FONT_SIZE) * dpi_s)
    _cmd_panel._apply_font(ff, fs)

    _cmd_panel._pending_command = (cmd, language) if runcmd and cmd else None
    _cmd_panel._cmd_content.set_text(cmd, chardelay)
    _cmd_panel._pending_result = result
    if not cmd:
        _cmd_panel._on_typing_finished()
        return

    loop = QEventLoop()
    _cmd_panel._current_loop = loop
    _cmd_panel.destroyed.connect(loop.quit)
    loop.exec()
    _cmd_panel._current_loop = None


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

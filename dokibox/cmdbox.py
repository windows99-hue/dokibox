# -*- coding: utf-8 -*-
"""dokibox.cmdbox -- top-left command panel"""
import sys
import os
import ctypes
import subprocess
import codecs
import io
import locale
import shutil
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
    content_size_changed = Signal()

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
        self.setMinimumHeight(self.sizeHint().height())
        self.updateGeometry()
        self.content_size_changed.emit()

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

    command_output = Signal(str)
    command_finished = Signal()

    def __init__(self, pinned=True):
        _get_app()
        super().__init__(None)
        self._pinned = pinned
        self._screen = self.screen()
        self._screen_w = self._screen.size().width()
        self._screen_h = self._screen.size().height()
        available = self._screen.availableGeometry()
        self._panel_x = available.x()
        self._panel_y = available.y()
        self._panel_w = int(self._screen_w / WIDTH_RATIO)
        self._base_panel_h = int(self._screen_h / HEIGHT_RATIO)
        self._max_panel_h = available.height()
        self._resizing_panel = False

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
        self._stream_started = False
        self.command_output.connect(self._on_command_output)
        self.command_finished.connect(self._on_command_finished)

        self._cmd_content = _CmdContent()
        self._cmd_content.typing_finished.connect(self._on_typing_finished)
        self._cmd_content.content_size_changed.connect(self._update_panel_size)

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
        self._result_edit.document().documentLayout().documentSizeChanged.connect(
            self._update_panel_size)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignTop)
        self._layout.addWidget(self._cmd_scroll)
        self._layout.addWidget(self._result_edit)

        self.setGeometry(self._panel_x, self._panel_y,
                         self._panel_w, self._base_panel_h)
        self.setFixedSize(self._panel_w, self._base_panel_h)
        QTimer.singleShot(0, self._update_panel_size)

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
        self._cmd_content._update_geometry()
        self._update_panel_size()

    def _content_heights(self):
        cmd_min = max(self._cmd_content._fm.lineSpacing() + 20, 32)
        cmd_h = max(self._cmd_content.sizeHint().height(), cmd_min)

        result_fm = QFontMetrics(self._result_edit.font())
        result_min = max(result_fm.lineSpacing() + 12, 32)
        visual_lines = 0
        block = self._result_edit.document().begin()
        while block.isValid():
            block_layout = block.layout()
            visual_lines += max(block_layout.lineCount(), 1) if block_layout else 1
            block = block.next()
        document_h = visual_lines * result_fm.lineSpacing() + 12
        result_h = max(document_h, result_min)
        return cmd_h, result_h, cmd_min, result_min

    def _update_panel_size(self, *args):
        if self._resizing_panel:
            return
        self._resizing_panel = True
        try:
            cmd_h, result_h, cmd_min, result_min = self._content_heights()
            desired_h = cmd_h + result_h
            panel_h = min(max(self._base_panel_h, desired_h), self._max_panel_h)

            if desired_h <= panel_h:
                visible_cmd_h = cmd_h
                visible_result_h = panel_h - visible_cmd_h
            else:
                visible_cmd_h = round(panel_h * cmd_h / desired_h)
                visible_cmd_h = max(
                    cmd_min,
                    min(visible_cmd_h, panel_h - result_min),
                )
                visible_result_h = panel_h - visible_cmd_h

            self._cmd_scroll.setFixedHeight(visible_cmd_h)
            self._result_edit.setFixedHeight(visible_result_h)
            self.setFixedSize(self._panel_w, panel_h)
        finally:
            self._resizing_panel = False

        QTimer.singleShot(0, self._scroll_visible_content_to_bottom)

    def _scroll_visible_content_to_bottom(self):
        cmd_bar = self._cmd_scroll.verticalScrollBar()
        cmd_bar.setValue(cmd_bar.maximum())
        self._scroll_result_to_bottom()

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
                _execute_command(cmd, language, self.command_output.emit)
            except BaseException as exc:
                self.command_output.emit(str(exc) or type(exc).__name__)
            self.command_finished.emit()

        self._stream_started = False
        self._command_thread = threading.Thread(target=run_command, daemon=True)
        self._command_thread.start()

    def _on_command_output(self, text):
        if not text:
            return
        self._result_edit.moveCursor(QTextCursor.End)
        cursor = self._result_edit.textCursor()
        fmt = cursor.blockFormat()
        fmt.setTopMargin(0)
        fmt.setBottomMargin(0)
        cursor.setBlockFormat(fmt)
        if not self._stream_started:
            if cursor.block().text():
                cursor.insertBlock(fmt)
            self._stream_started = True
        cursor.insertText(text)
        self._result_edit.setTextCursor(cursor)
        self._update_panel_size()
        self._scroll_result_to_bottom()

    def _on_command_finished(self):
        self._command_thread = None
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
        self._update_panel_size()

    def _scroll_result_to_bottom(self):
        cursor = self._result_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self._result_edit.setTextCursor(cursor)
        self._result_edit.ensureCursorVisible()


_cmd_panel = None


class _CallbackBinaryStream:
    """Turn byte writes into streamed UTF-8 text for cmdbox."""

    def __init__(self, output_callback):
        self._output_callback = output_callback
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    def write(self, data):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("a bytes-like object is required")
        raw = bytes(data)
        text = self._decoder.decode(raw)
        if text:
            self._output_callback(text)
        return len(raw)

    def flush(self):
        return None

    def writable(self):
        return True

    def isatty(self):
        return False

    def fileno(self):
        raise OSError("cmdbox output has no file descriptor")


class _CallbackTextStream:
    """A small stdout/stderr-compatible stream backed by a callback."""

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, output_callback):
        self._output_callback = output_callback
        self.buffer = _CallbackBinaryStream(output_callback)

    def write(self, text):
        if not isinstance(text, str):
            raise TypeError("write() argument must be str")
        if text:
            self._output_callback(text)
        return len(text)

    def flush(self):
        return None

    def writable(self):
        return True

    def isatty(self):
        return False

    def fileno(self):
        raise OSError("cmdbox output has no file descriptor")


class _ThreadStreamRouter:
    """Delegate a process-global sys stream according to the calling thread."""

    def __init__(self, default_stream):
        object.__setattr__(self, "_default_stream", default_stream)
        object.__setattr__(self, "_local", threading.local())

    def set_thread_stream(self, stream):
        self._local.stream = stream

    def _stream(self):
        return getattr(self._local, "stream", self._default_stream)

    def __getattr__(self, name):
        return getattr(self._stream(), name)

    def write(self, data):
        return self._stream().write(data)

    def flush(self):
        return self._stream().flush()

    def read(self, *args, **kwargs):
        return self._stream().read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self._stream().readline(*args, **kwargs)


_python_stream_lock = threading.Lock()


def _execute_python_in_process(cmd, output_callback):
    """Execute Python in this process while routing only this thread's streams."""
    # sys.stdin/stdout/stderr are process globals.  The temporary routers keep
    # other threads connected to their original streams while this worker gets
    # cmdbox-specific streams.
    with _python_stream_lock:
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        stdin_router = _ThreadStreamRouter(original_stdin)
        stdout_router = _ThreadStreamRouter(original_stdout)
        stderr_router = _ThreadStreamRouter(original_stderr)
        command_output = _CallbackTextStream(output_callback)

        stdin_router.set_thread_stream(io.StringIO(""))
        stdout_router.set_thread_stream(command_output)
        stderr_router.set_thread_stream(command_output)
        sys.stdin = stdin_router
        sys.stdout = stdout_router
        sys.stderr = stderr_router
        try:
            namespace = {
                "__name__": "__main__",
                "__builtins__": __builtins__,
            }
            exec(compile(cmd, "<cmdbox>", "exec"), namespace)
        finally:
            # Restore even when the command assigns to sys.stdout itself or
            # raises SystemExit/KeyboardInterrupt.
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr


def _stream_subprocess(args, output_callback, timeout=30, encoding=None, env=None):
    if encoding is None:
        encoding = locale.getpreferredencoding(False) or "utf-8"
    process = subprocess.Popen(
        args,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        bufsize=-1,
        env=env,
    )
    timed_out = threading.Event()

    def stop_process():
        if process.poll() is None:
            timed_out.set()
            process.kill()

    timeout_timer = threading.Timer(timeout, stop_process)
    timeout_timer.daemon = True
    timeout_timer.start()
    try:
        decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
        read_chunk = getattr(process.stdout, "read1", process.stdout.read)
        while True:
            chunk = read_chunk(4096)
            if not chunk:
                break
            text = decoder.decode(chunk)
            if text:
                output_callback(text)
        remaining = decoder.decode(b"", final=True)
        if remaining:
            output_callback(remaining)
        process.wait()
    finally:
        timeout_timer.cancel()
        if process.stdout is not None:
            process.stdout.close()

    if timed_out.is_set():
        raise subprocess.TimeoutExpired(args, timeout)


def _cmd_subprocess_args(cmd):
    comspec = os.environ.get("COMSPEC") or "cmd.exe"
    utf8_command = f"chcp 65001>nul & {cmd}"
    return [comspec, "/d", "/s", "/c", utf8_command]


def _powershell_subprocess_args(cmd):
    executable = (
        shutil.which("pwsh.exe")
        or shutil.which("pwsh")
        or shutil.which("powershell.exe")
        or shutil.which("powershell")
    )
    if executable is None:
        raise FileNotFoundError("PowerShell executable was not found")
    utf8_command = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "$OutputEncoding = [Console]::OutputEncoding; "
        f"& {{ {cmd}\n}}"
    )
    return [
        executable, "-NoLogo", "-NoProfile", "-NonInteractive",
        "-Command", utf8_command,
    ]


def _execute_command(cmd, language, output_callback=None):
    """Execute cmd in the given language and return the result string."""
    if output_callback is None:
        chunks = []
        output_callback = chunks.append
    else:
        chunks = None

    if language == "python":
        _execute_python_in_process(cmd, output_callback)
    elif language == "cmd":
        _stream_subprocess(
            _cmd_subprocess_args(cmd), output_callback, encoding="utf-8")
    elif language == "powershell":
        args = _powershell_subprocess_args(cmd)
        _stream_subprocess(args, output_callback, encoding="utf-8")
    else:
        raise ValueError(
            "language must be 'python', 'cmd', or 'powershell', "
            f"got {language!r}")

    return "".join(chunks) if chunks is not None else ""


def cmdbox(cmd="", result="", runcmd=False, language="python", clear=False,
           font_family=None, font_size=None, chardelay=50):
    """Show a gray semi-transparent command panel at top-left corner.

    Parameters:
        cmd:         command string to display (typewriter animation).
        result:      result text or callable (if callable, invoked after typing).
        runcmd:      if True, execute cmd and stream its output. Python runs in
                     this process; CMD and PowerShell run in subprocesses.
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

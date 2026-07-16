# -*- coding: utf-8 -*-
"""dokibox.textbox -- long text viewer window (square, side = screen height)"""
import random
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (QPainter, QColor, QFont, QTextOption,
                           QImage, QPixmap, qRgb)
from PySide6.QtWidgets import QTextEdit
from dokibox._base import _DokiBase

BG_COLOR = "#E4E2DD"
TEXT_COLOR = "#000000"
PAD_LEFT = 70
PAD_TOP = 100
PAD_RIGHT = 70
PAD_BOT = 40
TEXT_FONT_SIZE = 22

SCROLLBAR_QSS = """
QTextEdit {
    background: transparent;
    color: %s;
    border: none;
}
QScrollBar:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent, stop:0.42 transparent,
        stop:0.44 #000000, stop:0.56 #000000,
        stop:0.58 transparent, stop:1 transparent);
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: %s;
    border: 1px solid #000000;
    border-radius: 0px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #D5D3CE;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
""" % (TEXT_COLOR, BG_COLOR)

_paper_tile = None


def _get_paper_tile():
    global _paper_tile
    if _paper_tile is not None:
        return _paper_tile
    rng = random.Random(99)
    size = 256
    br, bg, bb = 0xE4, 0xE2, 0xDD
    img = QImage(size, size, QImage.Format_RGB32)
    for y in range(size):
        for x in range(size):
            n = rng.randint(-6, 6)
            w = rng.randint(-2, 2)
            img.setPixel(x, y, qRgb(br + n + w, bg + n, bb + n - w))
    for _ in range(400):
        x = rng.randint(0, size - 1)
        y = rng.randint(0, size - 1)
        d = rng.randint(8, 20)
        img.setPixel(x, y, qRgb(br - d, bg - d, bb - d))
    for _ in range(120):
        x = rng.randint(0, size - 4)
        y = rng.randint(0, size - 1)
        d = rng.randint(4, 10)
        for i in range(rng.randint(2, 4)):
            img.setPixel(x + i, y, qRgb(br - d, bg - d, bb - d))
    _paper_tile = QPixmap.fromImage(img)
    return _paper_tile


class _TextDialog(_DokiBase):

    def __init__(self, msg, font_family=None, font_size=None, delay=400):
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size
        self._delay = max(0, int(delay))
        self._fade = None
        super().__init__(msg, pinned=True)
        self._setup_text(msg)
        self.setWindowOpacity(0.0 if self._delay > 0 else 1.0)

    def showEvent(self, event):
        super().showEvent(event)
        if self._fade is None and self._delay > 0:
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(self._delay)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.setEasingCurve(QEasingCurve.OutCubic)
            self._fade.start()

    def _calc_size(self, msg):
        s = self._dpi_s
        self._pad_left = int(PAD_LEFT * s)
        self._pad_top = int(PAD_TOP * s)
        self._pad_right = int(PAD_RIGHT * s)
        self._pad_bot = int(PAD_BOT * s)
        fs = max(12, int((self._font_size or TEXT_FONT_SIZE) * s))
        self._text_font = QFont(self._font_family, fs)
        side = self.screen().size().height()
        return side, side

    def _setup_text(self, msg):
        self._text = QTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setFont(self._text_font)
        self._text.setPlainText(msg)
        self._text.setLineWrapMode(QTextEdit.WidgetWidth)
        self._text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self._text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._text.setStyleSheet(SCROLLBAR_QSS)
        self._text.setGeometry(
            self._pad_left, self._pad_top,
            self.w - self._pad_left - self._pad_right,
            self.h - self._pad_top - self._pad_bot
        )
        self._text.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        painter.drawTiledPixmap(self.rect(), _get_paper_tile())
        painter.end()

    def _draw_content(self, painter):
        pass

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            self._done(True)


def textbox(msg: str = "", font_family: str = None,
            font_size: int = None, delay: int = 400) -> bool:
    """Long text viewer window. Returns True when closed.

    A square window (side = screen height) centered on the desktop with a
    paper-like background. Long text wraps automatically; a scrollbar appears
    on the right when the text overflows vertically.

    Args:
        msg:         long text to display (supports \\n for multiple lines).
        font_family: custom font family name.
        font_size:   base font size (automatically scaled by DPI).
        delay:       fade-in duration in ms (default 400, 0 disables fade).

    Usage:
        import dokibox
        dokibox.textbox("A very long text...", font_size=18, delay=800)
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _TextDialog.run(msg, font_family=font_family, font_size=font_size,
                           delay=delay)

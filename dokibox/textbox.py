# -*- coding: utf-8 -*-
"""dokibox.textbox -- long text viewer window (square, side = screen height)"""
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QFont, QTextOption
from PySide6.QtWidgets import QTextEdit
from dokibox._base import _DokiBase

BG_COLOR = "#F3F3F3"
TEXT_COLOR = "#000000"
PAD = 40
TEXT_FONT_SIZE = 22

SCROLLBAR_QSS = """
QTextEdit {
    background: %s;
    color: %s;
    border: none;
}
QScrollBar:vertical {
    background: %s;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #C8C8C8;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #A8A8A8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
""" % (BG_COLOR, TEXT_COLOR, BG_COLOR)


class _TextDialog(_DokiBase):

    def __init__(self, msg):
        self._font_family = "Microsoft YaHei"
        self._fade = None
        super().__init__(msg, pinned=True)
        self._setup_text(msg)
        self.setWindowOpacity(0.0)

    def showEvent(self, event):
        super().showEvent(event)
        if self._fade is None:
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(400)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.setEasingCurve(QEasingCurve.OutCubic)
            self._fade.start()

    def _calc_size(self, msg):
        s = self._dpi_s
        self._pad = int(PAD * s)
        fs = max(12, int(TEXT_FONT_SIZE * s))
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
            self._pad, self._pad,
            self.w - self._pad * 2, self.h - self._pad * 2
        )
        self._text.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        painter.end()

    def _draw_content(self, painter):
        pass

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter):
            self._done(True)


def textbox(msg: str = "") -> bool:
    """Long text viewer window. Returns True when closed.

    A square window (side = screen height) centered on the desktop with a
    #F3F3F3 background. Long text wraps automatically; a scrollbar appears
    on the right when the text overflows vertically.

    Args:
        msg: long text to display (supports \\n for multiple lines).

    Usage:
        import dokibox
        dokibox.textbox("A very long text...")
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _TextDialog.run(msg)

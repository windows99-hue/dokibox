# -*- coding: utf-8 -*-
"""dokibox.textbox -- long text viewer window (square, side = screen height)"""
import random
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import (QPainter, QColor, QPen, QFont, QFontMetrics,
                           QTextOption, QImage, QPixmap, qRgb)
from PySide6.QtWidgets import QTextEdit, QScrollBar, QWidget
from dokibox._base import (_DokiBase, _hex_to_rgb, BORDER_COLOR, BODY_COLOR)
from dokibox.ynbox import get_system_locale

BG_COLOR = "#E4E2DD"
TEXT_COLOR = "#000000"
PAD_LEFT = 70
PAD_TOP = 100
PAD_RIGHT = 70
PAD_BOT = 40
TEXT_FONT_SIZE = 24
SBAR_W = 20

_BTN_TEXTS = {
    'zh': "继续",
    'en': "Continue",
    'ja': "続ける",
    'ko': "계속",
    'ru': "Продолжить",
}

TEXT_QSS = """
QTextEdit {
    background: transparent;
    color: %s;
    border: none;
}
"""

SBAR_QSS = """
QScrollBar:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent, stop:0.44 transparent,
        stop:0.45 #000000, stop:0.55 #000000,
        stop:0.56 transparent, stop:1 transparent);
    width: %(sbw)dpx;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: %(bg)s;
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
"""

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


class _ContinueWindow(QWidget):

    BORDER_W = 12
    MARGIN = 10

    def __init__(self, owner, btn_text=None):
        super().__init__(None)
        self._owner = owner
        self._fade = None
        self._text = btn_text if btn_text else _BTN_TEXTS.get(
            get_system_locale(), _BTN_TEXTS['en'])
        flags = Qt.FramelessWindowHint | Qt.Tool
        if owner._pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setCursor(Qt.PointingHandCursor)
        scr = owner.screen().size()
        self.w = scr.height() // 3
        self.h = int(self.w / 2.5)
        self.setGeometry(
            scr.width() - self.w - self.MARGIN,
            scr.height() - self.h - self.MARGIN,
            self.w, self.h
        )
        self.setFixedSize(self.w, self.h)
        fs = max(12, int(self.h * 0.2))
        self._font = QFont(owner._font_family, fs, QFont.Bold)
        self.setWindowOpacity(0.0 if owner._delay > 0 else 1.0)

    def fade_in(self, delay):
        if self._fade is None and delay > 0:
            self._fade = QPropertyAnimation(self, b"windowOpacity", self)
            self._fade.setDuration(delay)
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.setEasingCurve(QEasingCurve.OutCubic)
            self._fade.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BODY_COLOR))
        br, bg, bb = _hex_to_rgb(BORDER_COLOR)
        er, eg, eb = _hex_to_rgb(BODY_COLOR)
        bw = max(self.BORDER_W, 8)
        for i in range(bw):
            t = (i / max(bw - 1, 1)) ** 3
            p.setPen(QPen(QColor(
                int(br + (er - br) * t),
                int(bg + (eg - bg) * t),
                int(bb + (eb - bb) * t),
            ), 1))
            p.drawRect(i, i, self.w - i * 2, self.h - i * 2)
        p.setFont(self._font)
        fm = QFontMetrics(self._font)
        x = self.w // 2 - fm.horizontalAdvance(self._text) // 2
        y = self.h // 2 + fm.ascent() - fm.height() // 2
        p.setPen(QColor(TEXT_COLOR))
        p.drawText(int(x), int(y), self._text)
        p.end()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._owner._done(True)

    def closeEvent(self, event):
        event.accept()
        if self._owner is not None:
            self._owner._done(True)


class _TextDialog(_DokiBase):

    SYSTEM_CLOSE_RESULT = True

    def __init__(self, msg, font_family=None, font_size=None, delay=400,
                 okbtn=True, btn_text=None, pinned=True):
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size
        self._delay = max(0, int(delay))
        self._okbtn = bool(okbtn)
        self._btn_text = btn_text
        self._pinned = bool(pinned)
        self._fade = None
        self._cont = None
        super().__init__(msg, pinned=pinned)
        self._setup_text(msg)
        if self._okbtn:
            self._cont = _ContinueWindow(self, btn_text=btn_text)
        self.setWindowOpacity(0.0 if self._delay > 0 else 1.0)

    def showEvent(self, event):
        super().showEvent(event)
        vsb = self._text.verticalScrollBar()

        def _refresh():
            self._sync_range(vsb.minimum(), vsb.maximum())
            self._position_sbar()
        _refresh()
        QTimer.singleShot(0, _refresh)
        if self._cont is not None and not self._cont.isVisible():
            self._cont.show()
            self._cont.fade_in(self._delay)
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
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._text.setStyleSheet(TEXT_QSS % TEXT_COLOR)
        self._text.setGeometry(
            self._pad_left, self._pad_top,
            self.w - self._pad_left - self._pad_right,
            self.h - self._pad_top - self._pad_bot
        )
        self._text.setFocus()
        self._setup_scrollbar()

    def _setup_scrollbar(self):
        sb_w = max(8, int(SBAR_W * self._dpi_s))
        self._sbar = QScrollBar(Qt.Vertical, self)
        self._sbar.setStyleSheet(SBAR_QSS % {"sbw": sb_w, "bg": BG_COLOR})
        doc_m = int(self._text.document().documentMargin())
        x = (2 * self.w - self._pad_right - doc_m - sb_w) // 2
        self._sbar.setGeometry(
            x, self._pad_top, sb_w,
            self.h - self._pad_top - self._pad_bot
        )
        self._sbar.setVisible(False)
        vsb = self._text.verticalScrollBar()
        vsb.rangeChanged.connect(self._sync_range)
        vsb.valueChanged.connect(self._sbar.setValue)
        self._sbar.valueChanged.connect(vsb.setValue)
        self._sync_range(vsb.minimum(), vsb.maximum())

    def _position_sbar(self):
        sb_w = self._sbar.width()
        doc_m = self._text.document().documentMargin()
        limit = self.w - self._pad_right - int(doc_m)
        max_w = self._compute_max_line_width()
        if max_w > 0:
            text_right = self._pad_left + int(doc_m + max_w)
            cap = QFontMetrics(self._text_font).height()
            text_right = max(min(text_right, limit), limit - cap)
        else:
            text_right = limit
        x = (text_right + self.w - sb_w) // 2
        self._sbar.move(x, self._pad_top)

    def _compute_max_line_width(self):
        max_w = 0.0
        block = self._text.document().begin()
        while block.isValid():
            lay = block.layout()
            if lay is not None:
                for i in range(lay.lineCount()):
                    lw = lay.lineAt(i).naturalTextWidth()
                    if lw > max_w:
                        max_w = lw
            block = block.next()
        return max_w

    def _sync_range(self, mn, mx):
        vsb = self._text.verticalScrollBar()
        self._sbar.setRange(mn, mx)
        self._sbar.setPageStep(vsb.pageStep())
        self._sbar.setSingleStep(vsb.singleStep())
        self._sbar.setValue(vsb.value())
        self._sbar.setVisible(mx > mn)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BG_COLOR))
        painter.drawTiledPixmap(self.rect(), _get_paper_tile())
        painter.end()

    def _draw_content(self, painter):
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done(True)
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter) and self._okbtn:
            self._done(True)

    def _done(self, value):
        if self._cont is not None:
            self._cont.hide()
            self._cont.deleteLater()
            self._cont = None
        super()._done(value)


def textbox(msg: str = "", font_family: str = None,
            font_size: int = None, delay: int = 400,
            okbtn: bool = True, btn_text: str = None,
            pinned: bool = True) -> bool:
    """Long text viewer window. Returns True when closed.

    A square window (side = screen height) centered on the desktop with a
    paper-like background. Long text wraps automatically; a scrollbar appears
    on the right when the text overflows vertically.

    Args:
        msg:         long text to display (supports \\n for multiple lines).
        font_family: custom font family name.
        font_size:   base font size (automatically scaled by DPI).
        delay:       fade-in duration in ms (default 400, 0 disables fade).
        okbtn:       show the "continue" button at the bottom-right corner.
                     If False, the window can only be closed with Esc.
        btn_text:    custom text for the continue button.
                     Auto-detected from system language if None.
        pinned:      keep the window always on top of other windows.

    Usage:
        import dokibox
        dokibox.textbox("A very long text...", font_size=18, okbtn=False,
                        btn_text="点击继续", pinned=False)
    """
    from dokibox.dialogbox import _destroy_box
    _destroy_box()
    return _TextDialog.run(msg, font_family=font_family, font_size=font_size,
                           delay=delay, okbtn=okbtn, btn_text=btn_text,
                           pinned=pinned)

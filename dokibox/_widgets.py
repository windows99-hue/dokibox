# -*- coding: utf-8 -*-
"""dokibox shared widget drawing utilities -- text wrapping, stroked buttons, stroked text"""
import math
from typing import List

from PySide6.QtGui import QColor, QFontMetrics, QPainter, QFont


def text_wrap(text: str, font: QFont, max_w: int) -> List[str]:
    """Wrap a string into lines that fit within max_w when rendered with font."""
    raw_lines = text.split('\n')
    wrapped = []
    fm = QFontMetrics(font)
    for line in raw_lines:
        if fm.horizontalAdvance(line) <= max_w:
            wrapped.append(line)
            continue
        current = ""
        for ch in line:
            test = current + ch
            if fm.horizontalAdvance(test) <= max_w:
                current = test
            else:
                if current:
                    wrapped.append(current)
                current = ch
        if current:
            wrapped.append(current)
    return wrapped


def wrap_line_single(text: str, fm: QFontMetrics, max_w: int) -> List[str]:
    """Wrap a single line (no newlines) into multiple lines."""
    if fm.horizontalAdvance(text) <= max_w:
        return [text]
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        if fm.horizontalAdvance(test) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_stroked_button(painter: QPainter, x: int, y: int, text: str,
                        font: QFont, stroke_w: int,
                        hover: bool = False,
                        fill_color: str = "#ffffff",
                        hover_color: str = "#ffd0e8",
                        stroke_color: str = "#BD539D") -> tuple:
    """Draw stroked button text and return its bounding rect (rx, ry, rw, rh)."""
    painter.setFont(font)
    fm = QFontMetrics(font)
    tw = fm.horizontalAdvance(text)
    text_x = int(x - tw // 2)
    text_y = int(y + fm.ascent() - fm.height() // 2)

    fill_rgb = QColor(hover_color if hover else fill_color)
    stroke_rgb = QColor(stroke_color)

    for step in range(48):
        angle = 2 * math.pi * step / 36
        dx = int(stroke_w * math.cos(angle))
        dy = int(stroke_w * math.sin(angle))
        painter.setPen(stroke_rgb)
        painter.drawText(text_x + dx, text_y + dy, text)

    painter.setPen(fill_rgb)
    painter.drawText(text_x, text_y, text)

    br = fm.boundingRect(text)
    return (text_x - 15, text_y + br.top() - 10, tw + 30, fm.height() + 20)


def draw_stroked_text_centered(painter: QPainter, x: int, y: int, text: str,
                               font: QFont, fill_color: str, stroke_color: str,
                               stroke_w: int):
    """Draw stroked text centered at (x, y)."""
    painter.setFont(font)
    fm = QFontMetrics(font)
    tw = fm.horizontalAdvance(text)
    th = fm.height()
    text_x = int(x - tw // 2)
    text_y = int(y + fm.ascent() - th // 2)
    _draw_stroked(painter, text_x, text_y, text, stroke_color, fill_color, stroke_w)


def draw_stroked_text_left(painter: QPainter, x: int, y: int, text: str,
                           font: QFont, fill_color: str, stroke_color: str,
                           stroke_w: int):
    """Draw stroked text left-aligned at (x, y)."""
    painter.setFont(font)
    fm = QFontMetrics(font)
    text_y = int(y + fm.ascent() - fm.height() // 2)
    _draw_stroked(painter, int(x), text_y, text, stroke_color, fill_color, stroke_w)


def _draw_stroked(painter: QPainter, text_x: int, text_y: int, text: str,
                  stroke_color: str, fill_color: str, stroke_w: int):
    for step in range(48):
        angle = 2 * math.pi * step / 24
        dx = int(stroke_w * math.cos(angle))
        dy = int(stroke_w * math.sin(angle))
        painter.setPen(QColor(stroke_color))
        painter.drawText(text_x + dx, text_y + dy, text)
    painter.setPen(QColor(fill_color))
    painter.drawText(text_x, text_y, text)

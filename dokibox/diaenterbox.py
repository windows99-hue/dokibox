# -*- coding: utf-8 -*-
"""dokibox.diaenterbox -- DDLC-style bottom dialog with text input (no msg, user types directly)"""
import math
import sys
import ctypes
from typing import Optional, Union, List
from PySide6.QtCore import (
    Qt, QTimer, QEventLoop, QRectF, QPointF, Signal,
    QPropertyAnimation, QVariantAnimation, QEasingCurve,
    QParallelAnimationGroup, Property, QRect,
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath, QLinearGradient,
    QPixmap,
)
from PySide6.QtWidgets import QWidget, QApplication, QLineEdit
from dokibox._base import _get_app, _get_dpi_scale


BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#FFDEEF"
FADE_TO = "#FFFFFF"
CORNER_RADIUS = 18
INSET = 3

DOT_RADIUS = 13
DOT_GAP_X = 35
DOT_GAP_Y = 6
DOT_COLOR = "#FB94C1"

DWMWA_BORDER_COLOR = 34
DWMWA_SHADOW_OPACITY = 33

SPRITE_BASE_HEIGHT_RATIO = 0.95
SPRITE_SPEAKER_SCALE = 1.10
SPRITE_SILENT_SCALE = 1.0
SPRITE_SILENT_OPACITY = 1.0
SPRITE_ANIM_DURATION = 220
SPRITE_FADE_DURATION = 180

INPUT_BG = "#FFF0F7"
INPUT_BORDER = "#FFBBE3"
INPUT_FOCUS = "#CF80B5"
INPUT_TEXT = "#000000"
INPUT_H = 44


def _hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _blend(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 * t + r2 * (1 - t))
    g = int(g1 * t + g2 * (1 - t))
    b = int(b1 * t + b2 * (1 - t))
    return QColor(r, g, b)


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cxTopHeight", ctypes.c_int),
        ("cxBottomHeight", ctypes.c_int),
    ]


def remove_dwm_frame(hwnd):
    margins = MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))


def remove_window_shadow(hwnd):
    zero_val = ctypes.c_uint(0)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        hwnd,
        DWMWA_SHADOW_OPACITY,
        ctypes.byref(zero_val),
        ctypes.sizeof(zero_val)
    )


_enter_box = None


def _normalize_sprites(sprites):
    if sprites is None:
        return []
    if isinstance(sprites, (str, bytes)):
        return [sprites]
    return list(sprites)


def _normalize_sprite_pos(sprite_pos, count, allow_cover=False):
    if count == 0:
        return []
    if sprite_pos is None:
        if count == 1:
            result = [0.5]
        elif count == 2:
            result = [0.25, 0.75]
        elif count == 3:
            result = [0.25, 0.50, 0.75]
        elif count == 4:
            result = [0.12, 0.37, 0.63, 0.88]
        else:
            result = [i / max(count - 1, 1) for i in range(count)]
        if isinstance(allow_cover, list) and len(allow_cover) >= count:
            pos_indices = []
            pos_values = []
            for i in range(count):
                if not allow_cover[i]:
                    pos_indices.append(i)
                    pos_values.append(result[i])
            if pos_values and len(pos_values) > 1:
                resolved = _resolve_overlapping_positions(pos_values)
                for idx, val in enumerate(resolved):
                    result[pos_indices[idx]] = val
        elif not allow_cover:
            result = _resolve_overlapping_positions(result)
        return result
    if isinstance(sprite_pos, (str, float, int)):
        pos_list = [sprite_pos]
    else:
        pos_list = list(sprite_pos)
    result = []
    for i, p in enumerate(pos_list):
        if isinstance(p, str):
            p_lower = p.strip().lower()
            if p_lower == "left":
                result.append(0.25)
            elif p_lower == "center":
                result.append(0.50)
            elif p_lower == "right":
                result.append(0.75)
            else:
                result.append(float(p))
        else:
            result.append(float(p))
    while len(result) < count:
        result.append(0.5 + (len(result) - count / 2) * 0.1)
    result = result[:count]

    if isinstance(allow_cover, list) and len(allow_cover) >= count:
        pos_indices = []
        pos_values = []
        for i in range(count):
            if not allow_cover[i]:
                pos_indices.append(i)
                pos_values.append(result[i])
        if pos_values and len(pos_values) > 1:
            resolved = _resolve_overlapping_positions(pos_values)
            for idx, val in enumerate(resolved):
                result[pos_indices[idx]] = val
    elif not allow_cover:
        result = _resolve_overlapping_positions(result)
    return result


def _resolve_overlapping_positions(positions):
    n = len(positions)
    if n <= 1:
        return positions[:]

    rounded = [round(p, 4) for p in positions]
    if len(set(rounded)) == n:
        return positions[:]

    indexed = sorted(enumerate(positions), key=lambda x: (x[1], x[0]))

    groups = []
    i = 0
    while i < n:
        pos = indexed[i][1]
        j = i + 1
        while j < n and round(indexed[j][1], 4) == round(pos, 4):
            j += 1
        groups.append((pos, [indexed[k] for k in range(i, j)]))
        i = j

    if len(groups) == 1:
        MARGIN = 0.2
        usable = 1.0 - 2 * MARGIN
        targets = [MARGIN + i / max(n - 1, 1) * usable for i in range(n)]
        result = [0.0] * n
        for i, (idx, _) in enumerate(indexed):
            result[idx] = targets[i]
        return result

    INNER_GAP = 0.18
    MIN_GAP = 0.08

    result = [0.0] * n

    for pos, members in groups:
        count = len(members)
        if count == 1:
            idx, _ = members[0]
            result[idx] = pos
        else:
            total_w = (count - 1) * INNER_GAP
            for k, (idx, _) in enumerate(members):
                t = k / max(count - 1, 1)
                result[idx] = pos - total_w / 2 + t * total_w

    idx_to_group = {}
    for gi, (_, members) in enumerate(groups):
        for idx, _ in members:
            idx_to_group[idx] = gi

    def _push_apart(positions):
        for _ in range(100):
            sorted_pairs = sorted(enumerate(positions), key=lambda x: x[1])
            changed = False
            for k in range(n - 1):
                a, va = sorted_pairs[k]
                b, vb = sorted_pairs[k + 1]
                if idx_to_group[a] == idx_to_group[b]:
                    continue
                gap = vb - va
                if gap < MIN_GAP:
                    push = (MIN_GAP - gap) / 2
                    positions[a] = max(0.04, va - push)
                    positions[b] = min(0.96, vb + push)
                    changed = True
            if not changed:
                break

    _push_apart(result)

    return result


def _load_pixmap(data):
    if isinstance(data, bytes):
        pix = QPixmap()
        pix.loadFromData(data)
    elif isinstance(data, QPixmap):
        return data
    else:
        pix = QPixmap(data)
    if pix.isNull():
        if isinstance(data, bytes):
            raise ValueError("Cannot load sprite image from bytes data")
        else:
            raise FileNotFoundError(f"Cannot load sprite image: {data!r}")
    return pix


class Avatar:
    """Character avatar definition with name and emotion image sets."""

    def __init__(self, name, emotes):
        self.name = name
        self.emotes = emotes

    def __call__(self, position, emote, animation=None, width=None, height=None,
                 sprite_allow_cover=False):
        images = self.emotes.get(emote)
        if images is None:
            raise ValueError(
                f"Emote '{emote}' not found for avatar '{self.name}'. "
                f"Available: {list(self.emotes.keys())}"
            )
        if isinstance(images, str):
            images = [images]
        return _SpriteSlot(self, position, images, animation=animation, width=width, height=height,
                           allow_cover=sprite_allow_cover)

    def hide(self):
        return _HideSlot(self)


class _SpriteSlot:
    __slots__ = ("avatar", "position", "images", "animation", "width", "height", "allow_cover")

    def __init__(self, avatar, position, images, animation=None, width=None, height=None,
                 allow_cover=False):
        self.avatar = avatar
        self.position = position
        self.images = images
        self.animation = animation
        self.width = width
        self.height = height
        self.allow_cover = allow_cover


class _HideSlot:
    __slots__ = ("avatar",)

    def __init__(self, avatar):
        self.avatar = avatar


def _composite_sprite_pixmaps(images):
    pixmaps = []
    max_w = 0
    max_h = 0
    for img in images:
        pix = _load_pixmap(img)
        pixmaps.append(pix)
        max_w = max(max_w, pix.width())
        max_h = max(max_h, pix.height())
    if len(pixmaps) == 1:
        return pixmaps[0]
    composite = QPixmap(max_w, max_h)
    composite.fill(QColor(0, 0, 0, 0))
    painter = QPainter(composite)
    for pix in pixmaps:
        x = (max_w - pix.width()) // 2
        y = max_h - pix.height()
        painter.drawPixmap(x, y, pix)
    painter.end()
    return composite


class _SpriteWindow(QWidget):

    def __init__(self, image_data, x_frac, is_speaker, pinned):
        super().__init__(None)
        self._x_frac = x_frac
        self._is_speaker = is_speaker
        self._pinned = pinned
        self._opacity_val = 0.0
        self._anim_timer = None
        self._fade_timer = None
        self._avatar = None
        self._width_override = None
        self._height_override = None
        self._offset_y = 0.0
        self._offset_anim = None

        self._pixmap = _load_pixmap(image_data)
        self._pixmap_source = image_data

        self._anim_scale = SPRITE_SPEAKER_SCALE if is_speaker else SPRITE_SILENT_SCALE

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._apply_geometry(animate=False)
        self.show()
        self._start_fade_in()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            remove_dwm_frame(hwnd)
            remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def _compute_base_wh(self):
        screen = QApplication.primaryScreen()
        sh = screen.size().height()
        sw = screen.size().width()
        pw = self._pixmap.width()
        ph = self._pixmap.height()

        both_overrides = (self._width_override is not None and self._height_override is not None)

        if both_overrides:
            return self._width_override, self._height_override

        if self._height_override is not None:
            base_h = self._height_override
        else:
            base_h = int(sh * SPRITE_BASE_HEIGHT_RATIO)

        if ph > 0:
            base_w = int(base_h * pw / ph)
        else:
            base_w = base_h

        if self._width_override is not None:
            base_w = self._width_override

        if pw > 0 and self._width_override is None and base_w > sw * 0.5:
            base_w = int(sw * 0.5)
            if ph > 0:
                base_h = int(base_w * ph / pw)

        return base_w, base_h

    def _compute_max_geometry(self):
        base_w, base_h = self._compute_base_wh()
        screen = QApplication.primaryScreen()
        sw = screen.size().width()
        sh = screen.size().height()

        w = int(base_w * SPRITE_SPEAKER_SCALE)
        h = int(base_h * SPRITE_SPEAKER_SCALE)
        x = int(sw * self._x_frac - w // 2)
        x = max(-w // 2, min(x, sw - w // 2))
        y = sh - h
        return QRect(x, y, w, h)

    def _apply_geometry(self, animate=True):
        target_geom = self._compute_max_geometry()
        target_scale = SPRITE_SPEAKER_SCALE if self._is_speaker else SPRITE_SILENT_SCALE
        target_opacity = 1.0 if self._is_speaker else SPRITE_SILENT_OPACITY

        if animate and self.isVisible():
            if self._anim_timer is not None:
                self._anim_timer.stop()
                self._anim_timer.deleteLater()
                self._anim_timer = None
            if self._fade_timer is not None:
                self._fade_timer.stop()
                self._fade_timer.deleteLater()
                self._fade_timer = None

            start_geom = self.geometry()
            start_scale = self._anim_scale
            start_opacity = self._opacity_val
            geom_changed = (start_geom != target_geom)

            num_ticks = SPRITE_ANIM_DURATION // 10
            easing = QEasingCurve(QEasingCurve.OutCubic)
            tick = [0]

            self._anim_timer = QTimer(self)
            self._anim_timer.setInterval(10)

            sx = start_geom.x()
            sy = start_geom.y()
            sw_val = start_geom.width()
            sh_val = start_geom.height()
            tx = target_geom.x()
            ty = target_geom.y()
            tw = target_geom.width()
            th = target_geom.height()

            def on_tick():
                progress = tick[0] / max(num_ticks - 1, 1)
                t = easing.valueForProgress(min(progress, 1.0))
                if geom_changed:
                    self.setGeometry(
                        int(sx + (tx - sx) * t),
                        int(sy + (ty - sy) * t),
                        int(sw_val + (tw - sw_val) * t),
                        int(sh_val + (th - sh_val) * t),
                    )
                self._anim_scale = start_scale + (target_scale - start_scale) * t
                self._opacity_val = start_opacity + (target_opacity - start_opacity) * t
                self.repaint()
                tick[0] += 1
                if tick[0] >= num_ticks:
                    if geom_changed:
                        self.setGeometry(target_geom)
                    self._anim_scale = target_scale
                    self._opacity_val = target_opacity
                    self.repaint()
                    self._anim_timer.stop()
                    self._anim_timer.deleteLater()
                    self._anim_timer = None

            self._anim_timer.timeout.connect(on_tick)
            self._anim_timer.start()
        else:
            self.setGeometry(target_geom)
            self._anim_scale = target_scale
            self.update()

    def _start_fade_in(self):
        target = 1.0 if self._is_speaker else SPRITE_SILENT_OPACITY
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer.deleteLater()
            self._fade_timer = None

        num_ticks = SPRITE_FADE_DURATION // 10
        easing = QEasingCurve(QEasingCurve.OutCubic)
        tick = [0]

        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(10)

        def on_tick():
            progress = tick[0] / max(num_ticks - 1, 1)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = target * t
            self.repaint()
            tick[0] += 1
            if tick[0] >= num_ticks:
                self._opacity_val = target
                self.repaint()
                self._fade_timer.stop()
                self._fade_timer.deleteLater()
                self._fade_timer = None

        self._fade_timer.timeout.connect(on_tick)
        self._fade_timer.start()

    def update_state(self, image_data=None, x_frac=None, is_speaker=None):
        changed = False
        if image_data is not None:
            if self._offset_anim is not None:
                self._offset_anim.stop()
                self._offset_anim.deleteLater()
                self._offset_anim = None
            self._offset_y = 0.0
            self._pixmap = _load_pixmap(image_data)
            self._pixmap_source = image_data
            changed = True
        if x_frac is not None:
            self._x_frac = x_frac
            changed = True
        if is_speaker is not None:
            self._is_speaker = is_speaker
            changed = True
        if changed:
            self._apply_geometry(animate=True)

    def get_opacity(self):
        return self._opacity_val

    def set_opacity(self, val):
        self._opacity_val = val
        self.update()

    opacity = Property(float, get_opacity, set_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(self._opacity_val)

        ratio = self._anim_scale / SPRITE_SPEAKER_SCALE

        w = self.width()
        h = self.height()
        paint_w = int(w * ratio)
        paint_h = int(h * ratio)
        ox = (w - paint_w) // 2
        oy = h - paint_h + int(self._offset_y)

        scaled = self._pixmap.scaled(paint_w, paint_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        sx = ox + (paint_w - scaled.width()) // 2
        sy = oy + paint_h - scaled.height()
        painter.drawPixmap(sx, sy, scaled)
        painter.end()

    def destroy_sprite(self):
        try:
            if self._anim_timer is not None:
                self._anim_timer.stop()
                self._anim_timer.deleteLater()
                self._anim_timer = None
            if self._fade_timer is not None:
                self._fade_timer.stop()
                self._fade_timer.deleteLater()
                self._fade_timer = None
            if self._offset_anim is not None:
                self._offset_anim.stop()
                self._offset_anim.deleteLater()
                self._offset_anim = None

            num_ticks = SPRITE_FADE_DURATION // 10
            easing = QEasingCurve(QEasingCurve.OutCubic)
            start_opacity = self._opacity_val
            tick = [0]

            timer = QTimer(self)
            timer.setInterval(10)

            def on_tick():
                progress = tick[0] / max(num_ticks - 1, 1)
                t = easing.valueForProgress(min(progress, 1.0))
                self._opacity_val = start_opacity * (1.0 - t)
                self.repaint()
                tick[0] += 1
                if tick[0] >= num_ticks:
                    self._opacity_val = 0.0
                    self.repaint()
                    timer.stop()
                    timer.deleteLater()
                    self.hide()
                    self.deleteLater()

            timer.timeout.connect(on_tick)
            timer.start()
        except Exception:
            pass

    def _instant_destroy(self):
        try:
            if self._anim_timer is not None:
                self._anim_timer.stop()
                self._anim_timer.deleteLater()
                self._anim_timer = None
            if self._fade_timer is not None:
                self._fade_timer.stop()
                self._fade_timer.deleteLater()
                self._fade_timer = None
            if self._offset_anim is not None:
                self._offset_anim.stop()
                self._offset_anim.deleteLater()
                self._offset_anim = None
            self.hide()
            self.deleteLater()
        except Exception:
            pass

    def _get_offset_y(self):
        return self._offset_y

    def _set_offset_y(self, val):
        self._offset_y = val
        self.repaint()

    anim_offset_y = Property(float, _get_offset_y, _set_offset_y)

    def _play_animation(self, anim_type):
        if self._offset_anim is not None:
            self._offset_anim.stop()
            self._offset_anim.deleteLater()
            self._offset_anim = None

        if anim_type is None:
            if abs(self._offset_y) > 0.5:
                anim = QPropertyAnimation(self, b"anim_offset_y")
                self._offset_anim = anim
                anim.setDuration(300)
                anim.setEasingCurve(QEasingCurve.InOutCubic)
                anim.setStartValue(self._offset_y)
                anim.setEndValue(0.0)
                anim.start()
            return

        anim = QPropertyAnimation(self, b"anim_offset_y")
        self._offset_anim = anim

        if anim_type == "shocked":
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.OutBounce)
            anim.setStartValue(self._offset_y)
            anim.setKeyValueAt(0.12, -65.0)
            anim.setEndValue(0.0)
        elif anim_type in ("sad", "thanks"):
            anim.setDuration(900)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setStartValue(self._offset_y)
            anim.setEndValue(35.0)

        anim.start()


class _InputLineEdit(QLineEdit):

    escapePressed = Signal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.escapePressed.emit()
            return
        super().keyPressEvent(event)


class _DiaEnterBox(QWidget):

    dismissed = Signal()

    def __init__(self, w, h, name=None, pinned=True, fdst=False,
                 font_family=None, font_size=None, transparent=True, glare=True,
                 sprites=None, sprite_pos=None, speaker_idx=None,
                 sprite_allow_cover=False, sprite_allow_cover_list=None,
                 default="", max_length=None):
        global _enter_box

        _get_app()
        super().__init__(None)

        self.result = None
        self.w = w
        self.h = h
        self._name = name
        self._fdst = fdst
        self._pinned = pinned
        self._transparent = transparent
        self._glare = glare
        self._sprites = []
        self._sprite_allow_cover = sprite_allow_cover
        self._sprite_allow_cover_list = sprite_allow_cover_list

        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size or 20

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        self._body_fs = max(12, int(self._font_size * s))
        self._name_fs = max(12, int(self._font_size * s))
        self._pad_x = int(40 * s)
        self._name_pad_val = int(28 * s)
        self._dot_radius = int(DOT_RADIUS * s)
        self._dot_gap_x = int(DOT_GAP_X * s)
        self._dot_gap_y = int(DOT_GAP_Y * s)
        self._corner_radius = max(8, int(CORNER_RADIUS * s))
        self._inset = max(2, int(INSET * s))
        self._triangle_s = int(16 * s)
        self.r = self._corner_radius

        self._input_h = max(28, int(INPUT_H * s))

        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_pad = self._name_pad_val
        name_h = fm.lineSpacing() + name_pad
        if name:
            tw = fm.horizontalAdvance(name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

        cv_h = name_h + int(30 * s) + h + self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = w + self._inset * 2
        self._canvas_w = canvas_w
        self._dialog_left = (canvas_w - w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        dialog_screen_y = sh - h - 60
        win_y = dialog_screen_y - self._dialog_top

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        self.show()

        _enter_box = self

        self._init_sprites(sprites, sprite_pos, speaker_idx)
        self._setup_input(default, max_length)

        self.setFocusProxy(self._input)
        QApplication.processEvents()
        self.raise_()
        self.activateWindow()


    def _setup_input(self, default, max_length):
        input_w = self.w - self._pad_x * 2
        input_x = self._dialog_left + self._pad_x
        input_y = self._dialog_top + (self.h - self._input_h) // 2

        self._input = _InputLineEdit(self)
        self._input.setText(default)
        font = QFont(self._font_family, self._body_fs, QFont.Bold)
        self._input.setFont(font)
        self._input.setGeometry(int(input_x), int(input_y), int(input_w), int(self._input_h))
        self._input.setStyleSheet(
            "border: none; padding: 5px 10px;"
            f"background-color: {INPUT_BG};"
            f"color: {INPUT_TEXT};"
            f"border-radius: {max(4, int(8 / _get_dpi_scale()))}px;"
        )
        if max_length is not None:
            self._input.setMaxLength(max_length)
        self._input.returnPressed.connect(self._submit)
        self._input.escapePressed.connect(self._cancel)

    def _init_sprites(self, sprites, sprite_pos, speaker_idx):
        raw = _normalize_sprites(sprites)
        count = len(raw)
        if count == 0:
            return
        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, count, allow_cover)
        for i in range(count):
            is_speaker = (i == speaker_idx)
            sw = _SpriteWindow(raw[i], positions[i], is_speaker, self._pinned)
            self._sprites.append(sw)

    def _update_sprites(self, sprites, sprite_pos, speaker_idx, avatar_map=None):
        raw = _normalize_sprites(sprites)
        new_count = len(raw)
        old_count = len(self._sprites)

        if new_count == 0:
            self._destroy_sprites()
            return

        if old_count == 0 and new_count > 0:
            allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
            positions = _normalize_sprite_pos(sprite_pos, new_count, allow_cover)
            for i in range(new_count):
                is_speaker = (i == speaker_idx)
                sw = _SpriteWindow(raw[i], positions[i], is_speaker, self._pinned)
                self._sprites.append(sw)
            return

        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, new_count, allow_cover)

        if avatar_map is not None and len(avatar_map) > 0 and old_count > 0:
            old_x_frac = {}
            for sw in self._sprites:
                av = getattr(sw, '_avatar', None)
                if av is not None:
                    old_x_frac[av] = sw._x_frac

            allow_cover_list = self._sprite_allow_cover_list
            has_cover = allow_cover_list is not None and any(allow_cover_list[:new_count])

            if old_x_frac and not has_cover:
                sorted_remaining = sorted(positions)
                assigned = {}
                old_chars = []
                new_chars = []
                for new_i in range(new_count):
                    av = avatar_map[new_i] if new_i < len(avatar_map) else None
                    ox = old_x_frac.get(av) if av is not None else None
                    if ox is not None:
                        old_chars.append((new_i, ox))
                    else:
                        new_chars.append(new_i)

                old_chars.sort(key=lambda x: x[1])
                for new_i, ox in old_chars:
                    best_idx = min(range(len(sorted_remaining)),
                                   key=lambda j: abs(sorted_remaining[j] - ox))
                    assigned[new_i] = sorted_remaining.pop(best_idx)

                for new_i in new_chars:
                    assigned[new_i] = sorted_remaining.pop(0)

                for new_i, pos in assigned.items():
                    positions[new_i] = pos

        if avatar_map is not None:
            old_by_avatar = {}
            for old_i, sw in enumerate(self._sprites):
                av = getattr(sw, '_avatar', None)
                if av is not None:
                    old_by_avatar[av] = old_i

            new_sprites = [None] * new_count

            for new_i in range(new_count):
                new_av = avatar_map[new_i] if new_i < len(avatar_map) else None
                if new_av is not None and new_av in old_by_avatar:
                    old_i = old_by_avatar[new_av]
                    sw = self._sprites[old_i]
                    same_image = raw[new_i] == sw._pixmap_data_ref if hasattr(sw, '_pixmap_data_ref') else False
                    image_data = raw[new_i] if not same_image else None
                    is_speaker = (new_i == speaker_idx)
                    sw.update_state(image_data=image_data, x_frac=positions[new_i], is_speaker=is_speaker)
                    if image_data is not None:
                        sw._pixmap_data_ref = raw[new_i]
                    new_sprites[new_i] = sw

            for new_i in range(new_count):
                if new_sprites[new_i] is None:
                    is_speaker = (new_i == speaker_idx)
                    sw = _SpriteWindow(raw[new_i], positions[new_i], is_speaker, self._pinned)
                    sw._pixmap_data_ref = raw[new_i]
                    new_sprites[new_i] = sw

            used_old_indices = set()
            for new_i in range(min(len(avatar_map), new_count)):
                new_av = avatar_map[new_i]
                if new_av is not None and new_av in old_by_avatar:
                    used_old_indices.add(old_by_avatar[new_av])

            for old_i, sw in enumerate(self._sprites):
                if old_i not in used_old_indices:
                    sw.destroy_sprite()

            self._sprites = new_sprites
            return

        if new_count == old_count:
            for i in range(new_count):
                same_image = raw[i] == self._sprites[i]._pixmap_data_ref if hasattr(self._sprites[i], '_pixmap_data_ref') else False
                image_data = raw[i] if not same_image else None
                is_speaker = (i == speaker_idx)
                self._sprites[i].update_state(
                    image_data=image_data,
                    x_frac=positions[i],
                    is_speaker=is_speaker
                )
                if image_data is not None:
                    self._sprites[i]._pixmap_data_ref = raw[i]
        elif new_count > old_count:
            for i in range(old_count):
                same_image = raw[i] == self._sprites[i]._pixmap_data_ref if hasattr(self._sprites[i], '_pixmap_data_ref') else False
                image_data = raw[i] if not same_image else None
                is_speaker = (i == speaker_idx)
                self._sprites[i].update_state(
                    image_data=image_data,
                    x_frac=positions[i],
                    is_speaker=is_speaker
                )
                if image_data is not None:
                    self._sprites[i]._pixmap_data_ref = raw[i]
            for i in range(old_count, new_count):
                is_speaker = (i == speaker_idx)
                sw = _SpriteWindow(raw[i], positions[i], is_speaker, self._pinned)
                sw._pixmap_data_ref = raw[i]
                self._sprites.append(sw)
        else:
            for i in range(new_count):
                same_image = raw[i] == self._sprites[i]._pixmap_data_ref if hasattr(self._sprites[i], '_pixmap_data_ref') else False
                image_data = raw[i] if not same_image else None
                is_speaker = (i == speaker_idx)
                self._sprites[i].update_state(
                    image_data=image_data,
                    x_frac=positions[i],
                    is_speaker=is_speaker
                )
                if image_data is not None:
                    self._sprites[i]._pixmap_data_ref = raw[i]
            for i in range(new_count, old_count):
                self._sprites[i].destroy_sprite()
            self._sprites = self._sprites[:new_count]

    def _update_sprites_state_only(self, speaker_idx):
        count = len(self._sprites)
        if count == 0:
            return
        for i in range(count):
            is_speaker = (i == speaker_idx)
            self._sprites[i].update_state(is_speaker=is_speaker)

    def _destroy_sprites(self):
        for sw in self._sprites:
            sw.destroy_sprite()
        self._sprites = []

    def closeEvent(self, event):
        self._destroy_sprites()
        super().closeEvent(event)

    def _update_content(self, name=None, font_family=None, font_size=None,
                        transparent=None, glare=None,
                        sprites=None, sprite_pos=None, speaker_idx=None,
                        avatar_sprite_map=None, sprite_allow_cover=None,
                        sprite_allow_cover_list=None, default=None, max_length=None):
        self._name = name

        if transparent is not None:
            self._transparent = transparent
        if glare is not None:
            self._glare = glare
        if sprite_allow_cover is not None:
            self._sprite_allow_cover = sprite_allow_cover
        if sprite_allow_cover_list is not None:
            self._sprite_allow_cover_list = sprite_allow_cover_list

        if font_family is not None:
            self._font_family = font_family
        if font_size is not None:
            self._font_size = font_size

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        self._body_fs = max(12, int(self._font_size * s))
        self._name_fs = max(12, int(self._font_size * s))
        name_pad = int(28 * s)

        self._input_h = max(28, int(INPUT_H * s))

        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_h = fm.lineSpacing() + name_pad
        if self._name:
            tw = fm.horizontalAdvance(self._name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

        cv_h = name_h + int(30 * s) + self.h + self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = self.w + self._inset * 2
        self._canvas_w = canvas_w
        self._dialog_left = (canvas_w - self.w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        dialog_screen_y = sh - self.h - 60
        win_y = dialog_screen_y - self._dialog_top

        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        if default is not None:
            self._input.setText(default)
        if max_length is not None:
            self._input.setMaxLength(max_length)

        input_w = self.w - self._pad_x * 2
        input_x = self._dialog_left + self._pad_x
        input_y = self._dialog_top + (self.h - self._input_h) // 2
        font = QFont(self._font_family, self._body_fs, QFont.Bold)
        self._input.setFont(font)
        self._input.setGeometry(int(input_x), int(input_y), int(input_w), int(self._input_h))
        self._input.setStyleSheet(
            "border: none; padding: 5px 10px;"
            f"background-color: {INPUT_BG};"
            f"color: {INPUT_TEXT};"
            f"border-radius: {max(4, int(8 / _get_dpi_scale()))}px;"
        )

        if sprites is not None:
            self._update_sprites(sprites, sprite_pos, speaker_idx, avatar_map=avatar_sprite_map)
            QApplication.processEvents()
            self.raise_()
        else:
            self._update_sprites_state_only(speaker_idx)

        self._input.setFocus()
        self.setFocusProxy(self._input)
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            remove_dwm_frame(hwnd)
            remove_window_shadow(hwnd)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        r = self.r
        w = self.w
        top = self._dialog_top
        h = self.h
        dl = self._dialog_left

        if self._name:
            self._draw_name_tag_bg(painter)
            self._draw_name_text(painter, dl)

        dialog_rect = QRectF(dl, top, w, h)
        path = QPainterPath()
        path.addRoundedRect(dialog_rect, r, r)
        painter.setClipPath(path)

        self._draw_fill(painter, dl, top, w, h)
        self._draw_dots(painter, dl, top, w, h)
        if self._glare:
            self._draw_glare(painter, dl, top, w, h)
        painter.setClipping(False)

        self._draw_outline(painter, dl, top, w, h, r)
        self._draw_triangle(painter, dl, top, w, h)

        painter.end()

    def _draw_name_tag_bg(self, painter):
        tx = self.r + 10 + self._dialog_left
        ty = self._tag_top
        tw = self._tag_w
        th = self._tag_h
        tr = self._tag_r

        tag_path = QPainterPath()
        tag_path.addRoundedRect(QRectF(tx, ty, tw, th), tr, tr)
        painter.fillPath(tag_path, QColor("#ffffff"))

        grad_top = ty + th * 0.75
        grad_h = th * 0.25
        steps = 12
        for i in range(steps):
            t_bot = i / max(steps - 1, 1)
            t_top = min((i + 1) / max(steps - 1, 1), 1.0)
            opacity = (t_bot + t_top) / 2
            color = _blend("#000000", "#ffffff", opacity)

            y1 = int(grad_top + grad_h * t_bot)
            y2 = int(grad_top + grad_h * t_top)
            region = QPainterPath()
            region.addRect(QRectF(tx, y1, tw, y2 - y1))
            clipped = tag_path.intersected(region)
            painter.fillPath(clipped, color)

    def _draw_name_text(self, painter, dl):
        tx = self.r + 10 + dl
        ty = self._tag_top - 5
        tw = self._tag_w
        th = self._tag_h
        cx = tx + tw // 2
        cy = ty + th // 2
        font = QFont(self._font_family, self._name_fs, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)
        tw_text = fm.horizontalAdvance(self._name)
        text_x = int(cx - tw_text // 2)
        text_y = int(cy + fm.ascent() - fm.height() // 2)

        dpi = _get_dpi_scale()
        name_stroke = max(1, int(2 / dpi))
        for step in range(48):
            angle = 2 * math.pi * step / 48
            dx = int(math.cos(angle) * name_stroke)
            dy = int(math.sin(angle) * name_stroke)
            painter.setPen(QColor("#BD539D"))
            painter.drawText(text_x + dx, text_y + dy, self._name)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(text_x, text_y, self._name)

    def _draw_fill(self, painter, dl, top, w, h):
        if self._transparent:
            gradient = QLinearGradient(0, top + h * 0.333, 0, top + h)
            c_top = QColor(BODY_COLOR)
            c_bot = QColor(BODY_COLOR)
            c_bot.setAlpha(int(255 * 0.65))
            gradient.setColorAt(0, c_top)
            gradient.setColorAt(1, c_bot)
        else:
            gradient = QLinearGradient(0, top, 0, top + h)
            gradient.setColorAt(0, _blend(BODY_COLOR, FADE_TO, 1.0))
            gradient.setColorAt(1, _blend(BODY_COLOR, FADE_TO, 0.5))
        painter.setBrush(gradient)
        painter.drawRect(QRectF(dl, top, w, h))

    def _draw_glare(self, painter, dl, top, w, h):
        rx = w / 2 + 30
        ry = h * 0.40
        cx = dl + w / 2
        cy = top + h

        gradient = QLinearGradient(0, cy - ry, 0, cy)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 100))
        gradient.setColorAt(0.2, QColor(255, 255, 255, 60))
        gradient.setColorAt(0.3, QColor(255, 255, 255, 30))
        gradient.setColorAt(0.4, QColor(255, 255, 255, 15))
        gradient.setColorAt(1, QColor(255, 255, 255, 10))

        path = QPainterPath()
        path.moveTo(dl, cy)
        path.arcTo(QRectF(cx - rx, cy - ry, rx * 2, ry * 2), 180, -180)

        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(path)

    def _draw_dots(self, painter, dl, top, w, h):
        painter.save()
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)

        dr = self._dot_radius
        gap_x = self._dot_gap_x
        gap_y = self._dot_gap_y
        step_x = int(dr * 2 + gap_x)
        row_h = int(dr * 2 + gap_y)

        row = 0
        y = top + dr
        while y < top + h + row_h:
            t = max(0, min(1, (y - top) / h))

            offset_x = (step_x // 2) if row % 2 == 1 else 0
            x = dl + max(0, offset_x)
            while x < dl + w + step_x:
                if self._transparent:
                    color = QColor(DOT_COLOR)
                else:
                    opacity = 1.0 - 0.5 * t
                    color = _blend(DOT_COLOR, FADE_TO, opacity)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), dr, dr)
                x += step_x
            y += row_h
            row += 1

        painter.restore()

    def _draw_outline(self, painter, dl, top, w, h, r):
        color = QColor(BORDER_COLOR)
        pen = QPen(color, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(dl, top, w, h), r, r)

    def _draw_triangle(self, painter, dl, top, w, h):
        s = self._triangle_s
        tri_h = s * math.sqrt(3) / 2
        tip_x = dl + w - self._pad_x
        tip_y = top + h - int(20 / _get_dpi_scale())
        path = QPainterPath()
        path.moveTo(tip_x, tip_y)
        path.lineTo(tip_x - tri_h, tip_y - s / 2)
        path.lineTo(tip_x - tri_h, tip_y + s / 2)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, QColor("#ffffff"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            py = event.position().toPoint().y()
            input_top = self._dialog_top + (self.h - self._input_h) // 2
            input_bottom = input_top + self._input_h
            if input_top <= py <= input_bottom:
                return
            self._submit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._cancel()

    def _submit(self):
        self.result = self._input.text()
        self.dismissed.emit()

    def _cancel(self):
        self.result = None
        self.dismissed.emit()


def _destroy_box():
    global _enter_box
    if _enter_box is not None:
        try:
            _enter_box._destroy_sprites()
        except Exception:
            pass
        try:
            _enter_box.hide()
            _enter_box.deleteLater()
        except Exception:
            pass
        _enter_box = None


def diaenterbox(w: Optional[int] = None, h: Optional[int] = None,
                name: Optional[str] = None, pinned: bool = True,
                fdst: bool = False,
                font_family: str = None, font_size: int = None,
                transparent: bool = True, glare: bool = True,
                sprites: Optional[Union[str, bytes, List[Union[str, bytes]]]] = None,
                sprite_allow_cover: bool = False,
                default: str = "", max_length: int = None) -> Optional[str]:
    """DDLC-style bottom input dialog. Type in the field and press Enter or click to submit.

    The dialog body shows a DDLC-style rounded box containing a text input field.
    Character sprites (立绘) and name tags work exactly like dialogbox.

    Args:
        w:                   width in pixels. Defaults to 70% of screen width if None.
        h:                   dialog body height in pixels. Defaults to 100 (DPI-scaled) if None.
        name:                character name shown in a white rounded tag above the dialog.
                             Use an Avatar object for auto speaker detection with sprites.
        pinned:              keep the window always on top of other windows (default True).
        fdst:                If True, destroys the window when dismissed.
        font_family:         custom font family name.
        font_size:           base font size (automatically scaled by DPI).
        transparent:         apply alpha gradient from top to bottom (default True).
        glare:               draw a white semicircular highlight at the bottom (default True).
        sprites:             list of Avatar calls specifying character and position.
        sprite_allow_cover:  allow sprites at the same position to overlap (default False).
        default:             default value in the input field.
        max_length:          maximum number of characters allowed in the input.

    Returns:
        The text entered by the user, or None if cancelled (Escape).

    Usage:
        sayori = Avatar(name="Sayori", emotes={"happy": ["sayori_happy.png"]})
        name = dokibox.diaenterbox(name=sayori, sprites=[sayori("left", "happy")])
        print(name)
    """
    global _enter_box

    _get_app()
    sw = QApplication.primaryScreen().size().width()
    if w is None:
        w = min(int(sw * 0.7), 1200)
    if h is None:
        h = int(100 / _get_dpi_scale())

    display_name = name.name if isinstance(name, Avatar) else name
    avatar = name if isinstance(name, Avatar) else None
    speaker_idx = None
    avatar_sprite_map = []
    sprite_size_map = []
    sprite_animation_map = []
    sprite_allow_cover_list = []
    sprite_pos = None

    if sprites is not None:
        is_new_api = False
        processed_sprites = []
        processed_positions = []

        for chunk in sprites:
            if isinstance(chunk, _HideSlot):
                is_new_api = True
                continue
            elif isinstance(chunk, _SpriteSlot):
                is_new_api = True
                if len(chunk.images) == 1:
                    processed_sprites.append(chunk.images[0])
                else:
                    processed_sprites.append(_composite_sprite_pixmaps(chunk.images))
                processed_positions.append(chunk.position)
                avatar_sprite_map.append(chunk.avatar)
                sprite_size_map.append((chunk.width, chunk.height))
                sprite_animation_map.append(chunk.animation)
                sprite_allow_cover_list.append(chunk.allow_cover)
                if avatar is not None and chunk.avatar is avatar and speaker_idx is None:
                    speaker_idx = len(processed_sprites) - 1
            else:
                processed_sprites.append(chunk)
                sprite_size_map.append((None, None))
                sprite_animation_map.append(None)
                sprite_allow_cover_list.append(False)

        if is_new_api:
            sprites = processed_sprites if processed_sprites else []
            sprite_pos = processed_positions

    if sprites is None and avatar is not None and _enter_box is not None:
        for i, sw in enumerate(_enter_box._sprites):
            if getattr(sw, '_avatar', None) is avatar:
                speaker_idx = i
                break

    if speaker_idx is None:
        speaker_idx = -1

    if _enter_box is not None:
        try:
            if _enter_box.w == w and _enter_box.h == h:
                _enter_box._update_content(name=display_name,
                                           font_family=font_family, font_size=font_size,
                                           transparent=transparent, glare=glare,
                                           sprites=sprites, sprite_pos=sprite_pos,
                                           speaker_idx=speaker_idx,
                                           avatar_sprite_map=avatar_sprite_map,
                                           sprite_allow_cover=sprite_allow_cover,
                                           sprite_allow_cover_list=sprite_allow_cover_list,
                                           default=default, max_length=max_length)
            else:
                _destroy_box()
        except Exception:
            _destroy_box()

    if _enter_box is None:
        _enter_box = _DiaEnterBox(w, h, display_name, pinned=pinned, fdst=fdst,
                                  font_family=font_family, font_size=font_size,
                                  transparent=transparent, glare=glare,
                                  sprites=sprites, sprite_pos=sprite_pos,
                                  speaker_idx=speaker_idx,
                                  sprite_allow_cover=sprite_allow_cover,
                                  sprite_allow_cover_list=sprite_allow_cover_list,
                                  default=default, max_length=max_length)

    for i, sw in enumerate(_enter_box._sprites):
        if i < len(avatar_sprite_map):
            sw._avatar = avatar_sprite_map[i]
        if i < len(sprite_size_map):
            w_ov, h_ov = sprite_size_map[i]
            if w_ov != sw._width_override or h_ov != sw._height_override:
                sw._width_override = w_ov
                sw._height_override = h_ov
                sw._apply_geometry(animate=False)
        if i < len(sprite_animation_map):
            sw._play_animation(sprite_animation_map[i])

    _diaenterbox_loop = QEventLoop()
    _enter_box.dismissed.connect(_diaenterbox_loop.quit, Qt.SingleShotConnection)
    _diaenterbox_loop.exec()

    result = _enter_box.result

    if fdst:
        _destroy_box()

    return result

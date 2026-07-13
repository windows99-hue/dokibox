# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC-style bottom dialog (rounded corners, gradient opacity, white stroke)"""
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
from PySide6.QtWidgets import QWidget, QApplication
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


_box = None


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
            return [0.5]
        if count == 2:
            return [0.25, 0.75]
        if count == 3:
            return [0.25, 0.50, 0.75]
        if count == 4:
            return [0.12, 0.37, 0.63, 0.88]
        return [i / max(count - 1, 1) for i in range(count)]
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
    if not allow_cover:
        result = _resolve_overlapping_positions(result)
    return result


def _resolve_overlapping_positions(positions):
    """当多个角色被指定到同一位置时，重新分布以紧凑且有层次地排开。

    - 同位置的角色紧密围绕该位置分布（组内间距小）
    - 不同位置组之间按原始比例保持间距
    - 如果所有角色位置相同，则均分整个舞台

    Args:
        positions: 已转换为浮点数的位置列表 (0.0~1.0)。

    Returns:
        调整后的位置列表。
    """
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
    """Character avatar definition with name and emotion image sets.

    Usage:
        sayori = Avatar(name="Sayori", emotes={"happy": ["sayori_happy.png"],
                                                "sad": ["sayori_sad.png"]})
        sayori("left", "happy")   -> SpriteSlot on the left with happy emote
        sayori.hide()             -> HideSlot to remove from stage
    """

    def __init__(self, name, emotes):
        self.name = name
        self.emotes = emotes

    def __call__(self, position, emote, width=None, height=None):
        images = self.emotes.get(emote)
        if images is None:
            raise ValueError(
                f"Emote '{emote}' not found for avatar '{self.name}'. "
                f"Available: {list(self.emotes.keys())}"
            )
        if isinstance(images, str):
            images = [images]
        return _SpriteSlot(self, position, images, width=width, height=height)

    def hide(self):
        return _HideSlot(self)


class _SpriteSlot:
    """Internal: a character placed on stage at a position with an emote."""
    __slots__ = ("avatar", "position", "images", "width", "height")

    def __init__(self, avatar, position, images, width=None, height=None):
        self.avatar = avatar
        self.position = position
        self.images = images
        self.width = width
        self.height = height


class _HideSlot:
    """Internal: mark an avatar as leaving the stage."""
    __slots__ = ("avatar",)

    def __init__(self, avatar):
        self.avatar = avatar


def _composite_sprite_pixmaps(images):
    """Load multiple images and composite them into a single pixmap (layers stacked)."""
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
    """Single standing-picture (立绘) window displayed above the dialog.

    The window is kept at speaker-scale geometry to avoid resizing during
    silent<->speaker transitions.  All scale animation happens in paintEvent
    via a transform — this eliminates the DWM compositing jank that comes
    with per-frame setGeometry calls.
    """

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
        """Return the unscaled (base) width and height tuple."""
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
        """Window geometry at speaker scale (the largest it will ever be)."""
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
        oy = h - paint_h

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
            self.hide()
            self.deleteLater()
        except Exception:
            pass


class _DialogBox(QWidget):

    dismissed = Signal()

    def __init__(self, msg, w, h, name=None, typewriter=True, chardelay=50,
                 bold=False, pinned=True, fdst=False, overflow_mode="wrap",
                 font_family=None, font_size=None, transparent=True, glare=True,
                 sprites=None, sprite_pos=None, speaker_idx=None,
                 sprite_allow_cover=False):
        global _box

        if overflow_mode not in ("wrap", "overflow", "hide"):
            raise ValueError(
                f"overflow_mode must be 'wrap', 'overflow', or 'hide', got {overflow_mode!r}"
            )
        _get_app()
        super().__init__(None)

        self._overflow_mode = overflow_mode
        self.w = w
        self.h = h
        self._name = name
        self._typewriter = typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._fdst = fdst
        self._pinned = pinned
        self._typing = False
        self._typing_done = False
        self._after_timer = None
        self._transparent = transparent
        self._glare = glare
        self._sprites = []
        self._sprite_allow_cover = sprite_allow_cover

        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size or 20

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        self._body_fs = max(12, int(self._font_size * s))
        self._name_fs = max(12, int(self._font_size * s))
        self._line_h = int(44 * s)
        self._pad_top = int(40 * s)
        self._pad_x = int(40 * s)
        self._name_pad_val = int(28 * s)
        self._dot_radius = int(DOT_RADIUS * s)
        self._dot_gap_x = int(DOT_GAP_X * s)
        self._dot_gap_y = int(DOT_GAP_Y * s)
        self._corner_radius = max(8, int(CORNER_RADIUS * s))
        self._inset = max(2, int(INSET * s))
        sw_raw = 4 if bold else 1
        self._stroke_w = max(1, int(sw_raw * s))
        self._triangle_s = int(16 * s)
        self.r = self._corner_radius

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

        cv_h = h + name_h + int(30 * s)
        cv_h += self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = w
        vert_overflow = 0
        if self._overflow_mode == "overflow" and msg:
            f_body = QFont(self._font_family, self._body_fs, QFont.Bold)
            fm = QFontMetrics(f_body)
            max_line_w = max(fm.horizontalAdvance(line) for line in msg.split('\n'))
            needed_w = int(max_line_w + int(80 * s))
            if needed_w > canvas_w:
                canvas_w = needed_w
            num_lines = len(msg.split('\n'))
            text_h_needed = self._pad_top + num_lines * self._line_h
            if text_h_needed > h:
                vert_overflow = int(text_h_needed - h + self._pad_top)
                cv_h += vert_overflow
                self._cv_h = cv_h
        self._vert_overflow = vert_overflow
        canvas_w += self._inset * 2
        self._canvas_w = canvas_w
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        if self._overflow_mode == "overflow":
            x = (sw - w) // 2 - self._dialog_left
        dialog_screen_y = sh - h - 60
        win_y = dialog_screen_y - self._dialog_top

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        self._init_typewriter_state(msg)
        self.show()

        _box = self

        self._init_sprites(sprites, sprite_pos, speaker_idx)

        QApplication.processEvents()
        self.raise_()
        self.activateWindow()

    def _init_sprites(self, sprites, sprite_pos, speaker_idx):
        raw = _normalize_sprites(sprites)
        count = len(raw)
        if count == 0:
            return
        positions = _normalize_sprite_pos(sprite_pos, count, self._sprite_allow_cover)
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
            positions = _normalize_sprite_pos(sprite_pos, new_count, self._sprite_allow_cover)
            for i in range(new_count):
                is_speaker = (i == speaker_idx)
                sw = _SpriteWindow(raw[i], positions[i], is_speaker, self._pinned)
                self._sprites.append(sw)
            return

        positions = _normalize_sprite_pos(sprite_pos, new_count, self._sprite_allow_cover)

        if avatar_map is not None and len(avatar_map) > 0 and old_count > 0:
            old_x_frac = {}
            for sw in self._sprites:
                av = getattr(sw, '_avatar', None)
                if av is not None:
                    old_x_frac[av] = sw._x_frac

            if old_x_frac:
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
            sw._instant_destroy()
        self._sprites = []

    def closeEvent(self, event):
        self._destroy_sprites()
        super().closeEvent(event)

    def _update_content(self, msg, typewriter, chardelay, bold, overflow_mode, name=None,
                        font_family=None, font_size=None, transparent=None, glare=None,
                        sprites=None, sprite_pos=None, speaker_idx=None,
                        avatar_sprite_map=None, sprite_allow_cover=None):
        if self._after_timer:
            try:
                self._after_timer.stop()
            except Exception:
                pass
            self._after_timer.deleteLater()
            self._after_timer = None

        self._overflow_mode = overflow_mode
        self._typewriter = typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._typing = False
        self._typing_done = False
        if transparent is not None:
            self._transparent = transparent
        if glare is not None:
            self._glare = glare
        if sprite_allow_cover is not None:
            self._sprite_allow_cover = sprite_allow_cover

        self._name = name

        if font_family is not None:
            self._font_family = font_family
        else:
            self._font_family = "Microsoft YaHei"
        if font_size is not None:
            self._font_size = font_size
        else:
            self._font_size = 20
        self._body_fs = self._font_size
        self._name_fs = self._font_size

        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        name_pad = int(28 * s)

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

        cv_h = self.h + name_h + int(30 * s)
        cv_h += self._inset
        self._cv_h = cv_h
        self._dialog_top = name_h + int(20 * s) + self._inset

        canvas_w = self.w
        vert_overflow = 0
        if self._overflow_mode == "overflow" and msg:
            f_body = QFont(self._font_family, self._body_fs, QFont.Bold)
            fm = QFontMetrics(f_body)
            max_line_w = max(fm.horizontalAdvance(line) for line in msg.split('\n'))
            needed_w = int(max_line_w + int(80 * s))
            if needed_w > canvas_w:
                canvas_w = needed_w
            num_lines = len(msg.split('\n'))
            text_h_needed = self._pad_top + num_lines * self._line_h
            if text_h_needed > self.h:
                vert_overflow = int(text_h_needed - self.h + self._pad_top)
                cv_h += vert_overflow
                self._cv_h = cv_h
        self._vert_overflow = vert_overflow
        canvas_w += self._inset * 2
        self._canvas_w = canvas_w
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - self.w) // 2

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - canvas_w) // 2
        if self._overflow_mode == "overflow":
            x = (sw - self.w) // 2 - self._dialog_left
        dialog_screen_y = sh - self.h - 60
        win_y = dialog_screen_y - self._dialog_top

        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

        self._init_typewriter_state(msg)

        if sprites is not None:
            self._update_sprites(sprites, sprite_pos, speaker_idx, avatar_map=avatar_sprite_map)
            QApplication.processEvents()
            self.raise_()
        else:
            self._update_sprites_state_only(speaker_idx)

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

    def _init_typewriter_state(self, msg):
        self._full_msg = msg
        if self._typewriter and msg:
            self._typing = True
            self._typing_done = False
            self._cur_line = 0
            self._cur_char = 0
            font = QFont(self._font_family, self._body_fs, QFont.Bold)
            lines = self._process_lines(msg, font, self._text_area_width())
            self._typewriter_lines = lines
            self._typewriter_font = font
            self._typewriter_positions = self._layout_text_positions(lines)
            self._start_typewriter_timer()
        else:
            self._typing = False
            self._typing_done = True

    def _start_typewriter_timer(self):
        self._after_timer = QTimer(self)
        self._after_timer.setSingleShot(True)
        self._after_timer.timeout.connect(self._type_tick)
        self._after_timer.start(self._chardelay)

    def _type_tick(self):
        if self._cur_line >= len(self._typewriter_lines):
            self._typing = False
            self._typing_done = True
            self._after_timer = None
            return

        full_text = self._typewriter_lines[self._cur_line]
        self._cur_char += 1
        if self._cur_char > len(full_text):
            self._cur_line += 1
            self._cur_char = 0
            self._type_tick()
            return

        self.update()
        self._after_timer = QTimer(self)
        self._after_timer.setSingleShot(True)
        self._after_timer.timeout.connect(self._type_tick)
        self._after_timer.start(self._chardelay)

    def _finish_typewriter(self):
        if self._after_timer:
            try:
                self._after_timer.stop()
            except Exception:
                pass
            self._after_timer.deleteLater()
            self._after_timer = None
        self._typing = False
        self._typing_done = True
        self._cur_line = len(self._typewriter_lines)
        self._cur_char = 0
        self.update()

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

        if self._overflow_mode != "overflow":
            painter.setClipPath(path)
        self._draw_text(painter, dl, top)

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
        tip_y = top + h - self._pad_top
        path = QPainterPath()
        path.moveTo(tip_x, tip_y)
        path.lineTo(tip_x - tri_h, tip_y - s / 2)
        path.lineTo(tip_x - tri_h, tip_y + s / 2)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, QColor("#ffffff"))

    def _text_area_width(self):
        return self.w - self._pad_x * 2

    def _wrap_line(self, text, font, max_w):
        fm = QFontMetrics(font)
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

    def _truncate_line(self, text, font, max_w):
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= max_w:
            return text
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if fm.horizontalAdvance(text[:mid]) <= max_w:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo]

    def _process_lines(self, text, font, max_w):
        if self._overflow_mode == "overflow":
            return text.split('\n')
        raw_lines = text.split('\n')
        if self._overflow_mode == "wrap":
            result = []
            for line in raw_lines:
                result.extend(self._wrap_line(line, font, max_w))
            return result
        if self._overflow_mode == "hide":
            return [self._truncate_line(line, font, max_w) for line in raw_lines]
        return raw_lines

    def _layout_text_positions(self, lines):
        line_h = self._line_h
        pad_top = self._pad_top
        pad_x = self._pad_x
        top = self._dialog_top
        pos = []
        for j, line in enumerate(lines):
            y = top + pad_top + line_h // 2 + j * line_h
            pos.append((pad_x, y, line))
        return pos

    def _draw_text(self, painter, dl, top):
        msg = self._full_msg
        if not msg:
            return
        font = QFont(self._font_family, self._body_fs, QFont.Bold)

        if self._typewriter and self._typing:
            positions = self._typewriter_positions
            for j, (px, py, full_text) in enumerate(positions):
                if j < self._cur_line:
                    shown = full_text
                elif j == self._cur_line:
                    shown = full_text[:self._cur_char]
                else:
                    shown = ""
                if shown:
                    self._draw_stroked_text_left(painter, dl + px, py, shown, font)
        elif not self._typing and self._typing_done:
            lines = self._process_lines(msg, font, self._text_area_width())
            positions = self._layout_text_positions(lines)
            for px, py, line in positions:
                self._draw_stroked_text_left(painter, dl + px, py, line, font)

    def _draw_stroked_text_left(self, painter, x, y, text, font):
        sw = 4 if self._bold else 1
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_y = int(y + fm.ascent() - fm.height() // 2)
        for step in range(48):
            angle = 2 * math.pi * step / 24
            dx = int(math.cos(angle) * sw)
            dy = int(math.sin(angle) * sw)
            painter.setPen(QColor("#000000"))
            painter.drawText(int(x) + dx, text_y + dy, text)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(int(x), text_y, text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._on_click()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._done()

    def _on_click(self):
        if self._typewriter and self._typing:
            self._finish_typewriter()
        else:
            self._done()

    def _done(self):
        self.dismissed.emit()


def _destroy_box():
    global _box
    if _box is not None:
        if _box._after_timer:
            try:
                _box._after_timer.stop()
            except Exception:
                pass
            _box._after_timer.deleteLater()
            _box._after_timer = None
        try:
            _box._destroy_sprites()
        except Exception:
            pass
        try:
            _box.hide()
            _box.deleteLater()
        except Exception:
            pass
        _box = None


def dialogbox(msg: str = "", w: Optional[int] = None, h: Optional[int] = None,
              name: Optional[str] = None, typewriter: bool = True,
              chardelay: int = 50, bold: bool = False, pinned: bool = True,
              fdst: bool = False, overflow_mode: str = "wrap",
              font_family: str = None, font_size: int = None,
              transparent: bool = True, glare: bool = True,
              sprites: Optional[Union[str, bytes, List[Union[str, bytes]]]] = None,
              sprite_allow_cover: bool = False) -> None:
    """DDLC-style bottom rounded dialog. Click anywhere or press Esc to dismiss.

    Args:
        msg:           body text to display (supports \\n for multiple lines).
        w:             width in pixels. Defaults to 70% of screen width if None.
        h:             height in pixels. Defaults to 220 (DPI-scaled) if None.
        name:          character name shown in a white rounded tag above the dialog.
                       Use an Avatar object for auto speaker detection with sprites.
        typewriter:    animate text character-by-character (default True).
        chardelay:     delay in ms per character in typewriter mode (default 50).
        bold:          use a thicker black stroke outline for body text (default False).
        pinned:        keep the window always on top of other windows (default True).
        fdst:          If True, destroys the window when dismissed. Use this for the final line
                       of a dialogue scene or story branch to ensure the window closes completely.
        overflow_mode: how to handle text exceeding the dialog width:
                       'wrap'    – wrap text to the next line (default).
                       'overflow' – expand the window so text can render past the dialog boundary.
                       'hide'    – clip text at the boundary.
        transparent:   apply alpha gradient from top to bottom, making the body see-through (default True).
        glare:         draw a white semicircular highlight at the bottom of the dialog (default True).
        sprites:       list of Avatar calls specifying character and position, e.g.
                       [sayori("left", "happy"), yuri("right", "shocked")].
        sprite_allow_cover: If True, allow sprites at the same position to overlap (default False).
                       When False, sprites sharing a position are automatically spread apart.

    Usage:
        sayori = Avatar(name="Sayori", emotes={"happy": ["sayori_happy.png"]})
        yuri = Avatar(name="Yuri", emotes={"shocked": ["yuri_shocked.png"]})
        dokibox.dialogbox("Hello!", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "shocked")])
        dokibox.dialogbox("Hi!", name=yuri)  # sprites persist, speaker auto-detected
    """
    global _box

    _get_app()
    sw = QApplication.primaryScreen().size().width()
    if w is None:
        w = min(int(sw * 0.7), 1200)
    if h is None:
        h = int(220 / _get_dpi_scale())

    display_name = name.name if isinstance(name, Avatar) else name
    avatar = name if isinstance(name, Avatar) else None
    speaker_idx = None
    avatar_sprite_map = []
    sprite_size_map = []
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
                if avatar is not None and chunk.avatar is avatar and speaker_idx is None:
                    speaker_idx = len(processed_sprites) - 1
            else:
                processed_sprites.append(chunk)
                sprite_size_map.append((None, None))

        if is_new_api:
            sprites = processed_sprites if processed_sprites else []
            sprite_pos = processed_positions

    if sprites is None and avatar is not None and _box is not None:
        for i, sw in enumerate(_box._sprites):
            if getattr(sw, '_avatar', None) is avatar:
                speaker_idx = i
                break

    if speaker_idx is None:
        speaker_idx = -1

    if _box is not None:
        try:
            if _box.w == w and _box.h == h:
                _box._update_content(msg, typewriter, chardelay, bold, overflow_mode, display_name,
                                     font_family=font_family, font_size=font_size,
                                     transparent=transparent, glare=glare,
                                     sprites=sprites, sprite_pos=sprite_pos,
                                     speaker_idx=speaker_idx,
                                     avatar_sprite_map=avatar_sprite_map,
                                     sprite_allow_cover=sprite_allow_cover)
            else:
                _destroy_box()
        except Exception:
            _destroy_box()

    if _box is None:
        _box = _DialogBox(msg, w, h, display_name, typewriter, chardelay, bold, pinned=pinned,
                          fdst=fdst, overflow_mode=overflow_mode,
                          font_family=font_family, font_size=font_size,
                          transparent=transparent, glare=glare,
                          sprites=sprites, sprite_pos=sprite_pos,
                          speaker_idx=speaker_idx,
                          sprite_allow_cover=sprite_allow_cover)

    for i, sw in enumerate(_box._sprites):
        if i < len(avatar_sprite_map):
            sw._avatar = avatar_sprite_map[i]
        if i < len(sprite_size_map):
            w_ov, h_ov = sprite_size_map[i]
            if w_ov != sw._width_override or h_ov != sw._height_override:
                sw._width_override = w_ov
                sw._height_override = h_ov
                sw._apply_geometry(animate=False)

    _dialogbox_loop = QEventLoop()
    _box.dismissed.connect(_dialogbox_loop.quit, Qt.SingleShotConnection)
    _dialogbox_loop.exec()

    if fdst:
        _destroy_box()

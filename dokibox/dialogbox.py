# -*- coding: utf-8 -*-
"""dokibox.dialogbox -- DDLC-style bottom dialog (rounded corners, gradient opacity, white stroke)"""
import math
import sys
import ctypes
import locale
from typing import Optional, Union, List
from PySide6.QtCore import (
    Qt, QTimer, QEventLoop, QElapsedTimer, QRectF, QPointF, Signal,
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
SPRITE_SLIDE_DURATION = 350
SPRITE_FRAME_INTERVAL = 16

MENU_COLOR = QColor("#59242C")
MENU_HOVER_COLOR = QColor("#ffffff")
MENU_DISABLED_COLOR = QColor("#AA646F")

# A private sentinel lets dialogbox distinguish an omitted argument from an
# explicitly supplied value (including None).  Omitted arguments are resolved
# from the attributes on the public dialogbox function below.
_UNSET = object()

_MENU_I18N = {
    "zh": ["历史", "快进", "自动", "保存", "加载", "设置"],
    "ja": ["履歴", "スキップ", "自動", "セーブ", "ロード", "設定"],
    "en": ["History", "Skip", "Auto", "Save", "Load", "Settings"],
}


def _detect_lang():
    try:
        loc = locale.getdefaultlocale()
        if loc and loc[0]:
            lc = loc[0].lower()
            if lc.startswith("zh"):
                return "zh"
            if lc.startswith("ja"):
                return "ja"
            if lc.startswith("en") or lc == "C" or lc == "POSIX":
                return "en"
        if sys.platform == "win32":
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            lang = {0x0804: "zh", 0x0404: "zh", 0x0C04: "zh", 0x0411: "ja"}.get(lid)
            if lang:
                return lang
    except Exception:
        pass
    return "en"


MENU_LABELS = _MENU_I18N.get(_detect_lang(), _MENU_I18N["en"])


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
        hwnd, DWMWA_SHADOW_OPACITY, ctypes.byref(zero_val), ctypes.sizeof(zero_val))

_box = None
_menu_callback_box = None
_history = []


def addhistory(data):
    """向历史记录中添加对话，支持列表或JSON字符串。
    
    data 可以是：
      - [(name, msg), ...]  元组列表
      - [{"name": "...", "msg": "..."}, ...]  字典列表
      - JSON 字符串
    """
    global _history
    if isinstance(data, str):
        import json
        records = json.loads(data)
    else:
        records = data
    for item in records:
        if isinstance(item, (list, tuple)):
            _history.append((str(item[0]), str(item[1])))
        elif isinstance(item, dict):
            _history.append((str(item.get("name", "") or ""), str(item.get("msg", "") or "")))


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
        result = _default_positions(count)
    elif isinstance(sprite_pos, (str, float, int)):
        result = [_pos_to_float(sprite_pos)]
        while len(result) < count:
            result.append(0.5 + (len(result) - count / 2) * 0.1)
    else:
        result = [_pos_to_float(p) for p in sprite_pos[:count]]
        while len(result) < count:
            result.append(0.5 + (len(result) - count / 2) * 0.1)
    result = _apply_cover_policy(result, count, allow_cover)
    return result


def _default_positions(count):
    mapping = {1: [0.5], 2: [0.25, 0.75], 3: [0.25, 0.50, 0.75],
               4: [0.12, 0.37, 0.63, 0.88]}
    if count in mapping:
        return list(mapping[count])
    return [i / max(count - 1, 1) for i in range(count)]


def _pos_to_float(p):
    if isinstance(p, str):
        key = p.strip().lower()
        mapping = {"left": 0.25, "center": 0.50, "right": 0.75}
        if key in mapping:
            return mapping[key]
        return float(p)
    return float(p)


def _apply_cover_policy(result, count, allow_cover):
    if isinstance(allow_cover, list) and len(allow_cover) >= count:
        indices = [i for i in range(count) if not allow_cover[i]]
        values_to_resolve = [result[i] for i in indices]
        if len(values_to_resolve) > 1:
            resolved = _resolve_overlapping_positions(values_to_resolve)
            for idx, val in zip(indices, resolved):
                result[idx] = val
    elif not allow_cover:
        result = _resolve_overlapping_positions(result)
    return result


def _resolve_overlapping_positions(positions):
    """Redistribute overlapping positions so sprites spread gracefully."""
    n = len(positions)
    if n <= 1:
        return positions[:]
    rounded = [round(p, 4) for p in positions]
    if len(set(rounded)) == n:
        return positions[:]

    groups = _group_positions(positions)
    if len(groups) == 1:
        return _spread_across_stage(n)

    return _spread_within_groups(groups, n)


def _group_positions(positions):
    indexed = sorted(enumerate(positions), key=lambda x: (x[1], x[0]))
    groups = []
    i = 0
    n = len(positions)
    while i < n:
        pos = indexed[i][1]
        j = i + 1
        while j < n and round(indexed[j][1], 4) == round(pos, 4):
            j += 1
        groups.append((pos, [indexed[k] for k in range(i, j)]))
        i = j
    return groups


def _spread_across_stage(n):
    MARGIN = 0.2
    usable = 1.0 - 2 * MARGIN
    return [MARGIN + i / max(n - 1, 1) * usable for i in range(n)]


def _spread_within_groups(groups, n):
    INNER_GAP = 0.18
    MIN_GAP = 0.08

    result = [0.0] * n
    idx_to_group = {}

    for gi, (pos, members) in enumerate(groups):
        count = len(members)
        if count == 1:
            idx, _ = members[0]
            result[idx] = pos
        else:
            total_w = (count - 1) * INNER_GAP
            for k, (idx, _) in enumerate(members):
                t = k / max(count - 1, 1)
                result[idx] = pos - total_w / 2 + t * total_w
        for idx, _ in members:
            idx_to_group[idx] = gi

    for _ in range(100):
        sorted_pairs = sorted(enumerate(result), key=lambda x: x[1])
        changed = False
        for k in range(n - 1):
            a, va = sorted_pairs[k]
            b, vb = sorted_pairs[k + 1]
            if idx_to_group[a] == idx_to_group[b]:
                continue
            gap = vb - va
            if gap < MIN_GAP:
                push = (MIN_GAP - gap) / 2
                result[a] = max(0.04, va - push)
                result[b] = min(0.96, vb + push)
                changed = True
        if not changed:
            break
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
                f"Available: {list(self.emotes.keys())}")
        if isinstance(images, str):
            images = [images]
        return _SpriteSlot(self, position, images, animation=animation,
                           width=width, height=height, allow_cover=sprite_allow_cover)

    def hide(self, animation="fade"):
        return _HideSlot(self, animation)


class _SpriteSlot:
    """Internal: a character placed on stage at a position with an emote."""
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
    """Internal: mark an avatar as leaving the stage."""
    __slots__ = ("avatar", "animation")

    def __init__(self, avatar, animation="fade"):
        self.avatar = avatar
        self.animation = animation


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


def _process_sprites(sprites, avatar=None):
    """Process sprite list into normalized form for use by _DialogBox."""
    result = {
        'sprites': sprites,
        'sprite_pos': None,
        'avatar_sprite_map': [],
        'sprite_size_map': [],
        'sprite_animation_map': [],
        'sprite_allow_cover_list': [],
        'speaker_idx': None,
        'avatar_hide_animations': {},
    }
    if sprites is None:
        return result

    is_new_api = False
    processed_sprites = []
    processed_positions = []

    for chunk in sprites:
        if isinstance(chunk, _HideSlot):
            is_new_api = True
            result['avatar_hide_animations'][chunk.avatar] = chunk.animation
            continue
        elif isinstance(chunk, _SpriteSlot):
            is_new_api = True
            if len(chunk.images) == 1:
                processed_sprites.append(chunk.images[0])
            else:
                processed_sprites.append(_composite_sprite_pixmaps(chunk.images))
            processed_positions.append(chunk.position)
            result['avatar_sprite_map'].append(chunk.avatar)
            result['sprite_size_map'].append((chunk.width, chunk.height))
            result['sprite_animation_map'].append(chunk.animation)
            result['sprite_allow_cover_list'].append(chunk.allow_cover)
            if avatar is not None and chunk.avatar is avatar and result['speaker_idx'] is None:
                result['speaker_idx'] = len(processed_sprites) - 1
        else:
            processed_sprites.append(chunk)
            result['sprite_size_map'].append((None, None))
            result['sprite_animation_map'].append(None)
            result['sprite_allow_cover_list'].append(False)

    if is_new_api:
        result['sprites'] = processed_sprites if processed_sprites else []
        result['sprite_pos'] = processed_positions

    return result


class _SpriteWindow(QWidget):
    """Single standing-picture (立绘) window displayed above the dialog."""

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
        self._pixmap_data_ref = image_data

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
                hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int))
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

        base_h = self._height_override if self._height_override is not None else int(sh * SPRITE_BASE_HEIGHT_RATIO)
        base_w = int(base_h * pw / ph) if ph > 0 else base_h

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
        return QRect(x, sh - h, w, h)

    def _apply_geometry(self, animate=True):
        target_geom = self._compute_max_geometry()
        target_scale = SPRITE_SPEAKER_SCALE if self._is_speaker else SPRITE_SILENT_SCALE
        target_opacity = 1.0 if self._is_speaker else SPRITE_SILENT_OPACITY

        if animate and self.isVisible():
            self._animate_to(target_geom, target_scale, target_opacity)
        else:
            self.setGeometry(target_geom)
            self._anim_scale = target_scale
            self.update()

    def _animate_to(self, target_geom, target_scale, target_opacity):
        self._stop_animation()
        self._stop_fade()

        start_geom = self.geometry()
        start_scale = self._anim_scale
        start_opacity = self._opacity_val
        geom_changed = (start_geom != target_geom)
        scale_changed = not math.isclose(
            start_scale, target_scale, rel_tol=0.0, abs_tol=1e-6)
        opacity_changed = not math.isclose(
            start_opacity, target_opacity, rel_tol=0.0, abs_tol=1e-6)

        if not (geom_changed or scale_changed or opacity_changed):
            self.update()
            return

        easing = QEasingCurve(QEasingCurve.OutCubic)
        elapsed = QElapsedTimer()
        elapsed.start()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)
        self._anim_timer = timer

        sx, sy = start_geom.x(), start_geom.y()
        sw_val, sh_val = start_geom.width(), start_geom.height()
        tx, ty = target_geom.x(), target_geom.y()
        tw, th = target_geom.width(), target_geom.height()

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_ANIM_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            if geom_changed:
                self.setGeometry(
                    int(sx + (tx - sx) * t), int(sy + (ty - sy) * t),
                    int(sw_val + (tw - sw_val) * t), int(sh_val + (th - sh_val) * t))
            self._anim_scale = start_scale + (target_scale - start_scale) * t
            self._opacity_val = start_opacity + (target_opacity - start_opacity) * t
            self.update()
            if progress >= 1.0:
                if geom_changed:
                    self.setGeometry(target_geom)
                self._anim_scale = target_scale
                self._opacity_val = target_opacity
                self.update()
                timer.stop()
                timer.deleteLater()
                if self._anim_timer is timer:
                    self._anim_timer = None

        timer.timeout.connect(on_tick)
        timer.start()

    def _stop_animation(self):
        if self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer.deleteLater()
            self._anim_timer = None

    def _stop_fade(self):
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer.deleteLater()
            self._fade_timer = None

    def _start_fade_in(self):
        target = 1.0 if self._is_speaker else SPRITE_SILENT_OPACITY
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer.deleteLater()
            self._fade_timer = None

        easing = QEasingCurve(QEasingCurve.OutCubic)
        elapsed = QElapsedTimer()
        elapsed.start()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)
        self._fade_timer = timer

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_FADE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = target * t
            self.update()
            if progress >= 1.0:
                self._opacity_val = target
                self.update()
                timer.stop()
                timer.deleteLater()
                if self._fade_timer is timer:
                    self._fade_timer = None

        timer.timeout.connect(on_tick)
        timer.start()

    def update_state(self, image_data=None, x_frac=None, is_speaker=None):
        changed = False
        if image_data is not None and not _same_image(image_data, self):
            if self._offset_anim is not None:
                self._offset_anim.stop()
                self._offset_anim.deleteLater()
                self._offset_anim = None
            self._offset_y = 0.0
            self._pixmap = _load_pixmap(image_data)
            self._pixmap_data_ref = image_data
            changed = True
        if x_frac is not None and not math.isclose(
                x_frac, self._x_frac, rel_tol=0.0, abs_tol=1e-6):
            self._x_frac = x_frac
            changed = True
        if is_speaker is not None and is_speaker != self._is_speaker:
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

        source_w = self._pixmap.width()
        source_h = self._pixmap.height()
        if source_w > 0 and source_h > 0 and paint_w > 0 and paint_h > 0:
            scale = min(paint_w / source_w, paint_h / source_h)
            draw_w = max(1, int(source_w * scale))
            draw_h = max(1, int(source_h * scale))
            sx = ox + (paint_w - draw_w) // 2
            sy = oy + paint_h - draw_h
            painter.drawPixmap(
                QRect(sx, sy, draw_w, draw_h), self._pixmap, self._pixmap.rect())
        painter.end()

    def destroy_sprite(self, animation="fade"):
        try:
            self._stop_animation()
            self._stop_fade()
            self._stop_offset_anim()
            if animation == "rleft":
                self._slide_out_right_and_destroy()
            elif animation == "lleft":
                self._slide_out_left_and_destroy()
            else:
                self._fade_out_and_destroy()
        except Exception:
            pass

    def _stop_offset_anim(self):
        if self._offset_anim is not None:
            self._offset_anim.stop()
            self._offset_anim.deleteLater()
            self._offset_anim = None

    def _fade_out_and_destroy(self):
        easing = QEasingCurve(QEasingCurve.OutCubic)
        start_opacity = self._opacity_val
        elapsed = QElapsedTimer()
        elapsed.start()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_FADE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = start_opacity * (1.0 - t)
            self.update()
            if progress >= 1.0:
                self._opacity_val = 0.0
                self.update()
                timer.stop()
                timer.deleteLater()
                self.hide()
                self.deleteLater()

        timer.timeout.connect(on_tick)
        timer.start()

    def _slide_out_right_and_destroy(self):
        easing = QEasingCurve(QEasingCurve.InCubic)
        start_geom = self.geometry()
        start_opacity = self._opacity_val
        elapsed = QElapsedTimer()
        elapsed.start()

        screen = QApplication.primaryScreen()
        sw = screen.size().width()
        target_x = sw + start_geom.width()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_SLIDE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = start_opacity * (1.0 - t)
            new_x = int(start_geom.x() + (target_x - start_geom.x()) * t)
            self.move(new_x, start_geom.y())
            self.update()
            if progress >= 1.0:
                self._opacity_val = 0.0
                self.update()
                timer.stop()
                timer.deleteLater()
                self.hide()
                self.deleteLater()

        timer.timeout.connect(on_tick)
        timer.start()

    def _slide_out_left_and_destroy(self):
        easing = QEasingCurve(QEasingCurve.InCubic)
        start_geom = self.geometry()
        start_opacity = self._opacity_val
        elapsed = QElapsedTimer()
        elapsed.start()

        target_x = -start_geom.width()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_SLIDE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = start_opacity * (1.0 - t)
            new_x = int(start_geom.x() + (target_x - start_geom.x()) * t)
            self.move(new_x, start_geom.y())
            self.update()
            if progress >= 1.0:
                self._opacity_val = 0.0
                self.update()
                timer.stop()
                timer.deleteLater()
                self.hide()
                self.deleteLater()

        timer.timeout.connect(on_tick)
        timer.start()

    def _enter_from_left(self):
        target_geom = self._compute_max_geometry()
        start_x = -target_geom.width()
        start_opacity = self._opacity_val

        easing = QEasingCurve(QEasingCurve.OutCubic)
        elapsed = QElapsedTimer()
        elapsed.start()

        self.move(start_x, target_geom.y())
        self._opacity_val = 0.0
        self.update()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_SLIDE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = t
            new_x = int(start_x + (target_geom.x() - start_x) * t)
            self.move(new_x, target_geom.y())
            self.update()
            if progress >= 1.0:
                self._opacity_val = 1.0
                self.move(target_geom.x(), target_geom.y())
                self.update()
                timer.stop()
                timer.deleteLater()

        timer.timeout.connect(on_tick)
        timer.start()

    def _enter_from_right(self):
        target_geom = self._compute_max_geometry()
        screen = QApplication.primaryScreen()
        sw = screen.size().width()
        start_x = sw + target_geom.width()

        easing = QEasingCurve(QEasingCurve.OutCubic)
        elapsed = QElapsedTimer()
        elapsed.start()

        self.move(start_x, target_geom.y())
        self._opacity_val = 0.0
        self.update()

        timer = QTimer(self)
        timer.setInterval(SPRITE_FRAME_INTERVAL)

        def on_tick():
            progress = min(elapsed.elapsed() / SPRITE_SLIDE_DURATION, 1.0)
            t = easing.valueForProgress(min(progress, 1.0))
            self._opacity_val = t
            new_x = int(start_x + (target_geom.x() - start_x) * t)
            self.move(new_x, target_geom.y())
            self.update()
            if progress >= 1.0:
                self._opacity_val = 1.0
                self.move(target_geom.x(), target_geom.y())
                self.update()
                timer.stop()
                timer.deleteLater()

        timer.timeout.connect(on_tick)
        timer.start()

    def _instant_destroy(self):
        try:
            self._stop_animation()
            self._stop_fade()
            self._stop_offset_anim()
            self.hide()
            self.deleteLater()
        except Exception:
            pass

    def _get_offset_y(self):
        return self._offset_y

    def _set_offset_y(self, val):
        self._offset_y = val
        self.update()

    anim_offset_y = Property(float, _get_offset_y, _set_offset_y)

    def _play_animation(self, anim_type):
        if anim_type == "lenter":
            self._stop_fade()
            self._enter_from_left()
            return
        if anim_type == "renter":
            self._stop_fade()
            self._enter_from_right()
            return

        if self._offset_anim is not None:
            self._offset_anim.stop()
            self._offset_anim.deleteLater()
            self._offset_anim = None

        if anim_type is None:
            if abs(self._offset_y) > 0.5:
                self._reset_offset_anim()
            return

        anim = QPropertyAnimation(self, b"anim_offset_y")
        self._offset_anim = anim

        if anim_type == "shocked":
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.OutBounce)
            anim.setStartValue(self._offset_y)
            anim.setKeyValueAt(0.12, -65.0)
            anim.setEndValue(0.0)
        elif anim_type == "sad":
            anim.setDuration(900)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setStartValue(self._offset_y)
            anim.setEndValue(35.0)
        elif anim_type == "thanks":
            anim.setDuration(900)
            anim.setEasingCurve(QEasingCurve.InOutCubic)
            anim.setStartValue(0.0)
            anim.setKeyValueAt(0.5, 35.0)
            anim.setEndValue(0.0)

        anim.start()

    def _reset_offset_anim(self):
        anim = QPropertyAnimation(self, b"anim_offset_y")
        self._offset_anim = anim
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.setStartValue(self._offset_y)
        anim.setEndValue(0.0)
        anim.start()


class _DialogBox(QWidget):

    dismissed = Signal()

    def __init__(self, msg, w, h, name=None, typewriter=True, chardelay=50,
                 bold=False, pinned=True, fdst=False, overflow_mode="wrap",
                 font_family=None, font_size=None, transparent=True, glare=True,
                 sprites=None, sprite_pos=None, speaker_idx=None,
                 sprite_allow_cover=False, sprite_allow_cover_list=None,
                 mode="dialog", default="", max_length=None, allow_empty=False,
                 savecall=None, loadcall=None, settingscall=None):
        global _box

        if overflow_mode not in ("wrap", "overflow"):
            raise ValueError(
                f"overflow_mode must be 'wrap' or 'overflow', got {overflow_mode!r}")
        _get_app()
        super().__init__(None)

        self._mode = mode
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
        self._after_timer = QTimer(self)
        self._after_timer.setSingleShot(True)
        self._after_timer.timeout.connect(self._type_tick)
        self._transparent = transparent
        self._glare = glare
        self._menu_hover_idx = -1
        self._auto_mode = False
        self._skip_mode = False
        self._auto_advance_timer = None
        self.setMouseTracking(True)
        self._sprites = []
        self._sprite_allow_cover = sprite_allow_cover
        self._sprite_allow_cover_list = sprite_allow_cover_list
        self._avatar_hide_animations = {}
        self._savecall = savecall
        self._loadcall = loadcall
        self._settingscall = settingscall
        self._font_family = font_family or "Microsoft YaHei"
        self._font_size = font_size or 20

        self._calc_font_metrics()
        self._calc_name_tag()
        self._calc_canvas_size(msg)

        flags = Qt.FramelessWindowHint | Qt.Tool
        if pinned:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        x, win_y = self._calc_window_position()
        self.setGeometry(x, win_y, self._canvas_w, self._cv_h)
        self.setFixedSize(self._canvas_w, self._cv_h)

        if self._mode == "dialog":
            self._init_typewriter_state(msg)
        self.show()
        _box = self
        self._init_sprites(sprites, sprite_pos, speaker_idx)
        self._init_input_mode(default, max_length, allow_empty)

    def _calc_font_metrics(self):
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        self._body_fs = max(12, int(self._font_size * s))
        self._name_fs = max(12, int(self._font_size * s))
        self._body_font = QFont(self._font_family, self._body_fs, QFont.Bold)
        self._line_h = int(44 * s)
        self._pad_top = int(40 * s)
        self._pad_x = int(40 * s)
        self._name_pad_val = int(28 * s)
        self._dot_radius = int(DOT_RADIUS * s)
        self._dot_gap_x = int(DOT_GAP_X * s)
        self._dot_gap_y = int(DOT_GAP_Y * s)
        self._corner_radius = max(8, int(CORNER_RADIUS * s))
        self._inset = max(2, int(INSET * s))
        sw_raw = 4 if self._bold else 1
        self._stroke_w = max(1, int(sw_raw * s))
        self._triangle_s = int(16 * s)
        self.r = self._corner_radius
        self._menu_fs = max(10, self._body_fs - 3)
        self._menu_height = self._line_h
        self._menu_base_y = self.h - self._menu_height - int(4 * s)
        self._calc_menu_layout()

    def _calc_menu_layout(self):
        font = QFont(self._font_family, self._menu_fs, QFont.Bold)
        fm = QFontMetrics(font)
        total_w = self.w - self._pad_x * 2
        items = MENU_LABELS
        item_widths = [fm.horizontalAdvance(it) for it in items]
        total_text_w = sum(item_widths)
        n = len(items)
        if n > 1:
            target_w = self.w // 2
            gap = (target_w - total_text_w) // (n - 1)
        else:
            gap = 0

        total_menu_w = total_text_w + gap * (n - 1)
        start_x = (self.w - total_menu_w) // 2

        self._menu_text_xs = []
        self._menu_rects = []
        x = start_x
        for i, (it, iw) in enumerate(zip(items, item_widths)):
            self._menu_text_xs.append(x)
            self._menu_rects.append(QRectF(x - 10, 0, iw + 20, self._menu_height))
            x += iw + gap

        self._menu_text_y = int(self._menu_height // 2 + fm.ascent() - fm.height() // 2)

    def _calc_name_tag(self):
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_pad = self._name_pad_val
        name_h = fm.lineSpacing() + name_pad
        if self._name:
            tw = fm.horizontalAdvance(self._name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

    def _calc_canvas_size(self, msg):
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        name_h = self._tag_h
        cv_h = self.h + name_h + int(30 * s) + self._inset
        self._cv_h = cv_h
        self._base_cv_h = cv_h
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
        self._base_canvas_w = self.w + self._inset * 2
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - self.w) // 2

    def _calc_window_position(self):
        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        if self._overflow_mode == "overflow":
            x = (sw - self.w) // 2 - self._dialog_left
        else:
            x = (sw - self._canvas_w) // 2
        dialog_screen_y = sh - self.h - 60
        win_y = dialog_screen_y - self._dialog_top
        return x, win_y

    def _init_input_mode(self, default, max_length, allow_empty):
        self.result = None
        self._input_text = default
        self._cursor_pos = len(default)
        self._max_length = max_length
        self._allow_empty = allow_empty
        self._cursor_visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_cursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)

        QApplication.processEvents()
        self.raise_()
        self.activateWindow()
        if self._mode == "input":
            self._blink_timer.start(530)
            self.setFocus()

    def _init_sprites(self, sprites, sprite_pos, speaker_idx):
        raw = _normalize_sprites(sprites)
        count = len(raw)
        if count == 0:
            return
        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, count, allow_cover)
        for i in range(count):
            sw = _SpriteWindow(raw[i], positions[i], i == speaker_idx, self._pinned)
            self._sprites.append(sw)

    def _update_sprites(self, sprites, sprite_pos, speaker_idx, avatar_map=None):
        raw = _normalize_sprites(sprites)
        new_count = len(raw)
        old_count = len(self._sprites)

        if new_count == 0:
            self._destroy_sprites()
            return

        if old_count == 0 or (new_count != old_count and avatar_map is None and old_count > 0):
            self._replace_all_sprites(raw, new_count, sprite_pos, speaker_idx)
            return

        if avatar_map is not None and len(avatar_map) > 0 and old_count > 0:
            self._update_sprites_with_avatars(raw, new_count, sprite_pos, speaker_idx, avatar_map)
            return

        self._update_sprite_positions(raw, new_count, old_count, sprite_pos, speaker_idx)

    def _replace_all_sprites(self, raw, new_count, sprite_pos, speaker_idx):
        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, new_count, allow_cover)
        for i in range(new_count):
            sw = _SpriteWindow(raw[i], positions[i], i == speaker_idx, self._pinned)
            self._sprites.append(sw)

    def _update_sprites_with_avatars(self, raw, new_count, sprite_pos, speaker_idx, avatar_map):
        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, new_count, allow_cover)

        old_by_avatar = {}
        for old_i, sw in enumerate(self._sprites):
            av = getattr(sw, '_avatar', None)
            if av is not None:
                old_by_avatar[av] = old_i

        # Re-assign positions based on old avatar positions
        allow_cover_list = self._sprite_allow_cover_list
        has_cover = allow_cover_list is not None and any(allow_cover_list[:new_count])

        if old_by_avatar and not has_cover:
            old_x_frac = {av: sw._x_frac for av, sw in _iter_avatar_sprites(self._sprites)}
            if old_x_frac:
                self._reassign_positions_by_avatar(positions, old_x_frac, avatar_map, new_count)

        new_sprites = [None] * new_count
        used_old_indices = set()

        for new_i in range(new_count):
            new_av = avatar_map[new_i] if new_i < len(avatar_map) else None
            if new_av is not None and new_av in old_by_avatar:
                old_i = old_by_avatar[new_av]
                sw = self._sprites[old_i]
                sw.update_state(image_data=None if _same_image(raw[new_i], sw) else raw[new_i],
                                x_frac=positions[new_i], is_speaker=(new_i == speaker_idx))
                new_sprites[new_i] = sw
                used_old_indices.add(old_i)

        for new_i in range(new_count):
            if new_sprites[new_i] is None:
                sw = _SpriteWindow(raw[new_i], positions[new_i], new_i == speaker_idx, self._pinned)
                sw._pixmap_data_ref = raw[new_i]
                new_sprites[new_i] = sw

        for old_i, sw in enumerate(self._sprites):
            if old_i not in used_old_indices:
                av = getattr(sw, '_avatar', None)
                animation = self._avatar_hide_animations.get(av, "fade") if av is not None else "fade"
                sw.destroy_sprite(animation)

        self._sprites = new_sprites

    @staticmethod
    def _reassign_positions_by_avatar(positions, old_x_frac, avatar_map, new_count):
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

    def _update_sprite_positions(self, raw, new_count, old_count, sprite_pos, speaker_idx):
        allow_cover = self._sprite_allow_cover_list if self._sprite_allow_cover_list is not None else self._sprite_allow_cover
        positions = _normalize_sprite_pos(sprite_pos, new_count, allow_cover)

        for i in range(min(new_count, old_count)):
            same = _same_image(raw[i], self._sprites[i])
            self._sprites[i].update_state(
                image_data=None if same else raw[i],
                x_frac=positions[i], is_speaker=(i == speaker_idx))
            if not same:
                self._sprites[i]._pixmap_data_ref = raw[i]

        for i in range(old_count, new_count):
            sw = _SpriteWindow(raw[i], positions[i], i == speaker_idx, self._pinned)
            sw._pixmap_data_ref = raw[i]
            self._sprites.append(sw)

        for i in range(new_count, old_count):
            av = getattr(self._sprites[i], '_avatar', None)
            animation = self._avatar_hide_animations.get(av, "fade") if av is not None else "fade"
            self._sprites[i].destroy_sprite(animation)
        self._sprites = self._sprites[:new_count]

    def _update_sprites_state_only(self, speaker_idx):
        for i, sw in enumerate(self._sprites):
            sw.update_state(is_speaker=(i == speaker_idx))

    def _destroy_sprites(self):
        for sw in self._sprites:
            av = getattr(sw, '_avatar', None)
            animation = self._avatar_hide_animations.get(av, "fade") if av is not None else "fade"
            sw.destroy_sprite(animation)
        self._sprites = []

    def closeEvent(self, event):
        self._after_timer.stop()
        self._stop_auto_advance()
        try:
            self._blink_timer.stop()
        except Exception:
            pass
        self._destroy_sprites()
        if self._mode == "input":
            self.result = None
        self.dismissed.emit()
        super().closeEvent(event)

    def _update_content(self, msg, typewriter, chardelay, bold, overflow_mode, name=None,
                        font_family=None, font_size=None, transparent=None, glare=None,
                        sprites=None, sprite_pos=None, speaker_idx=None,
                        avatar_sprite_map=None, sprite_allow_cover=None,
                        sprite_allow_cover_list=None, avatar_hide_animations=None,
                        mode=None, default=None, max_length=None, allow_empty=None,
                        pinned=None, savecall=None, loadcall=None, settingscall=None):
        self._after_timer.stop()
        self._stop_auto_advance()

        self._apply_pinned(pinned)
        self._savecall = savecall
        self._loadcall = loadcall
        self._settingscall = settingscall

        self._apply_content_params(mode, overflow_mode, typewriter, chardelay, bold,
                                    transparent, glare, sprite_allow_cover, sprite_allow_cover_list,
                                    default, max_length, allow_empty, name)
        self._apply_font_params(font_family, font_size)
        self._recalc_name_tag()
        self._recalc_canvas(msg)
        self._reposition_window()

        if self._mode == "dialog":
            self._init_typewriter_state(msg)
            if self._skip_mode:
                self._start_auto_advance()
            try:
                self._blink_timer.stop()
            except Exception:
                pass
        else:
            try:
                self._blink_timer.stop()
            except Exception:
                pass
            self._blink_timer.start(530)
            self._recalc_input_geometry()

        self._refresh_sprites(sprites, sprite_pos, speaker_idx, avatar_sprite_map,
                               avatar_hide_animations)

        self.show()
        self.raise_()
        self.activateWindow()
        if self._mode == "input":
            self.setFocus()

    def _apply_pinned(self, pinned):
        if pinned is None:
            return
        pinned = bool(pinned)
        if pinned == self._pinned:
            return

        self._pinned = pinned
        self.setWindowFlag(Qt.WindowStaysOnTopHint, pinned)
        for sprite in self._sprites:
            sprite._pinned = pinned
            sprite.setWindowFlag(Qt.WindowStaysOnTopHint, pinned)
            sprite.show()

    def _apply_content_params(self, mode, overflow_mode, typewriter, chardelay, bold,
                               transparent, glare, sallow_cover, sallow_cover_list,
                               default, max_length, allow_empty, name):
        if mode is not None:
            self._mode = mode
        self._overflow_mode = overflow_mode
        self._typewriter = False if self._skip_mode else typewriter
        self._chardelay = chardelay
        self._bold = bold
        self._typing = False
        self._typing_done = False
        if transparent is not None:
            self._transparent = transparent
        if glare is not None:
            self._glare = glare
        if sallow_cover is not None:
            self._sprite_allow_cover = sallow_cover
        if sallow_cover_list is not None:
            self._sprite_allow_cover_list = sallow_cover_list
        if default is not None:
            self._input_text = default
            self._cursor_pos = len(default)
        self._max_length = max_length
        if allow_empty is not None:
            self._allow_empty = allow_empty
        self._name = name

    def _apply_font_params(self, font_family, font_size):
        if font_family is not None:
            self._font_family = font_family
        else:
            self._font_family = "Microsoft YaHei"
        if font_size is not None:
            self._font_size = font_size
        else:
            self._font_size = 20
        self._calc_font_metrics()

    def _recalc_name_tag(self):
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        f_name = QFont(self._font_family, self._name_fs, QFont.Bold)
        fm = QFontMetrics(f_name)
        name_pad = int(28 * s)
        name_h = fm.lineSpacing() + name_pad
        if self._name:
            tw = fm.horizontalAdvance(self._name)
            self._tag_w = int(tw + name_pad * 2) + int(80 * s)
        else:
            self._tag_w = 0
        self._tag_h = name_h
        self._tag_top = int(30 * s) + self._inset
        self._tag_r = 12

    def _recalc_canvas(self, msg):
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        name_h = self._tag_h
        cv_h = self.h + name_h + int(30 * s) + self._inset
        self._cv_h = cv_h
        self._base_cv_h = cv_h
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
                self._base_cv_h = cv_h
        self._vert_overflow = vert_overflow
        canvas_w += self._inset * 2
        self._canvas_w = canvas_w
        self._base_canvas_w = self.w + self._inset * 2
        if self._overflow_mode == "overflow":
            self._dialog_left = self._inset
        else:
            self._dialog_left = (canvas_w - self.w) // 2

    def _reposition_window(self):
        x, win_y = self._calc_window_position()
        self.setGeometry(x, win_y, self._canvas_w, self._cv_h)
        self.setFixedSize(self._canvas_w, self._cv_h)

    def _refresh_sprites(self, sprites, sprite_pos, speaker_idx, avatar_sprite_map,
                          avatar_hide_animations=None):
        if avatar_hide_animations is not None:
            self._avatar_hide_animations = avatar_hide_animations
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
                hwnd, DWMWA_BORDER_COLOR,
                ctypes.byref(ctypes.c_int(0xFFFFFFFE)),
                ctypes.sizeof(ctypes.c_int))
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
        self._after_timer.start(self._chardelay)

    def _type_tick(self):
        if self._cur_line >= len(self._typewriter_lines):
            self._typing = False
            self._typing_done = True
            if self._auto_mode or self._skip_mode:
                self._start_auto_advance()
            return

        self._cur_char += 1
        if self._cur_char > self._line_visible_len(self._typewriter_lines[self._cur_line]):
            self._cur_line += 1
            self._cur_char = 0
            self._type_tick()
            return

        self.update()
        self._after_timer.start(self._chardelay)

    def _finish_typewriter(self):
        self._after_timer.stop()
        self._typing = False
        self._typing_done = True
        self._cur_line = len(self._typewriter_lines)
        self._cur_char = 0
        self.update()
        if (self._auto_mode or self._skip_mode) and self._full_msg:
            self._start_auto_advance()

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
        self._draw_menu_items(painter, dl, top)

        if self._mode == "dialog":
            if self._overflow_mode != "overflow":
                painter.setClipPath(path)
            self._draw_text(painter, dl, top)
        else:
            if self._overflow_mode != "overflow":
                clip_path = QPainterPath()
                clip_path.addRoundedRect(QRectF(dl, top + 3, w, h - 6), r, r)
                painter.setClipPath(clip_path)
            self._draw_input_text(painter, dl)

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
                color = QColor(DOT_COLOR) if self._transparent else _blend(DOT_COLOR, FADE_TO, 1.0 - 0.5 * t)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), dr, dr)
                x += step_x
            y += row_h
            row += 1
        painter.restore()

    def _draw_outline(self, painter, dl, top, w, h, r):
        painter.setPen(QPen(QColor(BORDER_COLOR), 3))
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

    def _draw_menu_items(self, painter, dl, top):
        if not self._menu_rects:
            return
        font = QFont(self._font_family, self._body_fs, QFont.Bold)
        painter.setFont(font)
        for i, item in enumerate(MENU_LABELS):
            if not self._is_menu_enabled(i):
                painter.setPen(MENU_DISABLED_COLOR)
            elif i == self._menu_hover_idx or (i == 1 and self._skip_mode) or (i == 2 and self._auto_mode):
                painter.setPen(MENU_HOVER_COLOR)
            else:
                painter.setPen(MENU_COLOR)
            tx = dl + self._menu_text_xs[i]
            ty = top + self._menu_base_y + self._menu_text_y
            painter.drawText(int(tx), ty, item)

    def _text_area_width(self):
        return self.w - self._pad_x * 2

    def _body_style_font(self, bold=False, italic=False):
        weight = QFont.Black if bold else QFont.Bold
        font = QFont(self._font_family, self._body_fs, weight)
        font.setItalic(italic)
        return font

    def _parse_rich_text(self, text):
        segments = []
        bold = False
        italic = False
        buf = ""
        i = 0
        tags = {
            "{b}": ("bold", True),
            "{/b}": ("bold", False),
            "{i}": ("italic", True),
            "{/i}": ("italic", False),
        }
        while i < len(text):
            matched = None
            for tag, state in tags.items():
                if text.startswith(tag, i):
                    matched = (tag, state)
                    break
            if matched:
                if buf:
                    segments.append((buf, bold, italic))
                    buf = ""
                attr, value = matched[1]
                if attr == "bold":
                    bold = value
                else:
                    italic = value
                i += len(matched[0])
            else:
                buf += text[i]
                i += 1
        if buf:
            segments.append((buf, bold, italic))
        return segments

    def _plain_text(self, line):
        if isinstance(line, str):
            return line
        return "".join(seg[0] for seg in line)

    def _line_visible_len(self, line):
        return len(self._plain_text(line))

    def _take_visible_chars(self, line, count):
        if isinstance(line, str):
            return line[:count]
        remaining = count
        result = []
        for text, bold, italic in line:
            if remaining <= 0:
                break
            part = text[:remaining]
            if part:
                result.append((part, bold, italic))
            remaining -= len(part)
        return result

    def _line_width(self, line):
        if isinstance(line, str):
            return QFontMetrics(self._body_style_font()).horizontalAdvance(line)
        width = 0
        for text, bold, italic in line:
            width += QFontMetrics(self._body_style_font(bold, italic)).horizontalAdvance(text)
        return width

    def _append_segment(self, segments, text, bold, italic):
        if not text:
            return
        if segments and segments[-1][1] == bold and segments[-1][2] == italic:
            old_text, old_bold, old_italic = segments[-1]
            segments[-1] = (old_text + text, old_bold, old_italic)
        else:
            segments.append((text, bold, italic))

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

    def _wrap_rich_segments(self, segments, max_w):
        if self._line_width(segments) <= max_w:
            return [segments]
        lines = []
        current = []
        current_w = 0
        for text, bold, italic in segments:
            fm = QFontMetrics(self._body_style_font(bold, italic))
            for ch in text:
                ch_w = fm.horizontalAdvance(ch)
                if current and current_w + ch_w > max_w:
                    lines.append(current)
                    current = []
                    current_w = 0
                self._append_segment(current, ch, bold, italic)
                current_w += ch_w
        if current:
            lines.append(current)
        return lines

    def _process_lines(self, text, font, max_w):
        parsed_lines = [self._parse_rich_text(line) for line in text.split('\n')]
        has_rich = any(
            bold or italic
            for line in parsed_lines
            for _, bold, italic in line
        )
        if has_rich:
            if self._overflow_mode == "overflow":
                return parsed_lines
            if self._overflow_mode == "wrap":
                result = []
                for line in parsed_lines:
                    result.extend(self._wrap_rich_segments(line, max_w))
                return result
            return parsed_lines
        if self._overflow_mode == "overflow":
            return text.split('\n')
        if self._overflow_mode == "wrap":
            result = []
            for line in text.split('\n'):
                result.extend(self._wrap_line(line, font, max_w))
            return result
        return text.split('\n')

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
            for j, (px, py, full_text) in enumerate(self._typewriter_positions):
                if j < self._cur_line:
                    shown = full_text
                elif j == self._cur_line:
                    shown = self._take_visible_chars(full_text, self._cur_char)
                else:
                    shown = ""
                if shown:
                    self._draw_stroked(painter, dl + px, py, shown, font)
        elif not self._typing and self._typing_done:
            lines = self._process_lines(msg, font, self._text_area_width())
            positions = self._layout_text_positions(lines)
            for px, py, line in positions:
                self._draw_stroked(painter, dl + px, py, line, font)

    def _draw_stroked(self, painter, x, y, text, font):
        if not isinstance(text, str):
            self._draw_stroked_segments(painter, x, y, text)
            return
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

    def _draw_stroked_segments(self, painter, x, y, segments):
        sw = 4 if self._bold else 1
        cur_x = x
        for text, bold, italic in segments:
            if not text:
                continue
            font = self._body_style_font(bold, italic)
            painter.setFont(font)
            fm = QFontMetrics(font)
            text_y = int(y + fm.ascent() - fm.height() // 2)
            for step in range(48):
                angle = 2 * math.pi * step / 24
                dx = int(math.cos(angle) * sw)
                dy = int(math.sin(angle) * sw)
                painter.setPen(QColor("#000000"))
                painter.drawText(int(cur_x) + dx, text_y + dy, text)
            painter.setPen(QColor("#ffffff"))
            if bold:
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    painter.drawText(int(cur_x) + dx, text_y + dy, text)
            else:
                painter.drawText(int(cur_x), text_y, text)
            cur_x += fm.horizontalAdvance(text)

    def mousePressEvent(self, event):
        if _box is None:
            return
        if event.button() == Qt.LeftButton:
            hit_idx = self._menu_hit_index(event.position())
            if hit_idx == 0:
                self._show_history()
                return
            if hit_idx == 1:
                self._skip_mode = not self._skip_mode
                if self._skip_mode:
                    self._auto_mode = False
                    self._typewriter = False
                    if self._typing:
                        self._finish_typewriter()
                    elif self._typing_done and self._full_msg:
                        self._start_auto_advance()
                else:
                    self._stop_auto_advance()
                self.update()
                return
            if hit_idx == 2:
                self._auto_mode = not self._auto_mode
                if self._auto_mode:
                    self._skip_mode = False
                    if self._typing_done and self._full_msg:
                        self._start_auto_advance()
                elif not self._auto_mode:
                    self._stop_auto_advance()
                self.update()
                return
            if hit_idx == 3:
                if self._savecall is not None:
                    _call_menu_callback(self._savecall)
                return
            if hit_idx == 4:
                if self._loadcall is not None:
                    _call_menu_callback(self._loadcall)
                return
            if hit_idx == 5:
                if self._settingscall is not None:
                    _call_menu_callback(self._settingscall)
                return
            if hit_idx != -1:
                return
            self._stop_auto_advance()
            if self._mode == "input":
                self._submit()
            else:
                self._on_click()

    def mouseMoveEvent(self, event):
        new_idx = self._menu_hit_index(event.position())
        if new_idx != -1 and not self._is_menu_enabled(new_idx):
            new_idx = -1
        if new_idx != self._menu_hover_idx:
            self._menu_hover_idx = new_idx
            self.update()

    def enterEvent(self, event):
        pass

    def leaveEvent(self, event):
        if self._menu_hover_idx != -1:
            self._menu_hover_idx = -1
            self.update()

    def _menu_hit_index(self, pos):
        dl = self._dialog_left
        top = self._dialog_top
        px = pos.x() - dl
        py = pos.y() - top - self._menu_base_y
        for i, rect in enumerate(self._menu_rects):
            if rect.contains(QPointF(px, py)):
                return i
        return -1

    def _menu_hit_test(self, pos):
        return self._menu_hit_index(pos) != -1

    def _is_menu_enabled(self, idx):
        if idx == 3:
            return self._savecall is not None
        if idx == 4:
            return self._loadcall is not None
        if idx == 5:
            return self._settingscall is not None
        return True

    def keyPressEvent(self, event):
        if self._mode == "input":
            self._handle_input_key(event)
        elif event.key() == Qt.Key_Escape:
            self._done()

    def _handle_input_key(self, event):
        key = event.key()
        text = event.text()
        mods = event.modifiers()

        if key == Qt.Key_Return or key == Qt.Key_Enter:
            if mods & Qt.ShiftModifier:
                self._submit()
            else:
                self._insert_text("\n")
            return
        if key == Qt.Key_Escape:
            self._cancel()
            return
        if key == Qt.Key_Backspace:
            self._delete_before_cursor()
            return
        if key == Qt.Key_Delete:
            self._delete_after_cursor()
            return
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End):
            self._move_cursor(key)
            return
        if key == Qt.Key_V and mods == Qt.ControlModifier:
            self._paste_from_clipboard()
            return
        if text and len(text) > 0 and ord(text[0]) >= 32:
            self._insert_text(text)

    def _move_cursor(self, key):
        if key == Qt.Key_Left:
            self._cursor_pos = max(0, self._cursor_pos - 1)
        elif key == Qt.Key_Right:
            self._cursor_pos = min(len(self._input_text), self._cursor_pos + 1)
        elif key == Qt.Key_Home:
            self._cursor_pos = 0
        elif key == Qt.Key_End:
            self._cursor_pos = len(self._input_text)
        self._cursor_visible = True
        self.update()

    def _delete_before_cursor(self):
        if self._cursor_pos > 0:
            self._input_text = self._input_text[:self._cursor_pos - 1] + self._input_text[self._cursor_pos:]
            self._cursor_pos -= 1
            self._cursor_visible = True
            self.update()
            self._recalc_input_geometry()

    def _delete_after_cursor(self):
        if self._cursor_pos < len(self._input_text):
            self._input_text = self._input_text[:self._cursor_pos] + self._input_text[self._cursor_pos + 1:]
            self._cursor_visible = True
            self.update()
            self._recalc_input_geometry()

    def _paste_from_clipboard(self):
        from PySide6.QtWidgets import QApplication as QA
        cb = QA.clipboard()
        if cb:
            self._insert_text(cb.text())

    def _start_auto_advance(self):
        self._stop_auto_advance()
        if self._skip_mode:
            wait_ms = 100
        else:
            wait_ms = max(1000, 1500 + len(self._full_msg) * 20)
        self._auto_advance_timer = QTimer(self)
        self._auto_advance_timer.setSingleShot(True)
        self._auto_advance_timer.timeout.connect(self._done)
        self._auto_advance_timer.start(wait_ms)

    def _stop_auto_advance(self):
        if self._auto_advance_timer:
            try:
                self._auto_advance_timer.stop()
            except Exception:
                pass
            self._auto_advance_timer.deleteLater()
            self._auto_advance_timer = None

    def _show_history(self):
        if not _history:
            return
        was_auto = self._auto_mode
        was_skip = self._skip_mode
        self._stop_auto_advance()
        global _box
        saved_box = _box
        _box = None
        from dokibox.historybox import historybox
        historybox(pinned=self._pinned)
        _box = saved_box
        if was_auto or was_skip:
            self._auto_mode = was_auto
            self._skip_mode = was_skip
            if self._typing_done and self._full_msg:
                self._start_auto_advance()

    def _on_click(self):
        if _box is None:
            return
        if self._typewriter and self._typing:
            self._finish_typewriter()
        else:
            self._done()

    def _done(self):
        if _box is None:
            return
        self.dismissed.emit()

    def _submit(self):
        if not self._allow_empty and not self._input_text.strip():
            return
        self.result = self._input_text
        self.dismissed.emit()

    def _cancel(self):
        self.result = None
        self.dismissed.emit()

    def _recalc_input_geometry(self):
        if self._mode != "input" or self._overflow_mode != "overflow":
            return
        dpi = _get_dpi_scale()
        s = 1.0 / dpi
        text = self._input_text
        font = self._body_font
        fm = QFontMetrics(font)

        raw_lines = text.split('\n') if text else [""]
        max_line_w = max((fm.horizontalAdvance(rl) for rl in raw_lines), default=0)
        needed_w = max(int(max_line_w + int(80 * s)), self.w)
        canvas_w = needed_w + self._inset * 2

        num_lines = len(raw_lines)
        text_h_needed = self._pad_top + num_lines * self._line_h
        cv_h = self._base_cv_h
        if text_h_needed > self.h:
            cv_h = self._base_cv_h + int(text_h_needed - self.h + self._pad_top)

        if canvas_w == self._canvas_w and cv_h == self._cv_h:
            return

        self._canvas_w = canvas_w
        self._cv_h = cv_h
        self._dialog_left = self._inset

        sw = QApplication.primaryScreen().size().width()
        sh = QApplication.primaryScreen().size().height()
        x = (sw - self.w) // 2 - self._dialog_left
        dialog_screen_y = sh - self.h - 60
        win_y = dialog_screen_y - self._dialog_top
        self.setGeometry(x, win_y, canvas_w, cv_h)
        self.setFixedSize(canvas_w, cv_h)

    def _toggle_cursor(self):
        if self._mode == "input" and self.hasFocus():
            self._cursor_visible = not self._cursor_visible
            self.update()

    def _insert_text(self, text):
        if self._max_length is not None:
            remaining = self._max_length - len(self._input_text)
            if remaining <= 0:
                return
            if len(text) > remaining:
                text = text[:remaining]
        self._input_text = (self._input_text[:self._cursor_pos]
                            + text + self._input_text[self._cursor_pos:])
        self._cursor_pos += len(text)
        self._cursor_visible = True
        self.update()
        self._recalc_input_geometry()

    def _draw_input_text(self, painter, dl):
        text = self._input_text
        font = self._body_font
        x = dl + self._pad_x
        y = self._dialog_top + self._pad_top + self._line_h // 2

        painter.setFont(font)
        fm = QFontMetrics(font)
        max_w = self.w - self._pad_x * 2

        if self._overflow_mode == "wrap" and text:
            self._draw_input_wrap(painter, x, y, text, font, fm, max_w)
        elif self._overflow_mode == "overflow" and text:
            self._draw_input_overflow(painter, x, y, text, font, fm)
        else:
            self._draw_input_simple(painter, x, y, text, font, fm, max_w)

    def _draw_input_wrap(self, painter, x, base_y, text, font, fm, max_w):
        segments = text.split('\n')
        lines = []
        positions = []
        raw_pos = 0
        for seg in segments:
            wrapped = self._wrap_line(seg, font, max_w)
            for wl in wrapped:
                lines.append(wl)
                positions.append(raw_pos)
                raw_pos += len(wl)
            raw_pos += 1

        line_h = self._line_h
        for li, line in enumerate(lines):
            self._draw_stroked(painter, x, base_y + li * line_h, line, font)

        if self._mode == "input" and self.hasFocus() and self._cursor_visible and self._cursor_pos >= 0:
            cursor_line_idx, cursor_col_offset = _find_cursor_in_wrap(lines, positions, self._cursor_pos)
            cursor_x = x + fm.horizontalAdvance(lines[cursor_line_idx][:cursor_col_offset])
            cursor_h = fm.ascent() + fm.descent()
            cur_y = int(base_y + cursor_line_idx * line_h - fm.height() // 2)
            painter.setPen(QPen(QColor("#CF80B5"), 2))
            painter.drawLine(int(cursor_x), cur_y, int(cursor_x), cur_y + cursor_h)

    def _draw_input_overflow(self, painter, x, base_y, text, font, fm):
        raw_lines = text.split('\n')
        line_h = self._line_h

        cursor_line_idx, cursor_col_offset = _find_cursor_in_overflow(raw_lines, self._cursor_pos, text)

        for li, rl in enumerate(raw_lines):
            self._draw_stroked(painter, x, base_y + li * line_h, rl, font)

        if self._mode == "input" and self.hasFocus() and self._cursor_visible and self._cursor_pos >= 0:
            cursor_x = x + fm.horizontalAdvance(raw_lines[cursor_line_idx][:cursor_col_offset])
            cursor_h = fm.ascent() + fm.descent()
            cur_y = int(base_y + cursor_line_idx * line_h - fm.height() // 2)
            painter.setPen(QPen(QColor("#CF80B5"), 2))
            painter.drawLine(int(cursor_x), cur_y, int(cursor_x), cur_y + cursor_h)

    def _draw_input_simple(self, painter, x, base_y, text, font, fm, max_w):
        if self._mode == "input" and self.hasFocus() and fm.horizontalAdvance(text) <= max_w:
            cursor_x = x + fm.horizontalAdvance(text[:self._cursor_pos])
        elif self._mode == "input" and self.hasFocus() and self._cursor_pos >= 0:
            full_w = fm.horizontalAdvance(text)
            cursor_rel = fm.horizontalAdvance(text[:self._cursor_pos])
            scroll = max(0, cursor_rel - max_w + fm.horizontalAdvance(" "))
            scroll = min(scroll, max(0, full_w - max_w))
            cursor_x = x + cursor_rel - scroll

        if text:
            self._draw_stroked(painter, x, base_y, text, font)

        if self._mode == "input" and self.hasFocus() and self._cursor_visible and self._cursor_pos >= 0:
            if fm.horizontalAdvance(text) > max_w:
                full_w = fm.horizontalAdvance(text)
                cursor_rel = fm.horizontalAdvance(text[:self._cursor_pos])
                scroll = max(0, cursor_rel - max_w + fm.horizontalAdvance(" "))
                scroll = min(scroll, max(0, full_w - max_w))
                cursor_x = x + cursor_rel - scroll
            cursor_h = fm.ascent() + fm.descent()
            cursor_y = int(base_y - fm.height() // 2)
            painter.setPen(QPen(QColor("#CF80B5"), 2))
            painter.drawLine(int(cursor_x), cursor_y, int(cursor_x), cursor_y + cursor_h)

    def inputMethodEvent(self, event):
        commit = event.commitString()
        if commit:
            self._insert_text(commit)

    def inputMethodQuery(self, query):
        if query == Qt.ImCursorRectangle:
            return self._calc_im_cursor_rect()
        if query == Qt.ImEnabled:
            return True
        return super().inputMethodQuery(query)

    def _calc_im_cursor_rect(self):
        font = self._body_font
        fm = QFontMetrics(font)
        x = self._dialog_left + self._pad_x
        y = self._dialog_top + self._pad_top + self._line_h // 2 - fm.ascent()
        cursor_pos = self._cursor_pos

        if self._overflow_mode == "wrap" and self._input_text:
            cursor_x, y = _calc_im_wrap_cursor(self, font, fm, x, y, cursor_pos)
        elif self._overflow_mode == "overflow" and self._input_text:
            cursor_x, y = _calc_im_overflow_cursor(self, font, fm, x, y, cursor_pos)
        else:
            cursor_x = x + fm.horizontalAdvance(self._input_text[:cursor_pos])
        return QRectF(cursor_x, y, 2, fm.height())


def _call_menu_callback(callback):
    global _box, _menu_callback_box
    saved_box = _box
    saved_callback_box = _menu_callback_box
    _menu_callback_box = saved_box
    _box = None
    try:
        callback()
    finally:
        _box = saved_box
        _menu_callback_box = saved_callback_box


def _iter_avatar_sprites(sprites):
    for sw in sprites:
        av = getattr(sw, '_avatar', None)
        if av is not None:
            yield av, sw


def _same_image(raw_data, sw):
    return hasattr(sw, '_pixmap_data_ref') and raw_data == sw._pixmap_data_ref


def _find_cursor_in_wrap(lines, positions, cursor_pos):
    cursor_line_idx = len(lines) - 1
    cursor_col_offset = len(lines[-1]) if lines else 0
    for li in range(len(lines)):
        start = positions[li]
        end = start + len(lines[li])
        if start <= cursor_pos <= end:
            return li, cursor_pos - start
        if cursor_pos < start:
            return max(0, li - 1), len(lines[max(0, li - 1)])
    return cursor_line_idx, cursor_col_offset


def _find_cursor_in_overflow(raw_lines, cursor_pos, text):
    cursor_line_idx = len(raw_lines) - 1
    cursor_col_offset = len(raw_lines[-1]) if raw_lines else 0
    raw_pos = 0
    for li, rl in enumerate(raw_lines):
        if raw_pos + len(rl) >= cursor_pos:
            return li, cursor_pos - raw_pos
        raw_pos += len(rl) + 1
    if cursor_pos >= len(text):
        return cursor_line_idx, cursor_col_offset
    return cursor_line_idx, cursor_col_offset


def _calc_im_wrap_cursor(self, font, fm, x, y, cursor_pos):
    max_w = self.w - self._pad_x * 2
    segments = self._input_text.split('\n')
    lines = []
    positions = []
    raw_pos = 0
    for seg in segments:
        wrapped = self._wrap_line(seg, font, max_w)
        for wl in wrapped:
            lines.append(wl)
            positions.append(raw_pos)
            raw_pos += len(wl)
        raw_pos += 1

    cursor_line = 0
    cursor_col = 0
    for li in range(len(lines)):
        start = positions[li]
        end = start + len(lines[li])
        if start <= cursor_pos <= end:
            cursor_line = li
            cursor_col = cursor_pos - start
            break
        if cursor_pos < start:
            cursor_line = max(0, li - 1)
            cursor_col = len(lines[cursor_line])
            break
    else:
        if lines:
            cursor_line = len(lines) - 1
            cursor_col = len(lines[-1])
    cursor_x = x + fm.horizontalAdvance(lines[cursor_line][:cursor_col])
    y = y + cursor_line * self._line_h + self._line_h // 2
    return cursor_x, y


def _calc_im_overflow_cursor(self, font, fm, x, y, cursor_pos):
    raw_lines = self._input_text.split('\n')
    cursor_line = 0
    cursor_col = cursor_pos
    raw_pos = 0
    for li, rl in enumerate(raw_lines):
        if raw_pos + len(rl) >= cursor_pos:
            cursor_line = li
            cursor_col = cursor_pos - raw_pos
            break
        raw_pos += len(rl) + 1
    if cursor_pos >= len(self._input_text):
        cursor_line = len(raw_lines) - 1
        cursor_col = len(raw_lines[-1])
    cursor_x = x + fm.horizontalAdvance(raw_lines[cursor_line][:cursor_col])
    y = y + cursor_line * self._line_h + self._line_h // 2
    return cursor_x, y


def _destroy_box():
    global _box
    if _box is not None:
        try:
            _box._after_timer.stop()
        except Exception:
            pass
        try:
            _box._blink_timer.stop()
        except Exception:
            pass
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



def _get_shared_box():
    return _box


def dismiss() -> bool:
    """Request that the currently displayed dialogbox be dismissed.

    This also works inside save, load, and settings callbacks.  The dismissal
    is queued until the current Qt event has finished so callback bookkeeping
    can be restored safely.

    Returns True when an active dialogbox was found, otherwise False.
    """
    target_box = _menu_callback_box if _menu_callback_box is not None else _box
    if target_box is None:
        return False

    def dismiss_target():
        if _box is not target_box:
            return
        try:
            target_box._done()
        except RuntimeError:
            # The underlying Qt object may already have been deleted.
            pass

    QTimer.singleShot(0, dismiss_target)
    return True


def dialogbox(msg: str = "", w: Optional[int] = _UNSET, h: Optional[int] = _UNSET,
              name: Optional[str] = _UNSET, typewriter: bool = _UNSET,
              chardelay: int = _UNSET, bold: bool = _UNSET, pinned: bool = _UNSET,
              fdst: bool = _UNSET, overflow_mode: str = _UNSET,
              font_family: str = _UNSET, font_size: int = _UNSET,
              transparent: bool = _UNSET, glare: bool = _UNSET,
              sprites: Optional[Union[str, bytes, List[Union[str, bytes]]]] = _UNSET,
              sprite_allow_cover: bool = _UNSET,
              savecall=None, loadcall=None, settingscall=None) -> None:
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
        fdst:          If True, destroys the window when dismissed.
        overflow_mode: how to handle text exceeding the dialog width:
                       'wrap'    – wrap text to the next line (default).
                       'overflow' – expand the window so text can render past the dialog boundary.
        transparent:   apply alpha gradient from top to bottom, making the body see-through (default True).
        glare:         draw a white semicircular highlight at the bottom of the dialog (default True).
        sprites:       list of Avatar calls specifying character and position.
        sprite_allow_cover: If True, allow sprites at the same position to overlap (default False).
        savecall:      callback for the "Save" menu button. Overrides the global
                       ``dokibox.dialogbox.save`` if set. When None and no global
                       is set, the button appears disabled (#AA646F).
        loadcall:      callback for the "Load" menu button. Same priority rules
                       as savecall.
        settingscall:  callback for the "Settings" menu button. Same priority
                       rules as savecall.

    Global callbacks::
        dokibox.dialogbox.save = my_save_func
        dokibox.dialogbox.load = my_load_func
        dokibox.dialogbox.settings = my_settings_func
        These are fallbacks when savecall / loadcall / settingscall are not
        provided. If neither is set, the corresponding menu button is disabled.

    Global settings::
        Every option other than ``msg`` and the per-button callbacks can also
        be set on the function, for example ``dokibox.dialogbox.chardelay = 5``.
        An argument supplied to this call takes priority over its global value.
        The initial global values are the same as the original defaults.

    Usage:
        sayori = Avatar(name="Sayori", emotes={"happy": ["sayori_happy.png"]})
        yuri = Avatar(name="Yuri", emotes={"shocked": ["yuri_shocked.png"]})
        dokibox.dialogbox("Hello!", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "shocked")])
        dokibox.dialogbox("Hi!", name=yuri)  # sprites persist, speaker auto-detected
    """
    global _box

    # Per-call arguments have priority.  Only arguments that were genuinely
    # omitted use the corresponding global setting.
    w = dialogbox.w if w is _UNSET else w
    h = dialogbox.h if h is _UNSET else h
    name = dialogbox.name if name is _UNSET else name
    typewriter = dialogbox.typewriter if typewriter is _UNSET else typewriter
    chardelay = dialogbox.chardelay if chardelay is _UNSET else chardelay
    bold = dialogbox.bold if bold is _UNSET else bold
    pinned = dialogbox.pinned if pinned is _UNSET else pinned
    fdst = dialogbox.fdst if fdst is _UNSET else fdst
    overflow_mode = dialogbox.overflow_mode if overflow_mode is _UNSET else overflow_mode
    font_family = dialogbox.font_family if font_family is _UNSET else font_family
    font_size = dialogbox.font_size if font_size is _UNSET else font_size
    transparent = dialogbox.transparent if transparent is _UNSET else transparent
    glare = dialogbox.glare if glare is _UNSET else glare
    sprites = dialogbox.sprites if sprites is _UNSET else sprites
    sprite_allow_cover = (dialogbox.sprite_allow_cover
                          if sprite_allow_cover is _UNSET else sprite_allow_cover)

    _get_app()
    effective_save = savecall if savecall is not None else dialogbox.save
    effective_load = loadcall if loadcall is not None else dialogbox.load
    effective_settings = settingscall if settingscall is not None else dialogbox.settings
    sw = QApplication.primaryScreen().size().width()
    if w is None:
        w = min(int(sw * 0.7), 1200)
    if h is None:
        h = int(220 / _get_dpi_scale())

    display_name = name.name if isinstance(name, Avatar) else name
    avatar = name if isinstance(name, Avatar) else None

    if msg:
        _history.append((display_name, msg))

    sprite_data = _process_sprites(sprites, avatar)
    sprite_data['sprite_allow_cover'] = sprite_allow_cover

    if sprites is None and avatar is not None and _box is not None:
        for i, sw in enumerate(_box._sprites):
            if getattr(sw, '_avatar', None) is avatar:
                sprite_data['speaker_idx'] = i
                break

    if sprite_data['speaker_idx'] is None:
        sprite_data['speaker_idx'] = -1

    if _box is not None:
        try:
            _box.isVisible()
        except RuntimeError:
            _destroy_box()
        else:
            if _box.w == w and _box.h == h:
                _box._update_content(msg, typewriter, chardelay, bold, overflow_mode, display_name,
                                     font_family=font_family, font_size=font_size,
                                     transparent=transparent, glare=glare,
                                     sprites=sprite_data['sprites'],
                                     sprite_pos=sprite_data['sprite_pos'],
                                     speaker_idx=sprite_data['speaker_idx'],
                                     avatar_sprite_map=sprite_data['avatar_sprite_map'],
                                     sprite_allow_cover=sprite_data.get('sprite_allow_cover', False),
                                     sprite_allow_cover_list=sprite_data['sprite_allow_cover_list'],
                                     avatar_hide_animations=sprite_data.get('avatar_hide_animations', {}),
                                     mode="dialog",
                                     pinned=pinned,
                                     savecall=effective_save,
                                     loadcall=effective_load,
                                     settingscall=effective_settings)
            else:
                _destroy_box()

    if _box is None:
        _box = _DialogBox(msg, w, h, display_name, typewriter, chardelay, bold, pinned=pinned,
                          fdst=fdst, overflow_mode=overflow_mode,
                          font_family=font_family, font_size=font_size,
                          transparent=transparent, glare=glare,
                          sprites=sprite_data['sprites'],
                          sprite_pos=sprite_data['sprite_pos'],
                          speaker_idx=sprite_data['speaker_idx'],
                          sprite_allow_cover=sprite_data.get('sprite_allow_cover', False),
                          sprite_allow_cover_list=sprite_data['sprite_allow_cover_list'],
                          mode="dialog",
                          savecall=effective_save,
                          loadcall=effective_load,
                          settingscall=effective_settings)

    for i, sw in enumerate(_box._sprites):
        if i < len(sprite_data['avatar_sprite_map']):
            sw._avatar = sprite_data['avatar_sprite_map'][i]
        if i < len(sprite_data['sprite_size_map']):
            w_ov, h_ov = sprite_data['sprite_size_map'][i]
            if w_ov != sw._width_override or h_ov != sw._height_override:
                sw._width_override = w_ov
                sw._height_override = h_ov
                sw._apply_geometry(animate=False)
        if i < len(sprite_data['sprite_animation_map']):
            sw._play_animation(sprite_data['sprite_animation_map'][i])

    _dialogbox_loop = QEventLoop()
    _box.dismissed.connect(_dialogbox_loop.quit, Qt.SingleShotConnection)
    _dialogbox_loop.exec()

    if fdst:
        _destroy_box()

dialogbox.save = None
dialogbox.load = None
dialogbox.settings = None
dialogbox.w = None
dialogbox.h = None
dialogbox.name = None
dialogbox.typewriter = True
dialogbox.chardelay = 50
dialogbox.bold = False
dialogbox.pinned = True
dialogbox.fdst = False
dialogbox.overflow_mode = "wrap"
dialogbox.font_family = None
dialogbox.font_size = None
dialogbox.transparent = True
dialogbox.glare = True
dialogbox.sprites = None
dialogbox.sprite_allow_cover = False
dialogbox.dismiss = dismiss

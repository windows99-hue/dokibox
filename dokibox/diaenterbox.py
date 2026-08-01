# -*- coding: utf-8 -*-
"""dokibox.diaenterbox -- DDLC-style bottom dialog with text input (no msg, user types directly)"""
from typing import Optional, Union, List
from PySide6.QtCore import Qt, QEventLoop, Signal
from PySide6.QtWidgets import QApplication
from dokibox._base import _get_app, _get_dpi_scale


def _process_sprites(sprites, avatar=None):
    from dokibox.dialogbox import _process_sprites as _ps
    return _ps(sprites, avatar)


def _find_speaker_from_shared_box(avatar):
    from dokibox.dialogbox import _get_shared_box
    _box = _get_shared_box()
    if _box is None:
        return None
    for i, sw in enumerate(_box._sprites):
        if getattr(sw, '_avatar', None) is avatar:
            return i
    return None


def _apply_sprite_attributes(_box, avatar_sprite_map, sprite_size_map, sprite_animation_map):
    for i, sw in enumerate(_box._sprites):
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


def _create_or_reuse_box(w, h, display_name, sprite_data, font_config, style_config,
                         mode, default, max_length, allow_empty, overflow_mode,
                         pinned, fdst):
    from dokibox.dialogbox import _DialogBox, _get_shared_box, _destroy_box

    _box = _get_shared_box()

    if _box is not None:
        try:
            _box.isVisible()
        except RuntimeError:
            _destroy_box()
        else:
            if _box.w == w and _box.h == h:
                _box._update_content("", True, 50, False, overflow_mode,
                                     display_name,
                                     font_family=font_config.get('family'),
                                     font_size=font_config.get('size'),
                                     transparent=style_config.get('transparent', True),
                                     glare=style_config.get('glare', True),
                                     sprites=sprite_data['sprites'],
                                     sprite_pos=sprite_data['sprite_pos'],
                                     speaker_idx=(sprite_data['speaker_idx']
                                                  if sprite_data['speaker_idx'] is not None else -1),
                                     avatar_sprite_map=sprite_data['avatar_sprite_map'],
                                     sprite_allow_cover=sprite_data.get('sprite_allow_cover', False),
                                     sprite_allow_cover_list=sprite_data['sprite_allow_cover_list'],
                                     avatar_hide_animations=sprite_data.get('avatar_hide_animations', {}),
                                     mode=mode, default=default, max_length=max_length,
                                     allow_empty=allow_empty)
                return _box
            else:
                _destroy_box()

    if _get_shared_box() is None:
        _DialogBox("", w, h, display_name,
                   typewriter=True, chardelay=50, bold=False,
                   pinned=pinned, fdst=fdst, overflow_mode=overflow_mode,
                   font_family=font_config.get('family'),
                   font_size=font_config.get('size'),
                   transparent=style_config.get('transparent', True),
                   glare=style_config.get('glare', True),
                   sprites=sprite_data['sprites'],
                   sprite_pos=sprite_data['sprite_pos'],
                   speaker_idx=(sprite_data['speaker_idx']
                                if sprite_data['speaker_idx'] is not None else -1),
                   sprite_allow_cover=sprite_data.get('sprite_allow_cover', False),
                   sprite_allow_cover_list=sprite_data['sprite_allow_cover_list'],
                   mode=mode, default=default, max_length=max_length,
                   allow_empty=allow_empty)

    return _get_shared_box()


def diaenterbox(w: Optional[int] = None, h: Optional[int] = None,
                name: Optional[str] = None, pinned: bool = True,
                fdst: bool = False,
                font_family: str = None, font_size: int = None,
                transparent: bool = True, glare: bool = True,
                sprites: Optional[Union[str, bytes, List[Union[str, bytes]]]] = None,
                sprite_allow_cover: bool = False,
                default: str = "", max_length: int = None,
                overflow_mode: str = "wrap", allow_empty: bool = False) -> Optional[str]:
    """DDLC-style bottom input dialog.

    Press Enter to insert a newline, or Shift+Enter to submit the input.

    The dialog body shows a DDLC-style rounded box containing a text input field.
    Character sprites (立绘) and name tags work exactly like dialogbox.

    Args:
        w:                   width in pixels. Defaults to 70% of screen width if None.
        h:                   dialog body height in pixels. Defaults to 220 (DPI-scaled) if None.
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
        overflow_mode:       "wrap": auto word-wrap, "overflow": expand window and overflow text
                             (default "wrap").
        allow_empty:         if True, allow submitting empty input (default False).

    Returns:
        The text entered by the user, or None if cancelled (Escape).

    Usage:
        sayori = Avatar(name="Sayori", emotes={"happy": ["sayori_happy.png"]})
        name = dokibox.diaenterbox(name=sayori, sprites=[sayori("left", "happy")])
        print(name)
    """
    from dokibox.dialogbox import Avatar, _get_shared_box, _destroy_box

    _get_app()
    sw = QApplication.primaryScreen().size().width()
    if w is None:
        w = min(int(sw * 0.7), 1200)
    if h is None:
        h = int(220 / _get_dpi_scale())

    display_name = name.name if isinstance(name, Avatar) else name
    avatar = name if isinstance(name, Avatar) else None

    sprite_data = _process_sprites(sprites, avatar)
    sprite_data['sprite_allow_cover'] = sprite_allow_cover

    if sprites is None and avatar is not None:
        found_idx = _find_speaker_from_shared_box(avatar)
        if found_idx is not None:
            sprite_data['speaker_idx'] = found_idx

    if sprite_data['speaker_idx'] is None:
        sprite_data['speaker_idx'] = -1

    font_config = {'family': font_family, 'size': font_size}
    style_config = {'transparent': transparent, 'glare': glare}

    _box = _create_or_reuse_box(w, h, display_name, sprite_data, font_config,
                                 style_config, "input", default, max_length,
                                 allow_empty, overflow_mode, pinned, fdst)

    if _box is None:
        return None

    _apply_sprite_attributes(_box, sprite_data['avatar_sprite_map'],
                             sprite_data['sprite_size_map'],
                             sprite_data['sprite_animation_map'])

    _diaenterbox_loop = QEventLoop()
    _box.dismissed.connect(_diaenterbox_loop.quit, Qt.SingleShotConnection)
    _diaenterbox_loop.exec()

    result = _box.result

    if result is not None and result.strip():
        from dokibox.dialogbox import _history
        _history.append((display_name, result))

    if fdst:
        _destroy_box()

    return result

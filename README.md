# dokibox

A fan-made Python library for *Doki Doki Literature Club*, implementing various in-game prompt boxes using `PySide6`.

> ### ⚠️ Credit & IP Guidelines
> `dokibox` is a fan derivative work based on *Doki Doki Literature Club* (DDLC) and is not officially affiliated with Team Salvato. The original game can be downloaded [here](https://ddlc.moe/) or from the [Steam store page](https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/).
>
> Any user creating derivative works with this library **must** strictly follow the [official IP guidelines](https://teamsalvato.com/ip-guidelines).
>
> Special thanks to Joseph from Team Salvato for his support and responses via email!

<img width="2560" alt="image" src="https://github.com/user-attachments/assets/a25345b9-28a3-4415-9d14-4090bbb3ee51" />

## Installation

Install from PyPI:

~~~bash
pip install dokibox
~~~

## Import

```python
import dokibox
```

---

## ynbox — Yes/No Dialog

<img width="300" alt="image" src="https://github.com/user-attachments/assets/283ffc50-17c5-4095-85aa-ac9af918ab6e" />

```python
dokibox.ynbox(msg="Delete?", tooltip=None) → bool
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | str | `None` | Tooltip text shown on hover; disabled when `None` or empty |
| `btn_texts` | tuple | `None` | Confirm button prompts. When `None`, `dokibox` auto-detects the system language. To customize, pass a tuple — the first element replaces "Yes", the second replaces "No". English fallback if language is unknown. |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` or unset to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` or unset to use default. |
| `pinned` | bool | `True` | Keep window on top |

Return value: clicking "Yes" returns `True`; clicking "No" or pressing Esc returns `False`.

```python
if dokibox.ynbox("Delete?"):
    print("User clicked Yes")
```

---

## msgbox — Message Box

<img width="440" alt="image" src="https://github.com/user-attachments/assets/50aaa9b7-b972-4fa4-8508-90620626a4a1" />

```python
dokibox.msgbox(msg="Operation successful!", tooltip=None) → True
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | str | `None` | Tooltip text shown on hover; disabled when `None` or empty |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` to use default. |
| `pinned` | bool | `True` | Keep window on top |

Single OK button. Closes on click, Enter, or Esc; returns `True`.

```python
dokibox.msgbox("Saved successfully!")
```

---

## choicebox — Multiple Choice Dialog

<img width="609" alt="image" src="https://github.com/user-attachments/assets/a20b59e2-25c3-4f29-8625-4608f34e487b" />

```python
dokibox.choicebox(msg="", choices=None, tooltip=None, force=None) → str | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Prompt text; hidden when empty |
| `choices` | list | `None` | List of choices |
| `tooltip` | str | `None` | Tooltip text shown on hover; disabled when `None` or empty |
| `force` | int | `None` | Force-select an index (0-based); cursor moves to the center of that choice |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` to use default. |
| `pinned` | bool | `True` | Keep window on top |

Return value: the selected text content; Esc returns `None`.

```python
char = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
print(char)  # "Yuri"
```

---

## dialogbox — Bottom Dialog Box

<img width="1206" alt="image" src="https://github.com/user-attachments/assets/db7c4489-aa32-4cc0-a6fd-d702bcc77417" />

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, chardelay=50, bold=False)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `w` | int | `None` | Width (default: 60% of screen width) |
| `h` | int | `220` | Height |
| `name` | str or `dokibox.Avatar` (see below) | `None` | Character name tag (white rounded label protruding above the dialog). Pass an `Avatar` to enable auto speaker detection with sprites. |
| `typewriter` | bool | `True` | Typewriter mode |
| `chardelay` | int | `50` | Typewriter interval per character (ms) |
| `bold` | bool | `False` | Bold black stroke on text |
| `overflow_mode` | str | `wrap` | How to handle text exceeding dialog width: `wrap` – wrap to next line; `overflow` – expand window so text renders past the boundary; `hide` – clip text at the boundary |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points (default: 20). Set to `None` to use default. |
| `fdst` | bool | `False` | If True, destroys the window when dismissed. Use for the final line of a dialogue scene or story branch to ensure the window closes completely. |
| `transparent` | bool | `True` | Apply alpha gradient from top to bottom, making the body see-through |
| `glare` | bool | `True` | Draw a white semicircular highlight at the bottom of the dialog |
| `pinned` | bool | `True` | Keep window on top |

Sprite-related APIs are not listed in this table — see the Sprite section below.

In typewriter mode:

- Text appears character by character
- First click → reveals full text instantly
- Second click → closes

```python
dokibox.dialogbox("Do you actually go by Administrator or something?", name="Monika")
dokibox.dialogbox("Slower...", chardelay=80, bold=True)
dokibox.dialogbox("All at once", typewriter=False)
```

### Sprite (Standing Picture) Feature

Starting from `v2.3.0`, `dialogbox` supports rendering character sprites!

<img width="2560" alt="3f95a52f629bc382f2d1dc18cfcf4d9d" src="https://github.com/user-attachments/assets/3fe03e28-0e68-487d-9749-a72a1bc39fb5" />

[Demo Video](https://youtu.be/m4Sv5mAFWDY)

#### Declaring Characters

```python
sayori = dokibox.Avatar(name="Sayori", emotes={
    "normal": ["images\\sayori\\1l.png",
               "images\\sayori\\1r.png",
               "images\\sayori\\a.png"]
})
```

`dokibox.Avatar` initializes a character sprite. See `avatar_test.py` in the repository for a full example.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | `""` | Content displayed in the dialogbox name tag |
| `emotes` | dict | — | A dictionary where keys are emote names and values are lists of images. You can place any number of sprite images — they can be file path strings or `bytes` objects. `dokibox` composites all provided images into one and renders them together. |

#### Rendering Sprites

A typical sprite dialogbox call looks like this:

```python
dokibox.dialogbox("Wow, the scenery here is so relaxing!", name=sayori, sprites=[sayori("center", "happy")])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str or `dokibox.Avatar` | `""` | If an `Avatar` is passed, `dialogbox` treats that character as the speaker and scales them up by 10%. |
| `sprites` | list | `None` | A list of `dokibox.Avatar` calls (not recommended to exceed 6). Call the avatar variable as a **magic method** directly. |
| `sprite_allow_cover` | bool | `False` | If True, sprites at the same position are allowed to overlap. When False, sprites sharing a position are automatically spread apart. |

#### About `dokibox.Avatar` Magic Call

The full magic call signature, using the `sayori` character declared earlier:

```python
sayori(position="center", emote="happy", animation="shocked", width=200, height=300, sprite_allow_cover=True)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `position` | str | — | Must be one of `left`, `center`, or `right`. Represents the sprite's position on stage. Multiple sprites can share a position — the program adjusts them automatically. |
| `emote` | str | — | Must match a key in the `emotes` dictionary declared when creating the character. Represents the sprite's expression for this dialogbox. |
| `animation` | str | `None` | See the [About Animation Parameter](#about-animation-parameter) section below. |
| `width` | int | `None` | Sprite width. When only one of `width` or `height` is set, the other is scaled proportionally based on the original image aspect ratio. When both are set, the sprite is stretched to the exact dimensions. |
| `height` | int | `None` | Sprite height. Same proportional scaling rules as `width`. |
| `sprite_allow_cover` | bool | `False` | If True, this specific sprite ignores the averaging/spreading algorithm and overlays directly at its position. |

#### About Animation Parameter

| Name | Behavior |
|------|----------|
| `thanks` | Sprite moves down and then bounces back up, like a bow. |
| `sad` | Sprite moves down and stays there until the next `dialogbox` call. |
| `shocked` | Sprite quickly bounces upward. |

Multi-sprite example:

```python
dokibox.dialogbox("So that's it! No wonder it's so lush everywhere — it's so beautiful!", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "smiled")])
```

<img width="2558" alt="49e6c26587a69dfbd932b1a733669e25" src="https://github.com/user-attachments/assets/78a0fc50-43c7-467b-a5cf-7b20faa29b48" />

```python
dokibox.dialogbox("Yeah, such a healing place deserves to be visited together. Looks like we're on the same wavelength!", name=monika, sprites=[sayori("center", "happy"), monika("center", "happy2"), yuri("center", "shocked"), natsuki("center", "mild")])
```

<img width="2560" alt="3b5d931976ecf83a23869e02cd51b40f" src="https://github.com/user-attachments/assets/c74ce6a9-a0a2-4b9a-a289-7c056ff2648e" />

```python
dokibox.dialogbox("Hello!",name=monika,sprites=[sayori("left", "shocked"),monika("center", "normal", sprite_allow_cover=True),yuri("right", "shocked"),natsuki("center", "shocked")])
```

<img width="2556" alt="114fe540dc7259e95b1ac144294dfa74" src="https://github.com/user-attachments/assets/916184de-6fdd-4763-944a-90c8f0a5552c" />

#### About Continuous Calls

When the expression and position haven't changed, you can omit the `sprites` parameter or pass `None` — this reuses the previous `dialogbox` configuration:

```python
dokibox.dialogbox("So that's it! No wonder it's so lush everywhere — it's so beautiful!", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "smiled")])
dokibox.dialogbox("Such a cozy place... if only we had some sweet cookies, it'd be perfect! Ehehe~", name=sayori)
```

This is equivalent to:

```python
dokibox.dialogbox("So that's it! No wonder it's so lush everywhere — it's so beautiful!", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "smiled")])
dokibox.dialogbox("Such a cozy place... if only we had some sweet cookies, it'd be perfect! Ehehe~", name=sayori, sprites=[sayori("left", "happy"), yuri("right", "smiled")])
```

#### About Sprite Exit

Use the `hide()` method to make a sprite leave the stage:

```python
dokibox.dialogbox("Everyone looks at me in surprise, and I stare back at them", name="MC", sprites=[monika.hide(), sayori.hide(), yuri.hide(), natsuki.hide()])  # all leave
```

### Notes When Using Alongside Other Qt Windows

After your story/dialogue ends, it's recommended to set `fdst=True` on the last `dialogbox` call to properly destroy the window. This is a known workaround for window cleanup when integrating with other Qt-based applications.

---

## enterbox — Text Input Box

<img width="452" alt="image" src="https://github.com/user-attachments/assets/03f7d34e-d76f-4921-97ce-ab18a43969e5" />

```python
cmd = dokibox.enterbox("Please enter your name")
print(cmd)  # the user's input string
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Prompt text |
| `default` | str | `""` | Auto-filled content |
| `tooltip` | str | `None` | Tooltip text shown on hover; disabled when `None` or empty |
| `pinned` | bool | `True` | Keep window on top |
| `font_family` | str | `None` | Font name (default: "Microsoft YaHei"); pass `None` to use default |
| `font_size` | int | `None` | Font size in points (default: 20); pass `None` to use default |
| `max_length` | int | `None` | Maximum input character length |

---

## garbled — Generate Garbled Text

<img width="1649" alt="image" src="https://github.com/user-attachments/assets/0ffc1ac4-ce59-4120-9eb9-76844be07f09" />

```python
dokibox.dialogbox(dokibox.garbled(200), name="Monika", typewriter=True, chardelay=5, bold=True, overflow_mode="overflow")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | int | `200` | Length of the garbled string |

---

## Finally

This project is licensed under the `MIT` license. When using it, please **strictly** comply with Team Salvato's relevant fan work IP creation guidelines.

> Sayori is my favorite! 🎀

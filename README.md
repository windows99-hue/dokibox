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

### ynbox — Yes/No Dialog

<img width="300" alt="image" src="https://github.com/user-attachments/assets/283ffc50-17c5-4095-85aa-ac9af918ab6e" />

```python
dokibox.ynbox(msg="Delete?", tooltip=False) → bool
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Tooltip text |
| `btn_texts` | tuple | None | Confirm button prompt. When set to None, `dokibox` will automatically detect the system language. To modify, please pass in a tuple, replacing "Yes" with the first parameter and "No" with the second parameter. English is used by default when the language is unknown. |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` or unset to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` or unset to use default. |
| `pinned` | bool | `True` | Whether to pin |

Return value: clicking "Yes" returns `True`; clicking "No" or pressing Esc returns `False`.

```python
if dokibox.ynbox("Delete?"):
    print("User clicked Yes")
```

---

### msgbox — Message Box

<img width="440" alt="image" src="https://github.com/user-attachments/assets/50aaa9b7-b972-4fa4-8508-90620626a4a1" />

```python
dokibox.msgbox(msg="Operation successful!", tooltip=False) → True
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Tooltip text |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` to use default. |
| `pinned` | bool | `True` | Whether to pin |

Single OK button. Closes on click, Enter, or Esc; returns `True`.

```python
dokibox.msgbox("Saved successfully!")
```

---

### choicebox — Multiple Choice Dialog

<img width="609" alt="image" src="https://github.com/user-attachments/assets/a20b59e2-25c3-4f29-8625-4608f34e487b" />

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Prompt text; hidden when empty |
| `choices` | list | `None` | List of choices |
| `tooltip` | bool | `False` | Tooltip text |
| `force` | int | `None` | Force-select an index (0-based); cursor moves to the center of that choice |
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points. Set to `None` to use default. |
| `pinned` | bool | `True` | Whether to pin |

Return value: the selected text content; Esc returns `None`.

```python
char = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
print(char)  # "Yuri"
```

---

### dialogbox — Bottom Dialog Box

<img width="1206" alt="image" src="https://github.com/user-attachments/assets/db7c4489-aa32-4cc0-a6fd-d702bcc77417" />

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, speed=50, bold=False)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `w` | int | `None` | Width (default 60% of screen width) |
| `h` | int | `220` | Height |
| `name` | str | `None` | Character name tag (white rounded label protruding above the dialog) |
| `typewriter` | bool | `True` | Typewriter mode |
| `chardelay` | int | `50` | Typewriter interval per character (ms) |
| `bold` | bool | `False` | Bold black stroke on text |
| `overflow_mode` | string | `wrap` | Has three parameters: `wrap`, `overflow`, and `hide`. `wrap` enables automatic line wrapping, `overflow` causes content to overflow the screen, and `hide` hides the content that goes off-screen.|
| `font_family` | str | `None` | Font family (default: "Microsoft YaHei"). Set to `None` to use default. |
| `font_size` | int | `None` | Font size in points (default: 20). Set to `None` to use default. |
| `fdst` | bool | `False` | If True, destroys the window when dismissed. Use this for the final line of a dialogue scene or story branch to ensure the window closes completely. |
| `transparent` | bool | `True` | Apply alpha gradient from top to bottom, making the body see-through |
| `glare` | bool | `True` | Draw a white semicircular highlight at the bottom of the dialog |
| `pinned` | bool | `True` | Whether to pin |

In typewriter mode:
- Text appears character by character
- First click → reveals full text instantly
- Second click → closes

```python
dokibox.dialogbox("Do you actually go by Administrator or something?", name="Monika")
dokibox.dialogbox("Slower...", speed=80, bold=True)
dokibox.dialogbox("All at once", typewriter=False)
```

### enterbox - Text Enter Box

<img width="452" alt="image" src="https://github.com/user-attachments/assets/03f7d34e-d76f-4921-97ce-ab18a43969e5" />

~~~python
cmd = dokibox.enterbox("Please enter your name")
print(cmd) #The user input string
~~~

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `msg` | str | `""` | Prompt text |
| `default` | str | `""` | Auto-filled content |
| `tooltip` | bool | `False` | Tooltip text |
| `pinned` | bool | `True` | Whether to pin to the top |
| `font_family` | str | `None` | Font name (default "Microsoft YaHei"); pass `None` to use the default |
| `font_size` | int | `None` | Font size (in points, default 20); pass `None` to use the default |
| `max_length` | int | `None` | Maximum input character length |
| `pinned` | bool | `True` | Whether to pin |


### garbled — Generate Garbled String

<img width="1649" alt="image" src="https://github.com/user-attachments/assets/0ffc1ac4-ce59-4120-9eb9-76844be07f09" />

```python
dokibox.dialogbox(dokibox.garbled(200), name="Monika", typewriter=True,chardelay=5,bold=True,overflow_mode="overflow")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | int | `200` | the length of garbled string |

## Finally

This project is licensed under the `MIT` license. When using it, please **strictly** comply with Team Salvato's relevant fan work IP creation guidelines.

> Sayori is my favorite!🎀

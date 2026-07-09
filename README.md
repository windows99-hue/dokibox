# dokibox

A fan-made Python library for *Doki Doki Literature Club*, implementing various in-game prompt boxes using `tkinter`.

> ### ⚠️ Credit & IP Guidelines
> `dokibox` is a fan derivative work based on *Doki Doki Literature Club* (DDLC) and is not officially affiliated with Team Salvato. The original game can be downloaded [here](https://ddlc.moe/) or from the [Steam store page](https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/).
>
> Any user creating derivative works with this library **must** strictly follow the [official IP guidelines](https://teamsalvato.com/ip-guidelines).
>
> Special thanks to Joseph from Team Salvato for his support and responses via email!

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

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/d40c9881-14bd-4876-877c-1d2008805c06" />

```python
dokibox.ynbox(msg="Delete?", tooltip=False) → bool
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Tooltip text |

Return value: clicking "Yes" returns `True`; clicking "No" or pressing Esc returns `False`.

```python
if dokibox.ynbox("Delete?"):
    print("User clicked Yes")
```

---

### msgbox — Message Box

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/da5064d3-8d90-47ec-9b9e-20e87faf0fdc" />

```python
dokibox.msgbox(msg="Operation successful!", tooltip=False) → True
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Tooltip text |

Single OK button. Closes on click, Enter, or Esc; returns `True`.

```python
dokibox.msgbox("Saved successfully!")
```

---

### choicebox — Multiple Choice Dialog

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/a33088b1-363b-48f5-8509-44a5d3ef5f4d" />

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `msg` | str | `""` | Prompt text; hidden when empty |
| `choices` | list | `None` | List of choices |
| `tooltip` | bool | `False` | Tooltip text |
| `force` | int | `None` | Force-select an index (0-based); cursor moves to the center of that choice |

Return value: the selected text content; Esc returns `None`.

```python
char = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
print(char)  # "Yuri"
```

---

### dialogbox — Bottom Dialog Box

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/3817a140-66eb-496d-988d-7b728289a1ca" />

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
| `speed` | int | `50` | Typewriter interval per character (ms) |
| `bold` | bool | `False` | Bold black stroke on text |

In typewriter mode:
- Text appears character by character
- First click → reveals full text instantly
- Second click → closes

```python
dokibox.dialogbox("You're actually Administrator, right?", name="Monika")
dokibox.dialogbox("Slower...", speed=80, bold=True)
dokibox.dialogbox("All at once", typewriter=False)
```

## Finally

This project is licensed under the `MIT` license. When using it, please **strictly** comply with Team Salvato's relevant fan work IP creation guidelines.

> Sayori is my favorite!🎀

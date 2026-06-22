# dokibox

A DDLC-style Python dialog library built on tkinter.

## Installation

Place the `dokibox/` folder in your project directory.

## Import

```python
import dokibox
# or
from dokibox import ynbox, msgbox, choicebox, dialogbox
```

---

### ynbox — Yes / No Dialog

```python
dokibox.ynbox(msg="Are you sure?", tooltip=False) → bool
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Show floating tooltip |

Returns `True` for "Yes", `False` for "No" or Esc.

```python
if dokibox.ynbox("Delete this file?"):
    print("User clicked Yes")
```

---

### msgbox — Message Dialog

```python
dokibox.msgbox(msg="Done!", tooltip=False) → True
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `msg` | str | `""` | Message text |
| `tooltip` | bool | `False` | Show floating tooltip |

Single OK button. Click, Enter, or Esc to dismiss. Returns `True`.

```python
dokibox.msgbox("Save successful!")
```

---

### choicebox — Choice Dialog

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `msg` | str | `""` | Prompt text (hidden when empty) |
| `choices` | list | `None` | List of options |
| `tooltip` | bool | `False` | Show floating tooltip |
| `force` | int | `None` | Index (0-based), mouse warps to that option's center |

Returns the selected option text, or `None` on Esc.

```python
char = dokibox.choicebox("Choose a character", ["Sayori", "Yuri", "Natsuki"], force=1)
print(char)  # "Yuri"
```

---

### dialogbox — Dialogue Box

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, speed=50, bold=False)
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `msg` | str | `""` | Body text |
| `w` | int | `None` | Width (default 60% screen width) |
| `h` | int | `220` | Height |
| `name` | str | `None` | Character name tag (white rounded label above dialog) |
| `typewriter` | bool | `True` | Typewriter animation |
| `speed` | int | `50` | Typewriter interval per character (ms) |
| `bold` | bool | `False` | Thicker black text outline |

Typewriter mode:
- Characters appear one by one
- First click → instantly reveal all text
- Second click → dismiss

```python
dokibox.dialogbox("Hello world!", name="Monika")
dokibox.dialogbox("Slower...", speed=80, bold=True)
dokibox.dialogbox("Show all at once", typewriter=False)
```


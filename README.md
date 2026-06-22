# dokibox

一个受《Doki Doki Literature Club!》启发的 Python 对话框库，用于创建 DDLC 风格的角色对话、选择框和文本动画。

## 安装

Please~Wait~

### 导入

```python
import dokibox
# 或
from dokibox import ynbox, msgbox, choicebox, dialogbox
```

---

### ynbox — 是/否 对话框

```python
dokibox.ynbox(msg="确认删除？", tooltip=False) → bool
```

参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮提示 |

返回值：点击"是"返回 `True`，点击"否"或 Esc 返回 `False`。

```python
if dokibox.ynbox("确认删除？"):
    print("用户点了是")
```

---

### msgbox — 消息提示框

```python
dokibox.msgbox(msg="操作成功！", tooltip=False) → True
```

参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮提示 |

单 OK 按钮。点击、Enter 或 Esc 关闭，返回 `True`。

```python
dokibox.msgbox("保存成功！")
```

---

### choicebox — 多选对话框

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 提示文字 |
| `choices` | list | `None` | 选项列表 |
| `tooltip` | bool | `False` | 悬浮提示 |
| `force` | int | `None` | 指定索引（0 开始），鼠标自动移到该选项中央 |

返回值：选中的文字内容，Esc 返回 `None`。

```python
char = dokibox.choicebox("选择角色", ["纱世里", "优里", "夏树","莫妮卡"], force=3) #鼠标会到莫妮卡
print(char)  # "莫妮卡"
```

---

### dialogbox — 底部对话框

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, speed=50, bold=False)
```

参数：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `w` | int | `None` | 宽度（默认 70% 屏宽） |
| `h` | int | `220` | 高度 |
| `name` | str | `None` | 角色名牌 |
| `typewriter` | bool | `True` | 打字机模式 |
| `speed` | int | `50` | 每字间隔（ms） |
| `bold` | bool | `False` | 正文黑色描边加粗 |

打字机模式下：
- 文字逐个出现
- 第一次点击 → 全文瞬间显示
- 第二次点击 → 关闭

```python
dokibox.dialogbox("你好世界！", name="莫妮卡")
dokibox.dialogbox("慢一点……", speed=80, bold=True)
dokibox.dialogbox("一下全出来", typewriter=False)
```

## 配色

可在各模块顶部修改常量：

```python
# ynbox.py / msgbox.py
BORDER_COLOR = "#FFBBE3"   # 描边
BODY_COLOR = "#FEE6F4"     # 主体
BTN_STROKE_COLOR = "#BD539D"  # 按钮描边

# dialogbox.py
BODY_COLOR = "#FDA7D1"
BORDER_COLOR = "#ffffff"
DOT_COLOR = "#FB94C1"      # 圆点颜色
DOT_RADIUS = 24            # 圆点半径
```


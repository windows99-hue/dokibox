# dokibox

这是一个《心跳文学部》的粉丝二创python库，用`tkinter`实现了游戏内的各种提示框

>  ### ⚠️ 鸣谢与二创准则声明 / Credit & IP Guidelines 
>  `dokibox` 是基于《心跳文学部》（Doki Doki Literature Club）的粉丝衍生创作，与 Team Salvato 无官方关联。原版游戏可以在[这里](https://ddlc.moe/)或者[Steam商店链接](https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/)下载
>  
>  任何使用本库进行再创作的用户，**必须**严格遵守[官方准则](https://teamsalvato.com/ip-guidelines)。
>
>  特别感谢 Team Salvato 的 Joseph 在邮件中对本项目的支持与解答！

## 安装

从PyPI下载安装

~~~bash
pip install dokibox
~~~

## 导入

```python
import dokibox
```

---

### ynbox — 是/否 对话框

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/d40c9881-14bd-4876-877c-1d2008805c06" />

```python
dokibox.ynbox(msg="确认删除？", tooltip=False) → bool
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `btn_texts` | tuple | None| 确认按钮提示，为None时`dokibox`会自动检测系统语言，如需修改请传入一个元组，第一个参数替换"Yes"第二个参数替换"No"，语言未知时默认使用英文 |

返回值：点击"是"返回 `True`，点击"否"或 Esc 返回 `False`。

```python
if dokibox.ynbox("确认删除？"):
    print("用户点了是")
```

---

### msgbox — 消息提示框

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/da5064d3-8d90-47ec-9b9e-20e87faf0fdc" />

```python
dokibox.msgbox(msg="操作成功！", tooltip=False) → True
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮文字提示 |

单 OK 按钮。点击、Enter 或 Esc 关闭，返回 `True`。

```python
dokibox.msgbox("保存成功！")
```

---

### choicebox — 多选对话框

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/a33088b1-363b-48f5-8509-44a5d3ef5f4d" />

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 提示文字，为空时不显示 |
| `choices` | list | `None` | 选项列表 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `force` | int | `None` | 指定索引（0 开始），鼠标自动移到该选项中央 |

返回值：选中的文字内容，Esc 返回 `None`。

```python
char = dokibox.choicebox("选择角色", ["纱世里", "优里", "夏树"], force=1)
print(char)  # "优里"
```

---

### dialogbox — 底部对话框

<img width="2560" height="1392" alt="image" src="https://github.com/user-attachments/assets/3817a140-66eb-496d-988d-7b728289a1ca" />

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, speed=50, bold=False)
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `w` | int | `None` | 宽度（默认 60% 屏宽） |
| `h` | int | `220` | 高度 |
| `name` | str | `None` | 角色名牌（探出对话框上方的白色圆角标签） |
| `typewriter` | bool | `True` | 打字机模式 |
| `chardelay` | int | `50` | 打字机每字间隔（ms） |
| `bold` | bool | `False` | 正文黑色描边加粗 |

打字机模式下：
- 文字逐个出现
- 第一次点击 → 全文瞬间显示
- 第二次点击 → 关闭

```python
dokibox.dialogbox("其实你叫Administrator对吧", name="莫妮卡")
dokibox.dialogbox("慢一点……", speed=80, bold=True)
dokibox.dialogbox("一下全出来", typewriter=False)
```

## 在最后

本项目使用`MIT`协议，在使用的同时请**严格**遵守Team Salvato的相关同人ip创作条款

> 最爱纱世里！🎀

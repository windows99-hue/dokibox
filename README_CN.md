# dokibox

这是一个《心跳文学部》的粉丝二创python库，用`PySide6`实现了游戏内的各种提示框

>  ### ⚠️ 鸣谢与二创准则声明 / Credit & IP Guidelines 
>  `dokibox` 是基于《心跳文学部》（Doki Doki Literature Club）的粉丝衍生创作，与 Team Salvato 无官方关联。原版游戏可以在[这里](https://ddlc.moe/)或者[Steam商店链接](https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/)下载
>  
>  任何使用本库进行再创作的用户，**必须**严格遵守[官方准则](https://teamsalvato.com/ip-guidelines)。
>
>  特别感谢 Team Salvato 的 Joseph 在邮件中对本项目的支持与解答！

<img width="2560" alt="image" src="https://github.com/user-attachments/assets/a25345b9-28a3-4415-9d14-4090bbb3ee51" />

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

## ynbox — 是/否 对话框

<img width="300" alt="image" src="https://github.com/user-attachments/assets/283ffc50-17c5-4095-85aa-ac9af918ab6e" />

```python
dokibox.ynbox(msg="确认删除？", tooltip=False) → bool
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `btn_texts` | tuple | `None` | 确认按钮提示，为None时`dokibox`会自动检测系统语言，如需修改请传入一个元组，第一个参数替换"Yes"第二个参数替换"No"，语言未知时默认使用英文 |
| `font_family` | str | `None` | 字体名称（默认 "Microsoft YaHei"），传 `None` 或不填使用默认 |
| `font_size` | int | `None` | 字号，传 `None` 或不填使用默认 |
| `pinned` | bool | `True` | 是否置顶 |

返回值：点击"是"返回 `True`，点击"否"或 Esc 返回 `False`。

```python
if dokibox.ynbox("确认删除？"):
    print("用户点了是")
```

---

## msgbox — 消息提示框

<img width="440" alt="image" src="https://github.com/user-attachments/assets/50aaa9b7-b972-4fa4-8508-90620626a4a1" />

```python
dokibox.msgbox(msg="操作成功！", tooltip=False) → True
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `font_family` | str | `None` | 字体名称（默认 "Microsoft YaHei"），传 `None` 使用默认 |
| `font_size` | int | `None` | 字号，传 `None` 使用默认 |
| `pinned` | bool | `True` | 是否置顶 |

单 OK 按钮。点击、Enter 或 Esc 关闭，返回 `True`。

```python
dokibox.msgbox("保存成功！")
```

---

## choicebox — 多选对话框

<img width="609" alt="image" src="https://github.com/user-attachments/assets/a20b59e2-25c3-4f29-8625-4608f34e487b" />

```python
dokibox.choicebox(msg="", choices=None, tooltip=False, force=None) → str | None
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 提示文字，为空时不显示 |
| `choices` | list | `None` | 选项列表 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `force` | int | `None` | 指定索引（0 开始），鼠标自动移到该选项中央 |
| `font_family` | str | `None` | 字体名称（默认 "Microsoft YaHei"），传 `None` 使用默认 |
| `font_size` | int | `None` | 字号，传 `None` 使用默认 |
| `pinned` | bool | `True` | 是否置顶 |

返回值：选中的文字内容，Esc 返回 `None`。

```python
char = dokibox.choicebox("选择角色", ["纱世里", "优里", "夏树"], force=1)
print(char)  # "优里"
```

---

## dialogbox — 底部对话框

<img width="1206" alt="image" src="https://github.com/user-attachments/assets/db7c4489-aa32-4cc0-a6fd-d702bcc77417" />

```python
dokibox.dialogbox(msg="", w=None, h=220, name=None, typewriter=True, speed=50, bold=False)
```

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `msg` | str | `""` | 正文 |
| `w` | int | `None` | 宽度（默认 60% 屏宽） |
| `h` | int | `220` | 高度 |
| `name` | str或`dokibox.Avatar`（详情见下文） | `None` | 角色名牌（探出对话框上方的白色圆角标签） |
| `typewriter` | bool | `True` | 打字机模式 |
| `chardelay` | int | `50` | 打字机每字间隔（ms） |
| `bold` | bool | `False` | 正文黑色描边加粗 |
| `overflow_mode` | string | `wrap` | 有`wrap` `overflow` `hide`三个参数，`wrap` 为自动换行，`overflow` 为直接溢出屏幕，`hide`为隐藏出画的内容 |
| `font_family` | str | `None` | 字体名称（默认 "Microsoft YaHei"），传 `None` 使用默认 |
| `font_size` | int | `None` | 字号（磅值，默认 20），传 `None` 使用默认 |
| `fdst` | bool | `False` | 若设为 True，则在关闭时销毁该窗口。请在对话场景或剧情分支的最后一行使用此设置，以确保窗口彻底关闭。 |
| `transparent` | bool | `True` | 从上到下应用透明度渐变，使对话框主体看起来半透明 |
| `glare` | bool | `True` | 在对话框底部绘制白色半圆高光 |
| `pinned` | bool | `True` | 是否置顶 |

与立绘相关的api本表格不再赘述，请在后文查看

打字机模式下：

- 文字逐个出现
- 第一次点击 → 全文瞬间显示
- 第二次点击 → 关闭

```python
dokibox.dialogbox("其实你叫Administrator对吧", name="莫妮卡")
dokibox.dialogbox("慢一点……", speed=80, bold=True)
dokibox.dialogbox("一下全出来", typewriter=False)
```

### dialogbox的立绘功能

在`v2.3.0`之后的版本中，`dokibox`的`dialogbox`带有了渲染立绘功能！

[图片们]

立绘功能的API如下

#### 声明角色

~~~python
sayori = dokibox.Avatar(name="Sayori", emotes={
    "normal":["images\\sayori\\1l.png",
              "images\\sayori\\1r.png",
              "images\\sayori\\a.png"]
})
~~~

`dokibox.Avatar`类会初始化一个角色立绘，详情可见仓库内`avatar_test.py`

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `name` | str | `""` | dialogbox的nametag所显示的内容 |
| `emotes` | dict | "" | `emotes`参数接收一个字典，其中字典键为表情名称，字典值应为一个列表，你可以在其中放置任意数量的立绘图片，他们可以是字符串类型的图片路径，也可以是`bytes`字节串，`dokibox`会将传入的所有照片一同合并为一个整体，并参与到接下来的渲染中 |

#### 渲染立绘

一个普通的带立绘dialogbox调用办法如下

~~~python
dokibox.dialogbox("哇，这里的风景也太舒服啦！",name=sayori,sprites=[sayori("center", "happy")])
~~~

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `name` | str或`dokibox.Avatar` | `""` | 若传入类型为`dokibox.Avatar`，则dialogbox会将这个对象视为说话者，并放大10% |
| `sprites` | 列表 | None | 该列表可传入任意数量（不推荐超过6个）的`dokibox.Avatar`对象，请直接将变量作为**魔术函数**调用 |

#### 关于`dokibox.Avatar`的魔术调用

完全的魔术调用如下，以前文创建的`sayori`角色为例

~~~python
sayori(position="center", emote="happy", animation="shocked", width=200, height=300, sprite_allow_cover=True)
~~~

| 参数               | 类型 | 默认值 | 解释                                                         |
| ------------------ | ---- | ------ | ------------------------------------------------------------ |
| position           | str  | 无     | 必须是`left` `center` `right`中的一个，代表了立绘存在的位置，多个立绘可以在同一个位置，程序会自行调整 |
| emote              | str  | 无     | 请传入先前定义角色时`emotes`字典中的键名，代表立绘在这个dialogbox下的表情 |
| animation          | str  | 无     | 详见下文的`关于动作参数`                                     |
| width              | int  | 无     | 立绘的宽，当width和height只有一个设置时等比例缩放            |
| height             | int  | 无     | 立绘的高，当width和height只有一个设置时等比例缩放            |
| sprite_allow_cover | bool | False  | 若为True，则这个dialogbox的该立绘无视平均平滑排布算法，直接覆盖 |

#### 关于动作参数

| 名称    | 动作                                            |
| ------- | ----------------------------------------------- |
| thanks  | 立绘向下移动后向上恢复位置，就像鞠躬一样        |
| sad     | 立绘向下移动后不再回弹，直到下一次调用dialogbox |
| shocked | 立绘快速向上弹跳起来                            |

多个立绘示例

~~~python
dokibox.dialogbox("原来是这样！难怪到处都是郁郁葱葱的，也太漂亮啦～",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
~~~

[三人图片]

~~~python
dokibox.dialogbox("是啊，这么治愈的地方，值得大家一同前来。看来我们默契十足呢～",name=monika, sprites=[sayori("center", "happy"),monika("center", "happy2"),yuri("center", "shocked"),natsuki("center", "mild")])
~~~

[四人图片]

~~~python
dokibox.dialogbox("哈喽！",name=monika,sprites=[sayori("left", "shocked"),monika("center", "normal"),yuri("right", "shocked"),natsuki("right", "shocked")])
~~~

[sprite_allow_cover为True]演示图片

#### 关于连续调用

如果表情和位置都没有变化时，可以不传入sprites参数或者传入`None`这意味着直接使用上一个dialogbox的配置

~~~python
dokibox.dialogbox("原来是这样！难怪到处都是郁郁葱葱的，也太漂亮啦～",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
dokibox.dialogbox("这么舒服的地方，如果能配上甜甜的曲奇就更完美啦～诶嘿嘿~",name=sayori)
~~~

效果等同于

~~~python
dokibox.dialogbox("原来是这样！难怪到处都是郁郁葱葱的，也太漂亮啦～",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
dokibox.dialogbox("这么舒服的地方，如果能配上甜甜的曲奇就更完美啦～诶嘿嘿~",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
~~~

#### 关于立绘离场

请按照如下方式让想要立场立绘离场

~~~python
dokibox.dialogbox("大家惊讶地看着我，我也惊讶地看着他们", name="MC", sprites=[monika.hide(),sayori.hide(),yuri.hide(),natsuki.hide()]) #全离场
~~~

### 在伴随其他Qt窗口使用时的注意事项

在目标剧情结束后，建议把最后一个dialogbox的`fdst`参数设置为True，有效销毁窗口，我觉得这应该算个bug但可以通过fdst参数解决，所以搁置解决计划

---

## enterbox - 文本输入框

<img width="452" alt="image" src="https://github.com/user-attachments/assets/03f7d34e-d76f-4921-97ce-ab18a43969e5" />

~~~python
cmd = dokibox.enterbox("Please enter your name")
print(cmd) #用户输入的字符串
~~~

| 参数  | 类型 | 默认 | 说明   |
| ----- | ---- | ---- | ------ |
| `msg` | str  | `""` | 提示词 |
| `default` | str | `""` | 自动填充的内容 |
| `tooltip` | bool | `False` | 悬浮文字提示 |
| `pinned` | bool | `True` | 是否置顶 |
| `font_family` | str | `None` | 字体名称（默认 "Microsoft YaHei"），传 `None` 使用默认 |
| `font_size` | int | `None` | 字号（磅值，默认 20），传 `None` 使用默认 |
| `max_length` | int | `None` | 限制输入字符长度 |
| `pinned` | bool | `True` | 是否置顶 |


## garbled - 生成混乱文本

<img width="1649" alt="image" src="https://github.com/user-attachments/assets/0ffc1ac4-ce59-4120-9eb9-76844be07f09" />

```python
dokibox.dialogbox(dokibox.garbled(200), name="Monika", typewriter=True,chardelay=5,bold=True,overflow_mode="overflow")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n` | int | `200` | 混乱文本的长度 |

# 在最后

本项目使用`MIT`协议，在使用的同时请**严格**遵守Team Salvato的相关同人ip创作条款

> 最爱纱世里！🎀

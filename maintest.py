"""
dokibox 全功能测试
=================

覆盖内容：

✓ ynbox
    - 默认参数
    - tooltip
    - 自定义按钮
    - 中文按钮
    - 长文本
    - 多行文本
    - 返回值

✓ msgbox
    - 默认
    - tooltip
    - 长文本
    - 多行
    - 返回值

✓ choicebox
    - 默认
    - msg为空
    - force
    - tooltip
    - 中文
    - 长列表
    - 返回值(None)
    - 返回字符串

✓ dialogbox
    - 默认
    - name
    - width
    - height
    - typewriter=True
    - typewriter=False
    - chardelay
    - bold
    - overflow_mode=wrap
    - overflow_mode=overflow
    - overflow_mode=hide
    - 长文本
    - 多行文本
"""

import dokibox


print("=" * 60)
print("dokibox 全面测试")
print("=" * 60)


# ==========================================================
# ynbox
# ==========================================================

print("\n[1] ynbox 默认")

result = dokibox.ynbox("Delete?")
print(result)


print("\n[2] ynbox tooltip")

result = dokibox.ynbox(
    "Delete selected file?",
    tooltip="This action cannot be undone."
)
print(result)


print("\n[3] ynbox 中文按钮")

result = dokibox.ynbox(
    "确定删除吗？",
    btn_texts=("确定", "取消")
)
print(result)


print("\n[4] ynbox 自定义按钮")

result = dokibox.ynbox(
    "Overwrite existing file?",
    btn_texts=("Overwrite", "Keep")
)
print(result)


print("\n[5] ynbox 多行")

result = dokibox.ynbox(
    "Delete save file?\n\nThis operation cannot be undone."
)
print(result)


print("\n[6] ynbox 超长文本")

result = dokibox.ynbox(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam."
)
print(result)


# ==========================================================
# msgbox
# ==========================================================

print("\n[7] msgbox 默认")

dokibox.msgbox("Operation successful!")


print("\n[8] msgbox tooltip")

dokibox.msgbox(
    "Saved successfully!",
    tooltip="File written to disk."
)


print("\n[9] msgbox 多行")

dokibox.msgbox(
    "Download Complete!\n\nYou may close this window."
)


print("\n[10] msgbox 长文本")

dokibox.msgbox(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Vestibulum euismod nisl vitae justo consequat, sed posuere "
    "arcu faucibus."
)


print("\n[11] msgbox 返回值")

result = dokibox.msgbox("Return value test")
print(result)


# ==========================================================
# choicebox
# ==========================================================

print("\n[12] choicebox 默认")

choice = dokibox.choicebox(
    "Choose difficulty",
    [
        "Easy",
        "Normal",
        "Hard"
    ]
)

print(choice)


print("\n[13] choicebox force")

choice = dokibox.choicebox(
    "Choose a character",
    [
        "Sayori",
        "Yuri",
        "Natsuki",
        "Monika"
    ],
    force=2
)

print(choice)


print("\n[14] choicebox tooltip")

choice = dokibox.choicebox(
    "Select language",
    [
        "English",
        "日本語",
        "简体中文"
    ],
    tooltip="Only affects this session."
)

print(choice)


print("\n[15] choicebox msg为空")

choice = dokibox.choicebox(
    "",
    [
        "Apple",
        "Orange",
        "Banana"
    ]
)

print(choice)


print("\n[16] choicebox 中文")

choice = dokibox.choicebox(
    "请选择角色",
    [
        "纱世里",
        "优里",
        "夏树",
        "莫妮卡"
    ]
)

print(choice)


print("\n[17] choicebox 长列表")

choice = dokibox.choicebox(
    "Select one item",
    [f"Item {i}" for i in range(1, 31)]
)

print(choice)


print("\n[18] choicebox Esc测试")

choice = dokibox.choicebox(
    "Press Esc to return None",
    [
        "One",
        "Two",
        "Three"
    ]
)

print(repr(choice))


# ==========================================================
# dialogbox
# ==========================================================

print("\n[19] dialogbox 默认")

dokibox.dialogbox(
    "Hello World!"
)


print("\n[20] dialogbox 名称")

dokibox.dialogbox(
    "Welcome to Dokibox.",
    name="Monika"
)


print("\n[21] dialogbox 自定义尺寸")

dokibox.dialogbox(
    "Window Size Test",
    w=900,
    h=280
)


print("\n[22] dialogbox 无打字机")

dokibox.dialogbox(
    "This text appears immediately.",
    typewriter=False
)


print("\n[23] dialogbox 打字机慢")

dokibox.dialogbox(
    "Typing slowly...",
    chardelay=100
)


print("\n[24] dialogbox 打字机快")

dokibox.dialogbox(
    "Typing fast!",
    chardelay=10
)


print("\n[25] dialogbox 粗体")

dokibox.dialogbox(
    "Bold text test.",
    bold=True
)


print("\n[26] dialogbox wrap")

dokibox.dialogbox(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis."
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis.",
    overflow_mode="wrap"
)


print("\n[27] dialogbox overflow")

dokibox.dialogbox(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis."
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis.",
    overflow_mode="overflow"
)


print("\n[28] dialogbox hide")

dokibox.dialogbox(
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis."
    "Vivamus luctus urna sed urna ultricies ac tempor dui sagittis.",
    overflow_mode="hide"
)


print("\n[29] dialogbox 多行")

dokibox.dialogbox(
    "Line 1\n"
    "Line 2\n"
    "Line 3\n"
    "Line 4",
    name="Narrator"
)


print("\n[30] dialogbox 长文本")

dokibox.dialogbox(
    """
Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae.
Suspendisse potenti.
Donec id elit non mi porta gravida at eget metus.
Praesent commodo cursus magna.
Integer posuere erat a ante venenatis dapibus posuere velit aliquet.
""",
    name="Long Text",
    overflow_mode="wrap"
)


print("\n[31] dialogbox 综合")

dokibox.dialogbox(
    msg="Everything enabled.\nThis is the final dialog.",
    name="Monika",
    w=1000,
    h=260,
    typewriter=True,
    chardelay=40,
    bold=True,
    overflow_mode="wrap"
)


# ==========================================================
# enterbox
# ==========================================================

print("\n[32] enterbox 默认")

result = dokibox.enterbox("Enter your name:")
print(repr(result))


print("\n[33] enterbox 带默认值")

result = dokibox.enterbox(
    "Enter your name:",
    default="Player"
)
print(repr(result))


print("\n[34] enterbox 多行提示")

result = dokibox.enterbox(
    "Save File\nEnter a filename:"
)
print(repr(result))


print("\n[35] enterbox tooltip")

result = dokibox.enterbox(
    "Input value:",
    tooltip="Click OK to confirm."
)
print(repr(result))


print("\n[36] enterbox Esc取消")

result = dokibox.enterbox(
    "Press Esc to cancel"
)
print(repr(result))


print("\n[37] enterbox 中文")

result = dokibox.enterbox(
    "请输入你的名字：",
    default="勇者"
)
print(repr(result))


print("\n")
print("=" * 60)
print("所有测试结束")
print("=" * 60)
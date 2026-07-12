# ==========================================================
# enterbox
# ==========================================================

import dokibox

print("\n[32] enterbox 默认")

result = dokibox.enterbox("Please enter your name")
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
    default="MC",
    max_length=12
)
print(repr(result))
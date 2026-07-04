# -*- coding: utf-8 -*-
"""dokibox 使用示例"""
import dokibox
import time
if __name__ == "__main__":
    idx = dokibox.choicebox("",["纱世里", "优里", "夏树", "莫妮卡"])
    if idx is not None:
        print("选择了:", idx)
    else:
        print("未选择")
    
    dokibox.msgbox("只选莫妮卡。")
    idx = dokibox.choicebox("请选择", ["纱世里", "优里", "夏树", "莫妮卡"],force=3)
    if idx is not None:
        print("选择了:", idx)
    else:
        print("未选择")
    dokibox.ynbox("继续吗？", tooltip=True)
    dokibox.dialogbox("“你好，我是莫妮卡！这就是你所说的......\n现实世界？”", name="莫妮卡", typewriter=True, fdst=True)
    dokibox.dialogbox("“如果有天我真的能带着大家来到不被代码控制的世界，                             \n你会永远爱我吗？”", name="莫妮卡", typewriter=True)
    dokibox.ynbox("你会永远爱我吗？", tooltip=True)
    dokibox.dialogbox("“我会永远爱你。”", name="莫妮卡", typewriter=True)
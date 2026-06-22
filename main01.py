# -*- coding: utf-8 -*-
"""dokibox 使用示例"""
import dokibox
if __name__ == "__main__":
    idx = dokibox.choicebox("请选择", ["纱世里", "优里", "夏树", "莫妮卡"])
    if idx is not None:
        print("选择了:", ["纱世里", "优里", "夏树", "莫妮卡"][idx])
    else:
        print("未选择")

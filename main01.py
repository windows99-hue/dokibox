# -*- coding: utf-8 -*-
"""dokibox 自测 / 使用示例"""
import dokibox

if __name__ == "__main__":
    res = dokibox.ynbox("真的要退出DDLC吗？\n纱世里会伤心的...")
    print("用户选择了:", "是" if res else "否")

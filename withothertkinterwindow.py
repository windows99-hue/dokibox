import tkinter as tk
import dokibox
import time
import easygui

print("当前使用的 dokibox 路径是：", dokibox.__file__)

def check_block():
    # 只要主循环还在跑，这个定时器就会每100毫秒更新一次时间
    # 如果窗口被阻塞，这个数字就会卡住不动
    current_time = time.strftime("%H:%M:%S")
    label_status.config(text=f"主循环心跳 (每秒更新): {current_time}")
    root.after(100, check_block)

def on_button_click():
    label.config(text="弹窗已触发！请观察上方时间是否卡死，并尝试拖动主窗口。")
    # 触发 easygui
    dokibox.msgbox("Hi")
    # 弹窗关闭后才会执行这句
    label.config(text="弹窗已关闭，主窗口恢复。")

root = tk.Tk()
root.title("DDLC 阻塞测试")
root.geometry("400x200")

# 用于检测主循环是否活着的标签
label_status = tk.Label(root, text="检测中...", fg="red", font=("Arial", 12, "bold"))
label_status.pack(pady=10)

label = tk.Label(root, text="点击下方按钮触发 dokibox", font=("Arial", 10))
label.pack(pady=10)

button = tk.Button(root, text="点我弹窗", command=on_button_click)
button.pack(pady=5)

# 启动心跳检测
root.after(100, check_block)

root.mainloop()
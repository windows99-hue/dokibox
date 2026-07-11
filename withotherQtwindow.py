import sys
import time
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer, Qt
import dokibox

print("当前使用的 dokibox 路径是：", dokibox.__file__)

class DdlcBlockTest(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("DDLC 阻塞测试 (PySide6版)")
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # 用于检测主循环是否活着的标签
        self.label_status = QLabel("检测中...", self)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 设置红字粗体
        self.label_status.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.label_status)
        
        self.label = QLabel("点击下方按钮触发 dokibox", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.button = QPushButton("点我弹窗", self)
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        
        self.setLayout(layout)
        
        # 启动心跳检测定时器 (每100毫秒触发一次)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_block)
        self.timer.start(100)
        
    def check_block(self):
        # 只要主事件循环还在跑，这个定时器就会每100毫秒更新一次时间
        current_time = time.strftime("%H:%M:%S")
        self.label_status.setText(f"主循环心跳 (每秒更新): {current_time}")
        
    def on_button_click(self):
        self.label.setText("弹窗已触发！请观察上方时间是否卡死，并尝试拖动主窗口。")
        
        # 触发你重写后的 PySide6 版 dokibox
        dokibox.msgbox("Hi")
        
        # 弹窗关闭后才会执行这句
        self.label.setText("弹窗已关闭，主窗口恢复。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DdlcBlockTest()
    window.show()
    sys.exit(app.exec())
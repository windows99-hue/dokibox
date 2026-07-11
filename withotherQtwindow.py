import sys
import time
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import QTimer, Qt
import dokibox

class DdlcBlockTest(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("DDLC ynbox 测试")
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        self.label_status = QLabel("检测中...", self)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        layout.addWidget(self.label_status)
        
        self.label = QLabel("点击下方按钮触发 ynbox 确认框", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.button = QPushButton("触发 ynbox", self)
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_block)
        self.timer.start(100)
        
    def check_block(self):
        current_time = time.strftime("%H:%M:%S")
        self.label_status.setText(f"主循环心跳 (每秒更新): {current_time}")
        
    def on_button_click(self):
        self.label.setText("等待用户选择...")
        
        # 1. 直接用变量接收返回值，代码会在这里“暂停”等待弹窗关闭
        result = dokibox.ynbox("你喜欢文学部吗？")
        
        # 2. 弹窗关闭后，代码继续向下执行，直接判断结果
        if result:
            self.label.setText("用户选择了：Yes！太好了。")
        else:
            self.label.setText("用户选择了：No... (Just Monika?)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DdlcBlockTest()
    window.show()
    sys.exit(app.exec())
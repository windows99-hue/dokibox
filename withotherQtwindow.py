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
        QTimer.singleShot(0, self._show_dialogbox)

    def _show_dialogbox(self):
        dokibox.dialogbox("你喜欢文学部吗？")
        dokibox.dialogbox("你喜欢文学部吗111111111？",fdst=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DdlcBlockTest()
    window.show()
    sys.exit(app.exec())
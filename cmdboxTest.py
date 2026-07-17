import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import dokibox

app = QApplication(sys.argv)

dokibox.cmdbox("print('hello world')", runcmd=True, language="python")
dokibox.cmdbox("x = 1 + 2 + 3\nprint('result:', x)", runcmd=True, language="python")
dokibox.cmdbox("echo hello from cmd", runcmd=True, language="cmd")

QTimer.singleShot(10000, app.quit)
sys.exit(app.exec())

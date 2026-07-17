import sys
from PySide6.QtWidgets import QApplication
import dokibox

app = QApplication(sys.argv)

dokibox.cmdbox("print('hello world')", runcmd=True, language="python")
dokibox.cmdbox("1 + 2 + 3", runcmd=True, language="python")
dokibox.cmdbox("echo hello", runcmd=True, language="cmd")

sys.exit(app.exec())

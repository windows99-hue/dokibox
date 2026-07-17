import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import dokibox

app = QApplication(sys.argv)

dokibox.cmdbox("print('hello world')", runcmd=True, language="python")
dokibox.cmdbox("print('goooooooood')",runcmd=True)
dokibox.dialogbox("Hello, world!",fdst=True)
dokibox.cmdbox("x = 1 + 2 + 3\nprint('result:', x)", runcmd=True, language="python")
dokibox.cmdbox("echo hello from cmd", runcmd=True, language="cmd",clear=True)

dokibox.dialogbox("看到了吗")
dokibox.closecmdbox()
dokibox.dialogbox("算算数真好玩嘿嘿")

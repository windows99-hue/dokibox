import dokibox

def save2():
    dokibox.msgbox("保存2")

def save():
    dokibox.msgbox("保存")

dokibox.dialogbox.save = None

dokibox.dialogbox("hi", savecall=save2)
dokibox.dialogbox("hi2")
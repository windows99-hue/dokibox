import dokibox

def s():
    dokibox.msgbox("保存")

def s2():
    dokibox.msgbox("更高级的保存")

dokibox.dialogbox.save = s
dokibox.dialogbox.load = s
dokibox.dialogbox.settings = s2

dokibox.dialogbox("123")
dokibox.dialogbox("123123",loadcall=s2)
import dokibox
from avatar_test import sayori

cmd = dokibox.diaenterbox(name="MC")
print(repr(cmd))

dokibox.dialogbox("哇！MC你来啦！",name=sayori, sprites=[sayori("center", "happy")])
# dokibox.dialogbox("12")
cmd = dokibox.diaenterbox(name="MC",sprites=[sayori("center", "normal")],overflow_mode="overflow")
print(repr(cmd))
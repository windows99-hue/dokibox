import dokibox

# dokibox.cmdbox("print('hello world')", runcmd=True, language="python")
# dokibox.closecmdbox(1000)
# dokibox.cmdbox("print('goooooooood')",runcmd=True)
# dokibox.dialogbox("Hello, world!",fdst=True)
# dokibox.cmdbox("x = 1 + 2 + 3\nprint('result:', x)", runcmd=True, language="python")
# dokibox.cmdbox("echo hello from cmd", runcmd=True, language="cmd",clear=True)

# dokibox.dialogbox("看到了吗")
# dokibox.closecmdbox()
# dokibox.dialogbox("算算数真好玩嘿嘿")

dokibox.cmdbox("os.remove(\"y_cg2.png\")",result="y_cg2.png 已成功删除。")
dokibox.cmdbox("os.remove(\"y_cg1.png\")",result="y_cg1.png 已成功删除。")
dokibox.cmdbox("os.remove(\"n_cg2.png\")",result="n_cg2.png 已成功删除。")
dokibox.cmdbox("os.remove(\"n_cg1.png\")",result="n_cg1.png 已成功删除。")
dokibox.cmdbox("",result="")

dokibox.dialogbox("")

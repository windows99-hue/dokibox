import dokibox
import os

# dokibox.cmdbox("print('hello world')", runcmd=True, language="python")
# dokibox.closecmdbox(1000)
# dokibox.cmdbox("print('goooooooood')",runcmd=True)
# dokibox.dialogbox("Hello, world!",fdst=True)
# dokibox.cmdbox("x = 1 + 2 + 3\nprint('result:', x)", runcmd=True, language="python")
# dokibox.cmdbox("echo hello from cmd", runcmd=True, language="cmd",clear=True)

# dokibox.dialogbox("看到了吗")
# dokibox.closecmdbox()
# dokibox.dialogbox("算算数真好玩嘿嘿")

#dokibox.cmdbox("import os\nos.remove(\"E:\\\\99之没事写的小程序\\\\99ddlcmsgbox\\\\01-images\\\\cover4.png\")",runcmd=True)
def del_cover():
    path = r"E:\99之没事写的小程序\99ddlcmsgbox\01-images\cover4.png"
    try:
        os.remove(path)
        return "cover4.png 已成功删除"
    except FileNotFoundError:
        return "错误：cover4.png 文件不存在"
    except Exception as e:
        return f"删除失败：{str(e)}"

# runcmd=False，result 传删除函数
dokibox.cmdbox(
    cmd="os.remove cover4.png",
    result=del_cover
)
dokibox.cmdbox("os.remove(\"y_cg1.png\")",result="y_cg1.png 已成功删除。")
dokibox.cmdbox("os.remove(\"n_cg2.png\")",result="n_cg2.png 已成功删除。")
dokibox.cmdbox("os.remove(\"n_cg1.png\")",result="n_cg1.png 已成功删除。")
dokibox.cmdbox("",result="")

dokibox.dialogbox("")

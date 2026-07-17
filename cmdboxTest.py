import dokibox
import os

dokibox.ynbox("确定吗？")

def del_cover():
    path = r"E:\99之没事写的小程序\99ddlcmsgbox\01-images\cover111.png"
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
dokibox.textbox("123")
dokibox.cmdbox("os.remove(\"n_cg2.png\")",result="n_cg2.png 已成功删除。")
dokibox.diaenterbox(name="MC",fdst=True)
dokibox.cmdbox("os.remove(\"n_cg1.png\")",result="n_cg1.png 已成功删除。")
dokibox.cmdbox("",result="")

dokibox.dialogbox("好耶！")

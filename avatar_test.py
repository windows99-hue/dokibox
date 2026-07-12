import dokibox
import rpareader

IMAGE_ARCHIVE = r"J:\SteamLibrary\steamapps\common\Doki Doki Literature Club\game\images.rpa"

data = rpareader.RPAReader(IMAGE_ARCHIVE)

sayori_images = data.preload(["images/sayori/*"])
yuri_images = data.preload(["images/yuri/*"])

sayori_image_root = "images\\sayori\\"
yuri_image_root = "images\\yuri\\"

print(yuri_images.keys())

sayori = dokibox.Avatar(name="Sayori", emotes={
    "normal":[sayori_images[sayori_image_root + "1l.png"],
              sayori_images[sayori_image_root + "1r.png"],
              sayori_images[sayori_image_root + "a.png"]],

    "shocked":[sayori_images[sayori_image_root + "1l.png"],
               sayori_images[sayori_image_root + "1r.png"],
               sayori_images[sayori_image_root + "c.png"]],
    
    "suprised":[sayori_images[sayori_image_root + "2l.png"],
               sayori_images[sayori_image_root + "2r.png"],
               sayori_images[sayori_image_root + "m.png"]]
})

yuri = dokibox.Avatar(name="Yuri", emotes={
    "normal":[yuri_images[yuri_image_root + "1l.png"],
              yuri_images[yuri_image_root + "1r.png"],
              yuri_images[yuri_image_root + "a.png"]],

    "smiled":[yuri_images[yuri_image_root + "1l.png"],
              yuri_images[yuri_image_root + "1r.png"],
              yuri_images[yuri_image_root + "c.png"]]
})

dokibox.dialogbox("你好呀！我是纱世里！",name=sayori,sprites=[sayori("left", "normal")])  
dokibox.dialogbox("你好呀！我是优里！",name=yuri,sprites=[sayori("left", "normal"),yuri("right", "normal")])
dokibox.dialogbox("优里!?你也在这里！",name=sayori,sprites=[sayori("left", "suprised"),yuri("right", "normal")])
dokibox.dialogbox("我也不知道，听夏树说这里很好玩就来啦，看这里还有很多树木~",name=yuri,sprites=[sayori("left", "suprised"),yuri("right", "smiled")])
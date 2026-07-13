import dokibox
import rpareader

IMAGE_ARCHIVE = r"J:\SteamLibrary\steamapps\common\Doki Doki Literature Club\game\images.rpa"

data = rpareader.RPAReader(IMAGE_ARCHIVE)

sayori_images = data.preload(["images/sayori/*"])
yuri_images = data.preload(["images/yuri/*"])
natsuki_images = data.preload(["images/natsuki/*"])

sayori_image_root = "images\\sayori\\"
yuri_image_root = "images\\yuri\\"
natsuki_image_root = "images\\natsuki\\"

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
               sayori_images[sayori_image_root + "m.png"]],

    "happy":[sayori_images[sayori_image_root + "2l.png"],
             sayori_images[sayori_image_root + "2r.png"],
             sayori_images[sayori_image_root + "r.png"]]
})

yuri = dokibox.Avatar(name="Yuri", emotes={
    "normal":[yuri_images[yuri_image_root + "1l.png"],
              yuri_images[yuri_image_root + "1r.png"],
              yuri_images[yuri_image_root + "a.png"]],

    "smiled":[yuri_images[yuri_image_root + "1l.png"],
              yuri_images[yuri_image_root + "1r.png"],
              yuri_images[yuri_image_root + "c.png"]]
})

natsuki = dokibox.Avatar(name="Natsuki", emotes={
    "normal":[natsuki_images[natsuki_image_root + "1l.png"],
              natsuki_images[natsuki_image_root + "1r.png"],
              natsuki_images[natsuki_image_root + "1t.png"]],

    "smiled":[natsuki_images[natsuki_image_root + "1l.png"],
              natsuki_images[natsuki_image_root + "1r.png"],
              natsuki_images[natsuki_image_root + "c.png"]]
})

dokibox.dialogbox("你好呀！我是纱世里！",name=sayori,sprites=[sayori("center", "normal")])  
dokibox.dialogbox("你好呀！我是优里！",name=yuri,sprites=[sayori("left", "normal"),yuri("right", "normal")])
dokibox.dialogbox("优里!?你也在这里！",name=sayori,sprites=[sayori("left", "suprised"),yuri("right", "normal")])
dokibox.dialogbox("我也不知道，听夏树说这里很好玩就来啦，看这里还有很多树木~",name=yuri,sprites=[sayori("left", "suprised"),yuri("right", "smiled")])
dokibox.dialogbox("哇~好漂亮的树木呀！",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
dokibox.dialogbox("要是这里有曲奇就更好啦~诶嘿嘿~",name=sayori)
dokibox.dialogbox("曲奇？话说是不是你偷吃了我的曲奇啊纱世里！",name=natsuki,sprites=[natsuki("right", "normal"),sayori("left", "suprised"),yuri("center", "normal")])
dokibox.dialogbox("你们在干啥呐！",name="MC")
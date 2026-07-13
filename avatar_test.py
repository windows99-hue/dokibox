import dokibox
import rpareader
import copy

IMAGE_ARCHIVE = r"J:\SteamLibrary\steamapps\common\Doki Doki Literature Club\game\images.rpa"

data = rpareader.RPAReader(IMAGE_ARCHIVE)

sayori_images = data.preload(["images/sayori/*"])
yuri_images = data.preload(["images/yuri/*"])
natsuki_images = data.preload(["images/natsuki/*"])
monika_images = data.preload(["images/monika/*"])

sayori_image_root = "images\\sayori\\"
yuri_image_root = "images\\yuri\\"
natsuki_image_root = "images\\natsuki\\"
monika_images_root = "images\\monika\\"

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
              yuri_images[yuri_image_root + "c.png"]],

    "shocked":[yuri_images[yuri_image_root + "1l.png"],
               yuri_images[yuri_image_root + "1r.png"], 
               yuri_images[yuri_image_root + "f.png"]]
})

natsuki = dokibox.Avatar(name="Natsuki", emotes={
    "normal":[natsuki_images[natsuki_image_root + "1l.png"],
              natsuki_images[natsuki_image_root + "1r.png"],
              natsuki_images[natsuki_image_root + "1t.png"]],

    "smiled":[natsuki_images[natsuki_image_root + "1l.png"],
              natsuki_images[natsuki_image_root + "1r.png"],
              natsuki_images[natsuki_image_root + "c.png"]],
    
    "angry":[natsuki_images[natsuki_image_root + "1l.png"],
             natsuki_images[natsuki_image_root + "1r.png"],
                natsuki_images[natsuki_image_root + "f.png"]],

    "shocked":[natsuki_images[natsuki_image_root + "1l.png"],
               natsuki_images[natsuki_image_root + "1r.png"],
                natsuki_images[natsuki_image_root + "m.png"]]
})

monika = dokibox.Avatar(name="Monika", emotes={
    "normal":[monika_images[monika_images_root + "1l.png"],
                monika_images[monika_images_root + "1r.png"],
                monika_images[monika_images_root + "a.png"]],
})

sayori2 = copy.deepcopy(sayori)

dokibox.dialogbox("你好呀！我是纱世里！",name=sayori,sprites=[sayori("center", "normal")])  
dokibox.dialogbox("你好呀！我是优里！",name=yuri,sprites=[sayori("left", "normal"),yuri("right", "normal")])
dokibox.dialogbox("优里!?你也在这里！",name=sayori,sprites=[sayori("left", "suprised"),yuri("right", "normal")])
dokibox.dialogbox("我也不知道，听夏树说这里很好玩就来啦，看这里还有很多树木~",name=yuri,sprites=[sayori("left", "suprised"),yuri("right", "smiled")])
dokibox.dialogbox("哇~好漂亮的树木呀！",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
dokibox.dialogbox("要是这里有曲奇就更好啦~诶嘿嘿~",name=sayori)
dokibox.dialogbox("曲奇？话说是不是你偷吃了我的曲奇啊纱世里！",name=natsuki,sprites=[natsuki("center", "angry"),
                                                                sayori("left", "suprised"),
                                                                yuri("right", "shocked")])
dokibox.dialogbox("诶！？你....你们....是怎么到这里来的！？",name="MC",sprites=[natsuki("center", "shocked"),
                                                                sayori("left", "shocked"),
                                                                yuri("right", "shocked")])

dokibox.dialogbox("哈喽！",name=monika,sprites=[natsuki("center", "shocked"),
                                                                sayori("center", "shocked"),
                                                                monika("center", "normal"),
                                                                yuri("center", "shocked")])

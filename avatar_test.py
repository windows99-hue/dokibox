import dokibox
import rpareader
import copy
import os

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
    
    "surprised":[sayori_images[sayori_image_root + "2l.png"],
               sayori_images[sayori_image_root + "2r.png"],
               sayori_images[sayori_image_root + "m.png"]],

    "happy":[sayori_images[sayori_image_root + "2l.png"],
             sayori_images[sayori_image_root + "2r.png"],
             sayori_images[sayori_image_root + "r.png"]],

    "panicked":[sayori_images[sayori_image_root + "1l.png"],
                sayori_images[sayori_image_root + "1r.png"],
                sayori_images[sayori_image_root + "n.png"]]
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
               yuri_images[yuri_image_root + "f.png"]],

    "panicked":[yuri_images[yuri_image_root + "1l.png"],
                yuri_images[yuri_image_root + "1r.png"],
                yuri_images[yuri_image_root + "n.png"]]
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
                natsuki_images[natsuki_image_root + "m.png"]],

    "curious":[natsuki_images[natsuki_image_root + "1l.png"],
                natsuki_images[natsuki_image_root + "1r.png"],
                natsuki_images[natsuki_image_root + "k.png"]],

    "mild":[natsuki_images[natsuki_image_root + "1l.png"], 
            natsuki_images[natsuki_image_root + "1r.png"],
            natsuki_images[natsuki_image_root + "a.png"]]
})

monika = dokibox.Avatar(name="Monika", emotes={
    "normal":[monika_images[monika_images_root + "1l.png"],
                monika_images[monika_images_root + "1r.png"],
                monika_images[monika_images_root + "a.png"]],
    
    "happy":[monika_images[monika_images_root + "1l.png"],
                monika_images[monika_images_root + "1r.png"],
                monika_images[monika_images_root + "b.png"]],
    
    "happy2":[monika_images[monika_images_root + "2l.png"],
                monika_images[monika_images_root + "2r.png"],
                monika_images[monika_images_root + "b.png"]],
    
    "shocked":[monika_images[monika_images_root + "1l.png"],
               monika_images[monika_images_root + "1r.png"],
               monika_images[monika_images_root + "i.png"]],
})

sayori2 = copy.deepcopy(sayori)

dokibox.dialogbox("哇，这里的风景也太舒服啦！",name=sayori,sprites=[sayori("center", "happy")])
dokibox.dialogbox("你好，纱世里。没想到会在这里碰到你。",name=yuri,sprites=[sayori("left", "normal"),yuri("right", "normal")])
dokibox.dialogbox("诶！优里！？你也来这边散步嘛？太巧啦！",name=sayori,sprites=[sayori("left", "surprised"),yuri("right", "normal")])
dokibox.dialogbox("嗯，夏树说这边的林间很安静、景色很好，我便过来逛逛。这里的绿植确实让人心情很平和。",name=yuri,sprites=[sayori("left", "surprised"),yuri("right", "smiled")])
dokibox.dialogbox("原来是这样！难怪到处都是郁郁葱葱的，也太漂亮啦～",name=sayori,sprites=[sayori("left", "happy"),yuri("right", "smiled")])
dokibox.dialogbox("这么舒服的地方，如果能配上甜甜的曲奇就更完美啦～诶嘿嘿~",name=sayori)
dokibox.dialogbox("曲奇？！我就说我书包里的曲奇少了好几块！纱世里，是不是你偷偷吃掉的！",name=natsuki,sprites=[natsuki("center", "angry"),sayori("left", "panicked"),yuri("right", "shocked")])
dokibox.dialogbox("等等…！夏树、纱世里、优里？你们三个怎么都在这里？！",name=os.getlogin(),sprites=[natsuki("center", "shocked"),sayori("left", "shocked"),yuri("right", "shocked")])
dokibox.dialogbox("看来大家都不约而同找到了这个好去处呢。哈喽，各位。",name=monika,sprites=[sayori("left", "shocked"),monika("center", "normal", sprite_allow_cover=True),yuri("right", "shocked"),natsuki("center", "shocked")])
dokibox.dialogbox("莫妮卡！？你居然也来这里了！今天也太热闹了吧！",name=sayori, sprites=[sayori("left", "surprised"),monika("center", "normal"),yuri("right", "shocked"),natsuki("right", "curious")])
dokibox.dialogbox("是啊，这么治愈的地方，值得大家一同前来。看来我们默契十足呢～",name=monika, sprites=[sayori("center", "happy"),monika("center", "happy2"),yuri("center", "shocked"),natsuki("center", "mild")])
dokibox.dialogbox("可是这里......是我的电脑啊！",name=os.getlogin(), sprites=[sayori("center", "shocked"),monika("center", "shocked"),yuri("center", "shocked"),natsuki("center", "shocked")])
dokibox.dialogbox("大家惊讶地看着我，我也惊讶地看着他们", name=os.getlogin(), 
                            sprites=[monika.hide(),sayori.hide(),yuri.hide(),natsuki.hide()],fdst=True)
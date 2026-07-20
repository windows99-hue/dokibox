import sys
import time
import os
import copy
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import QTimer, Qt
import dokibox
import rpareader

class DdlcBlockTest(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_images()
        
    def init_ui(self):
        self.setWindowTitle("DDLC 综合测试 - ynbox + 立绘")
        self.resize(600, 400)
        
        main_layout = QVBoxLayout()
        
        # 状态显示区域
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QVBoxLayout(status_frame)
        
        self.label_status = QLabel("检测中...", self)
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.label_status)
        
        main_layout.addWidget(status_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.test_ynbox_btn = QPushButton("测试 ynbox", self)
        self.test_ynbox_btn.clicked.connect(self.test_ynbox)
        button_layout.addWidget(self.test_ynbox_btn)
        
        self.test_sprites_btn = QPushButton("测试立绘显示", self)
        self.test_sprites_btn.clicked.connect(self.test_sprites)
        button_layout.addWidget(self.test_sprites_btn)
        
        self.test_combined_btn = QPushButton("综合测试 (ynbox + 立绘)", self)
        self.test_combined_btn.clicked.connect(self.test_combined)
        button_layout.addWidget(self.test_combined_btn)

        self.test_textbox_btn = QPushButton("测试 textbox", self)
        self.test_textbox_btn.clicked.connect(self.test_textbox)
        button_layout.addWidget(self.test_textbox_btn)

        self.test_cmdbox_btn = QPushButton("测试 cmdbox (Monika用代码)", self)
        self.test_cmdbox_btn.clicked.connect(self.test_cmdbox)
        button_layout.addWidget(self.test_cmdbox_btn)

        self.test_notice_btn = QPushButton("测试 notice", self)
        self.test_notice_btn.clicked.connect(self.test_notice)
        button_layout.addWidget(self.test_notice_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态标签
        self.label = QLabel("点击上方按钮开始测试", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        main_layout.addWidget(self.label)
        
        # 额外的控制按钮
        clear_btn = QPushButton("清空状态信息", self)
        clear_btn.clicked.connect(self.clear_status)
        main_layout.addWidget(clear_btn)
        
        self.setLayout(main_layout)
        
        # 心跳定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_block)
        self.timer.start(100)
        
    def load_images(self):
        """加载DDLC立绘图片"""
        try:
            IMAGE_ARCHIVE = r"J:\SteamLibrary\steamapps\common\Doki Doki Literature Club\game\images.rpa"
            
            if not os.path.exists(IMAGE_ARCHIVE):
                self.label.setText("错误：未找到 images.rpa 文件，请检查路径")
                return
            
            self.data = rpareader.RPAReader(IMAGE_ARCHIVE)
            
            # 预加载所有角色图片
            sayori_images = self.data.preload(["images/sayori/*"])
            yuri_images = self.data.preload(["images/yuri/*"])
            natsuki_images = self.data.preload(["images/natsuki/*"])
            monika_images = self.data.preload(["images/monika/*"])
            
            sayori_image_root = "images\\sayori\\"
            yuri_image_root = "images\\yuri\\"
            natsuki_image_root = "images\\natsuki\\"
            monika_images_root = "images\\monika\\"
            
            # 创建Sayori角色
            self.sayori = dokibox.Avatar(name="Sayori", emotes={
                "normal": [sayori_images[sayori_image_root + "1l.png"],
                          sayori_images[sayori_image_root + "1r.png"],
                          sayori_images[sayori_image_root + "a.png"]],
                "shocked": [sayori_images[sayori_image_root + "1l.png"],
                           sayori_images[sayori_image_root + "1r.png"],
                           sayori_images[sayori_image_root + "c.png"]],
                "surprised": [sayori_images[sayori_image_root + "2l.png"],
                             sayori_images[sayori_image_root + "2r.png"],
                             sayori_images[sayori_image_root + "m.png"]],
                "happy": [sayori_images[sayori_image_root + "2l.png"],
                         sayori_images[sayori_image_root + "2r.png"],
                         sayori_images[sayori_image_root + "r.png"]],
                "panicked": [sayori_images[sayori_image_root + "1l.png"],
                            sayori_images[sayori_image_root + "1r.png"],
                            sayori_images[sayori_image_root + "n.png"]]
            })
            
            # 创建Yuri角色
            self.yuri = dokibox.Avatar(name="Yuri", emotes={
                "normal": [yuri_images[yuri_image_root + "1l.png"],
                          yuri_images[yuri_image_root + "1r.png"],
                          yuri_images[yuri_image_root + "a.png"]],
                "smiled": [yuri_images[yuri_image_root + "1l.png"],
                          yuri_images[yuri_image_root + "1r.png"],
                          yuri_images[yuri_image_root + "c.png"]],
                "shocked": [yuri_images[yuri_image_root + "1l.png"],
                           yuri_images[yuri_image_root + "1r.png"], 
                           yuri_images[yuri_image_root + "f.png"]],
                "panicked": [yuri_images[yuri_image_root + "1l.png"],
                            yuri_images[yuri_image_root + "1r.png"],
                            yuri_images[yuri_image_root + "n.png"]]
            })
            
            # 创建Natsuki角色
            self.natsuki = dokibox.Avatar(name="Natsuki", emotes={
                "normal": [natsuki_images[natsuki_image_root + "1l.png"],
                          natsuki_images[natsuki_image_root + "1r.png"],
                          natsuki_images[natsuki_image_root + "1t.png"]],
                "smiled": [natsuki_images[natsuki_image_root + "1l.png"],
                          natsuki_images[natsuki_image_root + "1r.png"],
                          natsuki_images[natsuki_image_root + "c.png"]],
                "angry": [natsuki_images[natsuki_image_root + "1l.png"],
                         natsuki_images[natsuki_image_root + "1r.png"],
                         natsuki_images[natsuki_image_root + "f.png"]],
                "shocked": [natsuki_images[natsuki_image_root + "1l.png"],
                           natsuki_images[natsuki_image_root + "1r.png"],
                           natsuki_images[natsuki_image_root + "m.png"]],
                "curious": [natsuki_images[natsuki_image_root + "1l.png"],
                           natsuki_images[natsuki_image_root + "1r.png"],
                           natsuki_images[natsuki_image_root + "k.png"]],
                "mild": [natsuki_images[natsuki_image_root + "1l.png"], 
                        natsuki_images[natsuki_image_root + "1r.png"],
                        natsuki_images[natsuki_image_root + "a.png"]]
            })
            
            # 创建Monika角色
            self.monika = dokibox.Avatar(name="Monika", emotes={
                "normal": [monika_images[monika_images_root + "1l.png"],
                          monika_images[monika_images_root + "1r.png"],
                          monika_images[monika_images_root + "a.png"]],
                "happy": [monika_images[monika_images_root + "1l.png"],
                         monika_images[monika_images_root + "1r.png"],
                         monika_images[monika_images_root + "b.png"]],
                "happy2": [monika_images[monika_images_root + "2l.png"],
                          monika_images[monika_images_root + "2r.png"],
                          monika_images[monika_images_root + "b.png"]],
                "shocked": [monika_images[monika_images_root + "1l.png"],
                           monika_images[monika_images_root + "1r.png"],
                           monika_images[monika_images_root + "i.png"]],
            })
            
            self.label.setText("✅ 立绘图片加载成功！")
            self.images_loaded = True
            
        except Exception as e:
            self.label.setText(f"❌ 加载立绘失败: {str(e)}")
            self.images_loaded = False
    
    def check_block(self):
        current_time = time.strftime("%H:%M:%S")
        status_text = f"⏰ 主循环心跳: {current_time}"
        if hasattr(self, 'images_loaded'):
            status_text += f" | 立绘状态: {'✅ 已加载' if self.images_loaded else '❌ 未加载'}"
        self.label_status.setText(status_text)
    
    def test_ynbox(self):
        """测试ynbox功能"""
        self.label.setText("开始测试 ynbox...")
        QTimer.singleShot(0, self._test_ynbox_dialogs)
    
    def _test_ynbox_dialogs(self):
        """执行ynbox对话框测试"""
        try:
            self.label.setText("等待用户输入名字...")
            self.mcname = dokibox.enterbox("请输入你的名字：", default="MC")
            
            if not self.mcname:
                self.mcname = "MC"
                
            self.label.setText(f"等待用户确认喜好... (用户: {self.mcname})")
            dokibox.dialogbox(f"哈喽 {self.mcname}！你喜欢文学部吗？", name="Monika")
            
            cmd = dokibox.ynbox("你喜欢文学部吗？", tooltip=True)
            
            if cmd:
                dokibox.dialogbox("你喜欢文学部！谢谢！", name="Monika", fdst=True)
                self.label.setText("✅ ynbox测试完成 - 用户选择了'是'")
            else:
                dokibox.dialogbox("你竟然不喜欢文学部！", name="Monika")
                dokibox.dialogbox(
                    dokibox.garbled(100) + "\n" + dokibox.garbled(20),
                    name="Monika", typewriter=True, chardelay=5, bold=True, 
                    overflow_mode="overflow", fdst=True
                )
                self.label.setText("✅ ynbox测试完成 - 用户选择了'否'")
                
        except Exception as e:
            self.label.setText(f"❌ ynbox测试出错: {str(e)}")
    
    def test_sprites(self):
        """测试立绘显示功能"""
        if not hasattr(self, 'images_loaded') or not self.images_loaded:
            self.label.setText("❌ 立绘未加载，请先检查图片路径")
            return
        
        self.label.setText("开始显示立绘场景...")
        QTimer.singleShot(0, self._test_sprites_scene)
    
    def _test_sprites_scene(self):
        """执行立绘场景测试"""
        try:
            self.label.setText("🎭 显示立绘场景...")
            
            # 原始场景（来自你的脚本）
            a = dokibox.diaenterbox(name="MC")
            self.label.setText(f"MC说{a}")
            dokibox.dialogbox("哇，这里的风景也太舒服啦！", name=self.sayori, 
                            sprites=[self.sayori("center", "happy")])
            dokibox.dialogbox("你好，纱世里。没想到会在这里碰到你。", name=self.yuri, 
                            sprites=[self.sayori("left", "normal"), self.yuri("right", "normal")])
            dokibox.dialogbox("诶！优里！？你也来这边散步嘛？太巧啦！", name=self.sayori, 
                            sprites=[self.sayori("left", "surprised"), self.yuri("right", "normal")])
            dokibox.dialogbox("嗯，夏树说这边的林间很安静、景色很好，我便过来逛逛。这里的绿植确实让人心情很平和。", 
                            name=self.yuri, sprites=[self.sayori("left", "surprised"), self.yuri("right", "smiled")])
            dokibox.dialogbox("原来是这样！难怪到处都是郁郁葱葱的，也太漂亮啦～", name=self.sayori, 
                            sprites=[self.sayori("left", "happy"), self.yuri("right", "smiled")])
            dokibox.dialogbox("这么舒服的地方，如果能配上甜甜的曲奇就更完美啦～诶嘿嘿~", name=self.sayori, 
                            sprites=[self.sayori("left", "happy"), self.yuri("right", "smiled")])
            dokibox.dialogbox("曲奇？！我就说我书包里的曲奇少了好几块！纱世里，是不是你偷偷吃掉的！", name=self.natsuki, 
                            sprites=[self.natsuki("center", "angry"), self.sayori("left", "panicked"), self.yuri("right", "shocked")])
            dokibox.dialogbox("等等…！夏树、纱世里、优里？你们三个怎么都在这里？！", name=self.mcname, 
                            sprites=[self.natsuki("center", "shocked"), self.sayori("left", "shocked"), self.yuri("right", "shocked")])
            dokibox.dialogbox("看来大家都不约而同找到了这个好去处呢。哈喽，各位。", name=self.monika, 
                            sprites=[self.sayori("left", "shocked"), self.monika("center", "normal"), 
                                    self.yuri("right", "shocked"), self.natsuki("right", "shocked")])
            dokibox.dialogbox("莫妮卡！？你居然也来这里了！今天也太热闹了吧！", name=self.sayori, 
                            sprites=[self.sayori("left", "surprised"), self.monika("center", "normal"), 
                                    self.yuri("right", "shocked"), self.natsuki("right", "curious")])
            dokibox.dialogbox("是啊，这么治愈的地方，值得大家一同前来。看来我们默契十足呢～", name=self.monika, 
                            sprites=[self.sayori("center", "happy"), self.monika("center", "happy2"), 
                                    self.yuri("center", "shocked"), self.natsuki("center", "mild")])
            dokibox.dialogbox("可是这里......是我的电脑啊！", name=self.mcname, 
                            sprites=[self.sayori("center", "shocked"), self.monika("center", "shocked"), 
                                    self.yuri("center", "shocked"), self.natsuki("center", "shocked")])
            dokibox.dialogbox("大家惊讶地看着我，我也惊讶地看着他们", name=self.mcname, 
                            sprites=[self.monika.hide(),self.sayori.hide(),self.yuri.hide(),self.natsuki.hide()],fdst=True)
            
            self.label.setText("✅ 立绘场景播放完成！")
            
        except Exception as e:
            self.label.setText(f"❌ 立绘测试出错: {str(e)}")
    
    def test_combined(self):
        """综合测试：先测试ynbox，再测试立绘"""
        self.label.setText("🔄 开始综合测试...")
        QTimer.singleShot(0, self._test_combined_sequence)
    
    def _test_combined_sequence(self):
        """执行综合测试序列"""
        try:
            self.label.setText("📝 第一部分：测试 ynbox...")
            self._test_ynbox_dialogs()
            
            # 等待一下再测试立绘
            self.label.setText("🎭 第二部分：测试立绘...")
            if hasattr(self, 'images_loaded') and self.images_loaded:
                self._test_sprites_scene()
            else:
                self.label.setText("⚠️ 跳过立绘测试（图片未加载）")
                
        except Exception as e:
            self.label.setText(f"❌ 综合测试出错: {str(e)}")
    
    def test_textbox(self):
        self.label.setText("开始测试 textbox...")
        QTimer.singleShot(0, self._test_textbox)

    def _test_textbox(self):
        try:
            dokibox.dialogbox("不如来看看这首诗吧~",name=self.monika,sprites=[self.monika("center","normal")])
            test = """
%
滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。滚出我的脑袋。
滚。
出。
我。
的。
脑。
袋。



在我想到该怎么收拾你才是最好之前给我滚出我的脑袋。
在我对她言听计从之前给我滚出我的脑袋。
在我告诉你我有多爱你之前给我滚出我的脑袋。
在我写完这首诗之前给我滚出我的脑袋。






但诗是永远无法写完的。
只是戛然而止而已。
"""
            dokibox.textbox(msg=test)
            dokibox.dialogbox("你把她晾在家里了",name=self.monika,sprites=[self.monika("center","normal")],fdst=True)
            self.label.setText("✅ textbox 测试完成")

        except Exception as e:
            self.label.setText(f"❌ textbox测试出错: {str(e)}")

    def test_cmdbox(self):
        self.label.setText("开始测试 cmdbox (Monika写代码)...")
        QTimer.singleShot(0, self._test_cmdbox_scene)

    def _test_cmdbox_scene(self):
        try:
            self.label.setText("Monika 正在写代码...")

            dokibox.dialogbox("让我来展示一下我的编程能力~", name=self.monika,
                            sprites=[self.monika("center", "normal")])

            dokibox.cmdbox("import os\nprint('当前目录:', os.getcwd())",
                           runcmd=True, language="python")

            dokibox.dialogbox("看，我能查看当前目录!", name=self.monika,
                            sprites=[self.monika("center", "happy")])

            dokibox.cmdbox("print('1 + 2 + 3 =', 1 + 2 + 3)\nprint('Hello from Monika!')",
                           runcmd=True, language="python")

            dokibox.dialogbox("我还会算数~", name=self.monika,
                            sprites=[self.monika("center", "happy2")])

            dokibox.cmdbox("echo Monika says hello from cmd!",
                           runcmd=True, language="cmd")

            dokibox.dialogbox("甚至连cmd命令我也能用!", name=self.monika,
                            sprites=[self.monika("center", "normal")])

            dokibox.cmdbox("print('你看，我可以\\n换行输出\\n多行内容!')",
                           runcmd=True, language="python")

            dokibox.dialogbox("代码就展示到这里吧~好玩吗？", name=self.monika,
                            sprites=[self.monika("center", "happy")], fdst=True)

            dokibox.closecmdbox()

            self.label.setText("✅ cmdbox 测试完成")

        except Exception as e:
            self.label.setText(f"❌ cmdbox 测试出错: {str(e)}")

    def test_notice(self):
        self.label.setText("开始测试 notice...")
        QTimer.singleShot(0, self._test_notice)

    def _test_notice(self):
        try:
            self.label.setText("notice 测试1: 基本调用 (默认 last=3)")
            dokibox.notice("这是一条基本通知", block=True)

            self.label.setText("notice 测试2: 自定义存活时间 last=1.5")
            dokibox.notice("1.5秒后消失", last=1.5, block=True)

            self.label.setText("notice 测试3: 长文本")
            dokibox.notice("这是一条很长很长的通知消息用于测试长文本的显示效果", last=2, block=True)

            self.label.setText("notice 测试4: 空消息")
            dokibox.notice("", last=1, block=True)

            self.label.setText("notice 测试5: block=True 短时间连续调用")
            dokibox.notice("第一条", last=1, block=True)
            dokibox.notice("第二条", last=1, block=True)
            dokibox.notice("第三条", last=1, block=True)

            self.label.setText("notice 测试6: block=False 与 dialogbox 同时显示")
            dokibox.notice("通知 + 对话框同时显示!", last=3, block=False)
            dokibox.dialogbox("看，左上角有一个通知同时显示着！", name=self.monika,
                            sprites=[self.monika("center", "happy")])
            dokibox.dialogbox("notice 是非阻塞的，可以和 dialogbox 一起用~", name=self.monika,
                            sprites=[self.monika("center", "normal")], fdst=True)

            self.label.setText("notice 测试7: 多条 block=False 通知堆叠 + dialogbox")
            dokibox.notice("堆叠通知 1", last=4, block=False)
            dokibox.notice("堆叠通知 2", last=4, block=False)
            dokibox.notice("堆叠通知 3", last=4, block=False)
            dokibox.dialogbox("左上角有三条通知堆叠在一起！", name=self.monika,
                            sprites=[self.monika("center", "happy2")])
            dokibox.dialogbox("它们各自主活，到期自动关闭~", name=self.monika,
                            sprites=[self.monika("center", "normal")], fdst=True)

            self.label.setText("✅ notice 全部测试完成")

        except Exception as e:
            self.label.setText(f"❌ notice 测试出错: {str(e)}")

    def clear_status(self):
        self.label.setText("状态已清空，准备进行新的测试")
        self.label_status.setText("检测中...")
        self.label.setText("状态已清空，准备进行新的测试")
        self.label_status.setText("检测中...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DdlcBlockTest()
    window.show()
    sys.exit(app.exec())
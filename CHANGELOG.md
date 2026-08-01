# Changelog

## [2.8.1] - 2026-08-01

### Fixed

1. 修复了`diaenterbox`关于<kbd>Enter</kbd>和<kbd>Shift</kbd>+<kbd>Enter</kbd>的ide文档行为与diaenterbox本身不一致的问题
2. 修复了`diaenterbox`的`speaker_idx`解析错误导致第一个立绘说话放大失效的问题
3. 修复了`diaenterbox`复用窗口时异常获取范围过大的问题
4. 修复了`dialogbox`连续调用时`savecall/loadcall/settingscall`三个自定义函数参数残留的问题
5. 修复了`diaenterbox`的`max_length`参数残留的问题
6. 修复了`dialogbox`和`diaenterbox`的`pinned`参数残留的问题
7. `historybox`可直接传入字典与元组
8. 优化了`historybox`文字描边重复绘制导致CPU占用过高的问题
9. 优化了`historybox`背景圆球重复路径绘制导致cpu占用过高的问题，现在使用图片内存缓存
10. 让`historybox`背景动画刷新调度同意
11. 修复了`dialogbox`在打字机动画中Timer重复新建且不关闭的问题
12. 优化了`dialogbox`的立绘动画算法，大幅度降低cpu占用
13. 优化了`dialogbox`的立绘绘画算法，高dpi下更清晰
14. 修复了所有box在按下Alt+F4时只隐藏窗口，阻塞调用不返回的问题
15. 优化了在源码开发下调用`__version__`时报错的问题，现在在源码开发下调用会返回`development`
16. `cmdbox`在`runcmd`为true时，播放完输入动画后再执行命令
17. `cmdbox`在执行代码时光标动画不阻塞
18. `cmdbox`支持流式传输`print`等stdout输出
19. `cmdbox`只捕获传入参数中的stdout输出，主进程不影响cmdbox输出的内容
20. `cmdbox`中的cmd和powershell以子进程运行

## [2.8.0] - 2026-07-20

### Added

1. 添加了`historybox`
2. 给`dialogbox`添加了下方的四个按钮

## [2.7.1] - 2026-07-20

### Added

1. 给`dialogbox`的Avatar类中的动画添加了`lenter`和`renter`，给`hide()`函数添加了animation参数
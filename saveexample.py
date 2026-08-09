"""dokibox 即时存档/读档示例。

点击 dialogbox 底部的“保存”或“加载”按钮时，回调会立即读写
脚本同目录下的 save.json，不需要额外的 keyboard 依赖。
"""

import json
from importlib import import_module
from pathlib import Path

import dokibox
from PySide6.QtCore import QTimer


SAVE_PATH = Path(__file__).with_name("save.json")
TEMP_SAVE_PATH = Path(__file__).with_name("save.json.tmp")

STORY = {
    1: [
        ("莫妮卡", "今天天气真不错！"),
        ("纱世里", "是啊，很好奇会发生什么事情。"),
        ("莫妮卡", "你可以随时点击下方的“保存”按钮。"),
        ("纱世里", "之后点击“加载”，就能读取刚才的进度啦！"),
        ("莫妮卡", "存档与读档的示例就到这里。"),
    ],
}

# 当前正在显示的台词位置。存档后再读档会重新显示这句台词。
progress = {"chapter": 1, "line": 0}

# 读档发生在按钮回调中，文件会当场读取。这个标记只用来防止
# 当前 dialogbox 关闭后把刚读取的行号再加 1。
load_happened = False

# dialogbox 按钮回调执行时，dokibox 会暂时放下共享窗口引用。
# 因此要在回调返回后的下一轮 Qt 事件中关闭当前对话框。
dialogbox_module = import_module("dokibox.dialogbox")


def show_notice(message):
    """显示非阻塞通知，让按钮回调可以立即返回。"""
    dokibox.notice(message, last=2, block=False)


def save_game():
    """立即把当前进度保存到 save.json。"""
    data = {
        "version": 1,
        "progress": dict(progress),
    }

    try:
        # 先写临时文件再替换旧存档，避免写入中断损坏原文件。
        TEMP_SAVE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        TEMP_SAVE_PATH.replace(SAVE_PATH)
    except OSError as exc:
        show_notice("保存失败：{}".format(exc))
        return

    show_notice(
        "已保存：第 {} 章，第 {} 句".format(
            progress["chapter"], progress["line"] + 1
        )
    )


def _validate_progress(data):
    """检查存档结构，避免错误存档导致剧情循环崩溃。"""
    saved_progress = data.get("progress")
    if not isinstance(saved_progress, dict):
        raise ValueError("缺少 progress 数据")

    chapter = saved_progress.get("chapter")
    line = saved_progress.get("line")
    if isinstance(chapter, bool) or not isinstance(chapter, int):
        raise ValueError("chapter 必须是整数")
    if isinstance(line, bool) or not isinstance(line, int):
        raise ValueError("line 必须是整数")
    if chapter not in STORY:
        raise ValueError("存档中的章节不存在")
    if not 0 <= line < len(STORY[chapter]):
        raise ValueError("存档中的台词位置超出范围")

    return chapter, line


def _dismiss_current_dialog():
    """结束当前对话，让剧情循环立即跳到读档位置。"""
    box = dialogbox_module._get_shared_box()
    if box is not None:
        box._done()


def load_game():
    """立即读取进度、关闭当前对话并刷新为存档内容。"""
    global load_happened

    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        chapter, line = _validate_progress(data)
    except FileNotFoundError:
        show_notice("还没有存档")
        return
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        show_notice("读取失败：{}".format(exc))
        return

    progress["chapter"] = chapter
    progress["line"] = line
    load_happened = True
    show_notice("已读取：第 {} 章，第 {} 句".format(chapter, line + 1))
    QTimer.singleShot(0, _dismiss_current_dialog)


def run_story():
    """从 progress 记录的位置开始播放剧情。"""
    global load_happened

    # 设置一次后，所有 dialogbox 都会使用这两个回调。
    dokibox.dialogbox.save = save_game
    dokibox.dialogbox.load = load_game

    while True:
        chapter = progress["chapter"]
        line = progress["line"]
        chapter_lines = STORY[chapter]

        if line >= len(chapter_lines):
            break

        speaker, message = chapter_lines[line]
        is_last_line = line == len(chapter_lines) - 1
        dokibox.dialogbox(
            message,
            name=speaker,
            fdst=is_last_line,
        )

        if load_happened:
            # 读档数据已在 load_game() 中立即生效，直接从该位置重新循环。
            load_happened = False
            continue

        progress["line"] += 1

    dokibox.msgbox("剧情已结束。")


if __name__ == "__main__":
    run_story()

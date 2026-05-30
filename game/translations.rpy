## translations.rpy
## Ren'Py 内置字符串中文翻译 / Chinese translations for Ren'Py built-in strings

init python:
    ## 替换 Ren'Py 内置的英文字符串为中文
    ## Replace Ren'Py built-in English strings with Chinese

    ## 确认对话框相关
    config.quit_action = Confirm("确定要退出游戏吗？", Quit(confirm=False), Return())

    ## 通知消息
    config.autosave_callback = lambda: renpy.notify(_("自动存档完成"))

## 使用 translate None strings 来翻译内置字符串
## 这会在默认语言(None)下替换英文字符串

translate None strings:

    ## 确认提示
    old "Are you sure?"
    new "确定吗？"

    old "Are you sure you want to delete this save?"
    new "确定要删除这个存档吗？"

    old "Are you sure you want to overwrite your save?"
    new "确定要覆盖这个存档吗？"

    old "Are you sure you want to quit?"
    new "确定要退出游戏吗？"

    old "Are you sure you want to return to the main menu?\nThis will lose unsaved progress."
    new "确定要返回主菜单吗？\n未保存的进度将会丢失。"

    old "Loading will lose unsaved progress.\nAre you sure you want to do this?"
    new "读档将丢失未保存的进度。\n确定要继续吗？"

    ## 按钮文本
    old "Yes"
    new "确定"

    old "No"
    new "取消"

    old "OK"
    new "确定"

    old "Cancel"
    new "取消"

    old "Delete"
    new "删除"

    ## 存档相关
    old "Empty Slot"
    new "空存档位"

    old "empty slot"
    new "空存档位"

    old "Quick Save"
    new "快速存档"

    old "Quick Load"
    new "快速读档"

    old "Auto"
    new "自动"

    old "Page {}"
    new "第 {} 页"

    old "auto"
    new "自动存档"

    old "quick"
    new "快速存档"

    ## 通知
    old "Quick save complete."
    new "快速存档完成。"

    old "Quick save failed."
    new "快速存档失败。"

    old "Quick load complete."
    new "快速读档完成。"

    old "Quick load failed."
    new "快速读档失败。"

    ## 设置相关
    old "Display"
    new "显示"

    old "Window"
    new "窗口"

    old "Fullscreen"
    new "全屏"

    old "Sound"
    new "音效"

    old "Music Volume"
    new "音乐音量"

    old "Sound Volume"
    new "音效音量"

    old "Voice Volume"
    new "语音音量"

    old "Mute All"
    new "全部静音"

    old "Text Speed"
    new "文字速度"

    old "Auto-Forward Time"
    new "自动前进时间"

    old "Skip"
    new "跳过"

    old "Unseen Text"
    new "未读文本"

    old "After Choices"
    new "选择后"

    old "Transitions"
    new "转场"

    old "Seen Messages"
    new "已读信息"

    old "All Messages"
    new "全部信息"

    old "Stop Skipping"
    new "停止跳过"

    old "Keep Skipping"
    new "继续跳过"

    ## 历史记录
    old "History"
    new "历史记录"

    old "The dialogue history is empty."
    new "对话历史为空。"

    ## 关于界面
    old "About"
    new "关于"

    ## 帮助界面
    old "Help"
    new "帮助"

    old "Keyboard"
    new "键盘"

    old "Mouse"
    new "鼠标"

    old "Gamepad"
    new "手柄"

    ## 无障碍
    old "Self-Voicing"
    new "自动朗读"

    old "Clipboard Voicing"
    new "剪贴板朗读"

    old "Debug Voicing"
    new "调试朗读"

    old "Disabled"
    new "禁用"

    old "Enabled"
    new "启用"

    ## 其他
    old "Return"
    new "返回"

    old "Start"
    new "开始游戏"

    old "Load"
    new "读档"

    old "Save"
    new "存档"

    old "Preferences"
    new "设置"

    old "Main Menu"
    new "主菜单"

    old "Quit"
    new "退出"

    old "End Replay"
    new "结束回放"

    ## 跳过提示
    old "Skipping"
    new "跳过中"

    old "Skipping Mode"
    new "跳过模式"

    ## 日期时间格式
    old "%A, %B %d %Y, %H:%M"
    new "%Y年%m月%d日 %H:%M"

    old "{#month_short}%b"
    new "%m月"

    old "{#time}%H:%M"
    new "%H:%M"

    old "{#day}%d"
    new "%d日"

    old "{#year}%Y"
    new "%Y年"

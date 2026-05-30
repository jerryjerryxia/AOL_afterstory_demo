## screens.rpy
## 游戏界面定义 / Screen Definitions

################################################################################
## 初始化
################################################################################

init offset = -1

################################################################################
## SFX Lock Screen - blocks player input until sound channel finishes playing
################################################################################

screen sfx_lock():
    modal True
    timer 0.1 repeat True action Function(sfx_lock_check)

init python:
    def sfx_lock_check():
        if not renpy.music.get_playing(channel='sound'):
            renpy.hide_screen('sfx_lock')

################################################################################
## 存档删除功能
################################################################################

init python:
    def _force_refresh_text():
        """Force the currently-shown say to re-evaluate its translation.

        Ren'Py's Language() action redraws screens but the say's `what` was
        already translated when the character was called. Rolling back one
        statement then auto-rolling forward re-runs the say with the new
        language. defer=True lets us call this safely from a screen action.
        """
        try:
            renpy.rollback(force=True, checkpoints=1, defer=True, greedy=False)
        except Exception:
            pass

    def dialog_size():
        """Per-language dialogue font size.

        English needs more horizontal room than the same Chinese — sentences
        stretch where 4–5 hanzi convey a clause. Shrinking the dialogue font
        a bit in English mode prevents big monologue blocks from overflowing
        the large_say textbox. Tweak the English value if the contrast feels
        too aggressive.
        """
        if _preferences.language == "english":
            return 27
        return gui.text_size

    def delete_all_saves():
        """Delete all save files using Ren'Py's built-in functions."""
        deleted_count = 0
        # Use Ren'Py's API to list and delete all saves properly
        for slot in renpy.list_slots():
            renpy.unlink_save(slot)
            deleted_count += 1
        # 没存档了，主菜单按钮回到"开始游戏"
        persistent.has_save_in_run = False
        renpy.notify("已删除 {} 个存档".format(deleted_count))

    def delete_persistent_data():
        """Delete all persistent data (route progress, endings, etc.)."""
        # Clear all persistent data by resetting to defaults
        persistent._clear(progress=True)
        # Notify the user
        renpy.notify("已清除所有持久化数据，请重启游戏")
        # Restart the game to apply changes
        renpy.utter_restart()

################################################################################
## GUI 变量定义（填补缺失的变量）
################################################################################

define gui.main_menu_background = None
define gui.game_menu_background = None
define gui.namebox_width = None
define gui.namebox_height = None
define gui.navigation_xpos = 60
define gui.navigation_spacing = 6
define gui.slot_spacing = 15
define gui.page_spacing = 15
define gui.pref_spacing = 0
define gui.notify_ypos = 68
define gui.skip_ypos = 15
define gui.unscrollable = "hide"

################################################################################
## 样式
################################################################################

style default:
    font gui.text_font
    size gui.text_size
    color gui.text_color
    language "unicode"

style input:
    color gui.accent_color
    adjust_spacing False

style hyperlink_text:
    color gui.accent_color
    hover_underline True

## GUI 基础样式 - Base GUI Styles
style gui_button is button:
    background None

style gui_button_text is button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.selected_color
    insensitive_color gui.insensitive_color

style gui_label:
    padding (0, 0, 0, 0)

style gui_label_text:
    font gui.interface_text_font
    size gui.label_text_size
    color gui.accent_color

style gui_viewport:
    xfill True
    yfill True

style gui_side:
    spacing 6

style gui_vscrollbar:
    xsize 18
    base_bar Solid("#333333")
    thumb Solid("#666666")
    hover_thumb Solid("#888888")

style gui_text:
    font gui.interface_text_font
    size gui.interface_text_size
    color gui.interface_text_color

style button:
    background None

style button_text is gui_text:
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.selected_color
    insensitive_color gui.insensitive_color
    yalign 0.5

style label_text is gui_text:
    color gui.accent_color

style prompt_text is gui_text

################################################################################
## 对话界面 - Say Screen
################################################################################

screen say(who, what):
    style_prefix "say"

    window:
        id "window"

        if who is not None:
            window:
                id "namebox"
                style "namebox"
                text who id "who"

        text what id "what"

    ## 快捷按钮（跳过、自动、菜单等）
    use quick_menu

    ## 开发者场景信息
    use dev_scene_info

    ## 开发者音乐选择器
    use dev_music_selector

style window is default
style say_label is default
style say_dialogue is default
style say_thought is say_dialogue

style namebox is default
style namebox_label is say_label

style say_label:
    font gui.name_text_font
    size gui.name_text_size
    color gui.accent_color
    xalign gui.name_xalign
    yalign 0.5

style say_dialogue:
    font gui.text_font
    size gui.text_size
    xpos gui.dialogue_xpos
    xsize gui.dialogue_width
    ypos gui.dialogue_ypos

style window:
    xalign 0.5
    xsize 1400
    yalign gui.textbox_yalign
    ysize gui.textbox_height
    background Frame("gui/box_dark.png", 20, 20)

style namebox:
    xpos gui.name_xpos
    xanchor gui.name_xalign
    ypos gui.name_ypos
    background Frame("gui/box_dark.png", 20, 20)
    padding (10, 5, 10, 5)

################################################################################
## 一次性"序章首文本框淡入"机制
## ----------------------------------------------------------------
## 只在主菜单退场后的第一条 large_say 对话上播放一次淡入；其它所有对话都瞬出。
##
## 用法：主菜单 timer 在 Start() 之前 SetVariable("_intro_fade_pending", True)。
## 下一条 large_say mount 时：
##   - flag=True  → 重置 flag，alpha 从 0 ease-in 到 1（淡入）
##   - flag=False → alpha 立刻设为 1 并把 ATL 永久"挂起"（无任何动画/影响）
## 由于 flag 在 first call 就被消费掉，后续所有 large_say 都走 False 分支。
default _intro_fade_pending = False

init python:
    def _say_intro_fade_or_halt(trans, st, at):
        if renpy.store._intro_fade_pending:
            renpy.store._intro_fade_pending = False
            return None  # 推进到下一行的 easein
        # 不淡入：直接显示，挂起 ATL（return 一个超大值，效果上=永不再唤醒）
        trans.alpha = 1.0
        return 999999.0

transform say_intro_fade:
    alpha 0.0
    function _say_intro_fade_or_halt
    easein 0.6 alpha 1.0

################################################################################
## 大文本框界面 - Large Textbox Screen (Full-height narrative text)
## 居中在屏幕正中央 (1920-1520)/2=200, (1080-800)/2=140
################################################################################

screen large_say(who, what):
    frame:
        at say_intro_fade
        xpos 200
        ypos 140
        xsize 1520
        ysize 800
        padding (80, 80, 80, 80)
        background Frame("gui/box_dark.png", 20, 20)

        text what id "what":
            ## Fixed top-left position for consistent reading experience
            xalign 0.0
            yalign 0.0
            text_align 0.0
            xsize 1360
            font gui.text_font
            size dialog_size()  # smaller in English; see init python at top
            color "#ffffff"
            line_spacing 10

    ## 快捷按钮
    use quick_menu

    ## 开发者场景信息
    use dev_scene_info

    ## 开发者音乐选择器
    use dev_music_selector

################################################################################
## 居中文本框界面 - Centered Textbox Screen (for striking single lines)
################################################################################

screen centered_say(who, what):
    frame:
        xpos 200
        ypos 140
        xsize 1520
        ysize 800
        padding (80, 80, 80, 80)
        background Frame("gui/box_dark.png", 20, 20)

        text what id "what":
            ## Centered for dramatic effect
            xalign 0.5
            yalign 0.5
            text_align 0.5
            xsize 1360
            font gui.text_font
            size dialog_size()  # smaller in English; see init python at top
            color "#ffffff"
            line_spacing 10

    ## 快捷按钮
    use quick_menu

    ## 开发者场景信息
    use dev_scene_info

    ## 开发者音乐选择器
    use dev_music_selector

################################################################################
## 居中大字文本框界面 - Centered Large Font Textbox Screen
################################################################################

screen centered_large_say(who, what):
    frame:
        xpos 200
        ypos 140
        xsize 1520
        ysize 800
        padding (80, 80, 80, 80)
        background Frame("gui/box_dark.png", 20, 20)

        text what id "what":
            ## Centered with larger font for dramatic effect
            xalign 0.5
            yalign 0.5
            text_align 0.5
            xsize 1360
            font gui.text_font
            size dialog_size() + 6  # smaller in English; see init python at top
            color "#ffffff"
            line_spacing 10

    ## 快捷按钮
    use quick_menu

    ## 开发者场景信息
    use dev_scene_info

    ## 开发者音乐选择器
    use dev_music_selector

################################################################################
## 快捷菜单 - Quick Menu
################################################################################

screen quick_menu():
    zorder 100

    if quick_menu:
        hbox:
            style_prefix "quick"

            xalign 0.5
            yalign 1.0
            yoffset -10
            spacing 20

            textbutton _("历史") action ShowMenu('history')
            textbutton _("跳过") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("自动") action Preference("auto-forward", "toggle")
            textbutton _("存档") action ShowMenu('save')
            textbutton _("读档") action ShowMenu('load')
            textbutton _("快存") action QuickSave()
            textbutton _("快读") action QuickLoad()
            textbutton _("设置") action ShowMenu('preferences')

default quick_menu = True

style quick_button is default
style quick_button_text is button_text

style quick_button:
    background None

style quick_button_text:
    size 21
    idle_color gui.idle_small_color
    hover_color gui.hover_color
    selected_color gui.selected_color

################################################################################
## 选择支界面 - Choice Screen
################################################################################

screen choice(items):
    style_prefix "choice"

    vbox:
        for i in items:
            textbutton i.caption action i.action

style choice_vbox is vbox
style choice_button is button
style choice_button_text is button_text

style choice_vbox:
    xalign 0.5
    ypos 405
    yanchor 0.5
    spacing 33

style choice_button is default:
    xsize gui.choice_button_width
    idle_background Frame("gui/choice_idle.png", 20, 20)
    hover_background Frame("gui/choice_hover.png", 20, 20)
    padding (150, 8, 150, 8)

style choice_button_text is default:
    xalign 0.5
    idle_color "#cccccc"
    hover_color "#ffffff"

################################################################################
## 主菜单 - Main Menu
################################################################################

## 主菜单"开始游戏"被点击时的退场动画状态。
## 动画驱动方式：用 ATL 的 `function` 轮询状态变量 _main_menu_starting。
## showif + on_hide 在 Ren'Py 里不能驱动退场动画（条件翻假 displayable 被
## 立刻从树里抽走）；transform_event 在 screen 重新求值时也不可靠。轮询稳。
default _main_menu_starting = False

init python:
    def _wait_for_main_menu_exit(trans, st, at):
        return None if _main_menu_starting else 0

## 标题：上滑淡出。先停在 alpha=1 yoffset=0，等变量翻 True，再易出动画。
transform menu_title_anim:
    alpha 1.0
    yoffset 0
    function _wait_for_main_menu_exit
    easeout 0.5 alpha 0.0 yoffset -50

## 菜单按钮：阶梯式左滑淡出。delay 让每个按钮错开开始时间，
## 从最底下的按钮 (delay 0) 阶梯上去到"开始游戏" (delay 0.42s)。
transform menu_btn_anim(delay=0.0):
    alpha 1.0
    xoffset 0
    function _wait_for_main_menu_exit
    pause delay
    easeout 0.35 alpha 0.0 xoffset -180

screen main_menu():
    ## 主菜单 - 这是游戏启动时显示的第一个界面
    tag menu

    style_prefix "main_menu"

    ## 玩家从游戏回到主菜单后强制重启 polyhedron channel —— 走过游戏一遭
    ## Movie/channel lifecycle 会乱，channel 显示 playing 但 Movie() 渲染成
    ## checker board。stop+play 一遍才能让显示恢复正常。flag 用 persistent
    ## 因为 MainMenu() action 清普通变量但保留 persistent。
    python:
        if persistent.polyhedron_started_game:
            try:
                renpy.music.stop(channel="polyhedron_video")
            except Exception:
                pass
            renpy.music.play(
                "images/bg/polyhedron.webm",
                channel="polyhedron_video", loop=True)
            persistent.polyhedron_started_game = False

    ## 背景：polyhedron Movie 从共享 channel 取帧，主菜单 → 序章首场景无缝。
    add "bg_polyhedron_video"

    ## 暗化效果（也跟标题一起淡出）
    frame at menu_title_anim:
        style "main_menu_frame"

    ## 游戏标题：上滑淡出
    vbox at menu_title_anim:
        xalign 0.5
        yalign 0.3

        text _("无休夏日综合症"):
            size 80
            xalign 0.5
            color "#ffffff"

    ## 主菜单按钮：直接 inline，不走 `use navigation`，因为每个要带自己的 delay。
    ## stagger = 0.06s。点击"开始游戏" → _main_menu_starting=True → 所有 transform
    ## 同时翻动；sensitive 在退场期间关掉所有按钮，避免误触发。
    vbox:
        style_prefix "navigation"
        xpos gui.navigation_xpos
        yalign 0.5
        spacing gui.navigation_spacing

        ## 当前周目有存档就显示"继续游戏"（点了 load 最近存档），否则显示
        ## "开始游戏"（点了走 start label）。两者共用退场动画，timer 跑完后
        ## exit_main_menu_to_game() 根据 has_save_in_run 决定 Continue 还是 Start。
        ## list_slots() 多查一道：flag 是 True 但没存档（边缘情况）也回退到 Start。
        if persistent.has_save_in_run and renpy.list_slots():
            textbutton _("继续游戏") action SetVariable("_main_menu_starting", True) sensitive not _main_menu_starting at menu_btn_anim(0.42)
        else:
            textbutton _("开始游戏") action SetVariable("_main_menu_starting", True) sensitive not _main_menu_starting at menu_btn_anim(0.42)
        textbutton _("读取存档") action ShowMenu("load") sensitive not _main_menu_starting at menu_btn_anim(0.36)
        textbutton _("删除存档") action Confirm("确定要删除所有存档吗？此操作无法撤销。", yes=Function(delete_all_saves), no=None) sensitive not _main_menu_starting at menu_btn_anim(0.30)
        textbutton _("清除进度") action Confirm("确定要清除所有进度吗？\n（周目、结局解锁等，游戏将重启）", yes=Function(delete_persistent_data), no=None) sensitive not _main_menu_starting at menu_btn_anim(0.24)
        textbutton _("音乐鉴赏") action ShowMenu("music_room") sensitive not _main_menu_starting at menu_btn_anim(0.18)
        textbutton _("设置") action ShowMenu("preferences") sensitive not _main_menu_starting at menu_btn_anim(0.12)
        textbutton _("关于") action ShowMenu("about") sensitive not _main_menu_starting at menu_btn_anim(0.06)

        if renpy.variant("pc") or (renpy.variant("web") and not renpy.variant("mobile")):
            textbutton _("退出") action Quit(confirm=not main_menu) sensitive not _main_menu_starting at menu_btn_anim(0.0)

    ## 时序：按钮 stagger 最顶 0.42 + 0.35 = 0.77s 完成；标题 0.5s。
    ## 再加 ~0.5s 让玩家看到纯背景视频"喘口气"，文本框再进。
    ## timer 跑完 → 重置状态 → exit_main_menu_to_game() 决定 Continue / Start。
    ## (exit_main_menu_to_game 内部按 has_save_in_run 选 load_most_recent_save
    ## 或者武装 intro_fade_pending + jump_out_of_context("start")。)
    if _main_menu_starting:
        timer 1.25 action [SetVariable("_main_menu_starting", False), Function(exit_main_menu_to_game)]

style main_menu_frame is empty
style main_menu_vbox is vbox
style main_menu_text is gui_text
style main_menu_title is main_menu_text
style main_menu_version is main_menu_text

style main_menu_frame:
    xsize 420
    yfill True

style main_menu_vbox:
    xalign 0.5
    xoffset 0
    xmaximum 1200
    yalign 0.5
    yoffset 0

style main_menu_text:
    xalign 0.5

style main_menu_button is gui_button:
    xalign 0.5
    xsize 400

style main_menu_button_text is gui_button_text:
    xalign 0.5
    size 36

################################################################################
## 游戏菜单基础框架 - Game Menu
################################################################################

screen game_menu(title, scroll=None, yinitial=0.0):
    style_prefix "game_menu"

    ## 占位符背景
    add Solid("#1a1a2acc")

    frame:
        style "game_menu_outer_frame"

        hbox:
            frame:
                style "game_menu_navigation_frame"

            frame:
                style "game_menu_content_frame"

                if scroll == "viewport":
                    viewport:
                        yinitial yinitial
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        pagekeys True
                        side_yfill True
                        vbox:
                            transclude
                elif scroll == "vpgrid":
                    vpgrid:
                        cols 1
                        yinitial yinitial
                        scrollbars "vertical"
                        mousewheel True
                        draggable True
                        pagekeys True
                        side_yfill True
                        transclude
                else:
                    transclude

    use navigation

    textbutton _("返回"):
        style "return_button"
        action Return()

    label title

    if main_menu:
        key "game_menu" action ShowMenu("main_menu")

style game_menu_outer_frame is empty
style game_menu_navigation_frame is empty
style game_menu_content_frame is empty
style game_menu_viewport is gui_viewport
style game_menu_side is gui_side
style game_menu_scrollbar is gui_vscrollbar

style game_menu_label is gui_label
style game_menu_label_text is gui_label_text

style return_button is navigation_button
style return_button_text is navigation_button_text

style game_menu_outer_frame:
    bottom_padding 45
    top_padding 180
    background Solid("#00000080")

style game_menu_navigation_frame:
    xsize 420
    yfill True

style game_menu_content_frame:
    left_margin 60
    right_margin 30
    top_margin 15

style game_menu_viewport:
    xsize 1380

style game_menu_vscrollbar:
    unscrollable gui.unscrollable

style game_menu_side:
    spacing 15

style game_menu_label:
    xpos 75
    ysize 180

style game_menu_label_text:
    size gui.title_text_size
    color gui.accent_color
    yalign 0.5

style return_button:
    xpos gui.navigation_xpos
    yalign 1.0
    yoffset -45

################################################################################
## 导航菜单 - Navigation
################################################################################

screen navigation():
    vbox:
        style_prefix "navigation"

        xpos gui.navigation_xpos
        yalign 0.5

        spacing gui.navigation_spacing

        if main_menu:
            textbutton _("开始游戏") action Start()
            textbutton _("读取存档") action ShowMenu("load")
            textbutton _("删除存档") action Confirm("确定要删除所有存档吗？此操作无法撤销。", yes=Function(delete_all_saves), no=None)
            textbutton _("清除进度") action Confirm("确定要清除所有进度吗？\n（周目、结局解锁等，游戏将重启）", yes=Function(delete_persistent_data), no=None)
            textbutton _("音乐鉴赏") action ShowMenu("music_room")
        else:
            textbutton _("历史记录") action ShowMenu("history")
            textbutton _("存档") action ShowMenu("save")
            textbutton _("读档") action ShowMenu("load")

        textbutton _("设置") action ShowMenu("preferences")

        if _in_replay:
            textbutton _("结束回放") action EndReplay(confirm=True)
        elif not main_menu:
            textbutton _("标题画面") action MainMenu()

        textbutton _("关于") action ShowMenu("about")

        if renpy.variant("pc") or (renpy.variant("web") and not renpy.variant("mobile")):
            textbutton _("退出") action Quit(confirm=not main_menu)

style navigation_button is gui_button
style navigation_button_text is gui_button_text

style navigation_button:
    size_group "navigation"
    background None

style navigation_button_text:
    size gui.interface_text_size
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.selected_color

################################################################################
## 存档/读档界面 - Save/Load Screens
################################################################################

screen save():
    tag menu
    use file_slots(_("存档"))

screen load():
    tag menu
    use file_slots(_("读档"))

screen file_slots(title):
    default page_name_value = FilePageNameInputValue(pattern=_("第 {} 页"), auto=_("自动存档"), quick=_("快速存档"))

    use game_menu(title):
        fixed:
            order_reverse True

            button:
                style "page_label"
                key_events True
                xalign 0.5
                action page_name_value.Toggle()

                input:
                    style "page_label_text"
                    value page_name_value

            grid gui.file_slot_cols gui.file_slot_rows:
                xalign 0.5
                yalign 0.5
                spacing gui.slot_spacing

                for i in range(gui.file_slot_cols * gui.file_slot_rows):
                    $ slot = i + 1

                    vbox:
                        style "slot_vbox"

                        button:
                            style "slot_button"
                            action FileAction(slot)

                            has vbox

                            add FileScreenshot(slot) xalign 0.5

                            text FileTime(slot, format=_("{#file_time}%Y-%m-%d %H:%M"), empty=_("空存档位")):
                                style "slot_time_text"

                            text FileSaveName(slot):
                                style "slot_name_text"

                        ## Delete button - only show if slot has a save
                        if FileLoadable(slot):
                            textbutton _("删除"):
                                style "slot_delete_button"
                                action FileDelete(slot)

                        key "save_delete" action FileDelete(slot)

            hbox:
                style_prefix "page"
                xalign 0.5
                yalign 1.0

                spacing gui.page_spacing

                textbutton _("<") action FilePagePrevious()
                key "save_page_prev" action FilePagePrevious()

                if config.has_autosave:
                    textbutton _("{#auto_page}A") action FilePage("auto")

                textbutton _("{#quick_page}Q") action FilePage("quick")

                for page in range(1, 10):
                    textbutton "[page]" action FilePage(page)

                textbutton _(">") action FilePageNext()
                key "save_page_next" action FilePageNext()

style page_label is gui_label
style page_label_text is gui_label_text
style page_button is gui_button
style page_button_text is gui_button_text

style page_label:
    xpadding 75
    ypadding 5

style page_label_text:
    textalign 0.5
    layout "subtitle"
    hover_color gui.hover_color

style page_button:
    background None

style page_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

style slot_vbox:
    spacing 5

style slot_button:
    background Solid("#333333aa")
    hover_background Solid("#555555aa")
    xsize gui.slot_button_width
    ysize gui.slot_button_height

style slot_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

style slot_time_text:
    idle_color gui.idle_color
    size gui.slot_button_text_size
    xalign gui.slot_button_text_xalign

style slot_name_text:
    idle_color gui.idle_color
    size gui.slot_button_text_size
    xalign gui.slot_button_text_xalign

style slot_delete_button:
    xalign 0.5
    background Solid("#552222")
    hover_background Solid("#773333")
    padding (15, 5, 15, 5)

style slot_delete_button_text:
    size 18
    idle_color "#ffaaaa"
    hover_color "#ffffff"

################################################################################
## 设置界面 - Preferences Screen
################################################################################

screen preferences():
    tag menu

    use game_menu(_("设置"), scroll="viewport"):
        vbox:
            hbox:
                box_wrap True

                vbox:
                    style_prefix "radio"
                    label _("语言 / Language")
                    ## Language() 会重渲屏幕，但 say 已经捕获了上一句的 `what`
                    ## 字符串（在那一句被调用时翻译完成），重渲后还是显示旧语言。
                    ## 用 renpy.rollback(checkpoints=1) 让 Ren'Py 退回上一条
                    ## 语句再自动滚到当前位置——这次的 say 调用会用新语言重新
                    ## 查翻译，文本盒里的文字才真的换语言。defer=True 让 rollback
                    ## 安全地从 screen action 里发起。
                    textbutton "中文" action [Language(None), Function(_force_refresh_text)]
                    textbutton "English" action [Language("english"), Function(_force_refresh_text)]

                if renpy.variant("pc") or renpy.variant("web"):
                    vbox:
                        style_prefix "radio"
                        label _("显示模式")
                        textbutton _("窗口") action Preference("display", "window")
                        textbutton _("全屏") action Preference("display", "fullscreen")

                vbox:
                    style_prefix "check"
                    label _("跳过设置")
                    textbutton _("未读文本") action Preference("skip", "toggle")
                    textbutton _("选项后继续") action Preference("after choices", "toggle")
                    textbutton _("过场后继续") action Preference("skip", "toggle")

                vbox:
                    style_prefix "check"
                    label _("开发者模式")
                    textbutton _("显示场景与音乐参考") action ToggleField(persistent, "dev_mode")

            null height 30

            hbox:
                style_prefix "slider"
                box_wrap True

                vbox:
                    label _("文字速度")
                    bar value Preference("text speed")

                    label _("自动前进时间")
                    bar value Preference("auto-forward time")

                vbox:
                    if config.has_music:
                        label _("音乐音量")
                        hbox:
                            bar value Preference("music volume")

                    if config.has_sound:
                        label _("音效音量")
                        hbox:
                            bar value Preference("sound volume")

                            if config.sample_sound:
                                textbutton _("测试") action Play("sound", config.sample_sound)

            null height 30

            hbox:
                style_prefix "pref"
                box_wrap True

                vbox:
                    label _("存档管理")
                    textbutton _("删除所有存档"):
                        style "delete_saves_button"
                        action Confirm("确定要删除所有存档吗？此操作无法撤销。",
                            yes=Function(delete_all_saves),
                            no=None)

style delete_saves_button is gui_button:
    background Solid("#552222")
    hover_background Solid("#773333")
    padding (20, 10, 20, 10)

style delete_saves_button_text is gui_button_text:
    idle_color "#ffaaaa"
    hover_color "#ffffff"

style pref_label is gui_label
style pref_label_text is gui_label_text
style pref_vbox is vbox

style radio_label is pref_label
style radio_label_text is pref_label_text
style radio_button is gui_button
style radio_button_text is gui_button_text
style radio_vbox is pref_vbox

style check_label is pref_label
style check_label_text is pref_label_text
style check_button is gui_button
style check_button_text is gui_button_text
style check_vbox is pref_vbox

style slider_label is pref_label
style slider_label_text is pref_label_text
style slider_slider is gui_slider
style slider_button is gui_button
style slider_button_text is gui_button_text
style slider_pref_vbox is pref_vbox

style pref_label:
    top_margin 15
    bottom_margin 3

style pref_label_text:
    yalign 1.0

style pref_vbox:
    xsize 338

style radio_vbox:
    spacing gui.pref_spacing

style radio_button:
    background None

style radio_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.selected_color

style check_vbox:
    spacing gui.pref_spacing

style check_button:
    background None

style check_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color
    selected_color gui.selected_color

style slider_slider:
    xsize 525

style slider_button:
    background None
    yalign 0.5
    left_margin 15

style slider_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

style slider_vbox:
    xsize 675

################################################################################
## 历史记录界面 - History Screen
################################################################################

screen history():
    tag menu

    predict False

    use game_menu(_("历史"), scroll="viewport", yinitial=1.0):
        style_prefix "history"

        for h in _history_list:
            window:
                has fixed:
                    yfit True

                if h.who:
                    label h.who:
                        style "history_name"
                        substitute False

                        if "color" in h.who_args:
                            text_color h.who_args["color"]

                $ what = renpy.filter_text_tags(h.what, allow=gui.history_allow_tags)
                text what:
                    substitute False

        if not _history_list:
            label _("暂无历史记录。")

define gui.history_allow_tags = {"b", "i", "u", "s", "color", "font", "size"}

style history_window is empty
style history_name is gui_label
style history_name_text is gui_label_text
style history_text is gui_text
style history_label is gui_label
style history_label_text is gui_label_text

style history_window:
    xfill True
    ysize gui.history_height

style history_name:
    xpos gui.history_name_xpos
    xanchor gui.history_name_xalign
    ypos gui.history_name_ypos
    xsize gui.history_name_width

style history_name_text:
    min_width gui.history_name_width
    textalign gui.history_name_xalign

style history_text:
    xpos gui.history_text_xpos
    ypos gui.history_text_ypos
    xanchor gui.history_text_xalign
    xsize gui.history_text_width
    min_width gui.history_text_width
    textalign gui.history_text_xalign

style history_label:
    xfill True

style history_label_text:
    xalign 0.5

################################################################################
## 音乐鉴赏界面 - Music Room
################################################################################

init python:
    ## 定义音乐列表
    music_tracks = [
        {"id": "main_theme", "name": "主题曲", "file": "audio/bgm/main_theme.ogg"},
        {"id": "peaceful", "name": "日常", "file": "audio/bgm/peaceful.ogg"},
        {"id": "emotional", "name": "感动", "file": "audio/bgm/emotional.ogg"},
        {"id": "ending", "name": "结局", "file": "audio/bgm/ending.ogg"},
    ]

screen music_room():
    tag menu

    use game_menu(_("音乐鉴赏"), scroll="viewport"):
        style_prefix "music_room"

        vbox:
            spacing 15

            for track in music_tracks:
                if is_music_unlocked(track["id"]):
                    textbutton track["name"]:
                        action Play("music", track["file"])
                else:
                    textbutton "???":
                        sensitive False

            null height 30

            hbox:
                spacing 30
                textbutton _("停止播放") action Stop("music", fadeout=1.0)

style music_room_button is gui_button
style music_room_button_text is gui_button_text

style music_room_button:
    xsize 400
    background Solid("#333333aa")
    hover_background Solid("#555555aa")
    padding (20, 10, 20, 10)

style music_room_button_text:
    xalign 0.5

################################################################################
## 关于界面 - About Screen
################################################################################

screen about():
    tag menu

    use game_menu(_("关于"), scroll="viewport"):
        style_prefix "about"

        vbox:
            label "[config.name!t]"
            text _("版本 [config.version!t]\n")

            text _("在此处添加游戏介绍...\n")

            text _("制作人员：\n")
            text _("- 策划：\n- 程序：\n- 美术：\n- 音乐：\n")

style about_label is gui_label
style about_label_text is gui_label_text
style about_text is gui_text

style about_label_text:
    size gui.label_text_size

################################################################################
## 确认对话框 - Confirm Screen
################################################################################

screen confirm(message, yes_action, no_action):
    modal True
    zorder 200

    style_prefix "confirm"

    add Solid("#000000aa")

    frame:
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 45

            label _(message):
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 150

                textbutton _("确定") action yes_action
                textbutton _("取消") action no_action

    key "game_menu" action no_action

style confirm_frame is gui_frame
style confirm_prompt is gui_prompt
style confirm_prompt_text is gui_prompt_text
style confirm_button is gui_button
style confirm_button_text is gui_button_text

style confirm_frame:
    background Solid("#333333ee")
    padding (60, 60, 60, 60)
    xalign 0.5
    yalign 0.5

style confirm_prompt_text:
    textalign 0.5
    layout "subtitle"

style confirm_button:
    background Solid("#555555")
    hover_background Solid("#777777")
    padding (30, 10, 30, 10)

style confirm_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

################################################################################
## 通知界面 - Notify Screen
################################################################################

screen notify(message):
    zorder 100
    style_prefix "notify"

    frame at notify_appear:
        text "[message!tq]"

    timer 3.25 action Hide('notify')

transform notify_appear:
    on show:
        alpha 0
        linear 0.25 alpha 1.0
    on hide:
        linear 0.5 alpha 0.0

style notify_frame is empty
style notify_text is gui_text

style notify_frame:
    ypos gui.notify_ypos
    background Solid("#333333cc")
    padding (24, 8, 60, 8)

style notify_text:
    size gui.notify_text_size

################################################################################
## 跳过指示器 - Skip Indicator
################################################################################

screen skip_indicator():
    zorder 100
    style_prefix "skip"

    frame:
        hbox:
            spacing 9
            text _("快进中")
            text ">" at delayed_blink(0.0, 1.0) style "skip_triangle"
            text ">" at delayed_blink(0.2, 1.0) style "skip_triangle"
            text ">" at delayed_blink(0.4, 1.0) style "skip_triangle"

transform delayed_blink(delay, cycle):
    alpha 0.5
    pause delay
    block:
        linear 0.2 alpha 1.0
        pause 0.2
        linear 0.2 alpha 0.5
        pause (cycle - 0.6)
        repeat

style skip_frame is empty
style skip_text is gui_text
style skip_triangle is skip_text

style skip_frame:
    ypos gui.skip_ypos
    background Solid("#333333aa")
    padding (24, 8, 30, 8)

style skip_text:
    size gui.notify_text_size

################################################################################
## 周目标题界面 - Route Title Screen
################################################################################

screen route_title(title, subtitle=None):
    ## 全屏显示周目标题，点击后淡出

    modal True
    zorder 100

    default closing = False

    ## 整个画面容器
    frame:
        background None
        xfill True
        yfill True

        if not closing:
            at route_title_fadein
        else:
            at route_title_fadeout

        ## 背景图片占位（之后替换为实际美术资源）
        add Solid("#000000")

        ## 标题文字容器
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 20

            text title:
                style "route_title_text"

            if subtitle:
                text subtitle:
                    style "route_subtitle_text"

    ## 点击任意处开始淡出
    if not closing:
        button:
            xfill True
            yfill True
            action SetScreenVariable("closing", True)

    ## 淡出完成后关闭
    if closing:
        timer 0.8 action Return()

transform route_title_fadein:
    alpha 0.0
    ease 1.0 alpha 1.0

transform route_title_fadeout:
    ease 0.8 alpha 0.0

style route_title_text:
    font gui.text_font
    size 120
    color "#ffffff"
    xalign 0.5
    outlines [(4, "#000000", 0, 0)]

style route_subtitle_text:
    font gui.text_font
    size 48
    color "#cccccc"
    xalign 0.5
    outlines [(2, "#000000", 0, 0)]

################################################################################
## 开发者场景信息显示 - Developer Scene Info Display
################################################################################

## Whether the scene description popup is visible
default scene_desc_visible = False

screen dev_scene_info():
    ## Only show if we have a scene name and in developer mode
    if current_scene_name and persistent.dev_mode:
        # Top-left corner panel
        frame:
            style "dev_scene_frame"
            xalign 0.0
            yalign 0.0
            xoffset 10
            yoffset 10

            vbox:
                spacing 5

                # Scene name button - click to toggle description
                textbutton current_scene_name:
                    style "dev_scene_name"
                    action ToggleVariable("scene_desc_visible")

                # Scene description - shown when clicked
                if scene_desc_visible and current_scene_desc:
                    null height 5
                    frame:
                        style "dev_scene_desc_frame"
                        text "[current_scene_desc]":
                            style "dev_scene_desc_text"

style dev_scene_frame:
    background Solid("#1a1a2acc")
    padding (15, 10, 15, 10)
    xmaximum 500

style dev_scene_name is button:
    background None
    hover_background None

style dev_scene_name_text is button_text:
    size 20
    color "#00ccff"
    hover_color "#66ddff"

style dev_scene_desc_frame:
    background Solid("#222233cc")
    padding (10, 8, 10, 8)
    xmaximum 470

style dev_scene_desc_text:
    size 16
    color "#cccccc"
    line_spacing 4

################################################################################
## 开发者音乐选择器 - Developer Music Selector
################################################################################

## Current scene music ID (set by script)
default current_music_scene = None

## Whether the music selector panel is expanded
default dev_music_expanded = False

screen dev_music_selector():
    ## Only show if we have a valid scene and in developer mode
    if current_music_scene and current_music_scene in scene_music and persistent.dev_mode:
        $ scene_data = scene_music[current_music_scene]
        $ tracks = scene_data["tracks"]
        $ scene_label = scene_data["label"]

        # Top-right corner panel
        frame:
            style "dev_music_frame"
            xalign 1.0
            yalign 0.0
            xoffset -10
            yoffset 10

            vbox:
                spacing 5

                # Header with toggle button
                hbox:
                    spacing 10
                    if dev_music_expanded:
                        textbutton "BGM参考菜单":
                            style "dev_music_header"
                            action SetVariable("dev_music_expanded", False)
                    else:
                        textbutton "BGM参考菜单 v":
                            style "dev_music_header"
                            action SetVariable("dev_music_expanded", True)

                # Expanded track list
                if dev_music_expanded:
                    null height 5
                    for track in tracks:
                        $ is_selected = (persistent.scene_music_selections.get(current_music_scene) == track["id"])
                        if is_selected:
                            textbutton track["name"]:
                                style "dev_music_track_selected"
                                action Function(select_and_play_music, current_music_scene, track["id"])
                        else:
                            textbutton track["name"]:
                                style "dev_music_track"
                                action Function(select_and_play_music, current_music_scene, track["id"])

                    null height 5
                    hbox:
                        spacing 15
                        textbutton "■ 停止":
                            style "dev_music_control"
                            action Stop("music", fadeout=1.0)

style dev_music_frame:
    background Solid("#1a1a2acc")
    padding (15, 10, 15, 10)
    xmaximum 450

style dev_music_header is button_text:
    size 18
    color "#ffcc00"
    hover_color "#ffffff"

style dev_music_track is button:
    background Solid("#333333aa")
    hover_background Solid("#555555aa")
    padding (10, 5, 10, 5)
    xfill True

style dev_music_track_text is button_text:
    size 16
    color "#cccccc"
    hover_color "#ffffff"

style dev_music_track_selected is button:
    background Solid("#4a5a3aaa")
    hover_background Solid("#5a6a4aaa")
    padding (10, 5, 10, 5)
    xfill True

style dev_music_track_selected_text is button_text:
    size 16
    color "#aaffaa"
    hover_color "#ffffff"

style dev_music_control is button:
    background Solid("#552222aa")
    hover_background Solid("#773333aa")
    padding (8, 4, 8, 4)

style dev_music_control_text is button_text:
    size 14
    color "#ffaaaa"
    hover_color "#ffffff"

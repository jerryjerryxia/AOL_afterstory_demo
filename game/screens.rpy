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
    ## English boxes use the full-size font (33) and so sit a touch lower than
    ## they did at the shrunk size; nudge the large/split boxes up in English
    ## only. Bump EN_BOX_YSHIFT to move them further up; Chinese is untouched.
    EN_BOX_YSHIFT = 40
    def box_ypos(base):
        if _preferences.language == "english":
            return base - EN_BOX_YSHIFT
        return base

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
        renpy.notify(_("已删除 {} 个存档").format(deleted_count))

    def delete_persistent_data():
        """Delete all persistent data (route progress, endings, etc.)."""
        # Clear all persistent data by resetting to defaults
        persistent._clear(progress=True)
        # Notify the user
        renpy.notify(_("已清除所有持久化数据，请重启游戏"))
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

init python:
    ## 运行时「逐句点击」：显示时在句末标点后插入 {w}（等待点击）标签，而不是把
    ## 分句写进源文本。好处：翻译 ID 永远是干净整句、与英文源 1:1，以后改分句规则
    ## 再也不会冲掉翻译（这是把转换期分句改成运行时分句的核心）。
    ## 规则（中英通吃）：
    ##   - 。！？… 和 ASCII . ! ? 之后断句（标点留在前），等待点击；—— 之后也断；
    ##   - 省略号不断：ASCII 连续 ≥2 个点当省略号（…/...），单个 . 当英文句号要断；
    ##   - 句尾（后面再无实质内容）不加 {w}——say 收尾本身就等点击；
    ##   - extend 边界（标点紧跟 Ren'Py 的 {fast} 标签）也不加 {w}：那个 {w} 会被
    ##     {fast} 瞬显跳过（冗余），更糟的是会吞掉紧随其后的 \n 换行（split/大文本框
    ##     里"几乎没有跨行"的元凶）。statement 边界本身就是一次点击。
    ##   - 用于旁白和所有有名字的角色对白（point：句号/问号/感叹号/破折号处处分句）；
    ##     只有居中大字框不分句。
    def add_click_pauses(what):
        if not what:
            return what
        ## 段落级「不分句」开关（转换器在 Extended 大文本框「不分句」块前后置 True/False）：
        ## 整段每行按 statement 边界一次点击展示，句中不插 {w}。用于破折号单句成行、
        ## 逐句点击太繁琐的段落。
        if getattr(renpy.store, "no_click_split", False):
            return what
        STRONG = u"。！？!?…"          # 单个即断的句末标点
        def wants_pause(rest):
            rest = rest.lstrip()
            if not rest or rest.startswith('{fast}'):
                return False
            ## 去掉文本标签（{size}/{i}/{/…} 等）后还有实质文字才断句——避免在闭合标签
            ## 前插看不见的空 {w}（如小字行 "…——{/size}"、斜体专有名词收尾）。
            import re as _re
            return bool(_re.sub(r'\{[^}]*\}', '', rest).strip())
        out = []
        n = len(what)
        i = 0
        while i < n:
            ch = what[i]
            if ch == '.':                # ASCII 点：≥2 个=省略号不断，单个=句号断
                j = i
                while j < n and what[j] == '.':
                    j += 1
                out.append(what[i:j])
                if j - i == 1 and wants_pause(what[j:]):
                    out.append('{w}')
                i = j
                continue
            if ch in STRONG or ch == u'—':
                j = i + 1
                while j < n and (what[j] in STRONG or what[j] == u'—'):
                    j += 1
                out.append(what[i:j])
                if wants_pause(what[j:]):
                    out.append('{w}')
                i = j
                continue
            out.append(ch)
            i += 1
        return ''.join(out)

    class ClickPauseCharacter(renpy.character.ADVCharacter):
        ## 旁白/对白角色：在 __call__ 最早处把整句 what 插入 {w}（逐句点击）。
        ## 关键——必须在 __call__ 里改，不能在 do_display 里改：ADVCharacter.__call__
        ## 会先 `dtt = DialogueTextTags(what)` 从原文解析出 {w} 停顿点，再带着这个 dtt
        ## 调 do_display。在 do_display 里加的 {w} 进了屏幕文本却没进 dtt，会被当成无效
        ## 标签静默吞掉 —— 整句一次显示、完全不分句（和文字速度无关，这是之前的真 bug）。
        ## {w} 停顿是按 dtt 拆出的独立 saybehavior 交互，逐段等点击，瞬显也照样生效。
        def __call__(self, what, *args, **kwargs):
            return super(ClickPauseCharacter, self).__call__(add_click_pauses(what), *args, **kwargs)

screen say(who, what):
    style_prefix "say"

    ## 底部渐变（替代原本的深灰底框）：让对话浮在画面上，
    ## 同时压暗底部保证文字可读。
    add "gui/say_scrim.png" xalign 0.5 yalign 1.0

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
    outlines gui.text_outlines

style say_dialogue:
    font gui.text_font
    size gui.text_size
    xpos gui.dialogue_xpos
    xsize gui.dialogue_width
    ypos gui.dialogue_ypos
    outlines gui.text_outlines

style window:
    xalign 0.5
    xsize 1400
    yalign gui.textbox_yalign
    ysize gui.textbox_height
    background None

style namebox:
    xpos gui.name_xpos
    xanchor gui.name_xalign
    ypos gui.name_ypos
    background None
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
    def _clear_demo_return_fade():
        # 清掉主菜单入场淡入标志。必须返回 None —— 若返回非 None（如 session.pop
        # 返回的 True），screen action 会以该值结束主菜单交互，被当成"开始游戏"。
        renpy.session.pop("_demo_return_fade", None)

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

## demo 通关 reboot 回主菜单后，整屏（背景+标题+按钮）从纯黑淡入一次。
## 出屏是 fade_to_black_long，落到黑；reboot 后主菜单本会瞬间弹出（很生硬），
## 这里盖一层黑幕 easeout 淡出，视觉上就是主菜单从黑里缓缓浮现。
transform _demo_return_fadein:
    alpha 1.0
    easeout 1.2 alpha 0.0

################################################################################
## 点击继续指示器 - CTC (click-to-continue) 打字光标（point 2）
## ----------------------------------------------------------------
## 一行文字打完、等待玩家点击时，在文字末尾出现一个闪烁的打字光标（竖条 ▏），
## 亮 0.5s / 灭 0.5s 循环，像文本框里在等你继续输入。挂在 Character 的 ctc 上
## （nestled，自动紧跟正文末尾）。
##
## 为什么用"竖条"而不是省略号：文字里的内联显示物是从基线往下挂的，句点 "."
## 落在基线最底端，看起来又低又"离得远"；而占满整行高度的竖条字形天然和正文
## 对齐。位置还想微调就改 characters.rpy 里 `define ctc = Transform("ctc_dots", …)`
## 的 xoffset / yoffset。
################################################################################

## 光标画成一根实心竖条（不是 Text "|"——那种会被字体上沿空白拖低，长度和位置分不开）。
## 每个 (文本框类型, 语言) 三个**互相独立**的旋钮：
##   length：竖条高度（长度）
##   yoff  ：上下位置。0 = 条顶和这行文字顶部齐平；往大调（正数）= 整条往下。
##           注意：往上只能到 0（内联元素超出行顶会被裁掉、变不可见），到 0 就和正文齐了。
##   width ：竖条粗细
##   xoff  ：左右位置。0 = 紧贴文字末尾；往大调（正数）= 往右留空。往左只能到 0
##           （超出文字末尾左边会被裁掉，和 yoff 同理）。
init python:
    _CARET_CFG = {
        # (类型,    语言)        (length, yoff, width, xoff)
        ("normal", "chinese"): (31, 5, 3, 0),
        ("normal", "english"): (30, 6, 3, 6),
        ("large",  "chinese"): (33, 5, 3, 0),
        ("large",  "english"): (33, 5, 3, 6),
    }
    def _caret_size(kind):
        def f(st, at):
            lang = "english" if _preferences.language == "english" else "chinese"
            length, yoff, width, xoff = _CARET_CFG[(kind, lang)]
            ow = 2  # 黑色描边宽度（浮在亮背景上也清晰）
            bar = Composite((width + 2 * ow, length + 2 * ow),
                            (0, 0), Solid("#000000", xsize=width + 2 * ow, ysize=length + 2 * ow),
                            (ow, ow), Solid(gui.text_color, xsize=width, ysize=length))
            # 内联元素裁掉文字行框以外的部分，所以横竖都靠在「框内」摆放竖条：
            # yoff 往下、xoff 往右（负值会被裁，下限 0）。
            bx = max(0, xoff)
            box_h = length + 2 * ow
            cur = Composite((width + 2 * ow + bx, box_h), (bx, yoff), bar)
            on = (st % 1.0) < 0.5
            return (Transform(cur, alpha=(1.0 if on else 0.0)),
                    ((0.5 - (st % 1.0)) if on else (1.0 - (st % 1.0))))
        return f

image ctc_dots = DynamicDisplayable(_caret_size("normal"))
image ctc_dots_large = DynamicDisplayable(_caret_size("large"))

################################################################################
## 操作锁定屏幕 - op_lock（point 5）
## ----------------------------------------------------------------
## 用一个全屏按钮把"点击/回车/空格"吃掉（NullAction），让玩家在 N 秒内无法靠点击
## 跳过文字展示或前进；但**不 modal**，所以 ctrl 快进（skip 是 keysym，不落到按钮
## 上）依然有效。N 秒后自动隐藏。配合 convert_script.py 的 【锁定操作Ns】。
## （"盯——"：不允许点击快速结束文字展示，但允许 ctrl 快进。）
################################################################################

screen op_lock(seconds):
    zorder 200
    button:
        xfill True
        yfill True
        background None
        hover_background None
        action NullAction()
    timer seconds action Hide("op_lock")

################################################################################
## 颤动文字标签 - {shake}...{/shake}（point 8）
## ----------------------------------------------------------------
## 给一段文字加持续颤动。把内容逐字替换为带 tremble 变换的内联 displayable，
## 这样只有被包裹的文字抖动，其余文字与名字框不受影响。
## 用法（剧本/raw script 内）：{shake}好刻薄{/shake}
################################################################################

transform tremble:
    subpixel True
    block:
        ease 0.06 yoffset -2 xoffset 1
        ease 0.06 yoffset 2 xoffset -1
        ease 0.06 yoffset -1 xoffset -2
        ease 0.06 yoffset 1 xoffset 2
        repeat

style tremble_char is default:
    font gui.text_font
    size gui.text_size
    color gui.text_color
    outlines gui.text_outlines

init python:
    def _shake_text_tag(tag, argument, contents):
        new_list = []
        for kind, text in contents:
            if kind == renpy.TEXT_TEXT:
                for ch in text:
                    new_list.append(
                        (renpy.TEXT_DISPLAYABLE, At(Text(ch, style="tremble_char"), tremble)))
            else:
                new_list.append((kind, text))
        return new_list

    config.custom_text_tags["shake"] = _shake_text_tag

################################################################################
## 大文本框界面 - Large Textbox Screen (Full-height narrative text)
## 居中在屏幕正中央 (1920-1520)/2=200, (1080-800)/2=140
################################################################################

screen large_say(who, what):
    frame:
        at say_intro_fade
        xpos 200
        ypos box_ypos(140)
        xsize 1520
        ysize 800
        padding (80, 80, 80, 80)
        background None

        text what id "what":
            ## Fixed top-left position for consistent reading experience
            xalign 0.0
            yalign 0.0
            text_align 0.0
            xsize 1360
            font gui.text_font
            ## Full-height box has room to spare, so keep English at the normal
            ## gui.text_size (33) — same as the other text — instead of shrinking
            ## it to dialog_size() (27) like the narrower boxes do.
            size gui.text_size
            color "#ffffff"
            line_spacing 10
            outlines gui.text_outlines

    ## 快捷按钮
    use quick_menu

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
        background None

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
            outlines gui.text_outlines

    ## 快捷按钮
    use quick_menu

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
        background None

        text what id "what":
            ## Centered with a much larger font — these are the prologue's
            ## single-sentence gut-punches (疯子。/ 逃避吧！/ 瘾。). The size jump
            ## is the whole point: make the impact land (point 1).
            xalign 0.5
            yalign 0.5
            text_align 0.5
            xsize 1360
            font gui.text_font
            size dialog_size() + 39  # ≈72 in CN / ≈66 in EN; see init python at top
            color "#ffffff"
            line_spacing 10
            outlines gui.text_outlines

    ## 快捷按钮
    use quick_menu

################################################################################
## 左右分栏大文本框 - Split Large Textbox（甜品店幻视段）
## ----------------------------------------------------------------
## 把大文本框分成左右两栏：先逐行点击填满左栏，再填右栏。中间留空避开王霜的头
## （她大致在画面正中）。两栏字数由转换器按行边界尽量切平均（见 convert_script.py
## 的 emit_split_large_block）。
##
## 两阶段，各阶段的"活动栏"就是带 id "what" 的那个 text —— 所以逐字速度（文字
## 速度设置）和"单击推进下一段"在两栏里都和普通文本框一样。
##   split_say_left ：左栏 = 活动 say（id "what"，逐字显示）。
##   split_say_right：左栏 = 静态 _split_left_text（上阶段冻结的内容）；
##                    右栏 = 活动 say（id "what"，逐字显示）。
## 左栏在两阶段坐标一致（xpos 90），切换时不跳动。两栏放在 fixed 里各自定位
## （frame 只能放单个子项，多个会乱——这是之前"前两句消失/重复"的根源）。
################################################################################

## 上阶段填满的左栏内容（由转换器 `$ _split_left_text = ...` 设置）
default _split_left_text = ""

## 分栏几何：左栏 90..710、右栏 1210..1830，中间 710..1210（~500px，画面正中）
## 留给王霜的头。想调就改下面 xpos / xsize。
style split_column_text is default:
    font gui.text_font
    color "#ffffff"
    xanchor 0.0
    yalign 0.0
    text_align 0.0
    line_spacing 10
    outlines gui.text_outlines

## 关键：活动 say（id "what"）和静态左栏必须渲染得**一模一样**，否则左栏在切到
## 右栏阶段时会"变高/行距变大"。两个差异都得内联写死（style 里的设不到 say 的 what）：
##   1. line_spacing 10 —— say 的 what 拿不到 style 里的行距（受 what_style 影响）。
##   2. adjust_spacing False —— 逐字显示默认 adjust_spacing=True，会为"打字时宽度稳定"
##      微调字间距，导致最终折行/高度和静态文本不一致。中文是逐字折行，关掉它不会
##      有"打字时回流"的副作用，却能让 say 和静态左栏折行、高度完全一致。
screen split_say_left(who, what):
    ## 左栏阶段：左栏就是活动 say（id "what" → 逐字显示、单击推进）。
    ## 顺手把（已翻译的）what 存进 _split_left_text，供右栏阶段静态显示——这样
    ## 英文模式下右栏开始后，左栏仍是英文，不会变回中文。
    ## 关键：必须用 renpy.predicting() 门控。Ren'Py 会预渲染（predict）后面的
    ## split_say_left，预测时这个 $ 会带着「后面某个分栏块」的 what 执行，污染
    ## _split_left_text，导致右栏阶段左栏显示成后文（例如"鼓的声音"那段反复顶替
    ## 前文）。只在真正显示（非预测）时写入，预测不写，bug 即消。
    ## 冻结左栏给右栏阶段静态显示：去掉 {w}（ClickPauseCharacter 给活动 what 插了
    ## 逐句点击标签，但静态左栏已全部显示完，不需要也不能用 {w}）。
    $ if not renpy.predicting(): store._split_left_text = what.replace("{w}", "")
    fixed:
        xpos 0
        ypos box_ypos(260)
        xsize 1920
        ysize 760

        text what id "what":
            style "split_column_text"
            xpos 90
            ypos 0
            yanchor 0.0
            xsize 620
            size gui.text_size  # full size in English too; matches large_say
            line_spacing 10
            adjust_spacing False

    use quick_menu

screen split_say_right(who, what):
    ## 右栏阶段：左栏静态（已填满），右栏是活动 say（id "what" → 逐字显示）。
    fixed:
        xpos 0
        ypos box_ypos(260)
        xsize 1920
        ysize 760

        ## 左栏：已填满，静态（和 split_say_left 同坐标 + 同行距 + 同字距 + 同纵向锚点，
        ## 切换不跳动/不上移）
        text _split_left_text:
            style "split_column_text"
            xpos 90
            ypos 0
            yanchor 0.0
            xsize 620
            size gui.text_size  # full size in English too; matches large_say
            line_spacing 10
            adjust_spacing False

        ## 右栏：活动 say，逐字显示
        text what id "what":
            style "split_column_text"
            xpos 1210
            ypos 0
            yanchor 0.0
            xsize 620
            size gui.text_size  # full size in English too; matches large_say
            line_spacing 10
            adjust_spacing False

    use quick_menu

################################################################################
## 右侧Split 大文本框 - 只占右半屏的单栏、分页（每页满 8 行翻页）
## 比左右分栏的"右栏"略往中间推一点（xpos 1120 vs 1210），左半屏留空。
## 想再往中间/往右挪就改下面的 xpos（越小越靠中间）。
## 翻页由转换器控制：每页第一行是新 say（清屏），其余 extend；满 8 行就开新页。
################################################################################
screen split_right_page(who, what):
    fixed:
        xpos 0
        ypos box_ypos(260)
        xsize 1920
        ysize 760

        text what id "what":
            style "split_column_text"
            xpos 1120
            ypos 0
            yanchor 0.0
            xsize 620
            size gui.text_size  # full size in English too; matches large_say
            line_spacing 10
            adjust_spacing False

    use quick_menu

################################################################################
## 快捷菜单 - Quick Menu
################################################################################

## 右下角悬停展开菜单的几何参数（虚拟 1920x1080 坐标）。改按钮数量/字号时只改这里。
define QM_EDGE_X = -30          ## 离右边界
define QM_EDGE_Y = -15          ## "菜单"按钮离下边界
define QM_PANEL_Y = -54         ## 选项列底边的位置 = 边距 + "菜单"按钮行高 + 间隙
define QM_AREA_W = 220          ## 悬停感应区宽度（比最宽的按钮宽即可）
define QM_AREA_H_SHUT = 62      ## 收起时只盖住"菜单"按钮本身

## 展开后的感应区高度必须真的盖住整列，否则鼠标移到靠上的选项时就掉出感应区、
## 整个菜单缩回去（原来写死 340，顶边正好落在"历史"这一项的中间）。
## 所以按几何算出来，别再手填：底边偏移 + 全部选项的高度 + 20px 余量。
define QM_ITEM_PITCH = 40       ## 单项行高：21px 文字的按钮高约 34 + spacing 6
define QM_ITEM_COUNT = 8        ## 选项数量。增删按钮时改这里，感应区自动跟着长
define QM_AREA_H_OPEN = -QM_PANEL_Y + QM_ITEM_COUNT * QM_ITEM_PITCH + 20

init python:
    def qm_is_open():
        return renpy.session.get("_qm_open", False)

    def qm_track_pointer():
        """轮询指针是否落在右下角感应区内，据此开合快捷菜单。

        为什么是直接读指针坐标，而不是 mousearea 或按钮的 hovered/unhovered
        —— 这两条路都试过，都不成立：
          * 挂在"菜单"按钮的 hovered/unhovered 上：玩家把鼠标往上移到选项时
            必然先离开按钮本身，菜单立刻收起，选项永远点不到。
          * mousearea：它的 render() 直接采用父容器给的尺寸（见 SDK 的
            display/behavior.py MouseArea.render），xsize/ysize 收不窄感应区；
            而且 quick_menu 是被 say 屏 `use` 进来的，SetScreenVariable 写的是
            say 屏的作用域、showif 读的是 use 块的作用域，两边根本对不上。
        "指针在不在这个矩形里"本来就是这个交互的原始问题，直接问指针坐标即可，
        不经过焦点系统就没有这些边角情况。

        状态存在 renpy.session：不写进存档、不参与 rollback。
        展开后感应区变高覆盖整列 —— 在列内移动不会收起，移出矩形才收起。
        """
        x, y = renpy.get_mouse_pos()
        open_now = qm_is_open()
        h = QM_AREA_H_OPEN if open_now else QM_AREA_H_SHUT
        want = (x >= config.screen_width - QM_AREA_W) and (y >= config.screen_height - h)
        if want != open_now:
            renpy.session["_qm_open"] = want
            renpy.restart_interaction()

## 选项列滑出。showif 条件翻转时触发 ATL 的 on show / on hide。
transform qm_slide:
    on show:
        alpha 0.0
        yoffset 24
        easein 0.18 alpha 1.0 yoffset 0
    on hide:
        easeout 0.14 alpha 0.0 yoffset 24

screen quick_menu():
    zorder 100

    ## 收起状态只占右下角一个"菜单"按钮，鼠标移上去整列向上滑出。
    ## 原来 8 个按钮常驻竖排，占掉右下角一大块画面。
    if quick_menu:
        ## _update_screens=False 是必须的：Function 默认在每次调用后
        ## renpy.restart_interaction() —— 这个 timer 一秒跑 20 次，等于每秒重启
        ## 20 次交互，所有靠 st 计时的 displayable（首当其冲是打字光标 ctc_dots，
        ## 它用 st % 1.0 闪烁）时钟被不停清零，表现为光标以诡异的不规则频率乱闪。
        ## qm_track_pointer 内部只在开合状态真正翻转时才自己 restart_interaction。
        timer 0.05 repeat True action Function(qm_track_pointer, _update_screens=False)

        ## "菜单"按钮和选项列各自独立定位（不放进同一个 vbox）：
        ## showif 隐藏时子件仍留在显示树里，同 vbox 会让按钮被顶离右下角。
        ## NullAction：它只是块悬停靶子和视觉提示，点击不该有额外行为。
        textbutton _("菜单"):
            style "quick_toggle"
            xalign 1.0
            yalign 1.0
            xoffset QM_EDGE_X
            yoffset QM_EDGE_Y
            action NullAction()

        showif qm_is_open():
            vbox:
                style_prefix "quick"
                at qm_slide

                xalign 1.0
                yalign 1.0
                xoffset QM_EDGE_X
                yoffset QM_PANEL_Y
                spacing 6

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
    xalign 1.0  # 竖排时每个按钮靠右对齐（贴右下角）

style quick_button_text:
    size 21
    idle_color gui.idle_small_color
    hover_color gui.hover_color
    selected_color gui.selected_color
    outlines gui.text_outlines  # 和正文一致的黑色描边，浮在画面上也清晰

## 收起状态那颗"菜单"按钮：比列表项亮一档，让人知道这里有东西可点。
style quick_toggle is quick_button
style quick_toggle_text is quick_button_text

style quick_toggle_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

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
    ## 纯文字选项：去掉深灰按钮底框，只保留少量内边距作为点击区域
    padding (40, 12, 40, 12)

style choice_button_text is default:
    xalign 0.5
    size gui.choice_button_text_size
    ## 加粗 + 与正文一致的黑色描边/阴影（gui.text_outlines），不再依赖按钮底框
    bold True
    outlines gui.text_outlines
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

## ---------------------------------------------------------------------------
## 涟漪过场：点下"开始游戏"的瞬间，整个主菜单画面（背景+标题+按钮）开始荡漾，
## 荡漾进行中切进序章。类似甜品店的 water_effect —— 那边是可循环的持续晃动，
## 这边是一次性的"石入水面"：有波前、向外推进、振幅衰减到平静。
##
## 结构（踩过的坑，别推翻）：
##   * 主菜单是 screen，jump_out_of_context 时它连同上面的一切立即消失，所以
##     "荡漾"必须两边接力：菜单侧把整个 screen 内容包进一个 fixed、挂涟漪 shader
##     （menu_ripple，点击瞬间启动）；游戏侧 label start 把同一张 bg_menu_sea 铺上
##     master 层、用 camera 挂 screen_ripple(RIPPLE_T0) 从中断处续跑 —— 两边
##     shader 参数一致、进度衔接，切换那一帧看不出接缝。
##   * 游戏侧用 camera 而不是 show layer：scene 语句会清 layer_at_list（见
##     shaders.rpy 里 screen_ripple 的注释），而序章第一句正好就是 scene。
##
## 时间轴（秒，从点击"开始游戏"算起）：
##   0.00  整屏开始荡漾（菜单侧 menu_ripple 从 t=0 起跑）
##   0.50  离开主菜单 → label start：bg_menu_sea 上 master，camera 从 RIPPLE_T0
##         续跑涟漪；序章首个 scene 同时以 ripple_reveal 从中心向外交叉溶解进来
##         （溶解方向和涟漪一致：都是从中心往四周走）
##   3.00  溶解完成（0.5 + 2.5）
##   3.30  荡漾衰减完毕（游戏侧在进入后 RIPPLE_CLEANUP 秒摘掉 camera transform）
define MENU_EXIT_DELAY = 0.5     ## 点击后多久离开主菜单 = 转场开始前的荡漾时间
define RIPPLE_DURATION = 3.3     ## 整屏荡漾从最强衰减到平静（从点击算起）
define RIPPLE_DISSOLVE = 2.5     ## 海面 → 序章首帧的交叉溶解时长
define RIPPLE_T0 = MENU_EXIT_DELAY / RIPPLE_DURATION   ## 游戏侧续跑的起点进度
define RIPPLE_CLEANUP = 3.0      ## 进游戏后多久摘 camera（> 剩余荡漾 2.8s 即可）

## 菜单侧的整屏涟漪：包住 main_menu 的全部内容（见下面 screen main_menu 的 fixed）。
## 平时 u_ripple_t 停在 0 —— t=0 时波包还压在落点半径里、settle=1 但 env≈0，
## 画面纹丝不动；点击"开始游戏"翻 _main_menu_starting → function 放行 → t 从 0 跑到 1。
## 所有参数引用 shaders.rpy 的 RIPPLE_* define（单一数据源），和游戏侧
## screen_ripple 必然一致，接力才无缝 —— 调参数去 shaders.rpy 改。
transform menu_ripple:
    mesh True
    shader "game.screen_ripple"
    u_ripple_amp RIPPLE_AMP
    u_ripple_freq RIPPLE_FREQ
    u_ripple_phspeed RIPPLE_PHSPEED
    u_ripple_r0 RIPPLE_R0
    u_ripple_gspeed RIPPLE_GSPEED
    u_ripple_w0 RIPPLE_W0
    u_ripple_spread RIPPLE_SPREAD
    u_ripple_impr RIPPLE_IMP_R
    u_ripple_impamp RIPPLE_IMP_AMP
    u_ripple_irreg RIPPLE_IRREG
    u_ripple_aspect RIPPLE_ASPECT
    u_ripple_pitch RIPPLE_PITCH
    u_ripple_focal RIPPLE_FOCAL
    u_ripple_height RIPPLE_HEIGHT
    u_ripple_t 0.0
    function _wait_for_main_menu_exit
    linear RIPPLE_DURATION u_ripple_t 1.0

## 游戏侧收尾：由 script.rpy 的 label start `show screen ripple_intro_fx` 拉起。
## RIPPLE_CLEANUP 后摘掉 master 层的 camera transform 并隐藏自己 ——
## 不摘的话整局游戏都会一直多跑一遍全屏 mesh 渲染。
screen ripple_intro_fx():
    timer RIPPLE_CLEANUP action [Function(renpy.show_layer_at, [], layer="master", camera=True), Hide("ripple_intro_fx")]
## ---------------------------------------------------------------------------

## 标题/按钮退场动画 —— 暂时停用（现在是整屏原地荡漾着切场景，元素不再滑出）。
## 想恢复：把 main_menu 里对应元素的 `at menu_title_anim` / `at menu_btn_anim(...)`
## 加回去即可（下面 screen 里有注释标出原来挂在哪），transform 本体保留：
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

    ## 主菜单不再显示 polyhedron 视频（背景是 sea.png），这里只把 channel 停掉：
    ## 一来省一路没人看的 webm 解码，二来把 channel 归零成干净状态。
    ## 真正的启动在 label start 里、序章 Movie 即将显示前做 stop+play ——
    ## 那是唯一可靠的重启时机（历史教训见 script.rpy label start 的注释：
    ## 在没有 Movie 取帧的时候重启 channel，到第二次进序章时它照样是坏的）。
    ## persistent.polyhedron_started_game 只是清一下，对外语义早已废弃。
    python:
        try:
            renpy.music.stop(channel="polyhedron_video")
        except Exception:
            pass
        persistent.polyhedron_started_game = False

    ## 整个可见内容（背景+暗化+标题+按钮）包进一个 fixed、挂 menu_ripple ——
    ## 点"开始游戏"的瞬间它们作为一个整体开始荡漾，而不是涟漪浮在表面。
    fixed at menu_ripple:

        ## 背景：sea.png，与 save/load/设置/音乐鉴赏（game_menu）统一。
        ## 图本身在 script.rpy 里定义成 bg_menu_sea（含黑底 + contain + 压暗层）。
        ## 这里和 label start 引用的必须是同一个 image —— 进游戏时要把它原样铺到
        ## master 层上接住画面，两边只要有一点不一样，切换的瞬间就会看到跳变。
        add "bg_menu_sea"

        ## 原背景：polyhedron Movie 从共享 channel 取帧，主菜单 → 序章首场景无缝。
        ## 想换回视频主菜单，取消下面这行的注释、并删掉上面的 bg_menu_sea：
        # add "bg_polyhedron_video"
        ##
        ## 注意：上面那段 stop+play polyhedron_video 的 python 块**故意保留在运行状态**，
        ## 没有一起注释掉。视频现在只是不显示，channel 仍在跑 —— 它撑着两件事：
        ##   1) prologue.rpy 的 `scene bg_polyhedron_video` 要有一个健康的 channel 才有画面；
        ##   2) 玩过一轮回主菜单后不 stop+play，第二次进序章会渲染成 checker board。
        ## 代价只是主菜单期间多解一路不可见的 webm。

        ## 暗化效果（退场动画停用中；恢复时在这行尾加回 at menu_title_anim）
        frame:
            style "main_menu_frame"

        ## 游戏标题。按语言切换中/英标题图。（恢复退场动画：at menu_title_anim）
        vbox:
            xalign 0.5
            yalign 0.18

            if _preferences.language == "english":
                add "images/ui/titles/en_title.png" zoom 0.24 xalign 0.5
            else:
                add "images/ui/titles/zh_title.png" zoom 0.30 xalign 0.5

        ## 主菜单按钮。sensitive 在退场期间关掉所有按钮，避免误触发。
        ## （恢复阶梯退场：给各按钮加回 at menu_btn_anim(0.42/0.36/…)，
        ## 自上而下 0.42→0.12，stagger 0.06s。）
        vbox:
            style_prefix "navigation"
            xpos gui.navigation_xpos
            yalign 0.5
            spacing gui.navigation_spacing

            ## 通关之后做的存档 → 显示"继续游戏"；否则显示"开始游戏"。
            ## has_continuable_save() 比较 max(slot_mtime) 和 last_route_completion_time，
            ## 通关后老存档自动失效；玩家新周目存档后又自动出 Continue。
            if has_continuable_save():
                textbutton _("继续游戏") action SetVariable("_main_menu_starting", True) sensitive not _main_menu_starting
            else:
                textbutton _("开始游戏") action SetVariable("_main_menu_starting", True) sensitive not _main_menu_starting
            textbutton _("读取存档") action ShowMenu("load") sensitive not _main_menu_starting
            textbutton _("音乐鉴赏") action ShowMenu("music_room") sensitive not _main_menu_starting
            textbutton _("设置") action ShowMenu("preferences") sensitive not _main_menu_starting
            textbutton _("关于") action ShowMenu("about") sensitive not _main_menu_starting

            if renpy.variant("pc") or (renpy.variant("web") and not renpy.variant("mobile")):
                textbutton _("退出") action Quit(confirm=not main_menu) sensitive not _main_menu_starting

    ## 点击"开始游戏"后：整屏立即开始荡漾（menu_ripple），MENU_EXIT_DELAY 秒后
    ## 离开主菜单，涟漪由游戏侧接力（见上面涟漪过场的时间轴）。
    ## timer 跑完 → 重置状态 → exit_main_menu_to_game() 决定 Continue / Start。
    ## (exit_main_menu_to_game 内部按 has_save_in_run 选 load_most_recent_save
    ## 或者武装 intro_fade_pending + jump_out_of_context("start")。)
    if _main_menu_starting:
        timer MENU_EXIT_DELAY action [SetVariable("_main_menu_starting", False), Function(exit_main_menu_to_game)]

    ## demo 通关 reboot 回主菜单：整屏从黑淡入一次，然后清标志（只淡入这一次）。
    ## 放在 screen 最后 = 盖在背景/标题/按钮之上；淡完由 timer 清 session 标志。
    if renpy.session.get("_demo_return_fade"):
        add Solid("#000000") at _demo_return_fadein
        timer 1.25 action Function(_clear_demo_return_fade)

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

    ## 背景：sea.png（3840x1240，3.10:1）。fit="contain" 按宽度铺满，
    ## 上下各留约 230px 黑边 —— 暂时接受，等有 16:9 版本的图再换。
    ## 铺满不透明 = 游戏中 ESC 进菜单不再透出当前场景（原来 #1a1a2acc 是 80% 遮罩）。
    ## 上面还叠着 game_menu_outer_frame 的 #00000080 压暗层，保证文字可读。
    add Solid("#000000")
    add Transform(
        "images/ui/menu_background/sea.png",
        xysize=(config.screen_width, config.screen_height),
        fit="contain", xalign=0.5, yalign=0.5)

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
            ## 跟主菜单按钮一致：通关之后有玩家"主动"做的存档就显示"继续游戏"，
            ## 否则"开始游戏"。FileLoad 用 _continuable_slots 最近的 slot —
            ## 玩家从这里进游戏的语义和主菜单 Continue 按钮相同。
            if has_continuable_save():
                $ _latest_continuable_slot = max(_continuable_slots(), key=lambda s: renpy.slot_mtime(s) or 0)
                textbutton _("继续游戏") action FileLoad(_latest_continuable_slot, confirm=False)
            else:
                textbutton _("开始游戏") action Start()
            textbutton _("读取存档") action ShowMenu("load")
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

                            ## 截图 = 槽位本身。以前是 384x216 的图装在 414x309 的
                            ## 灰框里、外加 vbox 把文字往下顶，四边留白全不均。
                            ## 现在 slot_button 的尺寸就是截图尺寸、padding 归零，
                            ## 再用 Transform 把截图强制拉到同一尺寸（fit="cover"），
                            ## 于是无论旧存档的缩略图是什么尺寸都逐像素铺满，不留边。
                            ## 时间/存档名压在底部半透明条上，不再改变槽位高度。
                            fixed:
                                add Transform(
                                    FileScreenshot(slot),
                                    xysize=(gui.slot_button_width, gui.slot_button_height),
                                    fit="cover")

                                frame:
                                    style "slot_caption"

                                    has vbox
                                    spacing 2

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

            ## 删除所有存档：存档界面右上角，二次确认后删除所有存档槽。
            ## （从主菜单移来；不碰持久进度，只删存档文件。复用设置里同名按钮的翻译。）
            textbutton _("删除所有存档"):
                style "delete_saves_button"
                xalign 1.0
                yalign 0.0
                action Confirm(_("确定要删除所有存档吗？此操作无法撤销。"), yes=Function(delete_all_saves), no=None)

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
    ## padding 归零：槽位的可视尺寸必须精确等于截图尺寸，否则又会出现留白。
    ## 背景只在空存档位（截图是透明的）时看得见。
    padding (0, 0, 0, 0)
    background Solid("#1a1d26cc")
    hover_background Solid("#2f3a4ccc")
    xsize gui.slot_button_width
    ysize gui.slot_button_height

style slot_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

## 截图底部的字幕条：压在图上，不占额外高度。
style slot_caption is empty:
    xfill True
    yalign 1.0
    background Solid("#000000b3")
    padding (12, 6, 12, 7)

## 继承 slot_button_text ⇒ 文字跟随按钮的 idle/hover 状态变色。
style slot_time_text is slot_button_text:
    size gui.slot_button_text_size
    xalign gui.slot_button_text_xalign
    outlines []

style slot_name_text is slot_button_text:
    size gui.slot_button_text_size
    xalign gui.slot_button_text_xalign
    outlines []

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

                ## 语言开关只在主菜单里显示。游戏内不让换 —— 之前用
                ## renpy.rollback 想在游戏中实时换语言，但对 large_say + extend
                ## 的组合不可靠（rollback 没法穿过 extend 重新执行 say）。
                ## 限制在主菜单切换，下一次 Start/Continue 之后看到的所有文字
                ## 都是新语言渲染的，避免 in-place refresh 的所有边角情况。
                if main_menu:
                    vbox:
                        style_prefix "radio"
                        label _("语言 / Language")
                        textbutton "中文" action Language(None)
                        textbutton "English" action Language("english")

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

            null height 30

            hbox:
                style_prefix "slider"
                box_wrap True

                vbox:
                    label _("文字速度")
                    ## 文字速度滑块上限砍半：默认 range=200cps，从中点往上（~100cps+）
                    ## 肉眼已分不出快慢、纯属浪费行程。改成 range=100，最慢端（最小值）
                    ## 不变，最大值取原来的一半，整条滑块的有效分辨率翻倍。
                    ## 注：逐句点击 {w} 是按 dtt 拆出的独立交互、逐段等点击，瞬显也照常
                    ## 生效（见 ClickPauseCharacter），所以这里**不需要**限制最高速度。
                    bar value Preference("text speed", range=100)

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
                        action Confirm(_("确定要删除所有存档吗？此操作无法撤销。"),
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

## 偏好设置滑动条本体。关键点：可调的 bar（value=Preference(...)）实际套用的是
## slider 样式（这里因 style_prefix "slider" 解析为 slider_slider），而不是下面那个
## bar 样式。本项目没有 slider 图片素材，默认 slider 整条不可见、ysize≈0，于是
## 文字速度 / 自动前进 / 音量 等滑块都无法点击或拖动。改用与 bar 一致的纯色绘制，
## 并加一个可见的白色滑块（thumb）方便拖动。
style slider_slider:
    xsize 525
    ysize 12
    left_bar Solid("#ffffff")
    right_bar Solid("#555555")
    hover_left_bar Solid("#ffffff")
    hover_right_bar Solid("#777777")
    left_gutter 0
    right_gutter 0
    thumb Solid("#ffffff", xsize=12, ysize=28)
    thumb_offset 6

style slider_button:
    background None
    yalign 0.5
    left_margin 15

style slider_button_text:
    idle_color gui.idle_color
    hover_color gui.hover_color

style slider_vbox:
    xsize 675

## 偏好设置滑动条（文字速度 / 自动前进 / 音量）。
## 这套界面没有附带 bar 图片素材，默认 bar 样式没有 left_bar/right_bar，
## 滑块整条不可见也就无法拖动。这里用纯色绘制：左段=已填充（白），
## 右段=轨道（深灰），整条可点击/拖动，无需任何图片素材。
style bar:
    xsize 500
    ysize 12
    left_bar Solid("#ffffff")
    right_bar Solid("#555555")
    hover_left_bar Solid("#ffffff")
    hover_right_bar Solid("#777777")
    left_gutter 0
    right_gutter 0
    thumb None

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

screen music_room():
    tag menu

    ## 曲目列表从 scene_music 推导（见 get_music_room_tracks）；未解锁显示 ???。
    ## 曲子在玩家第一次听到时（set_scene_music → unlock_music）解锁。
    use game_menu(_("音乐鉴赏"), scroll="viewport"):
        style_prefix "music_room"

        vbox:
            spacing 15

            for track in get_music_room_tracks():
                if is_music_unlocked(track["id"]):
                    ## music_track_spec 带上 <volume>/<loop> 前缀 —— 和剧情里
                    ## set_scene_music 播的是逐字相同的路径，所以鉴赏里的响度
                    ## 和循环点与游戏中完全一致（以前这里播裸文件名，偏响）。
                    textbutton _(track["name"]):
                        action Play("music", music_track_spec(track))
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

            text _("感谢游玩本Demo！\n请务必在正作继续下潜~\n")

            text _("制作人员：\n")
            text _("- 制作人：Jerrix\n- 剧本：Jerrix\n- 美术：Gara、Mermo\n- 音乐：Kevin, audionautix.com, FabienC@RustedMusicStudio\n- 音效：Sirderf，soundscalpel.com，rrehl, chewiesmissus, gravitysound.studio\n- 编辑：倪佼佼\n- 程序：Jerrix\n")

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

screen route_title(title, subtitle=None, sfx=None):
    ## 全屏显示周目标题（"浮潜"）。出现和消失都放慢；不允许鼠标点击快进，
    ## 只有按住 ctrl（快进/skip）才能跳过（point 3）。
    ## sfx：可选一次性音效，在标题"完整展示"（淡入 2.2s 结束）时播放一次。
    ## 用于落水泡泡这类需要在标题出现后、下个场景登场前播完的声音。

    modal True
    zorder 100

    default closing = False
    default sfx_played = False

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

    ## 标题完整展示（淡入 2.2s 结束）时播放一次性音效。play_sfx 同时记下结束时刻，
    ## 供调用处的 wait_sfx 等它播完再让下个场景登场。sfx_played 防止 closing 重渲染
    ## 时重复触发。
    if sfx and not sfx_played:
        timer 2.2 action [SetScreenVariable("sfx_played", True), Function(play_sfx, sfx)]

    ## 自走时序：淡入(2.2s) + 停留 → 到点自动开始淡出。没有任何鼠标点击区域，
    ## 因此点击不会快进；modal 也挡住了对下层的点击。
    if not closing:
        timer 4.0 action SetScreenVariable("closing", True)

    ## 淡出(2.2s)完成后关闭
    if closing:
        timer 2.2 action Return()

    ## 唯一的快进通道：按住 ctrl 进入 skip 时立即结束。轮询 is_skipping()，
    ## 因为 skip 是全局键映射，不依赖本 screen 的可聚焦元件。
    timer 0.05 repeat True action If(renpy.is_skipping(), true=Return(), false=NullAction())

## 出现/消失都放慢（point 3）：原来 1.0 / 0.8，现在 2.2 / 2.2。
transform route_title_fadein:
    alpha 0.0
    easein 2.2 alpha 1.0

transform route_title_fadeout:
    easeout 2.2 alpha 0.0

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

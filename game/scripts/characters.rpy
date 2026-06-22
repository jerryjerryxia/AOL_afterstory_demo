## characters.rpy
## 角色定义 / Character Definitions

################################################################################
## 角色定义
## 在这里定义所有角色。之后替换实际角色名称和颜色。
################################################################################

## CTC（点击继续）打字光标：nestled，自动跟在每行文字末尾（point 2）。
## 位置可调——改 xoffset（左右，负=往左靠近文字）/ yoffset（上下，负=往上抬）。
## 普通对话框和大文本框的正文基线不一样（大文本框多了 line_spacing、顶对齐），
## 同一个 yoffset 在两边高低会不同，所以分成两个：
##   ctc       —— 普通对话框（narrator + 所有角色）
##   ctc_large —— 大文本框（large_narrator）
## 各自单独调即可。居中文本框不挂 ctc（point 1）。
## 光标的字号（也就是高度/上下位置）在 screens.rpy 的 _CARET_CFG 表里按 (类型,语言) 调。
## 这里的 xoffset 只管水平贴近文字。
define ctc = Transform("ctc_dots", xoffset=-5)
## 大文本框用 ctc_dots_large：光标字号跟随 dialog_size()（英文小字号大文本框里不再
## 又长又低，见 screens.rpy）。yoffset 仍可单独微调高低。
define ctc_large = Transform("ctc_dots_large", xoffset=-5)

## 旁白/内心独白（无名字显示）—— ClickPauseCharacter：逐句点击由运行时 {w} 实现
## （见 screens.rpy add_click_pauses），翻译 ID 是干净整句、与英文源 1:1，改分句
## 逻辑不再冲掉翻译。居中旁白和有名字的角色仍用普通 Character（不分句）。
## ctc_pause=ctc：让光标在每个 {w} 断句处都出现（不止整行末尾）。Ren'Py 只在
## 最后一个 pause 用 ctc，中间的 {w} pause 用 ctc_pause——之前没设所以中间断句没光标。
define narrator = ClickPauseCharacter(None, kind=adv, ctc=ctc, ctc_pause=ctc)

## 大文本框旁白（用于长篇背景叙述）
define large_narrator = ClickPauseCharacter(None, kind=adv, screen="large_say", ctc=ctc_large, ctc_pause=ctc_large)

## 居中文本框旁白（用于戏剧性的单行文字）—— 不挂 CTC（point 1）
define centered_narrator = Character(None, kind=adv, screen="centered_say")

## 居中大字文本框旁白（用于戏剧性的单行大字）—— 不挂 CTC（point 1）
define centered_large_narrator = Character(None, kind=adv, screen="centered_large_say")

## 左右分栏大文本框（甜品店幻视段）：先填左栏，再填右栏，中间留空避开王霜的头。
## 两阶段：左栏阶段活动 say 在左栏（逐字显示），填满后冻结进 _split_left_text；
## 右栏阶段左栏静态、活动 say 在右栏。两阶段各自的可见栏就是带 id "what" 的活动
## 文本，所以逐字速度和单击推进在两栏都正常。CTC 用 ctc_large（和大文本框同基线）。
define split_left_narrator = ClickPauseCharacter(None, kind=adv, screen="split_say_left", ctc=ctc_large, ctc_pause=ctc_large)
define split_right_narrator = ClickPauseCharacter(None, kind=adv, screen="split_say_right", ctc=ctc_large, ctc_pause=ctc_large)

## 右侧Split：只占右半屏的单栏文本框，每页满 8 行翻页（新 say 清屏）。屏幕 split_right_page。
define split_right_page_narrator = ClickPauseCharacter(None, kind=adv, screen="split_right_page", ctc=ctc_large, ctc_pause=ctc_large)

## 主角内心独白 —— 也走 ClickPauseCharacter（句号/问号/感叹号/破折号处处分句）
define protag_thought = ClickPauseCharacter(None, kind=adv, what_prefix='"', what_suffix='"', what_italic=True, ctc=ctc, ctc_pause=ctc)

## 主要角色 —— 全部用 ClickPauseCharacter：角色对白也按标点逐句点击（用户要求"不管
## 任何地方"，含有名字的对白）。只有居中大字框（centered_*）不分句。
## 格式: define 变量名 = ClickPauseCharacter("显示名称", color="名字颜色")

define wangshuang = ClickPauseCharacter("王霜", color="#4a90d9", ctc=ctc, ctc_pause=ctc)  # 蓝色（原阿鹤的颜色）
define wangshuang_unknown = ClickPauseCharacter("王霜（？）", color="#4a90d9", ctc=ctc, ctc_pause=ctc)  # 蓝色，身份存疑
define ahe = ClickPauseCharacter("阿鹤", color="#f5c518", ctc=ctc, ctc_pause=ctc)  # 金黄色
define shishou = ClickPauseCharacter("尸首", color="#dc143c", ctc=ctc, ctc_pause=ctc)  # 深红色

## 配角 - Supporting Characters
define lurenjia = ClickPauseCharacter("路人甲", color="#7f8c8d", ctc=ctc, ctc_pause=ctc)  # 灰色
define lurenyi = ClickPauseCharacter("路人乙", color="#95a5a6", ctc=ctc, ctc_pause=ctc)  # 浅灰色
define lurenbing = ClickPauseCharacter("路人丙", color="#6c7a89", ctc=ctc, ctc_pause=ctc)  # 深灰色
define lurending = ClickPauseCharacter("路人丁", color="#a0a0a0", ctc=ctc, ctc_pause=ctc)  # 中灰色
define jieluowa = ClickPauseCharacter("杰罗瓦", color="#e67e22", ctc=ctc, ctc_pause=ctc)  # 橙色
define mijie = ClickPauseCharacter("米姐", color="#27ae60", ctc=ctc, ctc_pause=ctc)  # 绿色
define youliya = ClickPauseCharacter("尤里娅", color="#f1c40f", ctc=ctc, ctc_pause=ctc)  # 金色

## 未知角色（用于角色未揭示身份时）
define unknown = ClickPauseCharacter("???", color="#888888", ctc=ctc, ctc_pause=ctc)

################################################################################
## 角色精灵图定义
## 使用 layeredimage 实现表情变化
################################################################################

## 占位符精灵图 - 用纯色方块代替
## 当美术资源准备好后，替换为实际的 layeredimage 定义

image wangshuang_sprite = Solid("#9b59b6", xsize=400, ysize=800)
image ahe_sprite = Solid("#4a90d9", xsize=400, ysize=800)
image shishou_sprite = Solid("#dc143c", xsize=400, ysize=800)

## 实际角色精灵图示例（当资源准备好时使用）：
# layeredimage character_name:
#     always:
#         "sprites/character_name/base.png"
#     group expression:
#         attribute neutral default:
#             "sprites/character_name/neutral.png"
#         attribute happy:
#             "sprites/character_name/happy.png"
#         attribute sad:
#             "sprites/character_name/sad.png"
#         attribute angry:
#             "sprites/character_name/angry.png"

################################################################################
## 角色立绘位置预设
################################################################################

## 常用位置
transform left_pos:
    xalign 0.2
    yalign 1.0

transform center_pos:
    xalign 0.5
    yalign 1.0

transform right_pos:
    xalign 0.8
    yalign 1.0

transform far_left_pos:
    xalign 0.1
    yalign 1.0

transform far_right_pos:
    xalign 0.9
    yalign 1.0

## 带动画的入场/退场
transform enter_left:
    xalign 0.0
    alpha 0.0
    linear 0.3 xalign 0.2 alpha 1.0

transform enter_right:
    xalign 1.0
    alpha 0.0
    linear 0.3 xalign 0.8 alpha 1.0

transform exit_left:
    linear 0.3 xalign 0.0 alpha 0.0

transform exit_right:
    linear 0.3 xalign 1.0 alpha 0.0

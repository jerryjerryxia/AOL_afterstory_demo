# -*- coding: utf-8 -*-
"""
Script converter: Converts raw script to Ren'Py format
Handles branching with A:/B: options and 【选项分线到此结束】 convergence markers
"""

import argparse
import os
import re
import sys

# Resolve paths relative to this script so renaming the project folder never
# breaks the converter (root cause of past hardcoded-path coupling).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Force UTF-8 stdout so 中文 prints correctly on Windows consoles (the default
# cp936/cp1252 codepage mangles it). Safe no-op on POSIX. Python 3.7+.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# 音效标记只写文件基名（不含扩展名/子目录）；转换器在转换时扫描 game/audio/sfx/
# 建立 基名 -> 相对路径（含真实子目录与扩展名）索引，自动解析到文件的真实位置。
# 这样音效目录重组（把散放的文件归进 bubbles/ glass_smash/ 等子文件夹）后无需改
# 任何标记或代码。outdated/ 下的弃用文件不参与索引。
def _build_sfx_index():
    index = {}
    game_dir = os.path.join(BASE_DIR, 'game')
    sfx_root = os.path.join(game_dir, 'audio', 'sfx')
    for dirpath, dirnames, filenames in os.walk(sfx_root):
        rel_parts = os.path.relpath(dirpath, sfx_root).split(os.sep)
        # outdated/ = 弃用；masters/ = 处理前的原始素材（成品另存，见 desert_wind）。
        # 两者都不该被剧本引用到，所以干脆不进索引。
        if 'outdated' in rel_parts or 'masters' in rel_parts:
            continue
        for fn in filenames:
            base, ext = os.path.splitext(fn)
            if ext.lower() not in ('.wav', '.mp3', '.ogg'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), game_dir)
            index[base] = rel.replace(os.sep, '/')
    return index


SFX_INDEX = _build_sfx_index()


def resolve_sfx(sfx_name, label=""):
    """把音效基名解析为 audio/sfx/... 相对路径。找不到时回退到旧的平铺路径并告警，
    以免静默生成一个指向不存在文件的 play_sfx（游戏里会静默无声）。"""
    path = SFX_INDEX.get(sfx_name)
    if path is None:
        print(f"WARNING: 音效 '{sfx_name}' 在 game/audio/sfx/ 下找不到"
              f"{'（标记：' + label + '）' if label else ''}——回退到 audio/sfx/{sfx_name}.wav")
        return f"audio/sfx/{sfx_name}.wav"
    return path


# 有些音效标记只写"是什么声音"，不写文件名（如 【沙漠长风音效】）—— 剧本描述意图，
# 挑素材是后一步的事。这张表把意图名映射到 game/audio/sfx/ 下的文件基名；子目录与
# 扩展名仍旧由 SFX_INDEX 解析，所以素材换文件夹不用动这里。
#   ambient=True  -> 长循环铺底，走 ambient 声道（play_ambient）
#   ambient=False -> 一次性音效，走 sound 声道（play_sfx）
# 表里没有的标记照旧退化成纯注释（无声）—— 素材还没做的 cue 就是这个状态。
SFX_CUES = {
    # ---- 铺底（ambient 声道：场所的声音）----
    # 沙漠长风：4 分半的环境音。绝不能当一次性音效发 —— play_sfx 会把它记进
    # _sfx_end_time，下一句正文就要 hard 等 282 秒。
    # 指向限幅重制过的 _bed 版本，原始素材留在 masters/（不进索引）。
    '沙漠长风': {'file': 'desert_wind_bed', 'ambient': True},

    # 慢呼吸 ambience：深空段从「呼吸ambience音效开始」铺到「呼吸ambient音效停止」。
    # 中间那几处只写 【呼吸音效】 的落到同一条铺底上 —— if_changed 让它们成为空操作，
    # 正好是剧本的意思（那几处是提醒"还在呼吸"，不是要重新起一次）。
    '呼吸ambience音效开始': {'file': 'freesound_community-slow-breath-relaxmp3-14704',
                             'ambient': True, 'fadein': 4.0, 'level': 0.55},
    '呼吸ambient音效停止': {'stop': True},
    # 「随着文字进程逐渐加快&变响」：只做变响（14 秒从 0.55 档缓慢推到满档）。
    # 不做加快是定下来的 —— 心跳能加快是因为击点之间有干净静音可切、重排不碰波形；
    # 呼吸是连续气流声，没有那样的边界，任何重排都会切在气声中间。
    '呼吸音效渐强': {'swell': 1.0, 'swell_time': 14.0},
    '呼吸音效': {'file': 'freesound_community-slow-breath-relaxmp3-14704', 'ambient': True, 'level': 0.55},

    # ---- 脉冲（ambient_pulse 声道：身体的声音）----
    # 心跳有常速/急促两档，是同一素材重排出来的两个文件（60 / 104 BPM，波形逐样本相同，
    # 只是击点间隔不同 —— 见 variables.rpy 的 AMBIENT_GAIN 注释）。切换 = 换文件，
    # 所以 fadein 给短，让"心跳突然快起来"这件事听得见。
    '心跳音效渐强': {'file': 'heartbeat_104', 'ambient': True, 'channel': 'ambient_pulse',
                     'fadein': 0.6, 'level': 1.0},
    '心跳音效恢复': {'file': 'heartbeat_60', 'ambient': True, 'channel': 'ambient_pulse',
                     'fadein': 1.5, 'level': 0.6},
    '心跳音效': {'file': 'heartbeat_60', 'ambient': True, 'channel': 'ambient_pulse',
                 'fadein': 0.8, 'level': 0.6},
    # 必须显式列出：'心跳音效' 是 '心跳音效停' 的子串，没有这条的话长度优先匹配会落到
    # 上面那条，把心跳在 Demo 结尾又起一遍（而不是停掉）。
    '心跳音效停': {'stop': True, 'channel': 'ambient_pulse'},

    # ---- 一次性 ----
    # 电视机关机 / 关闭：剧本两种写法都有，'电视机关' 一并覆盖。
    '电视机关': {'file': 'dragon-studio-tv-shutdown-386167'},
    # 骨头断裂（"锁骨似乎断了"）：bone_break 用在这里名副其实。
    '骨头断裂': {'file': 'universfield-bone-break-2-140224'},
    # 玻璃破碎：剧本开头写了带文件名的 【玻璃破碎音效：glass-smash-normalized】，
    # 后面两处只写 【玻璃破碎音效】——同一记声音，裸 cue 也解析到同一素材。
    '玻璃破碎': {'file': 'glass-smash-normalized'},
    # 连续破裂（眼珠一颗颗炸开）：暂不接。bone_break 是骨裂声，未必是这里要的东西，
    # 等素材定下来再加一条。当前 cue 退化成纯注释（无声）。

    # glitch（★临时★）：素材是 23.3 秒连续的削顶噪声墙，不是一记 stinger，
    # 整段播下去会盖住后面二十几句旁白。改由运行时函数从中随机挑一段 0.55 秒的
    # 切片来放（切点与理由见 variables.rpy 的 GLITCH_CUTS / play_glitch）——
    # 这样多处 cue 不会听起来是同一记，重玩也不重样。
    # 键就写 'glitch'：剧本里 【glitch音效】/【glitchy音效】 两种写法都有。
    # 不会误伤 【glitch消失】 —— 那行不含"音效"，根本进不到这个分支。
    'glitch': {'call': 'play_glitch()'},
}

# Scene names (the part before the first period in 【转场：场景名。描述】) that
# have a real background image. Maps the scene name to its Ren'Py image name,
# defined in game/images/bg/placeholder.rpy. When a transition uses one of
# these names, the converter emits a `scene ... with scene_soft` line.
SCENE_BG_MAP = {
    '夏日对视': 'bg_summergaze',
    '张目对日pt1': 'bg_sungaze',
    '银白色沙漠': 'bg_desert',
    # 无色透明多面体：循环视频。剧本里所有引用此名的场景都用同一个 channel，
    # 主菜单和序章首场景共享帧位置。
    '无色透明多面体': 'bg_polyhedron_video',
    # 白屏 / 黑屏：循环视频背景（bg/white_screen.webm、black_screen.webm）。
    '白屏': 'bg_white_video',
    '黑屏': 'bg_black_video',
    # 粉红屏：临时版 —— 白屏视频蒙滤镜（见 placeholder.rpy 的 bg_pink_video）。
    # 专门素材做好后把 placeholder.rpy 那条换掉即可，这里不用动。
    # （灰屏不在这里 —— 它不换背景，是粉红屏就地褪过去的，见 IN_PLACE_SCENES。）
    '粉红屏': 'bg_pink_video',
    '红屏': 'bg_red_video',
    # 「黑屏，但是里面盖着王霜微笑的幽灵」：幽灵叠层的素材还没有，先按普通视频黑屏走。
    # 不让它掉进默认的纯黑 Solid —— 前后左右全是视频黑屏，一格死黑插在中间会跳。
    # 幽灵做好后在 placeholder.rpy 里定义叠层、把这里改指过去即可。
    '黑屏，但是里面盖着王霜微笑的幽灵': 'bg_black_video',
    # 图片黑屏：不走 Movie 的黑屏，用 black_screen.webm 截的一帧静帧。
    # 和 '黑屏'（循环视频）是有意区分的两种：视频黑屏是"会呼吸的深蓝黑"，
    # 图片黑屏是"灯灭一下"的段落节拍 —— 后者用在紧接 utter_restart、或者要长时间
    # 挂着放旁白的地方，Movie 在那两种场合 lifecycle 容易出乱子（见 placeholder.rpy）。
    '图片黑屏': 'bg_black_still',
    # 虚空对视：黑屏视频背景 + 透明立绘叠层（overlay 模型，见 SCENE_EXPRESSIONS）。
    # 用视频而非纯色 Solid，这样立绘透明处能透出"背景里的黑屏"动画。
    '虚空对视': 'bg_black_video',
    # 甜品店对视 1-8 + 6.51：场景渐进，详见 placeholder.rpy 里的注释。
    '甜品店对视1': 'bg_dessertgaze1',
    '甜品店对视2': 'bg_dessertgaze2',
    '甜品店对视3': 'bg_dessertgaze3',
    '甜品店对视4': 'bg_dessertgaze4',
    # 瘾：幻视高潮的转场卡（甜品店被瘾扭曲的样子，对视4→5 之间）。
    '瘾': 'bg_addiction',
    '甜品店对视5': 'bg_dessertgaze5',
    '甜品店对视6': 'bg_dessertgaze6',
    '甜品店对视6.51': 'bg_dessertgaze6_51',
    '甜品店对视7': 'bg_dessertgaze7',
    '甜品店对视8': 'bg_dessertgaze8',
    # 地下 1-8：沙漠地下（头埋进沙里）恐怖段的场景渐进，见 placeholder.rpy。
    '地下1': 'bg_underground1',
    '地下2': 'bg_underground2',
    '地下3': 'bg_underground3',
    '地下4': 'bg_underground4',
    '地下5': 'bg_underground5',
    '地下6': 'bg_underground6',
    '地下7': 'bg_underground7',
    '地下8': 'bg_underground8',
}

# 就地转场：不换背景，只在当前画面上启动一段效果。场景名 -> 要发的那一行。
# 剧本里的 【转场：X】 在这里表示"变化开始"，不是"立刻变完" —— 发出去的是一个
# 非阻塞的扳机，玩家照常点字推进，画面在背后自己走完。
#
# 灰屏：粉红屏用 10 秒缓慢褪成灰（ATL 在 placeholder.rpy 的 bg_pink_video 上，
# 时长/曲线都在那里调）。之所以不是 scene 换图，理由写在那条 image 上面。
IN_PLACE_SCENES = {
    '灰屏': '$ pink_to_grey_started = True',
}

# 转场完成后停住等玩家点击的场景：画面单独作为一拍展示（藏起文本框），
# 点一下才继续出后面的文字。用于「瘾」这类整屏揭示卡。
SCENE_CLICK_HOLD = {'瘾'}

# Scenes that should NOT emit the default fade-through-black transition.
# Used when the same background is already visible (e.g., main menu's video
# bg carries into the prologue's first scene), so a black-fade would break
# the continuity. These scenes emit `scene X with None` instead of
# `scene X with scene_soft`.
NO_TRANSITION_SCENES = set()

# Scenes that should cross-dissolve into view rather than fade through black.
# Use for visual evolution within the same location/moment — e.g., the dessert
# shop sequence (1 → 2 → 3 → ... → 7) where each scene is the same dining
# table at successive beats. A black-fade between them feels like "cut away
# and come back"; a dissolve reads as "time slipping forward in place."
# Note: 甜品店对视1 is NOT in here — that's the *entry* into the sequence,
# so it should use the standard fade-through-black from whatever preceded it.
CROSS_DISSOLVE_SCENES = {
    '甜品店对视2',
    # 瘾：幻视段内的揭示卡，溶解保持迷幻的连续感（黑场会打断药劲）。
    '瘾',
    '甜品店对视3',
    '甜品店对视4',
    '甜品店对视5',
    '甜品店对视6',
    '甜品店对视6.51',
    '甜品店对视7',
    '甜品店对视8',
    # 地下 2-8：同一视野的递进拍（沙砾→多面体→眼珠→爆裂），黑场会打断
    # "越看越清楚"的连续感。地下1 不在这里 —— 它是从图片黑屏睁眼的入场，
    # 走默认黑场淡入。
    '地下2',
    '地下3',
    '地下4',
    '地下5',
    '地下6',
    '地下7',
    '地下8',
}

# Tracks whether the prologue's first 【转场：...】 still needs its own special
# transition. convert_prologue() sets this to True at its start;
# convert_content_line()'s transition branch consumes it once.
#
# History: this used to emit `with None`, because the main menu's background WAS
# the polyhedron video the prologue scenes to — a fade would have broken a
# seamless handoff. The main menu is sea.png now, so there is nothing seamless
# left to protect and a hard cut is just a hard cut. It emits the water-drop
# ripple instead: the drop lands on the main menu, and the ripple wipes the
# prologue in from the centre. See PROLOGUE_ENTRY_TRANSITION.
_PROLOGUE_FIRST_TRANSITION_PENDING = False

# The transition on the main-menu → prologue boundary. Timed to start right as
# the water-drop overlay's ripple rings are spreading (see DROP_* in
# game/screens.rpy); defined in game/scripts/transitions.rpy.
PROLOGUE_ENTRY_TRANSITION = 'ripple_reveal'

# Standalone stage-direction keyword -> FX transition emitted right after
# the comment, for genuine *visual* dramatic beats only. Audio-only cues
# (containing 音效) are skipped. Transitions are defined in
# game/scripts/transitions.rpy.
# glitch 发的是 glitch_fx()（函数调用，不是常量）—— 每次随机挑一个视觉变体，
# 见 transitions.rpy。音效那条路径不经过这里：play_glitch() 自己会配一记画面故障。
SPECIAL_FX = [
    ('glitch', 'glitch_fx()'),
    ('黑影', 'fx_shock'),
]

# 停顿标记：【停顿：N】 与 【等待N秒】 是同义写法（剧本里两种都出现过）。
# 命中返回秒数字符串，否则 None。普通正文与 Extended 块内都要认——
# 块内若不认，会被"整行【】舞台提示"的兜底静默吃掉，两个转场就贴在一起了。
def _match_pause(line):
    m = re.match(r'^【停顿[：:]([\d.]+)】$', line) or re.match(r'^【等待([\d.]+)秒】$', line)
    return m.group(1) if m else None

# 表情切换过渡（短溶解；改这里改全局表情切换速度）。
# 秒数单独成常量：小跳 transform 要用它做起跳延迟（等溶解完成再跳）。
EXPR_TRANSITION_SECONDS = 0.2
EXPR_TRANSITION = f"Dissolve({EXPR_TRANSITION_SECONDS})"

# 电视机关机（CRT 断电）动画总时长，秒。必须与 transitions.rpy 里 crt_shutdown 的
# 时间轴总和一致 —— 短了会在光点没灭时就切走，长了会在黑屏上干等。
CRT_SHUTDOWN_SECONDS = 0.8

# 文字墙演出总时长，秒。必须与 transitions.rpy 里那组 transform 的时间轴一致：
# 4s 堆满 → 紧接着 6s 放大到 3.4 倍（铺满与开始变大之间不留空档）→ 0.55s 整面墙
# 从正中对半分开推出画面，同时白闪 + 黑底褪去露出红屏。合计 10.55，取 10.8 留余量。
# （逐字四散坠落试过两版都没做成，原因写在 transitions.rpy 的 WALL_SHATTER_AT 注释里。）
TEXT_WALL_SECONDS = 10.8

# 指定场景转场的特殊过渡（覆盖默认 scene_soft）。场景名 -> transitions.rpy 里的过渡名。
SCENE_TRANSITIONS = {
}

# 长黑场过渡 + 禁止点击快进。用黑色叠层 ATL 动画 + hard pause 实现：屏幕缓缓黑
# 下来 → 黑场停留 → 新场景缓缓浮现，全程 hard=True 不可点击跳过。
# 值 = (淡出到黑秒, 黑场停留秒, 新场景淡入秒)。白屏褪去后进甜品店用这个。
SCENE_HARD_FADE = {
    '甜品店对视1': (3.0, 0.5, 2.0),
}

# 表情差分配置：场景名 -> {model, ...}。场景名 = 脚本 【转场：X。…】 里的 X。
#   "full"    —— 整图差分：scene <img> 直接换整张背景（默认图==bg 目录原图）。
#   "overlay" —— 透明立绘：转场时 scene <bg> + show <default>，表情用 show 互换
#                （共用 image tag）。用于没有实景、只在黑屏上放人物的场景。
# 图片名与 placeholder.rpy 里的 image 定义一致。详见 expression_variations/。
SCENE_EXPRESSIONS = {
    '虚空对视': {
        'model': 'overlay',
        'continue_bg': True,   # 黑屏视频从浮潜连续过来，不重新 scene，只淡入立绘
        # 进场直接淡入第一句话的立绘姿势（旧的 void_default 占位整图已弃用）。
        # 此后的表情/姿势切换全部由剧本里的 【姿势，表情】 立绘标记驱动，
        # 所以这里不需要 map（仅表情的差分标记在这个场景里已不存在）。
        'default': 'ws backhand default at ws_mid',
        'map': {},
    },
    '夏日对视': {
        'model': 'full',
        'map': {
            '默认': 'summergaze_default',
            '小声嘀咕': 'summergaze_mutter',
            '面无表情': 'summergaze_blank',
            '大笑': 'summergaze_laugh',
            '小吃惊': 'summergaze_surprised',
        },
    },
    '甜品店对视1': {
        'model': 'full',
        'map': {
            '默认': 'dessert1_default', '坏笑': 'dessert1_smirk',
            '撇嘴': 'dessert1_pout', '疑惑': 'dessert1_puzzled',
        },
    },
    '甜品店对视2': {
        'model': 'full',
        'map': {'默认': 'dessert2_default', '撇嘴': 'dessert2_pout'},
    },
    '甜品店对视3': {
        'model': 'full',
        'map': {
            '默认': 'dessert3_default', '小激动': 'dessert3_excited',
            '撇嘴': 'dessert3_pout',
        },
    },
}

# 当前所处的表情场景（转场时更新）。决定 角色【表情】 切到哪张差分；
# 非表情场景（如甜品店对视4-8）置为该场景名、map 取不到 → 表情退化成注释。
_CURRENT_EXPR_SCENE = None

################################################################################
## 镜头缓移（Ken Burns 开场）
##
## 剧本标记：【镜头：左下缓移右上】，可选时长/变焦：【镜头：左下缓移右上，5秒，变焦1.1】
## 写在【转场：…】的前一行。标记只登记不发码——由紧随其后的 _emit_scene 发出。
## 发码形状是"沉黑 → 黑中设镜头 → 带镜头浮出"三段（cam_fade_out/cam_fade_in）：
## camera 变换包在图层过渡的**外面**，直接写在 `with` 前会让淡出中的旧画面也
## 跟着新镜头动。浮出时镜头已在漂移，走完后定格在终点、整段场景保持。
##
## 用 camera（作用于 master 层）而不是 scene 上的 at 变换，是因为整图表情差分
## 每次都发新的 scene 语句（见 emit_expression_change）——at 变换会被第一次差分
## 冲掉，而 camera 不受 scene 影响，能横跨整段场景存活。
##
## 复位是自动的：下一次 _emit_scene（真正的场景切换）发现镜头不在默认位，就在
## 自己的 scene 语句前补一行裸 `camera`。scene_soft 是 Fade 过黑，复位跳变被
## 黑场完全盖住；就地转场（IN_PLACE_SCENES）不换画面，不复位。
_CAMERA_PAN_PENDING = None   # {'from','to','secs','zoom'} 或 None
_CAMERA_PAN_ACTIVE = False   # 镜头当前不在默认位（下次转场需复位）

# 方位名 -> (xalign, yalign)。zoom>1 时 align 决定看到图的哪一块（角/边/中）。
_CAMERA_CORNERS = {
    '左上': ('0.0', '0.0'),
    '左下': ('0.0', '1.0'),
    '右上': ('1.0', '0.0'),
    '右下': ('1.0', '1.0'),
    '中央': ('0.5', '0.5'),
    '左': ('0.0', '0.5'),
    '右': ('1.0', '0.5'),
    '上': ('0.5', '0.0'),
    '下': ('0.5', '1.0'),
}
# 正则备选：长名在前，防止 '左' 抢走 '左上' 的匹配。
_CAMERA_CORNER_ALT = '|'.join(sorted(_CAMERA_CORNERS, key=len, reverse=True))
_CAMERA_DEFAULT_SECS = '5.0'
_CAMERA_DEFAULT_ZOOM = '1.06'

def _emit_camera_at_switch(out, indent, ease_back=False):
    """场景切换点的镜头语句。返回值告诉调用方这些行能不能见光：
      'switch' —— 硬设/硬复位，必须藏在全黑里发（调用方拆转场）；
      'inline' —— 缓回动画，可直接跟在交叉溶解前发（镜头随溶解一起归位）；
      None     —— 没有镜头变化。
    有登记的缓移 → 发 camera 块并标记生效中；没有新缓移但镜头还停在上一
    场景的终点 → 复位（ease_back=True 时改为 3 秒缓回默认位，用于藏不住
    硬复位的交叉溶解场景；config.keep_show_layer_state 默认开，新 camera
    块从当前镜头状态起插值）。"""
    global _CAMERA_PAN_PENDING, _CAMERA_PAN_ACTIVE
    if _CAMERA_PAN_PENDING:
        p = _CAMERA_PAN_PENDING
        fx, fy = _CAMERA_CORNERS[p['from']]
        tx, ty = _CAMERA_CORNERS[p['to']]
        out.append(f"{indent}## 镜头：{p['from']}缓移{p['to']}"
                   f"（{p['secs']}秒定格，变焦{p['zoom']}；下个转场自动复位）")
        out.append(f'{indent}camera:')
        # subpixel：缓移每帧只挪零点几像素，不开亚像素渲染会整像素跳格（可见抖动）
        out.append(f'{indent}    subpixel True')
        out.append(f"{indent}    zoom {p['zoom']} xalign {fx} yalign {fy}")
        out.append(f"{indent}    easein_quad {p['secs']} xalign {tx} yalign {ty}")
        _CAMERA_PAN_PENDING = None
        _CAMERA_PAN_ACTIVE = True
        return 'switch'
    if _CAMERA_PAN_ACTIVE:
        _CAMERA_PAN_ACTIVE = False
        if ease_back:
            out.append(f'{indent}## 镜头缓回默认位（随交叉溶解同走，不经黑场）')
            out.append(f'{indent}camera:')
            out.append(f'{indent}    subpixel True')
            out.append(f'{indent}    easein_quad 3.0 zoom 1.0 xalign 0.5 yalign 0.5')
            return 'inline'
        out.append(f'{indent}## 镜头复位')
        out.append(f'{indent}camera')
        return 'switch'
    return None

################################################################################
## 立绘（王霜全身立绘，game/images/sprites/）
##
## 剧本标记形状是区分的唯一依据：
##   王霜【<姿势>，<表情>表情】          → 立绘 show（本节）
##   王霜【<表情>】（无顿号）           → 场景表情差分（SCENE_EXPRESSIONS，整图/overlay）
## 姿势本身可以含顿号（右手叉腰，左手食指竖起做讲解状），所以从**最后一个**顿号拆。
## 表情段可带后缀「上蒙了glitch」→ 切到预生成的 glitch 动画帧（见 glitch/ 目录，
## 用 generate_glitch_art.py 从原图生成，命名 <原名>_glitch<seed>.png）。
##
## 素材与 .rpy 定义都由转换器自动管理：扫描 sprites/ 目录建索引，并生成
## game/images/sprites/sprites.rpy（image 定义 + 摆位 transform）。加新姿势/表情
## = 按 <姿势>(<表情>.png 命名丢进对应文件夹后重跑转换器，代码零改动。
## 剧本要的表情没有对应素材时回退到该姿势的默认表情并打 WARNING（不静默）。
################################################################################

# 姿势关键词 -> Ren'Py 属性名。文件夹/文件名里含关键词即归入该姿势
# （单手叉腰站立、右手叉腰左手按胸口 都落到 叉腰 —— 现有素材里最近的姿势）。
SPRITE_POSE_ATTRS = {'背手': 'backhand', '抱胸': 'crossed', '叉腰': 'akimbo'}

# 姿势别名：剧本里的简称 -> 素材姿势关键词。「讲解站立」是
# 「右手叉腰，左手食指竖起做讲解状」的新简称，素材就是叉腰那套。
# 只作用于剧本标记的解析，素材扫描（文件名）不经过这里。
SPRITE_POSE_ALIASES = {'讲解': '叉腰'}


def match_pose_keyword(pose_part):
    """姿势文本 -> SPRITE_POSE_ATTRS 的姿势 key（含别名解析），认不出返回 None。"""
    pose = next((k for k in SPRITE_POSE_ATTRS if k in pose_part), None)
    if pose is None:
        pose = next((v for k, v in SPRITE_POSE_ALIASES.items() if k in pose_part), None)
    return pose

# 表情 -> Ren'Py 属性名。剧本用到但素材还没画的表情也先列上（严肃/开心/疑问），
# 素材补上后无需改代码，重跑转换器即可。
SPRITE_EXPR_ATTRS = {
    '默认': 'default', '面无表情': 'blank', '吃惊': 'shocked',
    '坏笑': 'smirk', '无奈': 'wry', '得意': 'proud',
    '严肃': 'stern', '开心': 'happy', '疑问': 'puzzled',
}

SPRITE_GLITCH_SUFFIX = '上蒙了glitch'

# 立绘摆位：场景名 -> transform 名（定义在生成的 sprites.rpy 里）。
# 默认半身近景（第一人称对视感，参考 DDLC 的莫妮卡）——全身远景试过，
# 人物太小没有压迫感。某场景要不同摆位，在这里加映射即可。
# 沙漠桥段与虚空对视：缩到与店员立绘一致的大小（ws_mid 中景）。
SPRITE_SCENE_AT = {'银白色沙漠': 'ws_mid', '虚空对视': 'ws_mid',
                   '银白色沙漠跑动': 'ws_mid'}
SPRITE_DEFAULT_AT = 'ws_close'

# 摆位参数（写进生成的 sprites.rpy；改这里 + 重跑转换器即可调）。原图 2299x3824。
WS_CLOSE_ZOOM = 0.52      # 半身近景：头到腰约占满全屏
WS_CLOSE_YPOS = -50       # 近景往上提一点，让头顶留白自然
# glitch（毁容脸）：显示期间静止不动（试过 0.12s 连闪和 3s 溶解轮播，都不如
# 静帧——毁容本身够吓人，动起来反而提醒观众"这是特效"）。随机性放在 show
# 时：ATL choice 三选一，每次人物换表情/姿势重新 show 都重新抽一张脸。

# 店员（王霜复制体，甜品店段）摆位参数。素材与主立绘同一套，缩小放在两侧：
# 店员1 右侧正立，店员2 左侧从天花板倒吊（rotate 180）。
WS_CLERK_ZOOM = 0.42
WS_CLERK1_XPOS = 0.82     # 右侧（中心点的横向位置，屏幕比例）
WS_CLERK1_YPOS = 120      # 头顶离屏幕上沿的距离（px）
WS_CLERK2_XPOS = 0.18     # 左侧
# 倒吊时头部下沿的位置（px，越大垂得越低）。取 1080 - WS_CLERK1_YPOS：
# 两人同一动作时（如 都是讲解站立），左上店员2 和右下店员1 露出的身体量
# 一致，占据对称的空间。
WS_CLERK2_YPOS = 960
CLERK_MOVE_SECONDS = 0.7  # 入/退场垂直平移时长
CLERK_TRAVEL = 1100       # 垂直平移距离（px，足够整个移出屏幕）

# 店员 glitch 软化（_glitchsoft 动画）：绝大部分时间是干净立绘，每隔
# 2~3 秒（随机三选一）闪两下故障帧。持续循环的 _glitch 版对复制体太夸张。
WS_CLERK_GLITCH_PAUSES = (1.8, 2.4, 3.0)   # 干净帧停留时长候选
WS_CLERK_GLITCH_FLASH = 0.07               # 每帧故障闪现时长
WS_CLERK_GLITCH_GAP = 0.08                 # 两下故障之间的干净间隙

# 中景主立绘摆位（ws_mid，沙漠桥段/虚空对视）：大小与店员一致。
WS_MID_YPOS = 120

# 沙漠走路进场（剧本标记【王霜走路进场】，或台词行内【从左到右缓缓走入】——
# 后者是作者管理剧本用的行内别名，挂在 王霜【姿势，表情】 之后同样触发走路窗口）：
# 从屏幕左缘外走到画面偏右站定，水平匀速推进 + 每步一次轻微起伏。
# 想调手感改这里 + 重跑转换器。
WS_WALK_INLINE_MARK = '从左到右缓缓走入'
WS_WALK_SECONDS = 10.0   # 全程时长
WS_WALK_START_X = -0.3   # 起点 xpos（屏幕比例；-0.3 = 整个立绘在左缘外）
WS_WALK_END_X = 0.7      # 终点站定位置（偏右——她走在前头）
WS_WALK_STEP = 0.6       # 每步周期（秒），起伏一次 = 迈一步
WS_WALK_BOB = 12         # 起伏幅度（px）

# 走路窗口状态：标记登记 pending → 下一条立绘 show 挂 ws_desert_walk 并转
# active → 同场景内后续姿势/表情 show 一律不带 at 列表（带了会把走路
# transform 冲掉，人瞬移回 ws_mid）。转场（scene 清立绘）时窗口关闭。
_SPRITE_WALK_PENDING = False
_SPRITE_WALK_ACTIVE = False

# 跑动 sequence 计数：第 1 次 开始 用 bg_desert_run，之后用更狂的 run2。
_RUN_SEQ_COUNT = [0]

# 【转头】（第一视角猛回头就跑）：登记 pending，由紧随其后的跑动 sequence 起手
# 消费 —— 那次 scene 切换改用 whip_pan 甩头转场（shaders.rpy）而非溶解。
# 方向按次数交替（第一次向右甩、第二次向左），连续两次同向会像复播。
_HEAD_TURN = {'pending': False, 'count': 0}

# 小跳（剧本标记【小跳】，跟在姿势/表情标记后）：立绘原地轻跳一下（幅度小）。
# 实现 = re-show 当前立绘，at 换成对应摆位的 <摆位>_hop 版 —— ★必须是内联了
# 静态摆位的完整单元素 transform★（生成见 generate_sprites_rpy），不能用
# `at 摆位 + ATL block`：block 会追加成第二个 at 元素，替换 at 列表时 Ren'Py
# 从尾部对齐取状态，block 继承摆位的 zoom、摆位又套一遍 → zoom 平方立绘缩小
# （与店员入退场当年同一个坑，见 _CLERK_CFG 注释）。
# 起落 warper 与沙漠走路的 bob 同款：easeout 上（顶点减速）、easein 落。
SPRITE_HOP_PX = 28       # 跳起高度（px）
SPRITE_HOP_UP = 0.14     # 上升时长（秒）
SPRITE_HOP_DOWN = 0.12   # 落回时长（秒）


def _build_sprite_index():
    """扫描 game/images/sprites/ 建立立绘索引。
    返回 (base, glitch, soft)：
      base   = {(姿势key, 表情): 'images/sprites/...png'}
      glitch = {(姿势key, 表情): [帧路径, ...]}（按 seed 排序，全身 glitch）
      soft   = 同 glitch，但为 _glitchsoft 帧（局部小范围 glitch，店员用，
               generate_glitch_art.py --patches 生成）
    文件名约定：<姿势>(<表情>.png（全/半角括号、带不带闭括号都认），
    glitch 帧为 <原名>_glitch<seed>.png，软帧为 <原名>_glitchsoft<seed>.png。
    ★_glitchsoft 必须先于 _glitch 判断——后者的正则要求 glitch 后直接跟数字，
    软帧不满足，会掉进 base 索引变成一个不存在的"表情"。"""
    base, glitch, soft = {}, {}, {}
    game_dir = os.path.join(BASE_DIR, 'game')
    root = os.path.join(game_dir, 'images', 'sprites')
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if not fn.lower().endswith('.png'):
                continue
            stem = fn[:-4]
            sink = base
            sm = re.match(r'^(.*)_glitchsoft(\d+)$', stem)
            gm = re.match(r'^(.*)_glitch(\d+)$', stem)
            if sm:
                stem, sink = sm.group(1), soft
            elif gm:
                stem, sink = gm.group(1), glitch
            norm = stem.replace('（', '(').rstrip('）)')
            if '(' not in norm:
                continue
            pose_part, expr = norm.split('(', 1)
            pose = next((k for k in SPRITE_POSE_ATTRS if k in pose_part), None)
            if pose is None:
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), game_dir)
            rel = rel.replace(os.sep, '/')
            if sink is base:
                base[(pose, expr)] = rel
            else:
                sink.setdefault((pose, expr), []).append(rel)
    for idx in (glitch, soft):
        for frames in idx.values():
            frames.sort()
    return base, glitch, soft


SPRITE_INDEX, SPRITE_GLITCH_INDEX, SPRITE_GLITCHSOFT_INDEX = _build_sprite_index()

# 已经告警过的缺素材组合，避免同一条 WARNING 刷屏。
_SPRITE_WARNED = set()

# 最近一次 show 的立绘 (pose, expr, is_glitch)。给 【glitch消失】 用：剧本在那一刻
# 就要 glitch 停（下一条立绘标记可能隔着几句别人的台词），所以要知道当前立绘是谁、
# 才能就地切回它的无 glitch 版。转场时清掉（scene 会把立绘一起清掉）。
_LAST_SPRITE = None


def parse_sprite_marker(marker):
    """【<姿势>，<表情>表情[上蒙了glitch]】 → (姿势key, 表情, glitch) 或 None。
    None = 这不是立绘标记（交回场景表情差分/舞台提示注释的老路）。"""
    if '，' not in marker:
        return None
    pose_part, expr_part = marker.rsplit('，', 1)
    is_glitch = expr_part.endswith(SPRITE_GLITCH_SUFFIX)
    if is_glitch:
        expr_part = expr_part[:-len(SPRITE_GLITCH_SUFFIX)]
    if not expr_part.endswith('表情'):
        return None
    # 「面无表情」整体就是表情名；其余去掉「表情」后缀（默认表情→默认）。
    expr = expr_part if expr_part == '面无表情' else expr_part[:-len('表情')]
    pose = match_pose_keyword(pose_part)
    if pose is None:
        key = ('pose', marker)
        if key not in _SPRITE_WARNED:
            _SPRITE_WARNED.add(key)
            print(f"WARNING: 立绘标记姿势无法识别：【{marker}】——退化为注释")
        return None
    return pose, expr, is_glitch


def _resolve_sprite_attrs(pose, expr):
    """(姿势key, 表情) → (image 名, 实际使用的表情)；缺素材时回退到该姿势默认表情
    并告警，完全无素材可用返回 None。主立绘和店员立绘共用（同一套素材）。"""
    use_expr = expr
    if (pose, use_expr) not in SPRITE_INDEX:
        if (pose, '默认') not in SPRITE_INDEX:
            key = ('none', pose)
            if key not in _SPRITE_WARNED:
                _SPRITE_WARNED.add(key)
                print(f"WARNING: 立绘姿势 '{pose}' 没有任何素材——退化为注释")
            return None
        key = ('expr', pose, expr)
        if key not in _SPRITE_WARNED:
            _SPRITE_WARNED.add(key)
            print(f"WARNING: 立绘缺素材：{pose}·{expr} —— 回退到 {pose}·默认")
        use_expr = '默认'
    expr_attr = SPRITE_EXPR_ATTRS.get(use_expr)
    if expr_attr is None:
        key = ('attr', use_expr)
        if key not in _SPRITE_WARNED:
            _SPRITE_WARNED.add(key)
            print(f"WARNING: 表情 '{use_expr}' 不在 SPRITE_EXPR_ATTRS，"
                  f"补上映射后重跑——退化为注释")
        return None
    return f"ws {SPRITE_POSE_ATTRS[pose]} {expr_attr}", use_expr


def emit_sprite_change(marker, indent):
    """立绘标记 → show 语句。非立绘标记或完全无素材可用时返回 None。
    过渡与表情差分一致：只溶解 master 层，对话框/文字不闪。"""
    parsed = parse_sprite_marker(marker)
    if parsed is None:
        return None
    pose, expr, want_glitch = parsed
    resolved = _resolve_sprite_attrs(pose, expr)
    if resolved is None:
        return None
    img, use_expr = resolved
    is_glitch = want_glitch
    if is_glitch and (pose, use_expr) not in SPRITE_GLITCH_INDEX:
        key = ('glitch', pose, use_expr)
        if key not in _SPRITE_WARNED:
            _SPRITE_WARNED.add(key)
            print(f"WARNING: 立绘缺 glitch 帧：{pose}·{use_expr}"
                  f"（用 generate_glitch_art.py 生成到 sprites/glitch/）—— 先用无 glitch 版")
        is_glitch = False
    if is_glitch:
        img += "_glitch"   # glitch 并进表情属性名，避免 show 属性残留粘连
    at = SPRITE_SCENE_AT.get(_CURRENT_EXPR_SCENE, SPRITE_DEFAULT_AT)
    global _LAST_SPRITE, _SPRITE_WALK_PENDING, _SPRITE_WALK_ACTIVE
    _LAST_SPRITE = (pose, use_expr, is_glitch)
    # 走路窗口：首条立绘挂走路 transform；之后不带 at，沿用走路的位置/动画。
    if _SPRITE_WALK_PENDING:
        _SPRITE_WALK_PENDING = False
        _SPRITE_WALK_ACTIVE = True
        at_clause = ' at ws_desert_walk'
    elif _SPRITE_WALK_ACTIVE:
        at_clause = ''
    else:
        at_clause = f' at {at}'
    return (f'{indent}## 立绘：{marker}\n'
            f'{indent}show {img}{at_clause}\n'
            f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')


def emit_sprite_hop(indent):
    """【小跳】（主立绘）：re-show 当前立绘，at 换成摆位的 _hop 版。
    无立绘在场时返回 None；走路窗口内忽略——hop 版 transform 会把走路
    transform 冲掉（人瞬移回摆位落点）。"""
    if _LAST_SPRITE is None:
        return None
    if _SPRITE_WALK_ACTIVE or _SPRITE_WALK_PENDING:
        print("WARNING: 【小跳】出现在走路窗口内——忽略（会冲掉走路 transform）")
        return None
    pose, expr, is_glitch = _LAST_SPRITE
    img = f"ws {SPRITE_POSE_ATTRS[pose]} {SPRITE_EXPR_ATTRS[expr]}"
    if is_glitch:
        img += "_glitch"
    at = SPRITE_SCENE_AT.get(_CURRENT_EXPR_SCENE, SPRITE_DEFAULT_AT)
    return f'{indent}show {img} at {at}_hop'


def emit_clerk_hop(clerk, indent):
    """【小跳】（店员）：同 emit_sprite_hop，走店员的 as tag 与摆位 _hop 版。
    刚触发入场动画的同一拍内忽略（re-show 会打断入场平移）。"""
    st = _CLERK_STATE.get(clerk)
    if not st or not st['visible']:
        return None
    if st.get('enter_pending'):
        print("WARNING: 【小跳】紧跟店员入场——忽略（会打断入场动画）")
        return None
    resolved = _clerk_img(st['pose'], st['expr'])
    if resolved is None:
        return None
    cfg = _CLERK_CFG[clerk]
    return f'{indent}show {resolved[0]} as {cfg["tag"]} at {cfg["at"]}_hop'


def emit_sprite_unglitch(indent):
    """【glitch消失】：当前立绘若是 glitch 版，就地切回同姿势同表情的干净版。
    不能等下一条立绘标记 —— 中间可能隔着几句别人的台词，剧本要 glitch 即刻停。
    当前没有立绘或本来就没 glitch 时返回 None（只发画面特效那条老路）。"""
    global _LAST_SPRITE
    if not _LAST_SPRITE or not _LAST_SPRITE[2]:
        return None
    pose, expr, _ = _LAST_SPRITE
    _LAST_SPRITE = (pose, expr, False)
    img = f"ws {SPRITE_POSE_ATTRS[pose]} {SPRITE_EXPR_ATTRS[expr]}"
    at = SPRITE_SCENE_AT.get(_CURRENT_EXPR_SCENE, SPRITE_DEFAULT_AT)
    # 走路窗口内不带 at 列表（同 emit_sprite_change：别把走路 transform 冲掉）。
    at_clause = '' if _SPRITE_WALK_ACTIVE else f' at {at}'
    return (f'{indent}show {img}{at_clause}\n'
            f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')


################################################################################
## 店员（王霜复制体）：甜品店段的两个店员，与主立绘同素材、不同摆位（see 摆位
## 常量 WS_CLERK_*）。剧本标记：
##   【店员入场】/【店员2入场】          → 仅注释；下一句该店员台词时自动入场
##   【店员N进场，<姿势>，<表情>】       → 立即 show（带入场动画）
##   【店员N退场】                        → 垂直平移出屏幕（非阻塞；移出即不可见，
##                                          不发 hide——下次 show / scene 自然接管）
##   王霜（店员N）【<姿势>，<表情>】：…   → show / 换差分（未在场时自动入场）
##   王霜（店员N）【<表情>】：…           → 只换表情，姿势沿用上次
##   王霜【…三人集体<表情>】：…           → 主立绘（场景差分）+ 在场店员一起换表情
## 转场（scene 语句）会清掉店员立绘；有店员在场时 _emit_scene 先发垂直平移退场
## 动画再转场（剧本：「退场的形式是垂直平移出屏幕」）。
################################################################################

_CLERK_CFG = {
    # 入场都是垂直滑入（与各自退场方向相反）：店员1 从屏幕下方升上来，
    # 店员2 从天花板倒吊降下（「从屏幕左边天花板倒立下来」）。
    # ★enter/exit 都是**内联了静态摆位的完整 transform**，每次 show 的 at 列表
    # 永远只有一个元素。不能写成 `at 摆位, 动画` 组合：替换 at 列表时 Ren'Py 从
    # 列表尾部对齐取状态，外层动画 transform 会继承摆位的 rotate/zoom 状态、
    # 内层摆位又套一遍 —— rotate 叠成 360（倒吊转正）、zoom 平方（立绘缩小）。
    'clerk1': {'tag': 'ws_clerk1', 'at': 'ws_clerk_right',
               'enter': 'ws_clerk_right_enter',
               'exit': 'ws_clerk_right_exit', 'pose': '背手'},
    'clerk2': {'tag': 'ws_clerk2', 'at': 'ws_clerk_ceiling',
               'enter': 'ws_clerk_ceiling_enter',
               'exit': 'ws_clerk_ceiling_exit', 'pose': '抱胸'},
}

# clerk id -> {'pose', 'expr', 'visible'}。姿势/表情跨退场记忆（【店员2入场】后
# 只标【默认】的台词沿用上次姿势）。convert 每次全量重跑，转换开头清空。
_CLERK_STATE = {}


def _clerk_id(name):
    """店员/店员1 → clerk1，店员2 → clerk2（剧本两种写法都有）。"""
    return 'clerk2' if '店员2' in name else 'clerk1'


def _clerk_state(clerk):
    return _CLERK_STATE.setdefault(
        clerk, {'pose': _CLERK_CFG[clerk]['pose'], 'expr': '默认', 'visible': False})


def emit_clerk_show(clerk, indent, pose=None, expr=None):
    """店员 show/换差分。未在场时自动入场（店员2 走天花板降下动画，店员1 溶解）。
    素材缺失时返回 None（调用方退化为注释）。"""
    st = _clerk_state(clerk)
    pose = pose or st['pose']
    expr = expr or st['expr']
    resolved = _clerk_img(pose, expr)
    if resolved is None:
        return None
    img, use_expr = resolved
    cfg = _CLERK_CFG[clerk]
    entering = not st['visible']
    st.update(pose=pose, expr=use_expr, visible=True, enter_pending=None)
    if entering and cfg['enter']:
        # 入场动画名记下来：若同一交互内紧跟整图表情差分（scene 会清立绘，
        # _clerk_reshow_lines 要补发），补发沿用入场 transform 重新起播 ——
        # 同帧重启视觉上等于继续，否则动画会被基础摆位瞬移掉。
        # 这个窗口只到下一句 say 为止（_clerk_close_enter_window），
        # 不然后面几拍的表情差分补发会让入场动画重播一遍。
        st['enter_pending'] = cfg['enter']
        return f'{indent}show {img} as {cfg["tag"]} at {cfg["enter"]}'
    return (f'{indent}show {img} as {cfg["tag"]} at {cfg["at"]}\n'
            f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')


def emit_clerk_exit(clerk, indent):
    """店员退场：垂直平移出屏幕（非阻塞 ATL）。未在场返回 None。"""
    st = _CLERK_STATE.get(clerk)
    if not st or not st['visible']:
        return None
    resolved = _clerk_img(st['pose'], st['expr'])
    st['visible'] = False
    if resolved is None:
        return None
    cfg = _CLERK_CFG[clerk]
    return f'{indent}show {resolved[0]} as {cfg["tag"]} at {cfg["exit"]}'


def _clerk_img(pose, expr):
    """店员立绘用**软 glitch** 动画版（复制体=偶发信号抽搐：平时干净，每隔
    2~3 秒闪两下故障帧，见 _glitchsoft 生成）。缺 glitch 帧时回退干净版并告警
    （用 generate_glitch_art.py 补）。"""
    resolved = _resolve_sprite_attrs(pose, expr)
    if resolved is None:
        return None
    img, use_expr = resolved
    if (pose, use_expr) in SPRITE_GLITCH_INDEX:
        img += '_glitchsoft'
    else:
        key = ('clerk_glitch', pose, use_expr)
        if key not in _SPRITE_WARNED:
            _SPRITE_WARNED.add(key)
            print(f"WARNING: 店员立绘缺 glitch 帧：{pose}·{use_expr}"
                  f"（generate_glitch_art.py 生成到 sprites/glitch/）—— 先用干净版")
    return img, use_expr


def _clerk_close_enter_window(indent_unused=None):
    """一句 say 发出后调用：「同一交互内补发沿用入场动画」的窗口关闭。
    say 就是一次交互边界 —— 之后的表情差分补发若再沿用入场 transform，
    入场动画会凭空重播一遍（如 集体坏笑 让店员2 又降一次）。"""
    for st in _CLERK_STATE.values():
        st['enter_pending'] = None


def _clerk_reshow_lines(indent):
    """在场店员的原样 show 行（scene 换整图差分后补发，让店员不被 scene 清掉）。
    刚入场还没被点过的店员沿用入场动画 transform（见 emit_clerk_show），用一次即清。"""
    lines = []
    for clerk in sorted(_CLERK_STATE):
        st = _CLERK_STATE[clerk]
        if not st['visible']:
            continue
        resolved = _clerk_img(st['pose'], st['expr'])
        if resolved:
            cfg = _CLERK_CFG[clerk]
            at = st.get('enter_pending') or cfg['at']
            st['enter_pending'] = None
            lines.append(f'{indent}show {resolved[0]} as {cfg["tag"]} at {at}')
    return lines


def emit_collective_expr(expr, indent):
    """【…三人集体<表情>】：主立绘走场景表情差分 + 在场店员一起换表情，
    共用同一次 master 层溶解。当前场景没有该差分时主立绘跳过（只换店员）。"""
    lines = [f'{indent}## 三人集体{expr}']
    cfg = SCENE_EXPRESSIONS.get(_CURRENT_EXPR_SCENE)
    img = cfg['map'].get(expr) if cfg else None
    if img:
        verb = 'show' if cfg['model'] == 'overlay' else 'scene'
        lines.append(f'{indent}{verb} {img}')
    else:
        print(f"WARNING: 三人集体{expr}：场景 {_CURRENT_EXPR_SCENE} 没有 '{expr}' 差分，"
              "主立绘保持不变（只换店员）")
    for clerk in sorted(_CLERK_STATE):
        st = _CLERK_STATE[clerk]
        if not st['visible']:
            continue
        # 当前姿势没有这个表情的素材时，先试该店员的本命姿势（如 讲解站立 没有
        # 坏笑素材，店员2 回到 抱胸·坏笑）——集体表情的重点是表情，不是姿势。
        pose = st['pose']
        if (pose, expr) not in SPRITE_INDEX and \
                (_CLERK_CFG[clerk]['pose'], expr) in SPRITE_INDEX:
            pose = _CLERK_CFG[clerk]['pose']
        resolved = _clerk_img(pose, expr)
        if resolved:
            ccfg = _CLERK_CFG[clerk]
            # 同一交互内刚入场：沿用入场动画 transform（见 reshow）
            at = st.get('enter_pending') or ccfg['at']
            st['enter_pending'] = None
            lines.append(f'{indent}show {resolved[0]} as {ccfg["tag"]} at {at}')
            st.update(pose=pose, expr=resolved[1])
    lines.append(f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')
    return '\n'.join(lines)


def generate_sprites_rpy():
    """按扫描到的素材生成 game/images/sprites/sprites.rpy：
    image 定义（tag=ws，属性=姿势+表情；glitch 为 <表情>_glitch 循环动画）
    + 两个摆位 transform。缩放/摆位不烘进 image，统一由 at transform 做，
    这样 glitch 动画帧不用逐帧包 Transform。"""
    out = [
        '## AUTO-GENERATED by convert_script.py — 不要手改，重跑转换器会覆盖。',
        '## 王霜立绘：素材在本目录下按 <姿势>(<表情>.png 命名，扫描自动注册。',
        '## 摆位参数改 convert_script.py 里的 WS_* 常量。',
        '',
    ]
    for (pose, expr), rel in sorted(SPRITE_INDEX.items()):
        expr_attr = SPRITE_EXPR_ATTRS.get(expr)
        if expr_attr is None:
            print(f"WARNING: 素材 {rel} 的表情 '{expr}' 不在 SPRITE_EXPR_ATTRS，未注册")
            continue
        out.append(f'image ws {SPRITE_POSE_ATTRS[pose]} {expr_attr} = "{rel}"')
    for (pose, expr), frames in sorted(SPRITE_GLITCH_INDEX.items()):
        expr_attr = SPRITE_EXPR_ATTRS.get(expr)
        if expr_attr is None:
            continue
        out.append('')
        out.append(f'image ws {SPRITE_POSE_ATTRS[pose]} {expr_attr}_glitch:')
        for rel in frames:
            out.append('    choice:')
            out.append(f'        "{rel}"')
    # 软 glitch（店员用）：干净立绘挂着，每隔 2~3 秒随机闪两下故障帧。
    # 闪帧优先用 _glitchsoft 局部帧（只有几个小范围出故障，--patches 生成）；
    # 没有软帧的组合回退全身 glitch 帧并告警。持续循环的 _glitch 是
    # "信号完全失稳"的主立绘演出，复制体只要偶发的小范围抽搐。
    for (pose, expr), frames in sorted(SPRITE_GLITCH_INDEX.items()):
        expr_attr = SPRITE_EXPR_ATTRS.get(expr)
        clean = SPRITE_INDEX.get((pose, expr))
        if expr_attr is None or clean is None:
            continue
        soft = SPRITE_GLITCHSOFT_INDEX.get((pose, expr))
        if soft:
            frames = soft
        else:
            print(f"WARNING: {pose}·{expr} 没有 _glitchsoft 局部帧"
                  f"（generate_glitch_art.py --patches 3 生成到 glitch_soft/）"
                  f"—— 软 glitch 先用全身帧")
        f1 = frames[0]
        f2 = frames[1] if len(frames) > 1 else frames[0]
        out.append('')
        out.append(f'image ws {SPRITE_POSE_ATTRS[pose]} {expr_attr}_glitchsoft:')
        out.append('    block:')
        out.append(f'        "{clean}"')
        for p in WS_CLERK_GLITCH_PAUSES:
            out.append('        choice:')
            out.append(f'            pause {p}')
        out.append(f'        "{f1}"')
        out.append(f'        {WS_CLERK_GLITCH_FLASH}')
        out.append(f'        "{clean}"')
        out.append(f'        {WS_CLERK_GLITCH_GAP}')
        out.append(f'        "{f2}"')
        out.append(f'        {WS_CLERK_GLITCH_FLASH}')
        out.append('        repeat')
    # 小跳（【小跳】标记）的起落 ATL；每个摆位都配一个内联了自己静态摆位的
    # _hop 版完整 transform —— at 列表必须始终单元素（zoom 平方坑，见
    # SPRITE_HOP_PX 上方注释）。subpixel 同走路：位移小，不开会整像素跳格。
    hop_atl = [
        '    subpixel True',
        # 先等姿势/表情的 master 层溶解走完再起跳——小跳标记总是跟在立绘
        # 变化之后，同帧起跳会跳在半透明的切换过程上。
        f'    pause {EXPR_TRANSITION_SECONDS}',
        f'    easeout {SPRITE_HOP_UP} yoffset -{SPRITE_HOP_PX}',
        f'    easein {SPRITE_HOP_DOWN} yoffset 0',
    ]
    close_static = [
        '    xalign 0.5',
        '    yanchor 0.0',
        f'    ypos {WS_CLOSE_YPOS}',
        f'    zoom {WS_CLOSE_ZOOM}',
    ]
    mid_static = [
        '    xalign 0.5',
        '    yanchor 0.0',
        f'    ypos {WS_MID_YPOS}',
        f'    zoom {WS_CLERK_ZOOM}',
    ]
    out += [
        '',
        '## 半身近景（第一人称对视感）：头到腰占满屏，底部裁掉，水平居中。',
        'transform ws_close:'] + close_static + [
        '',
        '## 半身近景 + 小跳（【小跳】）。',
        'transform ws_close_hop:'] + close_static + hop_atl + [
        '',
        '## 中景（沙漠桥段/虚空对视）：大小与店员立绘一致。',
        'transform ws_mid:'] + mid_static + [
        '',
        '## 中景 + 小跳（【小跳】）。',
        'transform ws_mid_hop:'] + mid_static + hop_atl + [
        '',
    ]
    # 走路步数取整到完整周期：x 到位后最后一步在原地落定，像自然收步。
    walk_steps = max(1, round(WS_WALK_SECONDS / WS_WALK_STEP))
    out += [
        '## 沙漠走路进场（【王霜走路进场】）：左缘外走到画面偏右，水平匀速 +',
        '## 每步一次起伏。落点即站定位置 —— 走路窗口内的后续姿势 show 不带 at',
        '## 列表，沿用本 transform 的落点（见 convert_script.py 走路窗口逻辑）。',
        '## subpixel：起伏只有十几像素，不开亚像素会整像素跳格。',
        'transform ws_desert_walk:',
        '    subpixel True',
        '    xanchor 0.5',
        f'    xpos {WS_WALK_START_X}',
        '    yanchor 0.0',
        f'    ypos {WS_MID_YPOS}',
        f'    zoom {WS_CLERK_ZOOM}',
        '    parallel:',
        f'        linear {WS_WALK_SECONDS} xpos {WS_WALK_END_X}',
        '    parallel:',
        '        block:',
        f'            easeout {WS_WALK_STEP / 2} yoffset -{WS_WALK_BOB}',
        f'            easein {WS_WALK_STEP / 2} yoffset 0',
        f'            repeat {walk_steps}',
        '',
    ]
    # 店员摆位。入/退场是**内联静态摆位的完整 transform**——每次 show 的 at
    # 列表只有一个元素。不能拆成 `at 摆位, 动画`：替换 at 列表时 Ren'Py 从尾部
    # 对齐取状态，动画 transform 会继承摆位的 rotate/zoom、内层又套一遍 ——
    # rotate 叠成 360（倒吊转正）、zoom 平方（缩小），就是当初的退场 bug。
    clerk1_static = [
        '    xanchor 0.5',
        f'    xpos {WS_CLERK1_XPOS}',
        '    yanchor 0.0',
        f'    ypos {WS_CLERK1_YPOS}',
        f'    zoom {WS_CLERK_ZOOM}',
    ]
    clerk2_static = [
        '    rotate 180',
        '    xanchor 0.5',
        f'    xpos {WS_CLERK2_XPOS}',
        '    yanchor 1.0',
        f'    ypos {WS_CLERK2_YPOS}',
        f'    zoom {WS_CLERK_ZOOM}',
    ]
    out += ['## 店员（王霜复制体，甜品店段）：右侧正立。',
            'transform ws_clerk_right:'] + clerk1_static + [
        '',
        '## 店员1入场：从屏幕下方升上来（非阻塞，与店员2 的降下对称）。',
        'transform ws_clerk_right_enter:'] + clerk1_static + [
        f'    yoffset {CLERK_TRAVEL}',
        f'    ease {CLERK_MOVE_SECONDS} yoffset 0',
        '',
        '## 店员1退场：垂直平移沉出画面（非阻塞）。',
        'transform ws_clerk_right_exit:'] + clerk1_static + [
        f'    ease {CLERK_MOVE_SECONDS} yoffset {CLERK_TRAVEL}',
        '',
        '## 店员1 + 小跳（【小跳】）。',
        'transform ws_clerk_right_hop:'] + clerk1_static + hop_atl + [
        '',
        '## 店员2：左侧从天花板倒吊（rotate 180，底边=头部下沿）。',
        'transform ws_clerk_ceiling:'] + clerk2_static + [
        '',
        '## 店员2入场：从天花板上方倒吊降下（非阻塞）。',
        'transform ws_clerk_ceiling_enter:'] + clerk2_static + [
        f'    yoffset {-CLERK_TRAVEL}',
        f'    ease {CLERK_MOVE_SECONDS} yoffset 0',
        '',
        '## 店员2退场：垂直平移收回天花板（非阻塞）。',
        'transform ws_clerk_ceiling_exit:'] + clerk2_static + [
        f'    ease {CLERK_MOVE_SECONDS} yoffset {-CLERK_TRAVEL}',
        '',
        '## 店员2 + 小跳（【小跳】）：倒吊着向上（天花板方向）弹一下。',
        'transform ws_clerk_ceiling_hop:'] + clerk2_static + hop_atl + [
        '',
    ]
    path = os.path.join(BASE_DIR, 'game', 'images', 'sprites', 'sprites.rpy')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f"sprites.rpy generated: {len(SPRITE_INDEX)} base sprites, "
          f"{len(SPRITE_GLITCH_INDEX)} glitch animations")

def escape_quotes(text):
    """Escape straight double quotes for Ren'Py"""
    return text.replace('"', '\\"')

def has_curly_quotes(text):
    """Check if text contains curly double quotes"""
    return '"' in text or '"' in text

# 角色名 -> characters.rpy 里的 Character 变量。此前在三处各抄一份，加新角色
# 时漏改任何一处都会静默退化成旁白 —— 收敛成单一来源。
CHAR_VAR_MAP = {
    '王霜': 'wangshuang',
    '王霜（？）': 'wangshuang_unknown',
    # 店员 = 王霜复制体（甜品店段），台词归各自的 Character、立绘走店员系统。
    '王霜（店员）': 'wangshuang_clerk',
    '王霜（店员2）': 'wangshuang_clerk2',
    '阿鹤': 'ahe',
    '尸首': 'shishou',
    '路人甲': 'lurenjia',
    '路人乙': 'lurenyi',
    '路人丙': 'lurenbing',
    '路人丁': 'lurending',
    '杰罗瓦': 'jieluowa',
    '米姐': 'mijie',
    '尤里娅': 'youliya',
}

# 长名优先，避免 王霜（店员2） 被 王霜 截胡。
CHAR_PATTERN = '|'.join(
    re.escape(name) for name in sorted(CHAR_VAR_MAP, key=len, reverse=True))

# 专有名词列表（point 7）：这些字眼在正文中出现时用 {i}斜体{/i} 强调。
# 在 demo_script.txt 里直接以普通文字书写，由转换器负责加斜体标签——
# 这样剧本保持干净，新增名词只要往这个列表里加即可。
# 2026-08：作者决定去掉 尤里娅/KAS 的斜体，列表清空（机制保留备用）。
# 注意：增删名词会改 say 文本 → 英文 tl 的哈希 ID 失配，需要重打 key。
PROPER_NOUNS = []

def italicize_proper_nouns(text):
    """Wrap any proper noun (PROPER_NOUNS) in {i}...{/i} for italic emphasis."""
    for noun in PROPER_NOUNS:
        if noun in text:
            text = text.replace(noun, '{i}' + noun + '{/i}')
    return text

def apply_small_text(text):
    """【小字】 → 把标记之后的文字缩小，并去掉标记本身（point 2）。
    标记是行内前缀，缩小一直作用到该行结尾。"""
    marker = '【小字】'
    if marker not in text:
        return text
    idx = text.index(marker)
    before = text[:idx]
    after = text[idx + len(marker):]
    return before + '{size=-10}' + after + '{/size}'

def normalize_dots_line(text):
    """整行只有 ASCII 点（3 个以上）的省略号行 → 全角 …（每 3 点折 1 个，四舍五入）。
    像素字体里 ASCII 点是底线细点、全角 … 是中线方点，两种写法混用时后者明显更粗；
    统一成全角（粗）。只动"整行都是点"的行 —— 句中的 ... 是口吃/迟疑，保持原样。"""
    # extend 传进来的文本带字面 \n 前缀（两个字符：反斜杠 + n），剥掉再判断
    prefix, body = '', text
    if body.startswith('\\n'):
        prefix, body = '\\n', body[2:]
    # 允许问询段的 "——..."（破折号引出的沉默拍点）一并归一
    m = re.fullmatch(r'(——)?(\.{3,})', body.strip())
    if not m:
        return text
    dashes = m.group(1) or ''
    n = len(m.group(2))
    return prefix + dashes + '…' * max(1, int(round(n / 3.0)))

# 行内注释（名词浮窗）：正文里 概念【注释：解释文字】 → 概念变成带下划线的
# 可点击链接（{a=gloss:id}），点击后屏幕右侧滑出抽屉展示解释（见
# game/scripts/glossary_ui.rpy；词典数据生成到 glossary.rpy）。
#
# 概念的边界没法从中文里自动切出来（"出现冒充者综合征"会连动词一起抓），
# 所以和 PROPER_NOUNS 一样在这里列出所有被注释的术语——标记前的文字以哪个
# 术语结尾，链接就套在哪个术语上。加新注释 = 把术语加进这个列表。
# 找不到术语时的兜底：标记紧跟在破折号/省略号后（如 "柔软而光滑的——【注释：
# 想都别想】"）就把那串标点作为链接锚点；再不行取末尾的连续文字并告警。
ANNOTATION_TERMS = ['逝乐园', '冒充者综合征', '脑血屏障', '脑前叶白质切除术', '杰罗瓦', '被试']

_ANNOT_RE = re.compile(r'【注释：\s*(.*?)\s*】')

# 收集到的注释：[(gid, 术语, 解释)]。main() 末尾写进 glossary.rpy。
_GLOSSARY = []


def apply_annotations(text):
    """把 术语【注释：解释】 替换成 {a=gloss:gN}术语{/a}，解释收进 _GLOSSARY。"""
    while True:
        m = _ANNOT_RE.search(text)
        if not m:
            break
        before, body = text[:m.start()], m.group(1)
        term = next((t for t in sorted(ANNOTATION_TERMS, key=len, reverse=True)
                     if before.endswith(t)), None)
        if term is None:
            pm = re.search(r'([—…]+)$', before)
            wm = re.search(r'([0-9A-Za-z一-鿿]+)$', before)
            if pm:
                term = pm.group(1)
            elif wm:
                term = wm.group(1)
                print(f"WARNING: 注释术语不在 ANNOTATION_TERMS：按末尾连续文字"
                      f"『{term}』整段加链接——若范围不对，把正确术语加进列表后重跑")
            else:
                print(f"WARNING: 注释【注释：{body[:20]}…】前找不到可加链接的文字，"
                      "该注释被丢弃")
                text = before + text[m.end():]
                continue
        gid = 'g%d' % (len(_GLOSSARY) + 1)
        _GLOSSARY.append((gid, term, body))
        text = (before[:-len(term)]
                + '{a=gloss:%s}%s{/a}' % (gid, term)
                + text[m.end():])
    return text


def generate_glossary_rpy():
    """把收集到的注释写成 game/scripts/glossary.rpy（词典数据）。
    _() 标记让术语和解释进入翻译抽取；抽屉屏幕显示时再运行时翻译。"""
    def esc(s):
        return s.replace('\\', '\\\\').replace('"', '\\"')
    out = [
        '## AUTO-GENERATED by convert_script.py — 不要手改，重跑转换器会覆盖。',
        '## 行内注释词典：剧本 【注释：…】 标记收集而来，UI 见 glossary_ui.rpy。',
        'define GLOSSARY = {',
    ]
    for gid, term, body in _GLOSSARY:
        out.append('    "%s": (_("%s"), _("%s")),' % (gid, esc(term), esc(body)))
    out.append('}')
    out.append('')
    path = os.path.join(BASE_DIR, 'game', 'scripts', 'glossary.rpy')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
    print(f"glossary.rpy generated: {len(_GLOSSARY)} annotations")


def transform_display_text(text):
    """所有可见正文（对话/旁白/选项/extend）共用的行内文字变换。
    顺序：先注释链接（标记还在原文里才找得到术语边界），再 小字，再 斜体
    （斜体可嵌套进小字里，互不干扰）。"""
    text = apply_annotations(text)
    text = normalize_dots_line(text)
    text = apply_small_text(text)
    text = italicize_proper_nouns(text)
    return text

# 【锁定操作Ns】：文本展示完成后锁定所有操作 N 秒（point 5）。
LOCK_RE = re.compile(r'【锁定操作([\d.]+)s?】')

def extract_lock(dialogue):
    """从对话里抽出 【锁定操作Ns】，返回 (去掉标记的文本, 秒数 or None)。"""
    m = LOCK_RE.search(dialogue)
    if not m:
        return dialogue, None
    cleaned = LOCK_RE.sub('', dialogue).strip()
    return cleaned, m.group(1)

# 用于 Extended文本框 标点分句的占位符（【屏幕震动】被替换成它）。
_SHAKE_TOKEN = ''
# 断句标点（都"在其后断开"、归入前一块）：句号、问号、感叹号、中文省略号、破折号。
# 注意：ASCII 的 "..." 不算省略号（多为口吃/迟疑，不该断句），中文 … 才算。
_ENDERS = set('。！？…')
_SPLIT_AFTER = _ENDERS | {'—'}   # 破折号 —— 和其他标点一样，留在前一句末尾

def _has_content(s):
    """是否含实质内容（不只是断句标点/破折号/空白）——用于避免标点/破折号单独成块。"""
    return any((c not in _SPLIT_AFTER) and (not c.isspace()) for c in s)

def split_click_chunks(text):
    """把 Extended（大/小）文本框 的一段文字按标点切成若干"点击块"。

    返回 [(chunk_text, effect_before), ...]，effect_before 为 None 或 'shake'。
    规则：
    - 句号/问号/感叹号/中文省略号/破折号 之后断开（标点本身留在前一块末尾）。
    - 破折号 —— 也和其他标点一样归入前一块（不再引出下一块）。
    - 连续标点算一次断点，不产生空块；前面没有实质内容时不断（让破折号引出惨叫等）。
    - ASCII "..." 不断句。
    - 【屏幕震动】(占位符) 强制断点，且其后那一块带 'shake' 特效。
    """
    text = text.replace('【屏幕震动】', _SHAKE_TOKEN)
    result = []
    cur = ''
    pending_effect = None

    def flush(next_effect=None):
        nonlocal cur, pending_effect
        if cur.strip():
            result.append([cur, pending_effect])
            cur = ''
            pending_effect = next_effect
        elif next_effect:
            # 空块：不产出，但把特效带给下一块
            pending_effect = next_effect

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == _SHAKE_TOKEN:
            flush(next_effect='shake')
            i += 1
            continue
        if ch in _SPLIT_AFTER:
            # 句末标点 / 破折号：连续吃完（连续标点算一次），归入前一块，在其后断开。
            # 但前面没有实质内容时（破折号紧跟在强制断点之后、要引出后面的文字，
            # 如惨叫"——啊啊"）不断，让它和后面连在一起。
            while i < n and text[i] in _SPLIT_AFTER:
                cur += text[i]
                i += 1
            if _has_content(cur):
                flush()
            continue
        cur += ch
        i += 1

    if cur.strip():
        result.append([cur, pending_effect])
    return result

def format_dialogue(text):
    """Format dialogue string, using single quotes if curly quotes present"""
    # 行内显示变换（小字 / 专有名词斜体），对所有正文统一生效
    text = transform_display_text(text)
    # Escape square brackets for Ren'Py text interpolation: [ -> [[
    text = text.replace('[', '[[')
    if has_curly_quotes(text):
        # Use single quotes as delimiter, escape any single quotes in text
        escaped = text.replace("'", "\\'")
        return f"'{escaped}'"
    else:
        # Use double quotes as delimiter, escape any double quotes in text
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'

_SFX_TEXT_STMT_RE = re.compile(r'''^([a-z_]+ )?["']''')

def insert_sfx_waits(script_text):
    """在 `$ play_sfx(…)` 之后、下一句正文/对白之前插入 `$ wait_sfx()`（point 3）。

    正文/对白 = say / extend / 旁白（行首是「小写标识符 + 引号」或直接引号）。
    转场（## 注释、scene、$ 赋值、call screen 等）都不算正文会被跳过 —— 所以
    音效与碎裂等转场仍然同步触发，转场之后的第一句正文才阻塞等音效播完。
    """
    lines = script_text.split('\n')
    out = []
    pending = False
    for line in lines:
        if pending and _SFX_TEXT_STMT_RE.match(line.strip()):
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f'{indent}$ wait_sfx()')
            pending = False
        out.append(line)
        if 'play_sfx(' in line:
            pending = True
    return '\n'.join(out)

def _split_left_literal(left_lines):
    """把左栏各行拼成一个 Ren'Py 双引号字符串字面量，其值与左栏阶段累积出来的
    what 完全一致（逐行 transform_display_text + 字面 \\n 连接）。供右栏阶段
    `$ _split_left_text = ...` 把已填满的左栏静态显示。"""
    pieces = []
    for ln in left_lines:
        t = transform_display_text(ln)                   # 斜体/小字标签，和显示一致
        t = t.replace('\\', '\\\\').replace('"', '\\"')  # 先反斜杠再双引号
        t = t.replace('[', '[[')                         # 和 format_dialogue 一致
        pieces.append(t)
    return '"' + '\\n'.join(pieces) + '"'

# 左栏（固定高度）的视觉行容量与每视觉行字数估算。左栏约 800px 高、620px 宽、
# 字号 33 + 行距 10 ≈ 每视觉行 ~46px → ~16 行；620px / ~33px(一个汉字) ≈ 每视觉行
# ~18 字。改这两个数 = 改"左栏装多少才溢到右栏"。
_SPLIT_COL_CAPACITY_LINES = 8
_SPLIT_COL_CHARS_PER_LINE = 18

def _visual_lines(text):
    """一行原文按左栏宽度折行后占多少视觉行（向上取整，至少 1）。"""
    return max(1, -(-len(text) // _SPLIT_COL_CHARS_PER_LINE))

def _split_capacity_index(narration):
    """先把文本尽量塞进左栏：返回左栏能容纳的行数 k（累计视觉行数不超过容量）。
    k == len 表示整块都放得下左栏（右栏不用，渲染成单栏、无阶段切换）。
    至少保证左栏有一行（首行特别长也先放左栏）。"""
    cum = 0
    for idx, line in enumerate(narration):
        v = _visual_lines(line)
        if idx > 0 and cum + v > _SPLIT_COL_CAPACITY_LINES:
            return idx
        cum += v
    return len(narration)

def _emit_split_column(out, indent, lines, opening_stmt):
    """把分栏一栏的若干源行写成 say/extend：每个源行 = 一句**干净文本**，源行之间
    用字面 \\n 换行（point 2）。第一行用 opening_stmt 起头（split_left_narrator /
    split_right_narrator），其余 extend "\\n…"。标点逐句点击由运行时 {w} 处理
    （screens.rpy add_click_pauses），所以翻译 ID 与源行 1:1 稳定。"""
    first = True
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if first:
            out.append(f'{indent}{opening_stmt} {format_dialogue(ln)}')
            first = False
        else:
            out.append(f'{indent}extend {format_dialogue(chr(92) + "n" + ln)}')

def emit_split_large_block(lines, start_i, end_line, indent="    "):
    """Split Extended大文本框：文本先尽量塞进固定高度的左栏；放得下就单栏显示
    （文字尽量待在一侧），左栏装满才把溢出部分接到右栏。中间留白避开王霜的头。

    放得下（多数块）：只走左栏，split_left_narrator（屏幕 split_say_left），
      普通 say/extend、逐字显示、单击推进，没有阶段切换（也就没有"切换后行距变大"）。
    放不下：左栏阶段填到容量上限 → `$ _split_left_text = ...` 冻结左栏 → 切
      split_right_narrator（屏幕 split_say_right，左栏静态、右栏活动逐字）。
    返回 (output_lines, new_index)。
    """
    out = []
    i = start_i
    narration = []
    while i < end_line and i < len(lines):
        line = lines[i].strip()
        i += 1
        if 'Split Extended大文本框结束' in line:
            break
        if not line:
            continue
        # 块内转场：立即输出（一般在块首，如甜品店对视5）
        tm = re.match(r'^【转场[：:](.+?)】$', line)
        if tm:
            content = tm.group(1).strip()
            pm = re.search(r'。', content)
            if pm:
                sn, sd = content[:pm.start()].strip(), content[pm.end():].strip()
            else:
                sn, sd = content, ""
            emit_transition_lines(out, indent, sn, sd)
            continue
        # 其它舞台提示跳过
        if line.startswith('【') and line.endswith('】'):
            continue
        narration.append(line)

    if not narration:
        return out, i

    # 先尽量塞左栏；放得下就单栏（无右栏、无阶段切换），放不下才溢到右栏。
    k = _split_capacity_index(narration)
    left, right = narration[:k], narration[k:]

    # 左栏阶段：split_left_narrator（屏幕 split_say_left，左栏即活动 say，逐字显示）。
    # 每个源行内部再按标点切块逐次点击（point 4），源行之间 \n 换行（point 2）。
    _emit_split_column(out, indent, left, 'split_left_narrator')

    if right:
        # 左栏装不下，溢出部分进右栏。左栏内容由 split_say_left 屏幕在运行时把
        # （已翻译的）what 存进 _split_left_text，再切右栏活动 say —— 不在这里写
        # 中文字面量，否则英文模式下右栏阶段左栏会变回中文。
        _emit_split_column(out, indent, right, 'split_right_narrator')

    return out, i

def emit_rightpage_block(lines, start_i, end_line, indent="    "):
    """右侧Split Extended大文本框：只占右半屏的单栏文本框，逐行点击累积；
    每页最多 _SPLIT_COL_CAPACITY_LINES 视觉行，装不下的从"下一页"继续——
    下一页 = 新的一句 say（清掉上一页内容、从头开始），其余行 extend 累积。
    返回 (output_lines, new_index)。"""
    out = []
    i = start_i
    narration = []
    while i < end_line and i < len(lines):
        line = lines[i].strip()
        i += 1
        if '右侧Split Extended大文本框结束' in line:
            break
        if not line:
            continue
        tm = re.match(r'^【转场[：:](.+?)】$', line)
        if tm:
            content = tm.group(1).strip()
            pm = re.search(r'。', content)
            if pm:
                sn, sd = content[:pm.start()].strip(), content[pm.end():].strip()
            else:
                sn, sd = content, ""
            emit_transition_lines(out, indent, sn, sd)
            continue
        if line.startswith('【') and line.endswith('】'):
            continue
        narration.append(line)

    if not narration:
        return out, i

    page_first = True   # 该源行是否为某页第一行（第一行用 say 清屏，其余 extend）
    used = 0
    for ln in narration:
        ln = ln.strip()
        if not ln:
            continue
        v = _visual_lines(ln)
        if not page_first and used + v > _SPLIT_COL_CAPACITY_LINES:
            page_first = True   # 这一页装不下了 → 翻页
            used = 0
        # 每个源行 = 一句干净文本；标点逐句点击由运行时 {w} 处理。翻页/换行以源行为单位。
        if page_first:
            out.append(f'{indent}split_right_page_narrator {format_dialogue(ln)}')
            page_first = False
        else:
            out.append(f'{indent}extend {format_dialogue(chr(92) + "n" + ln)}')
        used += v

    return out, i

def emit_char_dialogue_inline(char_var, dialogue, indent):
    """角色台词，支持**行内**立绘/表情标记（台词说到一半换立绘）：
        王霜【讲解站立，默认表情】：不不不…。【讲解站立，得意表情】不过对于你来说…
    在标记处把台词拆成 say + extend，标记变成两段之间的立绘切换 —— 玩家点一下，
    立绘换掉、后半句接在同一个框里。认不出的行内【…】保持字面原样（老行为）。"""
    parts = re.split(r'(【[^】]+】)', dialogue)
    if len(parts) == 1:
        return emit_char_dialogue(char_var, dialogue, indent)
    out = []
    cur = ''
    said = False

    def flush():
        nonlocal cur, said
        text = cur.strip()
        cur = ''
        if not text:
            return
        if said:
            out.append(f'{indent}extend {format_dialogue(text)}')
        else:
            out.append(emit_char_dialogue(char_var, text, indent))
            said = True

    for part in parts:
        if part.startswith('【') and part.endswith('】'):
            change = emit_expression_change(part[1:-1], indent)
            if change is None:
                cur += part          # 不是立绘/表情标记：保持字面（{shake} 等同理）
            else:
                flush()
                out.append(change)
        else:
            cur += part
    flush()
    return '\n'.join(out) if out else emit_char_dialogue(char_var, dialogue, indent)


def emit_char_dialogue(char_var, dialogue, indent, comment=None):
    """生成一行角色对话，处理 【锁定操作Ns】（point 5）。

    带锁定时：说话前设置 say_allow_dismiss 的挂钟死线（见 variables.rpy 的
    op_lock_start）——N 秒内点击被静默丢弃、无法推进，到点自动放行。
    ★不再用 op_lock 屏幕★：它的 timer Hide 会在台词中途 restart_interaction、
    把打字机 st 清零，解锁瞬间文字重打闪烁（"盯——"的 glitch）。
    （也不用 {nw}+硬暂停：那会让文本框在暂停期间消失。）
    """
    cleaned, lock = extract_lock(dialogue)
    _clerk_close_enter_window()   # say = 交互边界，关闭入场动画的沿用窗口
    out = []
    if comment:
        out.append(f'{indent}## {comment}')
    if lock:
        out.append(f'{indent}$ op_lock_start({lock})')
    out.append(f'{indent}{char_var} {format_dialogue(cleaned)}')
    return '\n'.join(out)

def _emit_scene(out, indent, scene_name, bg_image, transition):
    """发出 scene 行，并更新当前表情场景。overlay 表情场景额外把透明立绘默认
    表情叠上去（scene <bg> + show <default> + with，三者同一个过渡一起淡入）。"""
    global _CURRENT_EXPR_SCENE, _LAST_SPRITE, _SPRITE_WALK_PENDING, _SPRITE_WALK_ACTIVE
    _LAST_SPRITE = None   # scene 语句会清掉所有 show，立绘追踪一起清
    _SPRITE_WALK_PENDING = False   # 走路窗口随立绘一起被 scene 清掉
    _SPRITE_WALK_ACTIVE = False
    # 有店员在场：先发垂直平移退场动画，pause 等动画走完再转场
    # （剧本：「店员和店员2退场，退场的形式是垂直平移出屏幕」）。
    clerk_exits = [e for e in (emit_clerk_exit(c, indent) for c in sorted(_CLERK_STATE))
                   if e]
    if clerk_exits:
        out.append(f'{indent}## 店员退场（垂直平移出屏幕）')
        out.extend(clerk_exits)
        out.append(f'{indent}pause {CLERK_MOVE_SECONDS + 0.05}')
    # 就地转场：不发 scene，只发一行扳机（见 IN_PLACE_SCENES）。画面上还是同一个
    # displayable，转场由它自己的 ATL 在后台走完，不阻塞、不吃点击。
    if scene_name in IN_PLACE_SCENES:
        out.append(f'{indent}{IN_PLACE_SCENES[scene_name]}')
        _CURRENT_EXPR_SCENE = scene_name
        return
    # 长黑场 + 禁止点击快进：黑色叠层渐入 → 停留 → 换场后渐出，全程 hard pause。
    if scene_name in SCENE_HARD_FADE:
        fo, hold, fi = SCENE_HARD_FADE[scene_name]
        out.append(f'{indent}## 长黑场过渡（不可点击快进）')
        # 屏幕开始变暗时同步淡出当前音乐，避免到甜品店时音乐"硬切"。
        # 新场景音乐随后由 set_scene_music(...) 淡入。
        out.append(f'{indent}stop music fadeout {fo}')
        out.append(f'{indent}show black zorder 100:')
        out.append(f'{indent}    alpha 0.0')
        out.append(f'{indent}    linear {fo} alpha 1.0')
        out.append(f'{indent}$ hard_pause({fo})')
        if hold:
            out.append(f'{indent}$ hard_pause({hold})')
        _emit_camera_at_switch(out, indent)   # 全黑期间设/复位镜头，跳变不可见
        out.append(f'{indent}scene {bg_image}')
        out.append(f'{indent}show black zorder 100:')
        out.append(f'{indent}    alpha 1.0')
        out.append(f'{indent}    linear {fi} alpha 0.0')
        out.append(f'{indent}$ hard_pause({fi})')
        out.append(f'{indent}hide black')
        _CURRENT_EXPR_SCENE = scene_name
        return
    # 镜头设/复位不能直接跟在 `with 过渡` 前面 —— camera 变换包在图层过渡外面，
    # 淡出中的旧画面会被新镜头带着动。'switch' 类镜头变化要把转场拆成"沉黑 →
    # 黑中动镜头 → 浮出"三段（cam_fade_out / cam_fade_in，见 transitions.rpy）；
    # 交叉溶解场景（scene_dissolve）藏不住黑场，复位退化成 'inline' 缓回动画。
    cam = []
    cam_kind = _emit_camera_at_switch(cam, indent,
                                      ease_back=(transition == 'scene_dissolve'))
    cfg = SCENE_EXPRESSIONS.get(scene_name)
    if cfg and cfg['model'] == 'overlay':
        if cfg.get('continue_bg'):
            # bg（黑屏视频）从上一场景连续过来：不重新 scene —— 重新 scene 会重启视频
            # 并经 scene_soft 的黑场"暗一下"。只把立绘 dissolve 淡入，黑屏全程连续。
            out.extend(cam)   # 画面是连续黑屏，镜头变化落在黑上不可见
            out.append(f'{indent}show {cfg["default"]} with scene_dissolve')
        elif cam_kind == 'switch':
            out.append(f'{indent}scene black with cam_fade_out')
            out.extend(cam)
            out.append(f'{indent}scene {bg_image}')
            out.append(f'{indent}show {cfg["default"]}')
            out.append(f'{indent}with cam_fade_in')
        else:
            out.extend(cam)
            out.append(f'{indent}scene {bg_image}')
            out.append(f'{indent}show {cfg["default"]}')
            out.append(f'{indent}with {transition}')
    elif cam_kind == 'switch' and transition != 'None':
        out.append(f'{indent}scene black with cam_fade_out')
        out.extend(cam)
        out.append(f'{indent}scene {bg_image} with cam_fade_in')
    else:
        # 'inline' 缓回随过渡同走；transition 为 None 的硬切与换景同帧，无残留。
        out.extend(cam)
        out.append(f'{indent}scene {bg_image} with {transition}')
    # 揭示卡场景：转场演完后藏文本框、等一次点击，画面自己占一拍。
    if scene_name in SCENE_CLICK_HOLD:
        out.append(f'{indent}## 画面单独一拍：点击后才继续出字')
        out.append(f'{indent}window hide')
        out.append(f'{indent}pause')
    _CURRENT_EXPR_SCENE = scene_name

def emit_expression_change(action, indent):
    """角色【…】 标记的统一入口（普通行与 Extended 块内共用）：
    1. 【姿势，表情】（含顿号）→ 立绘 show（emit_sprite_change）；
    2. 【表情】 → 场景表情差分（SCENE_EXPRESSIONS）；
    3. 都不是 → 返回 None，调用方按普通"舞台提示注释"处理。
    full 场景用 scene 换整图；overlay 场景用 show 换透明立绘（共用 tag）。

    过渡只作用于 master 层（renpy.transition(..., layer="master")），不碰 screens 层
    的对话框/文字 —— 这样换表情时背景平滑溶解，但对话框和当前那句文字全程不消失、
    不闪烁（不能用 `with`，那是全屏过渡，会把对话框和文字一起淡掉）。"""
    sprite = emit_sprite_change(action, indent)
    if sprite is not None:
        return sprite
    cfg = SCENE_EXPRESSIONS.get(_CURRENT_EXPR_SCENE)
    if not cfg:
        return None
    img = cfg['map'].get(action)
    if not img:
        return None
    verb = 'show' if cfg['model'] == 'overlay' else 'scene'
    lines = [f'{indent}## 表情：{action}', f'{indent}{verb} {img}']
    # 整图差分是 scene 语句，会顺带清掉店员立绘 —— 在场店员同一帧补发回去
    # （同一交互内重新 show，画面上店员全程不消失）。
    if verb == 'scene':
        lines.extend(_clerk_reshow_lines(indent))
    lines.append(f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')
    return '\n'.join(lines)

def emit_transition_lines(output, indent, scene_name, scene_desc):
    """把一个场景转场写进 output（供 Extended 累积块内部复用）。
    scene_desc 仅用于剧本可读性，不再写进 .rpy（开发者场景叠层已移除）。"""
    output.append(f'{indent}## 转场：{scene_name}')
    bg_image = SCENE_BG_MAP.get(scene_name, 'black')
    if scene_name in SCENE_TRANSITIONS:
        transition = SCENE_TRANSITIONS[scene_name]
    elif scene_name in NO_TRANSITION_SCENES:
        transition = 'None'
    elif scene_name in CROSS_DISSOLVE_SCENES:
        transition = 'scene_dissolve'
    else:
        transition = 'scene_soft'
    _emit_scene(output, indent, scene_name, bg_image, transition)

def emit_extended_segments(collected, output, indent, large=False, centered=False,
                           continued=False):
    """Extended文本框（大/小）：保留源换行（point 2）。每个源行 = 一句 say/extend，
    整句**干净文本**——标点的「逐句点击」改由运行时 {w} 处理（见 screens.rpy 的
    add_click_pauses）。这样翻译 ID 与源行 1:1 稳定，以后改分句逻辑再也不会冲掉翻译。

    collected 是 [(speaker_or_None or '__transition__', text/payload), ...]。
    - 段落第一行 = say；其后每行 = extend "\\n…"（源换行保留为视觉换行，point 2）。
    - 行内 【屏幕震动】(point 6)：在标记处把该行拆开，中间插 `with fx_quake`；
      拆出的后半段不另起 \\n（仍属同一句、同一视觉行）。这是唯一仍在转换期拆分的
      情况（震动是屏幕特效，没法靠 {w} 文本标签触发）。
    - __transition__ 结束当前段落（其后另起新 say，不带前导 \\n）。large=True 旁白
      走 large_narrator（大文本框屏幕），否则普通 narrator。
    """
    # centered：居中Extended 文本框 —— 累积句子走 centered_say 屏幕、屏幕正中显示。
    # continued=True：接续上一段累积（首行直接 extend，不另起 say）——
    # 嵌套选项的分支正文要接在菜单前的同一个框里，靠它续上。返回值 = 结束时
    # 是否处于"已开头"状态，供调用方跨菜单继续接。
    narr = 'centered_narrator ' if centered else ('large_narrator ' if large else '')
    first_emitted = continued   # 本段落是否已经发出开头 say

    def emit_piece(speaker, text, lead_newline, raw=False):
        nonlocal first_emitted
        if lead_newline:
            text = chr(92) + 'n' + text
        # raw=True：text 已是最终 Ren'Py 字符串内容（含 [var!t] 插值），
        # 不能走 format_dialogue（它会把 [ 转义成 [[，杀掉插值）。
        rendered = f'"{text}"' if raw else format_dialogue(text)
        if not first_emitted:
            if speaker:
                output.append(f'{indent}{speaker} {rendered}')
            else:
                output.append(f'{indent}{narr}{rendered}')
            first_emitted = True
        else:
            output.append(f'{indent}extend {rendered}')

    for speaker, text in collected:
        if speaker == '__eval__':
            # 问询段逻辑判断行（如 精神状态：平稳【仅平稳>1】/…）：原文条件表进注释，
            # 显示行换成运行时插值 —— 每类只展示 interro_evaluate() 算出的唯一结论。
            category, original = text
            output.append(f'{indent}## {original}')
            emit_piece(None, f'{category}：[{_EVAL_VAR_MAP[category]}!t]',
                       first_emitted, raw=True)
            continue
        if speaker == '__expr__':
            # 块内表情切换：master 层溶解，对话框/文字不动（见 emit_expression_change）。
            expr_line = emit_expression_change(text, indent)
            output.append(expr_line if expr_line else f'{indent}## {text}')
            first_emitted = False
            continue
        if speaker == '__sfx__':
            # 块内音频标记。不重置 first_emitted —— 声音不打断文字的累积，
            # 语句夹在两条 extend 之间，玩家点下一句时触发。
            code = convert_content_line(text, indent)
            if code:
                output.append(code)
            continue
        if speaker == '__transition__':
            scene_name, scene_desc = text
            emit_transition_lines(output, indent, scene_name, scene_desc)
            first_emitted = False
            continue
        if speaker == '__pause__':
            # 块内停顿：定格当前画面。不动 first_emitted —— 停顿不打断文字累积。
            output.append(f'{indent}pause {text}')
            continue
        # 行内屏幕震动：按标记拆段，段间插 with fx_quake（point 6）。
        parts = text.split('【屏幕震动】')
        for pidx, part in enumerate(parts):
            if pidx > 0:
                output.append(f'{indent}with fx_quake')
            part = part.strip()
            if not part:
                continue
            # 新源行的第一段（且非段落开头）才需要前导 \n；被震动拆出的后半段
            # （pidx>0）不加 \n，仍在同一视觉行。
            emit_piece(speaker, part, first_emitted and pidx == 0)

    return first_emitted

################################################################################
## Extended 块内的嵌套选项
##
## 剧本形如（见 demo_script.txt 「——录入中——」问询段）：
##     ——正文若干
##     A：选项文本
##     ——选完后的正文（继续堆在同一个大文本框里）
##     A：嵌套菜单的选项...
##         ...
##     【选项分线到此结束】       ← 收束最内层菜单
##     B：兄弟选项
##     【选项分线到此结束】       ← 收束外层菜单
##     ——后续正文
##
## 文法不看缩进，只看两条规则：A： 开一个新菜单；B/C/D： 是当前菜单的下一个
## 兄弟选项（同时结束上一个选项的正文）。每个菜单以自己的 【选项分线到此结束】
## 收束，嵌套的先收、外层的后收 —— 因此结构无歧义（缩进仅为剧本可读性）。
##
## 生成物：Ren'Py 原生嵌套 menu；标题用本项目惯用的 `extend ""` 保住文本框；
## 分支内正文全部 extend 续进同一个框（跨菜单不清屏）。选项标记
## 【选择该选项会在展示下列文字后重新展示本次选择】 → 菜单包进局部 label，
## 该分支末尾 jump 回去（正文照常累积后重新弹出同一个菜单）。
################################################################################

# 选项行：字母 + 可选【标记】 + 冒号 + 文本。只认 A-E，避免误伤普通正文。
_CHOICE_IN_BLOCK_RE = re.compile(r'^([A-E])\s*((?:【[^】]*】)*)\s*[：:]\s*(.*)$')

# 问询段数值标记 → variables.rpy 里的计数变量。疯狂 ≠ madness：疯狂只在问询
# 桥段内生效（interro_reset() 清零），madness 是全局值，两者互不相干。
_INTERRO_STAT_MAP = {
    '平稳': 'interro_calm',
    '疯狂': 'interro_insane',
    '对抗': 'interro_hostile',
    '幻觉': 'interro_halluc',
    '死亡': 'interro_death',
}
_INTERRO_STAT_RE = re.compile(r'(平稳|疯狂|对抗|幻觉|死亡)\s*\+\s*(\d+)')

# 计数变量 -> 风味字母（选项 hover 上色/诊断书同套颜色，见 variables.rpy 的
# INTERRO_FLAVOR_COLORS）。带数值的问询选项经 menu 参数 interro=(id, 风味)
# 传给选项屏；第 2 轮起、历轮选过的选项 hover 按此上色。
_INTERRO_FLAVOR = {
    'interro_calm': 'c', 'interro_insane': 'i', 'interro_hostile': 'h',
    'interro_halluc': 'u', 'interro_death': 'd',
}

_ONCE_MARK = '只加一次'

# 条件出现标记：引用另一个选项的文本前缀（尾部省略号在解析时剥掉）。
_COND_SEEN_RE = re.compile(r'本选项仅在观看过[“"](.+?)[”"]后出现')

# 条件双态文本标记：【本选项在观看过"X"后显示前者，否则显示后者】，
# 选项文本以 / 分隔前者/后者。生成两条互斥条件的 menu 项（同 id 同数值同分支，
# 只有显示文本不同），玩家任何时刻只见其一。
_COND_VARIANT_RE = re.compile(r'本选项在观看过[“"](.+?)[”"]后显示前者[，,]?\s*否则显示后者')

# 本次 Extended 块里被条件标记引用的选项前缀（emit_extended_choice_block 填充；
# 被引用的选项被选中时生成 interro_seen.add(前缀)）。
_COND_SEEN_PREFIXES = set()

# 问询段逻辑判断行：类别 → 运行时结果变量（interro_evaluate() 填充，见 variables.rpy）。
# say 里用 [var!t] 插值 —— !t 让插进来的中文结论走运行时翻译。
_EVAL_VAR_MAP = {
    '精神状态': 'interro_mental',
    '人格特质': 'interro_trait',
    '污染进程': 'interro_pollution',
    '建议执行': 'interro_verdict',
}

# 生成的循环菜单 label 全局计数（.extmenu_N 是当前 route label 的局部标签）。
_EXT_MENU_COUNTER = [0]

_CHOICE_LOOP_MARK = '重新展示本次选择'


def _parse_block_choice(line):
    """Extended 块内的选项行 → dict(letter, text, loop, madness, stats, once,
    cond_seen)，非选项行返回 None。"""
    m = _CHOICE_IN_BLOCK_RE.match(line)
    if not m:
        return None
    letter, mods, text = m.group(1), m.group(2), m.group(3).strip()
    loop = _CHOICE_LOOP_MARK in mods
    # 标记也可能写在文本尾部（与顶层选项的 【游戏继续】 风格一致）
    if _CHOICE_LOOP_MARK in text:
        loop = True
        text = re.sub(r'【[^】]*%s[^】]*】' % _CHOICE_LOOP_MARK, '', text).strip()
    madness = 0
    mm = re.search(r'[（(]madness\s*\+\s*(\d+)[）)]', text)
    if mm:
        madness = int(mm.group(1))
        text = re.sub(r'[（(]madness\s*\+\s*\d+[）)]', '', text).strip()
    # 问询段数值标记只从【】标记里解析（文本正文里出现这些字眼不受影响）。
    stats = [(_INTERRO_STAT_MAP[name], int(n))
             for name, n in _INTERRO_STAT_RE.findall(mods)]
    once = _ONCE_MARK in mods
    cond_seen = None
    cm = _COND_SEEN_RE.search(mods)
    if cm:
        cond_seen = cm.group(1).rstrip('.…。')
    # 条件双态文本：文本按第一个 / 拆成 前者/后者。
    cond_variant = None
    alt_text = None
    vm = _COND_VARIANT_RE.search(mods)
    if vm:
        cond_variant = vm.group(1).rstrip('.…。')
        if '/' in text:
            text, alt_text = (s.strip() for s in text.split('/', 1))
        else:
            print(f"WARNING: 条件双态选项 {letter} 的文本没有 '/' 分隔前者/后者，"
                  "两态将显示同一文本")
            alt_text = text
    return {'letter': letter, 'text': text, 'loop': loop, 'madness': madness,
            'stats': stats, 'once': once, 'cond_seen': cond_seen,
            'cond_variant': cond_variant, 'alt_text': alt_text}


def _build_choice_tree(items):
    """把含选项的条目序列组成树：返回顶层序列，元素为普通条目或
    ('__menu__', [(opt_dict, body_seq), ...])。"""
    def parse_seq(i):
        seq = []
        while i < len(items):
            kind = items[i][0]
            if kind == '__converge__':
                return seq, i              # 交给所属菜单消费
            if kind == '__choice__':
                if items[i][1]['letter'] == 'A':
                    menu, i = parse_menu(i)
                    seq.append(('__menu__', menu))
                    continue
                return seq, i              # 兄弟选项：当前正文结束
            seq.append(items[i])
            i += 1
        return seq, i

    def parse_menu(i):
        options = []
        expected = 'A'
        while (i < len(items) and items[i][0] == '__choice__'
               and items[i][1]['letter'] == expected):
            opt = items[i][1]
            body, i = parse_seq(i + 1)
            options.append((opt, body))
            expected = chr(ord(expected) + 1)
        if i < len(items) and items[i][0] == '__converge__':
            i += 1
        else:
            print("WARNING: Extended 块内嵌套选项缺少 【选项分线到此结束】，"
                  "已按当前收集到的选项收束")
        return options, i

    seq, i = parse_seq(0)
    while i < len(items):
        kind = items[i][0]
        if kind == '__converge__':
            print("WARNING: Extended 块内出现多余的 【选项分线到此结束】，已忽略")
            i += 1
        elif kind == '__choice__':
            print(f"WARNING: 选项 {items[i][1]['letter']}： 前面没有对应的 A： 开头，"
                  "该行按丢弃处理")
            i += 1
        else:
            more, i = parse_seq(i)
            seq.extend(more)
    return seq


def _collect_cond_prefixes(seq, acc):
    """递归收集树里所有被条件标记（仅在观看过X后出现 / 双态显示）引用的前缀。"""
    for item in seq:
        if item[0] == '__menu__':
            for opt, body in item[1]:
                if opt.get('cond_seen'):
                    acc.add(opt['cond_seen'])
                if opt.get('cond_variant'):
                    acc.add(opt['cond_variant'])
                _collect_cond_prefixes(body, acc)


def emit_extended_choice_block(collected, output, indent, large=False, centered=False):
    """含选项的 Extended 块总入口：组树 → 递归生成。"""
    seq = _build_choice_tree(collected)
    _COND_SEEN_PREFIXES.clear()
    _collect_cond_prefixes(seq, _COND_SEEN_PREFIXES)
    _emit_choice_seq(seq, output, indent, large, centered, started=False)


def _emit_choice_seq(seq, output, indent, large, centered, started):
    """按序生成：普通条目交给 emit_extended_segments（带续接状态），
    菜单递归生成。返回结束时的续接状态。"""
    run = []
    for item in seq:
        if item[0] == '__menu__':
            if run:
                started = emit_extended_segments(run, output, indent, large=large,
                                                 centered=centered, continued=started)
                run = []
            if not started:
                print("WARNING: Extended 块内的菜单前没有任何正文，"
                      "菜单标题的 extend 将无 say 可接")
            started = _emit_block_menu(item[1], output, indent, large, centered)
        else:
            run.append(item)
    if run:
        started = emit_extended_segments(run, output, indent, large=large,
                                         centered=centered, continued=started)
    return started


def _emit_block_menu(options, output, indent, large, centered):
    """生成一个（可嵌套的）菜单。带循环选项时把 menu 包进局部 label，
    循环分支末尾 jump 回来重新弹出。返回 True（菜单不清框，续接状态保持）。"""
    _EXT_MENU_COUNTER[0] += 1
    n = _EXT_MENU_COUNTER[0]
    has_loop = any(opt['loop'] for opt, _ in options)
    menu_indent = indent
    if has_loop:
        # ★label 必须以下划线开头★ —— 普通 label（含 .local）会重置翻译上下文，
        # 让它之后所有对话的翻译 ID 换基底，孤儿化整段既有英文翻译；
        # 下划线开头的 label 不参与翻译 ID（call...from _xxx 同理），因此安全。
        output.append(f'{indent}label _extmenu_{n}:')
        menu_indent = indent + '    '
    # 出选项时把大文本框整个藏起来（无标题菜单 + window hide 溶解），选项走普通
    # 的屏幕居中样式 —— 堆了多行的框和选项文字必然打架，躲位置治不了本。
    # 选完后：window show 溶解回大文本框 → 先把玩家的选择以 "——选项文本" 回显
    # 进框，再继续该分支的正文。溶解让文字↔选项的来回切换不生硬。
    output.append(f'{menu_indent}window hide Dissolve(.25)')
    output.append(f'{menu_indent}menu:')
    expanded = []
    for opt, body in options:
        if opt.get('cond_variant'):
            # 条件双态：拆成两条互斥条件的 menu 项（看过→前者，没看过→后者）。
            # id/数值/分支相同，玩家任何时刻只见其一；分支正文原样生成两份。
            expanded.append(({**opt, 'cond_seen': opt['cond_variant']}, body))
            expanded.append(({**opt, 'text': opt['alt_text'],
                              'cond_unseen': opt['cond_variant']}, body))
        else:
            expanded.append((opt, body))
    for opt, body in expanded:
        # 条件出现：仅在被引用选项已看过（选过）时出现；cond_unseen 反之。
        cond = ''
        if opt.get('cond_seen'):
            cond = f' if "{opt["cond_seen"]}" in interro_seen'
        elif opt.get('cond_unseen'):
            cond = f' if "{opt["cond_unseen"]}" not in interro_seen'
        # 带数值的选项：menu 参数捎上 (id, 风味)，第 2 轮起已选项 hover 上色。
        oid = f'm{n}{opt["letter"]}'
        flavor = (_INTERRO_FLAVOR.get(opt['stats'][0][0])
                  if opt.get('stats') else None)
        args = f' (interro=("{oid}", "{flavor}"))' if flavor else ''
        output.append(f'{menu_indent}    "{escape_quotes(opt["text"])}"{args}{cond}:')
        inner = menu_indent + '        '
        if flavor:
            output.append(f'{inner}$ interro_picked.add("{oid}")')
        if opt['madness']:
            output.append(f'{inner}$ madness += {opt["madness"]}')
        # 问询段数值：只加一次的选项包进 interro_once 守卫（id = 菜单号+字母）。
        if opt.get('stats'):
            if opt.get('once'):
                once_id = f'm{n}{opt["letter"]}'
                output.append(f'{inner}if "{once_id}" not in interro_once:')
                for var, amt in opt['stats']:
                    output.append(f'{inner}    $ {var} += {amt}')
                output.append(f'{inner}    $ interro_once.add("{once_id}")')
            else:
                for var, amt in opt['stats']:
                    output.append(f'{inner}$ {var} += {amt}')
        # 被条件标记引用的选项：选中即记录（供后续菜单的条件项判断）。
        for prefix in sorted(_COND_SEEN_PREFIXES):
            if opt['text'].startswith(prefix):
                output.append(f'{inner}$ interro_seen.add("{prefix}")')
        # 不发 window show —— 它会经 empty_window 用默认 narrator 的 say 屏幕垫场，
        # 把底部渐变 scrim 闪出来（"选完下半屏黑一下"）。改为置 _intro_fade_pending，
        # 让大文本框自己的 say_intro_fade 在重新挂载的这一次淡入（机制见 screens.rpy）。
        output.append(f'{inner}$ _intro_fade_pending = True')
        # 回显玩家的选择（——选项文本）。与分支第一条正文并进同一条 extend
        # （中间字面 \n 换行），一次点击同时看到回显和响应，不多耗一次点击。
        # 第一条不是纯正文时（如直接嵌套菜单）回显才单独成句。
        echo = '——' + opt['text']
        body = list(body)
        if body and body[0][0] is None:
            body[0] = (None, echo + chr(92) + 'n' + body[0][1])
        else:
            output.append(f'{inner}extend {format_dialogue(chr(92) + "n" + echo)}')
        _emit_choice_seq(body, output, inner, large, centered, started=True)
        if opt['loop']:
            output.append(f'{inner}## 重新展示本次选择')
            output.append(f'{inner}jump _extmenu_{n}')
    return True


def convert_content_line(line, indent="    ", use_large_textbox=False):
    """Convert a single content line to Ren'Py format"""
    line = line.strip()

    if not line:
        return None

    # Skip convergence marker (handled separately)
    if '选项分线到此结束' in line:
        return None

    # Skip conditional C choice marker (handled in convert_route)
    if is_conditional_c_marker(line):
        return None

    # Skip large textbox markers (handled in convert_route)
    if '大文本框开始' in line or '大文本框结束' in line:
        return None

    # Route transition screens 【展示X周目分屏"标题"】
    if '展示' in line and '周目分屏' in line:
        # Extract title between quotes using flexible matching
        import re as re2
        title_match = re2.search(r'分屏.(.+?).】$', line)
        if title_match:
            title = title_match.group(1)
            # _() wraps the title for translation so it changes with language
            return f'{indent}call screen route_title(_("{title}"))'

    # Music trigger markers 【音乐：scene_id】
    music_match = re.match(r'^【音乐[：:](.+?)】$', line)
    if music_match:
        scene_id = music_match.group(1).strip()
        return f'{indent}$ set_scene_music("{scene_id}")'

    # Music stop markers 【音乐停】 / 【音效和音乐停】
    # fadeout 3.0：让音乐柔和淡出而非戛然而止（1.0 太突兀）。
    # stash_music_pos() 必须在 stop 之前 —— 它记下停下那一刻的播放位置，供后面标了
    # "resume" 的场景接着放（route1_horror3：「从上次音乐停的位置继续，不要重头开始」）。
    #
    # 必须整行严格匹配标记本身。这里原来是 `'音乐停' in line` 的子串判断，而剧本里
    # 【场景音乐参考：N2-14 - 从上次音乐停的位置继续播放，不要重头开始】 这句说明性
    # 注释也含"音乐停"三个字 —— 子串匹配会在那儿凭空停一次音乐，并且因为那一刻已经
    # 没有音乐在播，stash 到的位置会被清成 0，恰好毁掉这句话要求的"接着放"。
    # 说明性注释里出现控制词是迟早的事，判断得盯着标记的形状，不是它的字面。
    if re.match(r'^【(?:音效和)?音乐停】$', line):
        return (f'{indent}$ stash_music_pos()\n'
                f'{indent}$ current_music_scene = None\n'
                f'{indent}stop music fadeout 3.0')

    # Music fade-out marker 【音乐开始fade out】：当前音乐缓缓淡出（进入幻视前的留白）。
    # current_music_scene 置 None，淡出后存档/读档不会把这段音乐恢复回来。
    # 时长 4s：调这里改淡出快慢（后面 set_scene_music 切幻视曲时会接管交叉淡入）。
    if '音乐开始fade out' in line:
        return (f'{indent}## 音乐开始 fade out\n'
                f'{indent}$ current_music_scene = None\n'
                f'{indent}stop music fadeout 4.0')

    # 【音效完成后再执行转场】：显式阻塞到当前音效播完，再放行后面的语句。
    # 默认规则是"音效与转场同帧触发、只在下一句正文前补等待"（见 insert_sfx_waits），
    # 这个标记用于剧本要求"声音先演完、画面再动"的地方。必须在下面的 音效 cue
    # 分支之前判断 —— 它同样含"音效"两个字，会被那条正则误吞成纯注释。
    if re.match(r'^【音效(?:完成|播完)后.*】$', line):
        return f'{indent}## {line.strip("【】")}\n{indent}$ wait_sfx()'

    # Sound-effect markers 【…音效：filename】 -> one-shot on the sound channel.
    # Convention: the marker names the clip explicitly (base name, no extension)
    # of a file in audio/sfx/ (all .wav). `play sound` is async and non-blocking,
    # so an SFX can sync with the transition that immediately follows it, and the
    # sound mixer ("音效音量") controls its volume. A 音效 marker without a named
    # file falls through to a plain comment (no sound) by design.
    sfx_match = re.match(r'^【(.*?音效)[：:]\s*(.+?)\s*】$', line)
    if sfx_match:
        sfx_label = sfx_match.group(1)
        sfx_name = sfx_match.group(2).strip()
        sfx_path = resolve_sfx(sfx_name, sfx_label)
        return f'{indent}## {sfx_label}：{sfx_name}\n{indent}$ play_sfx("{sfx_path}")'

    # 【…音效】（只写了声音是什么、没写文件名）-> 查 SFX_CUES 决定播什么、走哪条声道。
    # 查不到的（素材还没做的 cue）落到下面的 stage-direction 分支，退化成纯注释。
    cue_match = re.match(r'^【(.*?音效.*?)】$', line)
    if cue_match:
        cue = cue_match.group(1)
        # 按键长从长到短匹配：'心跳音效' 是 '心跳音效渐强'/'心跳音效恢复' 的子串，
        # 呼吸那几个也是一样的包含关系。谁更具体谁优先，不能靠字典顺序碰运气。
        for key in sorted(SFX_CUES, key=len, reverse=True):
            if key not in cue:
                continue
            cfg = SFX_CUES[key]
            head = f'{indent}## {cue}\n'
            # 'call' = 交给 variables.rpy 里的函数自己决定放什么
            # （glitch 要在运行时随机挑切片，转换期定不下来）。
            if 'call' in cfg:
                return head + f'{indent}$ {cfg["call"]}'
            ch = cfg.get('channel', 'ambient')
            # 'stop' = 停掉这条铺底声道
            if cfg.get('stop'):
                return head + f'{indent}$ stop_ambient(channel="{ch}")'
            # 'swell' = 不换素材，只把音量推上去（同一段声音逐渐变响）
            if 'swell' in cfg:
                return head + (f'{indent}$ swell_ambient({cfg["swell"]}, '
                               f'channel="{ch}", swell={cfg.get("swell_time", 8.0)})')
            cue_path = resolve_sfx(cfg['file'], cue)
            # 'to' = 只播开头这么多秒（Ren'Py 音频前缀），把长素材截成一击。
            if 'to' in cfg:
                cue_path = '<to %s>%s' % (cfg['to'], cue_path)
            if cfg.get('ambient'):
                args = [f'"{cue_path}"', f'channel="{ch}"']
                if 'fadein' in cfg:
                    args.append(f'fadein={cfg["fadein"]}')
                if 'level' in cfg:
                    args.append(f'level={cfg["level"]}')
                return head + f'{indent}$ play_ambient({", ".join(args)})'
            return head + f'{indent}$ play_sfx("{cue_path}")'

    # Demo 结尾 【fade out屏幕之后，回主菜单】：图像与音乐一起淡出、黑屏留白，
    # 随后 main() 追加的 demo_reboot_after_route() reboot 回主菜单。音乐一起淡出
    # （而非硬切），是为了衔接主菜单曲；current_music_scene 置 None 以免读档恢复。
    if 'fade out' in line and '回主菜单' in line:
        return (f'{indent}## fade out 屏幕（图像+音乐+环境音）之后，reboot 回主菜单\n'
                f'{indent}$ current_music_scene = None\n'
                f'{indent}$ stop_all_ambient(2.0)\n'
                f'{indent}stop music fadeout 2.0\n'
                f'{indent}scene black with fade_to_black_long\n'
                f'{indent}$ hard_pause(1.0)')

    # 镜头缓移标记 【镜头：左下缓移右上】（可选 ，5秒 / ，变焦1.1）。
    # 写在【转场：…】前一行。只登记不发码——camera 块由下一个 _emit_scene 在
    # scene 语句前发出（详见 _CAMERA_PAN_PENDING 上方的说明）。
    cam_match = re.match(
        r'^【镜头[：:](%s)缓移(%s)'
        r'(?:[，,]\s*([\d.]+)秒)?(?:[，,]\s*变焦([\d.]+))?】$'
        % (_CAMERA_CORNER_ALT, _CAMERA_CORNER_ALT), line)
    if cam_match:
        global _CAMERA_PAN_PENDING
        frm, to, secs, zoom = cam_match.groups()
        _CAMERA_PAN_PENDING = {
            'from': frm, 'to': to,
            'secs': secs or _CAMERA_DEFAULT_SECS,
            'zoom': zoom or _CAMERA_DEFAULT_ZOOM,
        }
        return f'{indent}## 镜头标记：{frm}缓移{to}（于下个转场生效）'

    # 走路进场标记（与店员进场同模式）：
    #   【王霜走路进场，<姿势>，<表情>】 → 立即以该姿势入场开走（可先于台词）；
    #   【王霜走路进场】                → 等下一条立绘 show 时才入场开走。
    # 挂 ws_desert_walk（左缘外走到画面偏右站定，见 sprites.rpy）。
    # 手感参数改 WS_WALK_* 常量。
    walk_match = re.match(
        rf'^【(?:王霜走路进场|{WS_WALK_INLINE_MARK})(?:[，,](.+))?】$', line)
    if walk_match:
        global _SPRITE_WALK_PENDING
        _SPRITE_WALK_PENDING = True
        rest = walk_match.group(1)
        if rest:
            code = emit_sprite_change(rest.strip(), indent)
            if code:
                return f'{indent}## 王霜走路进场\n{code}'
            # 姿势解析不出素材：退化成"下一条立绘生效"（pending 已置位）
        return f'{indent}## 王霜走路进场（下一条立绘生效）'

    # 跑动 sequence（尸首追逐段）：【跑动sequence开始[，并锁操作N秒]】起跑 /
    # 【跑动sequence结束】收——溶解回静止沙漠。单背景奔跑错觉（bg_desert_run/
    # run2，光流 shader + 颠簸 ATL，见 placeholder.rpy 和 shaders.rpy desert_run）。
    # 第二次及以后的 开始 用更狂的 run2（配剧本侧心跳渐强的递进）。锁操作 =
    # hard_pause，让起跑演出播完才收点击。走 _emit_scene 复用立绘清理/镜头复位
    # （scene 清立绘 = 【王霜和尸首退场】所要的效果，那行标记本身保持注释）。
    # 【转头】：只登记，不出画面 —— 甩头转场由下面的跑动 sequence 起手消费。
    if line == '【转头】':
        _HEAD_TURN['pending'] = True
        _HEAD_TURN['count'] += 1
        return f'{indent}## 转头（跑动起手换用 whip_pan 甩头转场）'

    run_start = re.match(r'^【跑动sequence开始(?:[，,]\s*并?锁操作([\d.]+)秒)?】$', line)
    if run_start:
        _RUN_SEQ_COUNT[0] += 1
        bg = 'bg_desert_run' if _RUN_SEQ_COUNT[0] == 1 else 'bg_desert_run2'
        run_lines = [f'{indent}## {line.strip("【】")}']
        if _HEAD_TURN['pending']:
            _HEAD_TURN['pending'] = False
            whip_dir = 1.0 if _HEAD_TURN['count'] % 2 else -1.0
            transition = f'whip_pan(direction={whip_dir})'
            # 先就地排掉 pending 的镜头设/复位：whip_pan 只渲染新画面、首帧即
            # 最大模糊，镜头跳变不可见 —— 不需要 _emit_scene 的黑场三段式
            # （那会把甩头转场整个吃掉，换成 cam_fade_out/in）。
            _emit_camera_at_switch(run_lines, indent)
        else:
            transition = 'scene_dissolve'
        _emit_scene(run_lines, indent, '银白色沙漠跑动', bg, transition)
        if run_start.group(1):
            run_lines.append(f'{indent}$ hard_pause({run_start.group(1)})')
        return '\n'.join(run_lines)
    if line == '【跑动sequence结束】':
        run_lines = [f'{indent}## 跑动sequence结束']
        _emit_scene(run_lines, indent, '银白色沙漠', 'bg_desert', 'scene_dissolve')
        return '\n'.join(run_lines)

    # Pause markers 【停顿：N】/【等待N秒】 -> `pause N` (N is seconds, float ok)
    # Use sparingly — for breathing room before a scene's first line, etc.
    pause_match = _match_pause(line)
    if pause_match:
        return f'{indent}pause {pause_match}'

    # 场景滤镜 【场景滤镜：黑红混沌，逐渐加深】/【停止场景滤镜：…】。
    # 滤镜住在独立的 "chaos" 图层上（scene 只清 master，中途的转场/跑动 sequence
    # 冲不掉它），"逐渐加深"由 chaos_vignette_fx 的 ATL 自己完成 —— show 的那一刻
    # 强度为 0，所以起点不需要转场。停止标记按剧本约定写在转场之前 —— 雾先在
    # 当前画面上用 1.5 秒 dissolve 退散，然后画面才切走（"滤镜先停，再转场"）。
    # 实现见 shaders.rpy「黑红混沌 vignette」一节。未知滤镜名退化为注释并告警。
    filter_match = re.match(r'^【(停止)?场景滤镜[：:](.+?)】$', line)
    if filter_match:
        stopping, filter_name = filter_match.groups()
        if '黑红混沌' not in filter_name and '红黑' not in filter_name:
            print(f"WARNING: 未实现的场景滤镜 '{filter_name}' —— 仅注释")
            return f'{indent}## {line.strip("【】")}'
        if stopping:
            return (f'{indent}## 停止场景滤镜：{filter_name}\n'
                    f'{indent}hide chaos_vignette onlayer chaos\n'
                    f'{indent}with Dissolve(1.5)')
        return (f'{indent}## 场景滤镜：{filter_name}\n'
                f'{indent}show chaos_vignette onlayer chaos')

    # (Removed 【文本框淡入】 marker — `window show TRANSITION` does not affect
    # custom say screens, which is what this project uses. Fade-in is now
    # handled by transforms on large_say/centered_say/centered_large_say
    # directly, so every time those screens first appear they ease in.)

    # Scene transition markers 【转场：场景名。场景描述】
    transition_match = re.match(r'^【转场[：:](.+?)】$', line)
    if transition_match:
        content = transition_match.group(1).strip()
        # Split by first Chinese period only (。). Not ASCII period, because
        # scene names may legitimately contain `.` (e.g., 甜品店对视6.51).
        # Convention in the raw script is to always use 。 as the name/description
        # separator, so this is safe.
        period_match = re.search(r'。', content)
        if period_match:
            scene_name = content[:period_match.start()].strip()
            scene_desc = content[period_match.end():].strip()
        else:
            # No period - entire content is scene name, no description
            scene_name = content
            scene_desc = ""

        # Generate the comment and the background scene. Scenes without
        # dedicated art fall back to a plain black background.
        output_lines = [f'{indent}## 转场：{scene_name}']
        bg_image = SCENE_BG_MAP.get(scene_name, 'black')
        global _PROLOGUE_FIRST_TRANSITION_PENDING
        if _PROLOGUE_FIRST_TRANSITION_PENDING:
            # Entering the game from the main menu: the water drop's ripple
            # wipes this first scene in from the centre.
            transition = PROLOGUE_ENTRY_TRANSITION
            _PROLOGUE_FIRST_TRANSITION_PENDING = False
        elif scene_name in SCENE_TRANSITIONS:
            transition = SCENE_TRANSITIONS[scene_name]
        elif scene_name in NO_TRANSITION_SCENES:
            transition = 'None'
        elif scene_name in CROSS_DISSOLVE_SCENES:
            transition = 'scene_dissolve'
        else:
            transition = 'scene_soft'
        _emit_scene(output_lines, indent, scene_name, bg_image, transition)
        return '\n'.join(output_lines)

    # 【电视机关机转场】-> CRT 断电：画面纵向塌成亮线、横向收成光点、熄灭。
    # 变换作用在整个 master 图层上，所以塌的是画面本身而不是盖一层遮罩。
    #
    # ★与音效严格同步★：剧本把 【电视机关机音效】 写在这一行前面，两条语句之间
    # 没有任何阻塞，所以在同一帧发出 —— 音画起点对齐到毫秒级。之后的 0.80s 时间轴
    # 是照着音效波形逐段对的（见 transitions.rpy 的 crt_shutdown 注释）。
    # CRT_SHUTDOWN_SECONDS 必须和那条 transform 的总时长一致，改一个就要改另一个。
    #
    # 结尾的 scene black 是必须的：动画结束时图层已经 alpha 0（看不见），此时把内容
    # 换成纯黑，再复位图层变换 —— 否则一复位就会把塌陷前的旧画面整张闪回来一帧。
    if line.strip() == '【电视机关机转场】':
        return (f'{indent}## 电视机关机转场（CRT 断电，与关机音效同帧触发）\n'
                f'{indent}show layer master at crt_shutdown\n'
                f'{indent}$ hard_pause({CRT_SHUTDOWN_SECONDS})\n'
                f'{indent}scene black with None\n'
                f'{indent}show layer master')

    # Bad End markers - unlock ending and return to main menu (MUST be before general stage direction check)
    bad_end_match = re.match(r'^【(Bad End \d+[：:].*)】$', line)
    if bad_end_match:
        end_text = bad_end_match.group(1)
        # Extract the bad end number
        num_match = re.search(r'Bad End (\d+)', end_text)
        end_num = num_match.group(1) if num_match else "1"
        return f"{indent}## {end_text}\n{indent}$ unlock_ending(\"bad_end_{end_num}\")\n{indent}return"

    # Normal End marker - unlock and return to main menu
    if re.match(r'^【Normal End[：:：](.*)】$', line) or line.strip() == '【Normal End】':
        return f"{indent}## Normal End\n{indent}$ unlock_ending(\"normal_end\")\n{indent}return"

    # Happy End marker - unlock and return to main menu
    if re.match(r'^【Happy End[?？]?】$', line):
        return f"{indent}## Happy End\n{indent}$ unlock_ending(\"happy_end\")\n{indent}return"

    # True End marker - unlock and return to main menu
    if re.match(r'^【True End[：:：]?(.*)】$', line) or line.strip() == '【True End】':
        return f"{indent}## True End\n{indent}$ unlock_ending(\"true_end\")\n{indent}return"

    # 店员入/退场独立标记（见 _CLERK_CFG 上方的说明）。必须先于通用舞台提示注释。
    clerk_marker = re.match(r'^【(店员\d?)\s*(入场|进场|退场)(?:[，,](.+))?】$', line)
    if clerk_marker:
        name, action, rest = clerk_marker.groups()
        clerk = _clerk_id(name)
        head = f'{indent}## {line.strip("【】")}'
        if action == '退场':
            code = emit_clerk_exit(clerk, indent)
            return head + ('\n' + code if code else '')
        if rest:
            # 【店员N进场，<姿势>，<表情>】：带姿势的立即入场
            parsed = parse_sprite_marker(rest.strip())
            if parsed:
                code = emit_clerk_show(clerk, indent, pose=parsed[0], expr=parsed[1])
                return head + ('\n' + code if code else '')
            print(f"WARNING: 店员进场标记无法解析姿势/表情：{line} —— 仅注释")
        # 无姿势的【店员入场】：仅注释，下一句该店员台词时自动入场
        return head

    # Stage direction (standalone) -> comment, plus an FX transition when
    # the cue is a genuine visual dramatic beat. Audio cues (音效) are
    # comment-only - a sound effect should not shake the screen.
    stage_match = re.match(r'^【(.+?)】$', line)
    if stage_match:
        text = stage_match.group(1)
        # 【glitch消失】：除了画面特效，还要把当前 glitch 立绘就地切回干净版 ——
        # 剧本要 glitch 即刻停，不能挂到下一条立绘标记（中间隔着别人的台词）。
        if 'glitch消失' in text:
            out = f"{indent}## {text}\n{indent}with glitch_fx()"
            unglitch = emit_sprite_unglitch(indent)
            if unglitch:
                out += '\n' + unglitch
            return out
        # 【王霜面部glitch移除】：只把当前立绘的脸换回干净版（master 层溶解）。
        # 与【glitch消失】的区别：不放全屏 glitch_fx —— 安静地恢复，不搞动静。
        if '面部glitch移除' in text:
            out = f"{indent}## {text}"
            unglitch = emit_sprite_unglitch(indent)
            if unglitch:
                out += '\n' + unglitch
            else:
                print(f"WARNING: 【{text}】处没有 glitch 立绘在场 —— 仅注释")
            return out
        if '音效' not in text:
            for keyword, fx in SPECIAL_FX:
                if keyword in text:
                    return f"{indent}## {text}\n{indent}with {fx}"
        return f"{indent}## {text}"

    # Character name to variable mapping（单一来源见模块级 CHAR_VAR_MAP）
    char_var_map = CHAR_VAR_MAP
    char_pattern = CHAR_PATTERN

    # Character dialogue with one or more leading 【…】 markers（表情 / 小字 / 道具提示）。
    # 一句可带多个 marker，如 王霜【小声嘀咕】【小字】：…（既切表情又缩小字体）。
    char_action_match = re.match(rf'^({char_pattern})((?:【.+?】)+)[：:](.*)$', line)
    if char_action_match:
        char_name = char_action_match.group(1)
        dialogue = char_action_match.group(3).strip()
        char_var = char_var_map[char_name]
        is_clerk = '店员' in char_name
        pre = []   # 表情切换 / 注释，放在台词前
        markers = re.findall(r'【(.+?)】', char_action_match.group(2))
        # 行内走路标记：走路窗口的别名。★必须先于同行姿势标记置 pending★——
        # 这样本行的立绘 show 直接挂 ws_desert_walk 入场开走，而不是先按静态
        # 摆位站定。（global 声明在上方 walk_match 分支，同函数共享。）
        if WS_WALK_INLINE_MARK in markers and not is_clerk:
            _SPRITE_WALK_PENDING = True
        for m in markers:
            if m == WS_WALK_INLINE_MARK:
                pre.append(f'{indent}## {m}（走路进场，挂在本行立绘 show 上）')
                continue
            if m == '小字':
                # 把 【小字】 放回台词开头，交给 apply_small_text 缩小到行尾。
                dialogue = '【小字】' + dialogue
                continue
            if m == '小跳':
                # 立绘原地轻跳（跟在姿势/表情标记后，见 emit_sprite_hop）。
                code = (emit_clerk_hop(_clerk_id(char_name), indent) if is_clerk
                        else emit_sprite_hop(indent))
                pre.append(f'{indent}## 小跳' + ('\n' + code if code else ''))
                continue
            if is_clerk:
                # 店员台词的标记：立绘归店员系统（as tag 独立于主立绘）。
                parsed = parse_sprite_marker(m)
                if parsed:
                    code = emit_clerk_show(_clerk_id(char_name), indent,
                                           pose=parsed[0], expr=parsed[1])
                elif m == '面无表情' or m in SPRITE_EXPR_ATTRS:
                    # 仅【表情】：姿势沿用上次（如 王霜（店员2）【默认】）
                    code = emit_clerk_show(_clerk_id(char_name), indent, expr=m)
                else:
                    code = None   # 位置说明（出现在屏幕右边 等）→ 注释
                pre.append(code if code else f'{indent}## {m}')
                continue
            coll = re.search(r'三人集体(.+)$', m)
            if coll:
                # 【本人和店员、店员2，三人集体<表情>】：主立绘 + 在场店员齐换
                pre.append(emit_collective_expr(coll.group(1).strip(), indent))
                continue
            swap = emit_expression_change(m, indent)   # 已知表情 → master 层溶解切差分
            pre.append(swap if swap else f'{indent}## {m}')  # 否则当舞台提示注释
        # 店员开口但立绘还没上（标记都不含姿势/表情时）：按记忆的姿势自动入场
        if is_clerk and not _clerk_state(_clerk_id(char_name))['visible']:
            code = emit_clerk_show(_clerk_id(char_name), indent)
            if code:
                pre.append(code)
        return '\n'.join(pre + [emit_char_dialogue_inline(char_var, dialogue, indent)])

    # Character dialogue (simple)
    char_match = re.match(rf'^({char_pattern})[：:](.*)$', line)
    if char_match:
        char_name = char_match.group(1)
        dialogue = char_match.group(2).strip()
        char_var = char_var_map[char_name]
        pre = []
        # 店员开口但立绘还没上：自动入场（姿势/表情沿用上次）。
        if '店员' in char_name and not _clerk_state(_clerk_id(char_name))['visible']:
            code = emit_clerk_show(_clerk_id(char_name), indent)
            if code:
                pre.append(code)
        return '\n'.join(pre + [emit_char_dialogue_inline(char_var, dialogue, indent)])

    # Section headers
    if re.match(r'^[一二三四五六七八九十]+周目', line):
        return f"\n## {line}\n"

    # Narrative text - choose narrator based on mode
    _clerk_close_enter_window()   # 旁白同样是交互边界（见 emit_char_dialogue）
    if use_large_textbox:
        return f'{indent}large_narrator {format_dialogue(line)}'
    return f'{indent}{format_dialogue(line)}'


def is_choice_a(line):
    return bool(re.match(r'^A[：:]\s*.+$', line.strip()))

def is_choice_b(line):
    return bool(re.match(r'^B[：:]\s*.+$', line.strip()))

def is_choice_c(line):
    return bool(re.match(r'^C[：:]\s*.+$', line.strip()))

def is_conditional_c_marker(line):
    """Check for the conditional C choice marker"""
    return '当 Normal End 和 Happy End' in line and '出现选项C' in line

def is_convergence(line):
    return '选项分线到此结束' in line

def parse_choice(line):
    """Parse choice line, returns (text, madness_add, action)
    action can be: None, 'continue', or 'return_to_menu'
    """
    match = re.match(r'^[ABC][：:]\s*(.+)$', line.strip())
    if match:
        text = match.group(1).strip()
        madness_add = 0
        action = None

        # Check for special action tags
        if '【游戏继续】' in text:
            action = 'continue'
            text = text.replace('【游戏继续】', '').strip()
        elif '【回到主菜单】' in text:
            action = 'return_to_menu'
            text = text.replace('【回到主菜单】', '').strip()

        # Check for madness modifier
        madness_match = re.search(r'[（(]madness\s*\+\s*(\d+)[）)]', text)
        if madness_match:
            madness_add = int(madness_match.group(1))
            text = re.sub(r'[（(]madness\s*\+\s*\d+[）)]', '', text).strip()

        return text, madness_add, action
    return None, 0, None


def _lr_transform(line):
    """「左右分开对齐」块内的行首对齐标记：
    【左】= 默认左对齐，纯剥前缀（正文与历史版本逐字节一致，不动翻译 ID）；
    【右】= 整行包成 {r}…{/r}，运行时 custom text tag 把该行整体右对齐
    （见 screens.rpy _lr_right_text_tag）。无前缀的行（——录入中—— 等系统行）
    保持原样走左对齐。"""
    if line.startswith('【左】'):
        return line[3:].lstrip()
    if line.startswith('【右】'):
        return '{r}' + line[3:].lstrip() + '{/r}'
    return line


def collect_accumulating_block(lines, start_i, end_line, marker_end, use_large=False, centered=False,
                               lr=False):
    """
    Collect lines between markers and output them with extend for accumulating display.
    First line is normal dialogue, subsequent lines use extend to append.
    centered=True：居中累积框（centered_say），用于 demo 结尾谢幕卡等。
    lr=True：开始标记带「左右分开对齐」，行首【左】/【右】决定该行对齐（见 _lr_transform）。
    Returns (output_lines, new_index)
    """
    # Character name to variable mapping（单一来源见模块级 CHAR_VAR_MAP）
    char_var_map = CHAR_VAR_MAP
    char_pattern = CHAR_PATTERN

    collected = []
    i = start_i

    while i < end_line and i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # Check for end marker
        if marker_end in line:
            break

        # 左右分开对齐：行首【左】/【右】标记先行消化（【右】行包 {r}…{/r}），
        # 必须在下面所有解析之前——否则会被当成整行【】舞台提示静默吃掉。
        if lr:
            line = _lr_transform(line)

        # 嵌套选项（Extended 块内，见 emit_extended_choice_block）：
        # 汇合标记必须先于下面通用的【】跳过截获，否则会被静默吃掉。
        if is_convergence(line):
            collected.append(('__converge__', None))
            continue
        block_choice = _parse_block_choice(line)
        if block_choice:
            collected.append(('__choice__', block_choice))
            continue

        # 问询段逻辑判断行（精神状态/人格特质/污染进程/建议执行：…【条件】…）：
        # 原文是"罗列全部候选+条件"的规则表，运行时每类只展示一个结论 ——
        # 收成 __eval__，emit 阶段换成 [interro_*!t] 插值（见 emit_extended_segments）。
        # 条件表新版用全角圆括号（稳定（仅平稳>1）/…），旧版用【】——两种都认。
        eval_match = re.match(r'^(精神状态|人格特质|污染进程|建议执行)：', line)
        if eval_match and ('【' in line or '（' in line):
            collected.append(('__eval__', (eval_match.group(1), line)))
            continue

        # Check for scene transition markers - these need to be output before dialogue continues
        transition_match = re.match(r'^【转场[：:](.+?)】$', line)
        if transition_match:
            content = transition_match.group(1).strip()
            # Split on Chinese period only (same convention as convert_content_line)
            period_match = re.search(r'。', content)
            if period_match:
                scene_name = content[:period_match.start()].strip()
                scene_desc = content[period_match.end():].strip()
            else:
                scene_name = content
                scene_desc = ""
            # Mark as scene transition (special marker)
            collected.append(('__transition__', (scene_name, scene_desc)))
            continue

        # 块内停顿（【停顿：N】/【等待N秒】，如 地下5→等待3秒→地下6）：
        # 必须先于下面的舞台提示兜底，否则被静默吃掉、两个转场贴在一起。
        pause_secs = _match_pause(line)
        if pause_secs:
            collected.append(('__pause__', pause_secs))
            continue

        # Character dialogue with one or more leading 【…】（块内也可能出现，如夏日对视
        # 那段 Extended 里的 王霜【面无表情】）。先于普通 char_match 判断。支持多 marker
        # （表情 + 小字）。
        char_action = re.match(rf'^({char_pattern})((?:【.+?】)+)[：:](.*)$', line)
        if char_action:
            char_var = char_var_map[char_action.group(1)]
            dialogue = char_action.group(3).strip()
            for m in re.findall(r'【(.+?)】', char_action.group(2)):
                if m == '小字':
                    dialogue = '【小字】' + dialogue
                else:
                    collected.append(('__expr__', m))
            collected.append((char_var, dialogue))
            continue

        # Character dialogue
        char_match = re.match(rf'^({char_pattern})[：:](.*)$', line)
        if char_match:
            char_name = char_match.group(1)
            dialogue = char_match.group(2).strip()
            char_var = char_var_map[char_name]
            collected.append((char_var, dialogue))
        else:
            # 块内的音频标记（音效 / 音乐）不能跟着普通舞台提示一起被丢掉。
            # 剧本会把 cue 写在文本框里（如 【心跳音效恢复】 就在 Extended 块的第一行），
            # 以前会被下面那句 skip 静默吃掉 —— 心跳再也回不到常速，而且不报任何错。
            # 交回 convert_content_line 处理，作为 __sfx__ 插进累积序列，
            # 真正的代码在 emit 阶段按当时的缩进生成。
            if (line.startswith('【') and line.endswith('】')
                    and ('音效' in line or '音乐' in line)):
                collected.append(('__sfx__', line))
                continue
            # Stage directions - skip
            if line.startswith('【') and line.endswith('】'):
                continue
            # Narration
            collected.append((None, line))

    if not collected:
        return [], i

    output = []
    indent = "    "

    # 问询段数值：块内含带数值标记的选项 → 桥段开头先清零全部 interro 计数
    # （疯狂 ≠ madness：疯狂只在本桥段内生效）。
    if any(k == '__choice__' and (v['stats'] or v['once'] or v['cond_seen'])
           for k, v in collected):
        output.append(f'{indent}$ interro_reset()')
    # 逻辑判断块：先算出四项唯一结论，再让 __eval__ 行插值展示。
    if any(k == '__eval__' for k, _ in collected):
        output.append(f'{indent}$ interro_evaluate()')

    # Extended 文本框（大/小）现在统一走同一段落、按标点逐次点击的分句逻辑。
    # 大文本框只是旁白用 large_narrator、屏幕用 large_say，分句规则完全一致。
    # 块内含选项行时走嵌套菜单路径（正文跨菜单续在同一个框里）。
    if any(k == '__choice__' for k, _ in collected):
        emit_extended_choice_block(collected, output, indent,
                                   large=use_large, centered=centered)
    else:
        stray = [it for it in collected if it[0] == '__converge__']
        if stray:
            print("WARNING: Extended 块内有 【选项分线到此结束】 但没有选项行，已忽略")
        collected = [it for it in collected if it[0] != '__converge__']
        emit_extended_segments(collected, output, indent, large=use_large, centered=centered)
    return output, i


def process_choice_content(content_lines, indent="            "):
    """
    Process content lines within a choice branch, handling Extended textbox markers.
    Returns list of output lines.
    """
    output = []
    i = 0

    while i < len(content_lines):
        line = content_lines[i].strip()
        i += 1

        if not line:
            continue

        # 右侧Split（右半屏分页）必须在普通 Split 之前判断（子串包含关系）
        if '右侧Split Extended大文本框开始' in line:
            output.append(f"{indent}## 右侧Split Extended大文本框开始 - 右半屏分页")
            rp_out, i = emit_rightpage_block(content_lines, i, len(content_lines), indent)
            output.extend(rp_out)
            output.append(f"{indent}## 右侧Split Extended大文本框结束")
            continue

        # Check for Split Extended大文本框 markers (左右分栏；必须在普通大文本框之前判断，
        # 因为 'Split Extended大文本框开始' 包含 'Extended大文本框开始' 子串)
        if 'Split Extended大文本框开始' in line:
            output.append(f"{indent}## Split Extended大文本框开始 - 左右分栏")
            split_out, i = emit_split_large_block(content_lines, i, len(content_lines), indent)
            output.extend(split_out)
            output.append(f"{indent}## Split Extended大文本框结束")
            continue

        # Check for Extended大文本框 markers（也走同段落标点分句，large=True）
        if 'Extended大文本框开始' in line:
            lr = '左右分开对齐' in line
            output.append(f"{indent}## Extended大文本框开始 - 大文本框分句")
            entries = []
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if 'Extended大文本框结束' in next_line:
                    break
                if not next_line:
                    continue
                if lr:
                    next_line = _lr_transform(next_line)
                if next_line.startswith('【') and next_line.endswith('】'):
                    continue
                entries.append((None, next_line))
            emit_extended_segments(entries, output, indent, large=True)
            output.append(f"{indent}## Extended大文本框结束")
            continue

        # Check for Extended文本框 markers (non-large)
        # All lines accumulate with extend after the first.
        # 【居中Extended文本框…】= 居中累积框（centered_say），如 demo 结尾谢幕卡。
        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            centered_box = '居中' in line
            label = '居中Extended文本框' if centered_box else 'Extended文本框'
            output.append(f"{indent}## {label}开始 - {'centered ' if centered_box else ''}accumulating textbox")
            # Character name to variable mapping（单一来源见模块级 CHAR_VAR_MAP）
            char_var_map = CHAR_VAR_MAP
            char_pattern = CHAR_PATTERN

            # 收集块内所有行，再交给 emit_extended_segments 做"同段落标点分句"
            # （point 4/6）；行内 【屏幕震动】保留在对话里由分句逻辑处理。
            entries = []
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if 'Extended文本框结束' in next_line:
                    break
                if not next_line:
                    continue
                if next_line.startswith('【') and next_line.endswith('】'):
                    continue
                char_match = re.match(rf'^({char_pattern})[：:](.*)$', next_line)
                if char_match:
                    entries.append((char_var_map[char_match.group(1)], char_match.group(2).strip()))
                else:
                    entries.append((None, next_line))
            emit_extended_segments(entries, output, indent, centered=centered_box)
            output.append(f"{indent}## {label}结束")
            continue

        # Check for 居中文本框 markers
        if '居中文本框开始' in line and '大字' not in line:
            output.append(f"{indent}## 居中文本框开始 - centered textbox")
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if '居中文本框结束' in next_line:
                    output.append(f"{indent}## 居中文本框结束")
                    break
                if not next_line:
                    continue
                output.append(f'{indent}centered_narrator {format_dialogue(next_line)}')
            continue

        # Check for 居中大字文本框 markers
        if '居中大字文本框开始' in line:
            output.append(f"{indent}## 居中大字文本框开始 - centered large font textbox")
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if '居中大字文本框结束' in next_line:
                    output.append(f"{indent}## 居中大字文本框结束")
                    break
                if not next_line:
                    continue
                output.append(f'{indent}centered_large_narrator {format_dialogue(next_line)}')
            continue

        # Check for 大文本框 markers (non-Extended, single line mode)
        if '大文本框开始' in line and 'Extended' not in line and '居中' not in line:
            output.append(f"{indent}## 大文本框开始")
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if '大文本框结束' in next_line and 'Extended' not in next_line and '居中' not in next_line:
                    output.append(f"{indent}## 大文本框结束")
                    break
                if not next_line:
                    continue
                # Skip stage directions
                if next_line.startswith('【') and next_line.endswith('】'):
                    converted = convert_content_line(next_line, indent)
                    if converted:
                        output.append(converted)
                    continue
                output.append(f'{indent}large_narrator {format_dialogue(next_line)}')
            continue

        # Regular content line
        converted = convert_content_line(line, indent)
        if converted:
            output.append(converted)

    return output


## 允许环境音上提越过的标记：淡出音乐、转场、以及普通舞台指示。
## 反过来说，遇到正文/选项/文本框边界/结局标记就停 —— 那些是段落骨架，
## 跨过去会打乱块结构或让声音出现在错误的段落里。
_HOIST_BLOCKERS = ('文本框', '选项', '音乐：', '展示', 'Bad End', 'Normal End',
                   'Happy End', 'True End', '回主菜单')


def hoist_ambient_cues(lines):
    """把环境音铺底的 cue 上提到它所属的这一段转场之前。

    为什么需要：铺底是"场所本身的声音"，玩家进这个场所时它就该在了。但剧本里
    自然的写法是 【音乐停】→【转场：银白色沙漠】→【沙漠长风音效】，按字面顺序生成
    出来是这样的 ——

        stop music fadeout 3.0          # 非阻塞，音乐开始 3 秒淡出
        scene bg_desert with scene_soft # ★阻塞★，转场演完才往下走（1~2 秒）
        $ play_ambient(...)             # 到这儿才起，再 2 秒淡入

    结果风声完全建立起来时音乐早没了，听感是"音乐先没，过一会儿才刮起风"，
    而不是"风一直在，音乐从风里退出去"。关键在那个 with 是阻塞的 —— 只把
    fadeout 调长没用。所以在转换前把 cue 提到这一段的最前面，让风先起、音乐
    再从它上面淡出去。

    只上提 ambient=True 的 cue（一次性音效必须留在原位，它们是踩点用的）。
    """
    ambient_keys = [k for k, cfg in SFX_CUES.items() if cfg.get('ambient')]
    if not ambient_keys:
        return lines

    out = list(lines)
    for i, raw in enumerate(out):
        line = raw.strip()
        m = re.match(r'^【(.*?音效.*?)】$', line)
        if not m or not any(k in m.group(1) for k in ambient_keys):
            continue
        # 往回走，跨过空行与"可跨越"的标记，找到该插入的位置
        j = i
        while j > 0:
            prev = out[j - 1].strip()
            if not prev:
                j -= 1
                continue
            pm = re.match(r'^【(.+)】$', prev)
            if not pm or any(b in pm.group(1) for b in _HOIST_BLOCKERS):
                break
            j -= 1
        if j < i:
            out.insert(j, out.pop(i))
    return out


def _collect_jail_sections(lines, start_i, end_line):
    """监禁循环块探测：从 start_i 起若块内含【如果…无限期监禁…】条件标记，
    收集整块并按 【监禁marker…】/【释放marker…】/【监禁2marker…】 分段，
    返回 (条件标记原文, {'jail':…, 'free':…, 'jail2':…}, 新下标)；
    不是监禁块返回 None（不消费任何行，走普通累积框老路）。"""
    block = []
    i = start_i
    while i < end_line and i < len(lines):
        ln = lines[i].strip()
        i += 1
        if 'Extended文本框结束' in ln:
            break
        if ln:
            block.append(ln)
    cond = next((b for b in block if re.match(r'^【如果.*无限期监禁.*】$', b)), None)
    if cond is None:
        return None
    sections = {'jail': [], 'free': [], 'jail2': []}
    cur = None
    for b in block:
        if b is cond:
            continue
        m = re.match(r'^【(监禁2|监禁|释放)marker[^】]*】$', b)
        if m:
            cur = {'监禁': 'jail', '释放': 'free', '监禁2': 'jail2'}[m.group(1)]
            continue
        if b.startswith('【') and b.endswith('】'):
            continue
        if cur is None:
            cur = 'jail'   # 旧格式（无 marker）：全部当监禁段
        sections[cur].append(b)
    return cond, sections, i


def convert_route(lines, start_line, end_line, label_name, route_num):
    """Convert a route section with proper branching"""
    output = []
    output.append(f"## route{route_num}.rpy")
    output.append(f"## Route {route_num}")
    output.append("")
    output.append(f"label {label_name}:")

    i = start_line
    choice_counter = 0
    last_dialogue = None  # Track the last dialogue line for menu caption
    use_large_textbox = False  # Track large textbox mode
    # 最近一个含嵌套选项的 Extended 块在 output 里的起始下标。问询段的监禁循环
    # （居中大字块里的【如果…无限期监禁…重新回到这部分选项的最开始】）要跳回
    # 「这部分选项」——即这个块的块首。见下方 居中大字文本框 分支。
    interro_menu_anchor = None

    while i < end_line and i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # 周目分屏标题，且紧跟一个音效标记 → 把音效折进 route_title：标题完整展示时
        # 播放，再 wait_sfx 等它播完，之后的转场（王霜登场）才发生。用于"浮潜→落水
        # 泡泡→虚空对视"：泡泡声在标题出现后完整播放，王霜才登场。
        if '展示' in line and '周目分屏' in line:
            tm = re.search(r'分屏.(.+?).】$', line)
            title = tm.group(1) if tm else ''
            j = i
            while j < end_line and j < len(lines) and not lines[j].strip():
                j += 1
            sm = (re.match(r'^【(?:.*?音效)[：:]\s*(.+?)\s*】$', lines[j].strip())
                  if j < end_line and j < len(lines) else None)
            if sm:
                sfx_name = sm.group(1).strip()
                sfx_path = resolve_sfx(sfx_name)
                output.append(f'    call screen route_title(_("{title}"), sfx="{sfx_path}")')
                output.append('    $ wait_sfx()')
                i = j + 1   # 吃掉音效标记
            else:
                output.append(f'    call screen route_title(_("{title}"))')
            continue

        # Check for accumulating block markers (【Extended文本框开始】 or 【Extended大文本框开始】)
        # These use extend to accumulate text with each click
        # 右侧Split（右半屏分页）必须在普通 Split 之前判断
        # （'右侧Split...开始' 含 'Split...开始' 子串）。
        if '右侧Split Extended大文本框开始' in line:
            output.append("    ## 右侧Split Extended大文本框开始 - 右半屏分页")
            rp_out, i = emit_rightpage_block(lines, i, end_line)
            output.extend(rp_out)
            output.append("    ## 右侧Split Extended大文本框结束")
            continue

        # Split Extended大文本框（左右分栏）必须在普通大文本框之前判断
        # （'Split Extended大文本框开始' 含 'Extended大文本框开始' 子串）。
        if 'Split Extended大文本框开始' in line:
            output.append("    ## Split Extended大文本框开始 - 左右分栏")
            split_out, i = emit_split_large_block(lines, i, end_line)
            output.extend(split_out)
            output.append("    ## Split Extended大文本框结束")
            continue

        if 'Extended大文本框开始' in line:
            # 「不分句」变体：整块每行整句一次点击展示（句中不插 {w}）。用 no_click_split
            # 开关把这段 say 包起来，运行时 add_click_pauses 直接放行。say 文本/角色不变，
            # 不影响翻译 ID。
            no_split = '不分句' in line
            lr = '左右分开对齐' in line
            block_anchor = len(output)   # 块首（含开始注释）在 output 里的下标
            output.append("    ## Extended大文本框开始 - accumulating large textbox"
                          + ("（不分句）" if no_split else "")
                          + ("（左右分开对齐）" if lr else ""))
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True, lr=lr)
            if no_split:
                output.append("    $ no_click_split = True")
            output.extend(accumulated)
            if no_split:
                output.append("    $ no_click_split = False")
            output.append("    ## Extended大文本框结束")
            # 含嵌套选项的块 = 问询段选项部分，记下块首供监禁循环跳回。
            if any('menu:' in seg for seg in accumulated):
                interro_menu_anchor = block_anchor
            continue

        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            centered_box = '居中' in line
            label = '居中Extended文本框' if centered_box else 'Extended文本框'
            # 问询段监禁循环块：块内有【如果…无限期监禁…】条件标记 + 监禁/释放/
            # 监禁2 三段 marker → 三分支生成（首监禁跳回重来 / 释放继续 /
            # 二连监禁强制调和后继续）。见 _collect_jail_sections。
            jail = _collect_jail_sections(lines, i, end_line)
            if jail is not None:
                cond, sections, i = jail
                output.append(f"    ## {label}开始 - 监禁循环（条件展示）")
                output.append(f"    ## {cond.strip('【】')}")
                if interro_menu_anchor is not None:
                    output.insert(interro_menu_anchor, "    label _interro_restart:")
                    output.insert(interro_menu_anchor + 1, "        pass")
                    interro_menu_anchor = None   # 只插一次
                    output.append("    if interro_imprisoned and interro_attempt == 1:")
                    emit_extended_segments([(None, l) for l in sections['jail']],
                                           output, "        ", centered=centered_box)
                    output.append("        ## 监禁+1，重新回到问询选项的最开始")
                    output.append("        $ interro_attempt += 1")
                    output.append("        jump _interro_restart")
                    output.append("    elif interro_imprisoned:")
                    output.append("        ## 第二次连续监禁：强制调和，继续流程")
                    emit_extended_segments([(None, l) for l in sections['jail2']],
                                           output, "        ", centered=centered_box)
                    output.append("    else:")
                    emit_extended_segments([(None, l) for l in sections['free']],
                                           output, "        ", centered=centered_box)
                else:
                    print("WARNING: 监禁循环标记前找不到含选项的问询块，"
                          "监禁/释放段按顺序无条件展示")
                    for sec in ('jail', 'free', 'jail2'):
                        emit_extended_segments([(None, l) for l in sections[sec]],
                                               output, "    ", centered=centered_box)
                output.append(f"    ## {label}结束")
                continue
            output.append(f"    ## {label}开始 - {'centered ' if centered_box else ''}accumulating textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended文本框结束', use_large=False, centered=centered_box)
            output.extend(accumulated)
            output.append(f"    ## {label}结束")
            continue

        # 文字墙：【大文本框开始 - 这里锁操作，…堆满…抖动…放大…】
        # 这一段不是普通文本框 —— 它是一段固定时长的演出（锁操作，文字一行行堆满
        # 屏幕，然后抖动，然后一边抖一边压过来），走专门的 text_wall 屏幕。
        # 必须排在下面普通大文本框分支之前：它同样含 '大文本框开始'。
        if '大文本框开始' in line and '锁操作' in line:
            wall = []
            while i < end_line and i < len(lines):
                nxt = lines[i].strip()
                i += 1
                if '大文本框结束' in nxt and 'Extended' not in nxt:
                    break
                if not nxt or (nxt.startswith('【') and nxt.endswith('】')):
                    continue
                wall.append(nxt)
            if wall:
                body = escape_quotes('\\n'.join(wall))
                output.append("    ## 文字墙演出：锁操作 / 堆满 → 抖动 → 放大"
                              f"（约 {TEXT_WALL_SECONDS} 秒，见 transitions.rpy 的 text_wall_anim）")
                output.append(f'    show screen text_wall(_("{body}"))')
                output.append(f"    $ hard_pause({TEXT_WALL_SECONDS})")
                output.append("    hide screen text_wall")
            continue

        # Check for large textbox markers (non-combined, single line mode)
        if '大文本框开始' in line and 'Extended' not in line and '居中' not in line:
            use_large_textbox = True
            output.append("    ## 大文本框开始")
            continue
        if '大文本框结束' in line and 'Extended' not in line and '居中' not in line:
            use_large_textbox = False
            output.append("    ## 大文本框结束")
            continue

        # Check for centered textbox markers 【居中文本框开始】【居中文本框结束】
        if '居中文本框开始' in line and '大字' not in line:
            output.append("    ## 居中文本框开始 - centered textbox")
            # Collect all lines until end marker
            while i < end_line and i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if '居中文本框结束' in next_line:
                    output.append("    ## 居中文本框结束")
                    break
                if next_line:
                    output.append(f'    centered_narrator {format_dialogue(next_line)}')
            continue

        # Check for centered large font textbox markers 【居中大字文本框开始】【居中大字文本框结束】
        # （监禁循环块已改用 居中Extended文本框 格式，见上方 _collect_jail_sections 分支）
        if '居中大字文本框开始' in line:
            output.append("    ## 居中大字文本框开始 - centered large font textbox")
            while i < end_line and i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if '居中大字文本框结束' in next_line:
                    output.append("    ## 居中大字文本框结束")
                    break
                if next_line:
                    output.append(f'    centered_large_narrator {format_dialogue(next_line)}')
            continue

        # Check for choice A - starts a branching block
        if is_choice_a(line):
            choice_counter += 1
            choice_a_text, choice_a_madness, choice_a_action = parse_choice(line)

            # Collect content for choice A until we hit B:
            choice_a_content = []
            while i < end_line and i < len(lines):
                next_line = lines[i].strip()
                if is_choice_b(next_line):
                    break
                if next_line:  # Skip empty lines
                    choice_a_content.append(next_line)
                i += 1

            # Now at B: line
            choice_b_text = None
            choice_b_madness = 0
            choice_b_action = None
            choice_b_content = []

            if i < end_line and is_choice_b(lines[i].strip()):
                choice_b_text, choice_b_madness, choice_b_action = parse_choice(lines[i].strip())
                i += 1

                # Collect content for choice B until convergence, next choice A, or conditional C marker
                while i < end_line and i < len(lines):
                    next_line = lines[i].strip()
                    if is_convergence(next_line):
                        i += 1  # Skip the convergence marker
                        break
                    if is_choice_a(next_line):
                        # Another choice block without convergence - B leads to ending?
                        break
                    if is_conditional_c_marker(next_line):
                        # Conditional C choice follows - stop B content here
                        i += 1  # Skip the conditional marker
                        break
                    if next_line:
                        choice_b_content.append(next_line)
                    i += 1

            # Check for conditional choice C
            choice_c_text = None
            choice_c_madness = 0
            choice_c_action = None
            choice_c_content = []

            # Skip empty lines to find C:
            while i < end_line and i < len(lines) and not lines[i].strip():
                i += 1

            if i < end_line and is_choice_c(lines[i].strip()):
                choice_c_text, choice_c_madness, choice_c_action = parse_choice(lines[i].strip())
                i += 1

                # Collect content for choice C until convergence or end of route
                while i < end_line and i < len(lines):
                    next_line = lines[i].strip()
                    if is_convergence(next_line):
                        i += 1
                        break
                    if is_choice_a(next_line):
                        break
                    if next_line:
                        choice_c_content.append(next_line)
                    i += 1

            # Generate menu structure
            # Keep the dialogue line before menu, use "extend" to keep textbox visible
            output.append("")
            output.append("    menu:")
            output.append('        extend ""')
            last_dialogue = None

            # Choice A
            output.append(f'        "{choice_a_text}":')
            if choice_a_madness > 0:
                output.append(f"            $ madness += {choice_a_madness}")
            # Handle special actions
            if choice_a_action == 'return_to_menu':
                output.append("            return")
            elif choice_a_content:
                # Use process_choice_content to handle Extended textbox markers
                processed = process_choice_content(choice_a_content, "            ")
                output.extend(processed)
            else:
                # 'continue' action or no content - need pass for valid Ren'Py
                output.append("            pass")

            # Choice B
            if choice_b_text:
                output.append(f'        "{choice_b_text}":')
                if choice_b_madness > 0:
                    output.append(f"            $ madness += {choice_b_madness}")
                # Handle special actions
                if choice_b_action == 'return_to_menu':
                    output.append("            return")
                elif choice_b_content:
                    # Use process_choice_content to handle Extended textbox markers
                    processed = process_choice_content(choice_b_content, "            ")
                    output.extend(processed)
                else:
                    # 'continue' action or no content - need pass for valid Ren'Py
                    output.append("            pass")

            # Choice C (conditional - only shows when both Normal End and Happy End are unlocked)
            if choice_c_text:
                output.append(f'        "{choice_c_text}" if persistent.normal_end_unlocked and persistent.happy_end_unlocked:')
                if choice_c_madness > 0:
                    output.append(f"            $ madness += {choice_c_madness}")
                if choice_c_action == 'return_to_menu':
                    output.append("            return")
                elif choice_c_content:
                    processed = process_choice_content(choice_c_content, "            ")
                    output.extend(processed)
                else:
                    output.append("            pass")

            output.append("")
            continue

        # Regular content line (not part of choice)
        converted = convert_content_line(line, use_large_textbox=use_large_textbox)
        if converted:
            output.append(converted)
            # Track dialogue lines (character dialogue or narration) for menu captions
            # These are lines that display in the textbox
            stripped = converted.strip()
            if not stripped.startswith('##') and not stripped.startswith('$') and not stripped.startswith('call '):
                last_dialogue = stripped

    # End of route
    output.append("")
    output.append(f"    ## Route {route_num} 结束")
    output.append(f"    $ unlock_route({route_num})")
    output.append("    return")

    return '\n'.join(output)


def convert_prologue(lines, start_line, end_line):
    """Convert the prologue section (before route 1)"""
    # Arm the seamless-handoff flag; the first 【转场：...】 we see in this
    # section will emit `with None` to avoid a fade-through-black on the
    # main-menu→prologue boundary (where the bg is already the same video).
    global _PROLOGUE_FIRST_TRANSITION_PENDING, _CURRENT_EXPR_SCENE
    global _CAMERA_PAN_PENDING, _CAMERA_PAN_ACTIVE
    global _SPRITE_WALK_PENDING, _SPRITE_WALK_ACTIVE
    _PROLOGUE_FIRST_TRANSITION_PENDING = True
    _CURRENT_EXPR_SCENE = None
    _CAMERA_PAN_PENDING = None
    _CAMERA_PAN_ACTIVE = False
    _SPRITE_WALK_PENDING = False
    _SPRITE_WALK_ACTIVE = False
    _CLERK_STATE.clear()
    _RUN_SEQ_COUNT[0] = 0

    output = []
    output.append("## prologue.rpy")
    output.append("## 序章 / Prologue - AUTO-GENERATED")
    output.append("")
    output.append("label prologue:")
    output.append("    ## 根据进度跳转到对应周目")
    output.append("    $ route = get_current_route()")
    output.append("")
    output.append("    if route == 1:")
    output.append("        jump route1_prologue")
    output.append("    elif route == 2:")
    output.append("        jump route2_start")
    output.append("    else:")
    output.append("        jump route3_start")
    output.append("")
    output.append("################################################################################")
    output.append("## 一周目序章 - 只在第一次游戏时播放")
    output.append("################################################################################")
    output.append("")
    output.append("label route1_prologue:")

    i = start_line
    use_large_textbox = False

    while i < end_line and i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # Skip the very first non-empty content line — that's the script title
        # (e.g. "无休夏日综合征" or "疯子的青春期 完美夏日后日谈"). Was hardcoded
        # to one specific phrase before; this catches whatever title the script
        # currently uses. Markers (【...】) are handled later so they aren't
        # captured here.
        if i <= 5 and not line.startswith('【'):
            # Music reference comments live in 【...】 and won't reach here.
            # Anything else this early is the title — skip it silently.
            continue

        # Pass scene-music reference comments through as Ren'Py comments
        if i <= 5 and '场景音乐参考' in line:
            output.append(f"    ## {line.strip('【】')}")
            continue

        # Check for accumulating block markers
        # 右侧Split（右半屏分页）必须在普通 Split 之前判断
        # （'右侧Split...开始' 含 'Split...开始' 子串）。
        if '右侧Split Extended大文本框开始' in line:
            output.append("    ## 右侧Split Extended大文本框开始 - 右半屏分页")
            rp_out, i = emit_rightpage_block(lines, i, end_line)
            output.extend(rp_out)
            output.append("    ## 右侧Split Extended大文本框结束")
            continue

        # Split Extended大文本框（左右分栏）必须在普通大文本框之前判断
        # （'Split Extended大文本框开始' 含 'Extended大文本框开始' 子串）。
        if 'Split Extended大文本框开始' in line:
            output.append("    ## Split Extended大文本框开始 - 左右分栏")
            split_out, i = emit_split_large_block(lines, i, end_line)
            output.extend(split_out)
            output.append("    ## Split Extended大文本框结束")
            continue

        if 'Extended大文本框开始' in line:
            # 「不分句」变体：整块每行整句一次点击展示（句中不插 {w}）。用 no_click_split
            # 开关把这段 say 包起来，运行时 add_click_pauses 直接放行。say 文本/角色不变，
            # 不影响翻译 ID。
            no_split = '不分句' in line
            lr = '左右分开对齐' in line
            output.append("    ## Extended大文本框开始 - accumulating large textbox"
                          + ("（不分句）" if no_split else "")
                          + ("（左右分开对齐）" if lr else ""))
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True, lr=lr)
            if no_split:
                output.append("    $ no_click_split = True")
            output.extend(accumulated)
            if no_split:
                output.append("    $ no_click_split = False")
            output.append("    ## Extended大文本框结束")
            continue

        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            centered_box = '居中' in line
            label = '居中Extended文本框' if centered_box else 'Extended文本框'
            output.append(f"    ## {label}开始 - {'centered ' if centered_box else ''}accumulating textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended文本框结束', use_large=False, centered=centered_box)
            output.extend(accumulated)
            output.append(f"    ## {label}结束")
            continue

        # Check for large textbox markers
        if '大文本框开始' in line and 'Extended' not in line and '居中' not in line:
            use_large_textbox = True
            output.append("    ## 大文本框开始")
            continue
        if '大文本框结束' in line and 'Extended' not in line and '居中' not in line:
            use_large_textbox = False
            output.append("    ## 大文本框结束")
            continue

        # Check for centered textbox markers 【居中文本框开始】【居中文本框结束】
        if '居中文本框开始' in line and '大字' not in line:
            output.append("    ## 居中文本框开始 - centered textbox")
            # Collect all lines until end marker
            while i < end_line and i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if '居中文本框结束' in next_line:
                    output.append("    ## 居中文本框结束")
                    break
                if next_line:
                    output.append(f'    centered_narrator {format_dialogue(next_line)}')
            continue

        # Check for centered large font textbox markers 【居中大字文本框开始】【居中大字文本框结束】
        if '居中大字文本框开始' in line:
            output.append("    ## 居中大字文本框开始 - centered large font textbox")
            # Collect all lines until end marker
            while i < end_line and i < len(lines):
                next_line = lines[i].strip()
                i += 1
                if '居中大字文本框结束' in next_line:
                    output.append("    ## 居中大字文本框结束")
                    break
                if next_line:
                    output.append(f'    centered_large_narrator {format_dialogue(next_line)}')
            continue

        # Regular content line
        converted = convert_content_line(line, use_large_textbox=use_large_textbox)
        if converted:
            output.append(converted)

    # End of prologue - jump to route 1
    output.append("")
    output.append("    ## 一周目序章结束，跳转到一周目正式开始")
    output.append("    jump route1_start")

    return '\n'.join(output)


def find_route_boundaries(lines):
    """Dynamically find route boundaries based on markers in the script"""
    prologue_end = None
    route1_start = None
    route1_end = None
    route2_start = None
    route2_end = None
    route3_start = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Route 1 starts at first 一周目 header (this also marks end of prologue)
        if route1_start is None and re.match(r'^一周目', stripped):
            route1_start = i
            prologue_end = i
        # Route 1 ends at 【一周目End】 or 【一周目end】
        if re.match(r'^【一周目[Ee]nd】$', stripped):
            route1_end = i
        # Route 2 starts at 二周目 header
        if route2_start is None and re.match(r'^二周目', stripped):
            route2_start = i
        # Route 2 ends at 【二周目End】 or 【二周目end】
        if re.match(r'^【二周目[Ee]nd】$', stripped):
            route2_end = i
        # Route 3 starts at 三周目 header
        if route3_start is None and re.match(r'^三周目', stripped):
            route3_start = i

    return {
        'prologue': (0, prologue_end),
        'route1': (route1_start, route1_end),
        'route2': (route2_start, route2_end),
        'route3': (route3_start, len(lines))
    }


def find_unmapped_scenes(lines):
    """Return sorted list of 转场 scene names not in SCENE_BG_MAP / IN_PLACE_SCENES.
    These currently fall back to a black background — usually a signal that
    a new marker was added to the raw script but the image registration in
    placeholder.rpy / SCENE_BG_MAP is missing.

    Scenes that intentionally use a solid-color fallback (e.g. 黑屏, 白屏,
    红屏...) will also appear; filter those out manually if they're false
    positives for your workflow.
    """
    seen = set()
    for line in lines:
        m = re.match(r'^【转场[：:](.+?)】$', line.strip())
        if not m:
            continue
        content = m.group(1).strip()
        period_match = re.search(r'。', content)
        scene_name = content[:period_match.start()].strip() if period_match else content
        if scene_name:
            seen.add(scene_name)
    return sorted(seen - set(SCENE_BG_MAP) - set(IN_PLACE_SCENES))


def report_unmapped(lines, prefix=""):
    """Print a warning block listing unmapped 转场 scene names."""
    unmapped = find_unmapped_scenes(lines)
    if not unmapped:
        print(f"{prefix}All 转场 scenes are mapped.")
        return 0
    print(f"{prefix}WARNING: {len(unmapped)} unmapped 转场 scene(s) (will fall back to black):")
    for name in unmapped:
        print(f"{prefix}  - {name}")
    return len(unmapped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-unmapped", action="store_true",
        help="Only scan demo_script.txt for 转场 scene names that aren't "
             "in SCENE_BG_MAP. No conversion. Useful after editing the raw "
             "script to catch new scenes you forgot to register.",
    )
    args = parser.parse_args()

    with open(os.path.join(BASE_DIR, 'demo_script.txt'), 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    lines = hoist_ambient_cues(lines)

    if args.check_unmapped:
        report_unmapped(lines)
        return

    print(f"Total lines: {len(lines)}")

    # Demo only has prologue + route 1; route 1 runs to end of file.
    prologue_end = None
    route1_start = None
    for i, line in enumerate(lines):
        if re.match(r'^一周目', line.strip()):
            route1_start = i
            prologue_end = i
            break

    if prologue_end is None:
        print("ERROR: Could not find route 1 start marker (一周目)")
        return

    print(f"Demo boundaries:")
    print(f"  Prologue: lines 1-{prologue_end}")
    print(f"  Route 1: lines {route1_start+1}-{len(lines)}")

    # 立绘 image 定义 + 摆位 transform（按 sprites/ 目录扫描结果生成）
    generate_sprites_rpy()

    _GLOSSARY.clear()   # 注释词典（转换过程中收集，最后写 glossary.rpy）

    # Prologue
    prologue = insert_sfx_waits(convert_prologue(lines, 0, prologue_end))
    with open(os.path.join(BASE_DIR, 'game', 'scripts', 'prologue.rpy'), 'w', encoding='utf-8') as f:
        f.write(prologue)
    print("Prologue converted!")

    # Route 1 (runs to end of file - no end marker in demo)
    route1 = insert_sfx_waits(convert_route(lines, route1_start, len(lines), "route1_start", 1))
    # Demo-only: replace the route's trailing `return` with utter_restart().
    # Why: the demo is the only repo where the player returns from a finished
    # route back to the same polyhedron main menu. That round-trip puts the
    # Movie/channel into a state where the second `scene bg_polyhedron_video`
    # renders as checkerboard. utter_restart fully reloads the game (init runs
    # again, channel cleanly re-registers, Movie state resets), so the menu
    # they see after finishing is from a fresh boot — polyhedron works.
    # persistent (settings, unlocked endings) is preserved across utter_restart.
    if route1.rstrip().endswith("return"):
        route1 = route1.rstrip()[:-len("return")] + (
            "## demo 通关后整个游戏 reboot 一次，让 polyhedron channel 状态干净，\n"
            "    ## 第二次 Start 不会渲染成 checker board。persistent 不会被清。\n"
            "    ## 走 helper 而不是直接 utter_restart：自动化测试时跳过 reboot，\n"
            "    ## 否则测试跑完进程无法退出（卡死在最后）。见 variables.rpy。\n"
            "    $ demo_reboot_after_route()\n"
        )
    with open(os.path.join(BASE_DIR, 'game', 'scripts', 'route1.rpy'), 'w', encoding='utf-8') as f:
        f.write(route1)
    print("Route 1 converted!")

    # 行内注释词典（本次转换收集到的 【注释：…】）
    generate_glossary_rpy()

    print("Demo conversion complete!")
    print()
    report_unmapped(lines)


if __name__ == "__main__":
    main()

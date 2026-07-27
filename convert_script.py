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
        if 'outdated' in rel_parts:
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
    # 虚空对视：黑屏视频背景 + 透明立绘叠层（overlay 模型，见 SCENE_EXPRESSIONS）。
    # 用视频而非纯色 Solid，这样立绘透明处能透出"背景里的黑屏"动画。
    '虚空对视': 'bg_black_video',
    # 甜品店对视 1-8 + 6.51：场景渐进，详见 placeholder.rpy 里的注释。
    '甜品店对视1': 'bg_dessertgaze1',
    '甜品店对视2': 'bg_dessertgaze2',
    '甜品店对视3': 'bg_dessertgaze3',
    '甜品店对视4': 'bg_dessertgaze4',
    '甜品店对视5': 'bg_dessertgaze5',
    '甜品店对视6': 'bg_dessertgaze6',
    '甜品店对视6.51': 'bg_dessertgaze6_51',
    '甜品店对视7': 'bg_dessertgaze7',
    '甜品店对视8': 'bg_dessertgaze8',
}

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
    '甜品店对视3',
    '甜品店对视4',
    '甜品店对视5',
    '甜品店对视6',
    '甜品店对视6.51',
    '甜品店对视7',
    '甜品店对视8',
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
SPECIAL_FX = [
    ('glitch', 'fx_glitch'),
    ('黑影', 'fx_shock'),
]

# 表情切换过渡（短溶解；改这里改全局表情切换速度）。
EXPR_TRANSITION = "Dissolve(0.2)"

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
        'default': 'void default',
        'map': {'默认': 'void default', '小吃惊': 'void surprised'},
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

def escape_quotes(text):
    """Escape straight double quotes for Ren'Py"""
    return text.replace('"', '\\"')

def has_curly_quotes(text):
    """Check if text contains curly double quotes"""
    return '"' in text or '"' in text

# 专有名词列表（point 7）：这些字眼在正文中出现时用 {i}斜体{/i} 强调。
# 在 demo_script.txt 里直接以普通文字书写，由转换器负责加斜体标签——
# 这样剧本保持干净，新增名词只要往这个列表里加即可。
PROPER_NOUNS = ['尤里娅', 'KAS']

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

def transform_display_text(text):
    """所有可见正文（对话/旁白/选项/extend）共用的行内文字变换。
    顺序：先 小字 再 斜体（斜体可嵌套进小字里，互不干扰）。"""
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

def emit_char_dialogue(char_var, dialogue, indent, comment=None):
    """生成一行角色对话，处理 【锁定操作Ns】（point 5）。

    带锁定时：先 show 一个 modal 的 op_lock 屏幕（zorder 高、吃掉所有点击）N 秒，
    再正常说这句话——文本框照常显示且保持可见，但玩家在 N 秒内无法点击前进。
    op_lock 到点自动隐藏。（不用 {nw}+硬暂停：那会让文本框在暂停期间消失。）
    """
    cleaned, lock = extract_lock(dialogue)
    out = []
    if comment:
        out.append(f'{indent}## {comment}')
    if lock:
        out.append(f'{indent}show screen op_lock({lock})')
        out.append(f'{indent}{char_var} {format_dialogue(cleaned)}')
        # 一旦推进过这句（等满 N 秒、或 ctrl 快进），立刻收掉锁，避免 op_lock
        # 残留到后面几句继续吃点击。
        out.append(f'{indent}hide screen op_lock')
    else:
        out.append(f'{indent}{char_var} {format_dialogue(cleaned)}')
    return '\n'.join(out)

def _emit_scene(out, indent, scene_name, bg_image, transition):
    """发出 scene 行，并更新当前表情场景。overlay 表情场景额外把透明立绘默认
    表情叠上去（scene <bg> + show <default> + with，三者同一个过渡一起淡入）。"""
    global _CURRENT_EXPR_SCENE
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
        out.append(f'{indent}scene {bg_image}')
        out.append(f'{indent}show black zorder 100:')
        out.append(f'{indent}    alpha 1.0')
        out.append(f'{indent}    linear {fi} alpha 0.0')
        out.append(f'{indent}$ hard_pause({fi})')
        out.append(f'{indent}hide black')
        _CURRENT_EXPR_SCENE = scene_name
        return
    cfg = SCENE_EXPRESSIONS.get(scene_name)
    if cfg and cfg['model'] == 'overlay':
        if cfg.get('continue_bg'):
            # bg（黑屏视频）从上一场景连续过来：不重新 scene —— 重新 scene 会重启视频
            # 并经 scene_soft 的黑场"暗一下"。只把立绘 dissolve 淡入，黑屏全程连续。
            out.append(f'{indent}show {cfg["default"]} with scene_dissolve')
        else:
            out.append(f'{indent}scene {bg_image}')
            out.append(f'{indent}show {cfg["default"]}')
            out.append(f'{indent}with {transition}')
    else:
        out.append(f'{indent}scene {bg_image} with {transition}')
    _CURRENT_EXPR_SCENE = scene_name

def emit_expression_change(action, indent):
    """角色【表情】 → 切换差分。当前场景没有该表情（或非表情场景）返回 None，
    交还给调用方按普通"舞台提示注释"处理（道具/第一人称提示等）。
    full 场景用 scene 换整图；overlay 场景用 show 换透明立绘（共用 tag）。

    过渡只作用于 master 层（renpy.transition(..., layer="master")），不碰 screens 层
    的对话框/文字 —— 这样换表情时背景平滑溶解，但对话框和当前那句文字全程不消失、
    不闪烁（不能用 `with`，那是全屏过渡，会把对话框和文字一起淡掉）。"""
    cfg = SCENE_EXPRESSIONS.get(_CURRENT_EXPR_SCENE)
    if not cfg:
        return None
    img = cfg['map'].get(action)
    if not img:
        return None
    verb = 'show' if cfg['model'] == 'overlay' else 'scene'
    return (f'{indent}## 表情：{action}\n'
            f'{indent}{verb} {img}\n'
            f'{indent}$ renpy.transition({EXPR_TRANSITION}, layer="master")')

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

def emit_extended_segments(collected, output, indent, large=False, centered=False):
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
    narr = 'centered_narrator ' if centered else ('large_narrator ' if large else '')
    first_emitted = False   # 本段落是否已经发出开头 say

    def emit_piece(speaker, text, lead_newline):
        nonlocal first_emitted
        if lead_newline:
            text = chr(92) + 'n' + text
        if not first_emitted:
            if speaker:
                output.append(f'{indent}{speaker} {format_dialogue(text)}')
            else:
                output.append(f'{indent}{narr}{format_dialogue(text)}')
            first_emitted = True
        else:
            output.append(f'{indent}extend {format_dialogue(text)}')

    for speaker, text in collected:
        if speaker == '__expr__':
            # 块内表情切换：master 层溶解，对话框/文字不动（见 emit_expression_change）。
            expr_line = emit_expression_change(text, indent)
            output.append(expr_line if expr_line else f'{indent}## {text}')
            first_emitted = False
            continue
        if speaker == '__transition__':
            scene_name, scene_desc = text
            emit_transition_lines(output, indent, scene_name, scene_desc)
            first_emitted = False
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

    # Music stop markers 【音乐停】 or 【音效和音乐停】
    # fadeout 3.0：让音乐柔和淡出而非戛然而止（1.0 太突兀）。
    if '音乐停' in line:
        return f'{indent}$ current_music_scene = None\n{indent}stop music fadeout 3.0'

    # Music fade-out marker 【音乐开始fade out】：当前音乐缓缓淡出（进入幻视前的留白）。
    # current_music_scene 置 None，淡出后存档/读档不会把这段音乐恢复回来。
    # 时长 4s：调这里改淡出快慢（后面 set_scene_music 切幻视曲时会接管交叉淡入）。
    if '音乐开始fade out' in line:
        return (f'{indent}## 音乐开始 fade out\n'
                f'{indent}$ current_music_scene = None\n'
                f'{indent}stop music fadeout 4.0')

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

    # Demo 结尾 【fade out屏幕之后，回主菜单】：图像与音乐一起淡出、黑屏留白，
    # 随后 main() 追加的 demo_reboot_after_route() reboot 回主菜单。音乐一起淡出
    # （而非硬切），是为了衔接主菜单曲；current_music_scene 置 None 以免读档恢复。
    if 'fade out' in line and '回主菜单' in line:
        return (f'{indent}## fade out 屏幕（图像+音乐）之后，reboot 回主菜单\n'
                f'{indent}$ current_music_scene = None\n'
                f'{indent}stop music fadeout 2.0\n'
                f'{indent}scene black with fade_to_black_long\n'
                f'{indent}$ hard_pause(1.0)')

    # Pause markers 【停顿：N】 -> `pause N` (N is seconds, float ok)
    # Use sparingly — for breathing room before a scene's first line, etc.
    pause_match = re.match(r'^【停顿[：:]([\d.]+)】$', line)
    if pause_match:
        return f'{indent}pause {pause_match.group(1)}'

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

    # Stage direction (standalone) -> comment, plus an FX transition when
    # the cue is a genuine visual dramatic beat. Audio cues (音效) are
    # comment-only - a sound effect should not shake the screen.
    stage_match = re.match(r'^【(.+?)】$', line)
    if stage_match:
        text = stage_match.group(1)
        if '音效' not in text:
            for keyword, fx in SPECIAL_FX:
                if keyword in text:
                    return f"{indent}## {text}\n{indent}with {fx}"
        return f"{indent}## {text}"

    # Character name to variable mapping
    char_var_map = {
        '王霜': 'wangshuang',
        '王霜（？）': 'wangshuang_unknown',
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

    # Build regex pattern from character names (longer names first to avoid partial matches)
    char_names = sorted(char_var_map.keys(), key=len, reverse=True)
    char_pattern = '|'.join(re.escape(name) for name in char_names)

    # Character dialogue with one or more leading 【…】 markers（表情 / 小字 / 道具提示）。
    # 一句可带多个 marker，如 王霜【小声嘀咕】【小字】：…（既切表情又缩小字体）。
    char_action_match = re.match(rf'^({char_pattern})((?:【.+?】)+)[：:](.*)$', line)
    if char_action_match:
        char_name = char_action_match.group(1)
        dialogue = char_action_match.group(3).strip()
        char_var = char_var_map[char_name]
        pre = []   # 表情切换 / 注释，放在台词前
        for m in re.findall(r'【(.+?)】', char_action_match.group(2)):
            if m == '小字':
                # 把 【小字】 放回台词开头，交给 apply_small_text 缩小到行尾。
                dialogue = '【小字】' + dialogue
                continue
            swap = emit_expression_change(m, indent)   # 已知表情 → master 层溶解切差分
            pre.append(swap if swap else f'{indent}## {m}')  # 否则当舞台提示注释
        return '\n'.join(pre + [emit_char_dialogue(char_var, dialogue, indent)])

    # Character dialogue (simple)
    char_match = re.match(rf'^({char_pattern})[：:](.*)$', line)
    if char_match:
        char_name = char_match.group(1)
        dialogue = char_match.group(2).strip()
        char_var = char_var_map[char_name]
        return emit_char_dialogue(char_var, dialogue, indent)

    # Section headers
    if re.match(r'^[一二三四五六七八九十]+周目', line):
        return f"\n## {line}\n"

    # Narrative text - choose narrator based on mode
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


def collect_accumulating_block(lines, start_i, end_line, marker_end, use_large=False, centered=False):
    """
    Collect lines between markers and output them with extend for accumulating display.
    First line is normal dialogue, subsequent lines use extend to append.
    centered=True：居中累积框（centered_say），用于 demo 结尾谢幕卡等。
    Returns (output_lines, new_index)
    """
    # Character name to variable mapping (must match convert_content_line)
    char_var_map = {
        '王霜': 'wangshuang',
        '王霜（？）': 'wangshuang_unknown',
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
    char_names = sorted(char_var_map.keys(), key=len, reverse=True)
    char_pattern = '|'.join(re.escape(name) for name in char_names)

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
            # Stage directions - skip
            if line.startswith('【') and line.endswith('】'):
                continue
            # Narration
            collected.append((None, line))

    if not collected:
        return [], i

    output = []
    indent = "    "

    # Extended 文本框（大/小）现在统一走同一段落、按标点逐次点击的分句逻辑。
    # 大文本框只是旁白用 large_narrator、屏幕用 large_say，分句规则完全一致。
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
            output.append(f"{indent}## Extended大文本框开始 - 大文本框分句")
            entries = []
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if 'Extended大文本框结束' in next_line:
                    break
                if not next_line:
                    continue
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
            # Character name to variable mapping
            char_var_map = {
                '王霜': 'wangshuang',
                '王霜（？）': 'wangshuang_unknown',
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
            char_names = sorted(char_var_map.keys(), key=len, reverse=True)
            char_pattern = '|'.join(re.escape(name) for name in char_names)

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
            output.append("    ## Extended大文本框开始 - accumulating large textbox"
                          + ("（不分句）" if no_split else ""))
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True)
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
    _PROLOGUE_FIRST_TRANSITION_PENDING = True
    _CURRENT_EXPR_SCENE = None

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
            output.append("    ## Extended大文本框开始 - accumulating large textbox"
                          + ("（不分句）" if no_split else ""))
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True)
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
    """Return sorted list of 转场 scene names not in SCENE_BG_MAP.
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
    return sorted(seen - set(SCENE_BG_MAP))


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

    print("Demo conversion complete!")
    print()
    report_unmapped(lines)


if __name__ == "__main__":
    main()

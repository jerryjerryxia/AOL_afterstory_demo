# -*- coding: utf-8 -*-
"""
Script converter: Converts raw script to Ren'Py format
Handles branching with A:/B: options and 【选项分线到此结束】 convergence markers
"""

import argparse
import re
import sys

# Force UTF-8 stdout so 中文 prints correctly on Windows consoles (the default
# cp936/cp1252 codepage mangles it). Safe no-op on POSIX. Python 3.7+.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

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

# Tracks whether the prologue's first 【转场：...】 still needs to be emitted
# without a transition (with None). The main menu's polyhedron video bg
# already shows what the prologue is about to scene to, so a fade-through-black
# would break the seamless handoff. convert_prologue() sets this to True at
# its start; convert_content_line()'s transition branch consumes it once.
_PROLOGUE_FIRST_TRANSITION_PENDING = False

# Standalone stage-direction keyword -> FX transition emitted right after
# the comment, for genuine *visual* dramatic beats only. Audio-only cues
# (containing 音效) are skipped. Transitions are defined in
# game/scripts/transitions.rpy.
SPECIAL_FX = [
    ('glitch', 'fx_glitch'),
    ('黑影', 'fx_shock'),
]

def escape_quotes(text):
    """Escape straight double quotes for Ren'Py"""
    return text.replace('"', '\\"')

def has_curly_quotes(text):
    """Check if text contains curly double quotes"""
    return '"' in text or '"' in text

def format_dialogue(text):
    """Format dialogue string, using single quotes if curly quotes present"""
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
    if '音乐停' in line:
        return f'{indent}$ current_music_scene = None\n{indent}stop music fadeout 1.0'

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

        # Escape quotes in scene name and description
        scene_name_escaped = scene_name.replace('"', '\\"')
        scene_desc_escaped = scene_desc.replace('"', '\\"')

        # Generate the comment, the background scene, and the variables.
        # Scenes without dedicated art fall back to a plain black background.
        output_lines = [f'{indent}## 转场：{scene_name}']
        bg_image = SCENE_BG_MAP.get(scene_name, 'black')
        global _PROLOGUE_FIRST_TRANSITION_PENDING
        if _PROLOGUE_FIRST_TRANSITION_PENDING:
            # Main menu's bg is already what we're scening to; skip the fade.
            transition = 'None'
            _PROLOGUE_FIRST_TRANSITION_PENDING = False
        elif scene_name in NO_TRANSITION_SCENES:
            transition = 'None'
        elif scene_name in CROSS_DISSOLVE_SCENES:
            transition = 'scene_dissolve'
        else:
            transition = 'scene_soft'
        output_lines.append(f'{indent}scene {bg_image} with {transition}')
        output_lines.append(f'{indent}$ current_scene_name = "{scene_name_escaped}"')
        if scene_desc:
            output_lines.append(f'{indent}$ current_scene_desc = "{scene_desc_escaped}"')
        else:
            output_lines.append(f'{indent}$ current_scene_desc = None')
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

    # Character dialogue with inline stage direction
    char_action_match = re.match(rf'^({char_pattern})【(.+?)】[：:](.*)$', line)
    if char_action_match:
        char_name = char_action_match.group(1)
        action = char_action_match.group(2)
        dialogue = char_action_match.group(3).strip()
        char_var = char_var_map[char_name]
        return f'{indent}## {action}\n{indent}{char_var} {format_dialogue(dialogue)}'

    # Character dialogue (simple)
    char_match = re.match(rf'^({char_pattern})[：:](.*)$', line)
    if char_match:
        char_name = char_match.group(1)
        dialogue = char_match.group(2).strip()
        char_var = char_var_map[char_name]
        return f'{indent}{char_var} {format_dialogue(dialogue)}'

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


def collect_accumulating_block(lines, start_i, end_line, marker_end, use_large=False):
    """
    Collect lines between markers and output them with extend for accumulating display.
    First line is normal dialogue, subsequent lines use extend to append.
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

    # Track whether this is the first content line (after which we use extend)
    first_line = True

    for speaker, text in collected:
        # Handle scene transitions - they break the extend chain
        if speaker == '__transition__':
            scene_name, scene_desc = text
            scene_name_escaped = scene_name.replace('"', '\\"')
            scene_desc_escaped = scene_desc.replace('"', '\\"')
            output.append(f'{indent}## 转场：{scene_name}')
            bg_image = SCENE_BG_MAP.get(scene_name, 'black')
            # Same transition-choice logic as convert_content_line.
            # (We don't touch _PROLOGUE_FIRST_TRANSITION_PENDING here because
            # the prologue's first 转场 is at the top of the file, never inside
            # an accumulating textbox block.)
            if scene_name in NO_TRANSITION_SCENES:
                transition = 'None'
            elif scene_name in CROSS_DISSOLVE_SCENES:
                transition = 'scene_dissolve'
            else:
                transition = 'scene_soft'
            output.append(f'{indent}scene {bg_image} with {transition}')
            output.append(f'{indent}$ current_scene_name = "{scene_name_escaped}"')
            if scene_desc:
                output.append(f'{indent}$ current_scene_desc = "{scene_desc_escaped}"')
            else:
                output.append(f'{indent}$ current_scene_desc = None')
            # Next dialogue line should start fresh
            first_line = True
            continue

        # First line outputs normally, all subsequent lines use extend
        if first_line:
            if speaker:
                # Character dialogue
                output.append(f'{indent}{speaker} {format_dialogue(text)}')
            else:
                # Narration
                if use_large:
                    output.append(f'{indent}large_narrator {format_dialogue(text)}')
                else:
                    output.append(f'{indent}{format_dialogue(text)}')
            first_line = False
        else:
            # All subsequent lines use extend
            output.append(f'{indent}extend {format_dialogue(chr(92) + "n" + text)}')

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

        # Check for Extended大文本框 markers
        if 'Extended大文本框开始' in line:
            output.append(f"{indent}## Extended大文本框开始 - accumulating large textbox")
            # Collect lines until end marker
            first_line = True
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if 'Extended大文本框结束' in next_line:
                    output.append(f"{indent}## Extended大文本框结束")
                    break
                if not next_line:
                    continue
                # Skip stage directions
                if next_line.startswith('【') and next_line.endswith('】'):
                    continue
                if first_line:
                    output.append(f'{indent}large_narrator {format_dialogue(next_line)}')
                    first_line = False
                else:
                    output.append(f'{indent}extend {format_dialogue(chr(92) + "n" + next_line)}')
            continue

        # Check for Extended文本框 markers (non-large)
        # All lines accumulate with extend after the first
        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            output.append(f"{indent}## Extended文本框开始 - accumulating textbox")
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

            first_line = True
            while i < len(content_lines):
                next_line = content_lines[i].strip()
                i += 1
                if 'Extended文本框结束' in next_line:
                    output.append(f"{indent}## Extended文本框结束")
                    break
                if not next_line:
                    continue
                if next_line.startswith('【') and next_line.endswith('】'):
                    continue
                # Check for character dialogue
                char_match = re.match(rf'^({char_pattern})[：:](.*)$', next_line)
                if char_match:
                    char_name = char_match.group(1)
                    dialogue = char_match.group(2).strip()
                    char_var = char_var_map[char_name]
                    if first_line:
                        output.append(f'{indent}{char_var} {format_dialogue(dialogue)}')
                        first_line = False
                    else:
                        output.append(f'{indent}extend {format_dialogue(chr(92) + "n" + dialogue)}')
                else:
                    # Narration
                    if first_line:
                        output.append(f'{indent}{format_dialogue(next_line)}')
                        first_line = False
                    else:
                        output.append(f'{indent}extend {format_dialogue(chr(92) + "n" + next_line)}')
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

        # Check for accumulating block markers (【Extended文本框开始】 or 【Extended大文本框开始】)
        # These use extend to accumulate text with each click
        if 'Extended大文本框开始' in line:
            output.append("    ## Extended大文本框开始 - accumulating large textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True)
            output.extend(accumulated)
            output.append("    ## Extended大文本框结束")
            continue

        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            output.append("    ## Extended文本框开始 - accumulating textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended文本框结束', use_large=False)
            output.extend(accumulated)
            output.append("    ## Extended文本框结束")
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
    global _PROLOGUE_FIRST_TRANSITION_PENDING
    _PROLOGUE_FIRST_TRANSITION_PENDING = True

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
        if 'Extended大文本框开始' in line:
            output.append("    ## Extended大文本框开始 - accumulating large textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended大文本框结束', use_large=True)
            output.extend(accumulated)
            output.append("    ## Extended大文本框结束")
            continue

        if 'Extended文本框开始' in line and 'Extended大文本框' not in line:
            output.append("    ## Extended文本框开始 - accumulating textbox")
            accumulated, i = collect_accumulating_block(lines, i, end_line, 'Extended文本框结束', use_large=False)
            output.extend(accumulated)
            output.append("    ## Extended文本框结束")
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

    with open(r'X:\GameDev\AOL_afterstory_demo\demo_script.txt', 'r', encoding='utf-8') as f:
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
    prologue = convert_prologue(lines, 0, prologue_end)
    with open(r'X:\GameDev\AOL_afterstory_demo\game\scripts\prologue.rpy', 'w', encoding='utf-8') as f:
        f.write(prologue)
    print("Prologue converted!")

    # Route 1 (runs to end of file - no end marker in demo)
    route1 = convert_route(lines, route1_start, len(lines), "route1_start", 1)
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
            "    $ renpy.utter_restart()\n"
        )
    with open(r'X:\GameDev\AOL_afterstory_demo\game\scripts\route1.rpy', 'w', encoding='utf-8') as f:
        f.write(route1)
    print("Route 1 converted!")

    print("Demo conversion complete!")
    print()
    report_unmapped(lines)


if __name__ == "__main__":
    main()

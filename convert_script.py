# -*- coding: utf-8 -*-
"""
Script converter: Converts raw script to Ren'Py format
Handles branching with A:/B: options and 【选项分线到此结束】 convergence markers
"""

import re

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
            return f'{indent}call screen route_title("{title}")'

    # Music trigger markers 【音乐：scene_id】
    music_match = re.match(r'^【音乐[：:](.+?)】$', line)
    if music_match:
        scene_id = music_match.group(1).strip()
        return f'{indent}$ set_scene_music("{scene_id}")'

    # Music stop markers 【音乐停】 or 【音效和音乐停】
    if '音乐停' in line:
        return f'{indent}$ current_music_scene = None\n{indent}stop music fadeout 1.0'

    # Scene transition markers 【转场：场景名。场景描述】
    transition_match = re.match(r'^【转场[：:](.+?)】$', line)
    if transition_match:
        content = transition_match.group(1).strip()
        # Split by first period (Chinese or English)
        # The scene name is before the first period, description is after
        period_match = re.search(r'[。.]', content)
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

        # Generate both the comment and the variable assignment
        output_lines = [f'{indent}## 转场：{scene_name}']
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

    # Stage direction (standalone) -> comment
    stage_match = re.match(r'^【(.+?)】$', line)
    if stage_match:
        return f"{indent}## {stage_match.group(1)}"

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
            # Split by first period (Chinese or English)
            period_match = re.search(r'[。.]', content)
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

        # Skip title line and music reference comments at the very beginning
        if i <= 5 and ('疯子的青春期' in line or '场景音乐参考' in line):
            if '场景音乐参考' in line:
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


def main():
    with open(r'X:\GameDev\AOL_afterstory_demo\demo_script.txt', 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    print(f"Total lines: {len(lines)}")

    # Find prologue/route1 boundary (demo only has prologue + route 1)
    prologue_end = None
    route1_start = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if route1_start is None and re.match(r'^一周目', stripped):
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
    with open(r'X:\GameDev\AOL_afterstory_demo\game\scripts\route1.rpy', 'w', encoding='utf-8') as f:
        f.write(route1)
    print("Route 1 converted!")

    print("Demo conversion complete!")


if __name__ == "__main__":
    main()

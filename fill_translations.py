# -*- coding: utf-8 -*-
"""
Fill Ren'Py translation stubs with English text from bilingual script.
Parses demo_script_eng.txt (alternating Chinese/English lines) and fills
game/tl/english/ translation files.
"""

import re
import os

# Character names used in the raw script (Chinese → English)
CHAR_NAMES_EN = {
    '王霜': 'Wang Shuang',
    '王霜（？）': 'Wang Shuang (?)',
    '阿鹤': 'Kaku',
    '尸首': 'The Corpse',
    '路人甲': 'Passerby A',
    '路人乙': 'Passerby B',
    '路人丙': 'Passerby C',
    '路人丁': 'Passerby D',
    '杰罗瓦': 'Jerowald',
    '米姐': 'Sister Mi',
    '尤里娅': 'Julia',
}

# Character variable names in converter
CHAR_VARS = {
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

# Build sorted character names for regex
char_names = sorted(CHAR_VARS.keys(), key=len, reverse=True)
char_pattern = '|'.join(re.escape(name) for name in char_names)

# English names used in demo_script_eng.txt (may differ from CHAR_NAMES_EN display names)
ENG_SCRIPT_NAMES = set(CHAR_NAMES_EN.values()) | {
    'Kaku',  # 阿鹤 is called Kaku in the English script
}

# Build English character name pattern for stripping from translations
eng_char_names = sorted(ENG_SCRIPT_NAMES, key=len, reverse=True)
eng_char_pattern = '|'.join(re.escape(name) for name in eng_char_names)


def is_stage_direction(line):
    """Check if line is a stage direction 【...】"""
    return line.startswith('【') and line.endswith('】')


def is_choice_line(line):
    """Check if line is a choice marker A:–E:, with optional 【…】 tags before
    the colon (问询段 options like A【疯狂+1】：… / B【…只加一次】：…)."""
    return bool(re.match(r'^[A-E]\s*(?:【[^】]*】)*\s*[：:]\s*.+$', line))


# Strip the choice prefix (letter + optional 【…】 tags + colon) from a choice line.
_CHOICE_PREFIX_RE = re.compile(r'^[A-E]\s*(?:【[^】]*】)*\s*[：:]\s*')


def is_section_header(line):
    """Check if line is a section header like 一周目：浮潜"""
    return bool(re.match(r'^[一二三四五六七八九十]+周目', line))


def is_chinese(text):
    """Check if text contains Chinese characters"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def is_music_reference(line):
    """Check if line is a music/scene reference comment"""
    return '场景音乐参考' in line or '场景音乐风格参考' in line


def _strip_eng_char_prefix(text):
    """Strip English character name prefix from a translation line."""
    eng_char_match = re.match(rf'^({eng_char_pattern})[：:]\s*(.+)$', text)
    return eng_char_match.group(2).strip() if eng_char_match else text


def _is_english_line(text):
    """Check if a line looks like an English translation.

    Note: do NOT require text[0].isascii() — many English lines in this script
    start with `——` (em dash, U+2014) before the first Latin word, e.g.
    "——But 'Everything' is a lazy term." Use a Latin-letter search instead.
    """
    return (text and
            not is_stage_direction(text) and
            not is_choice_line(text) and
            not is_section_header(text) and
            not re.match(rf'^({char_pattern})', text) and
            not text.startswith('【') and
            not is_chinese(text.split()[0] if text.split() else '') and
            bool(re.search(r'[A-Za-z]', text)))


def parse_bilingual_script(filepath):
    """
    Parse the bilingual script file.
    Returns (translations, standalone_lines):
      - translations: dict mapping Chinese text -> list of English text parts
        Usually one part, but 【EN独立】 between English lines splits into multiple.
      - standalone_lines: set of Chinese texts where the FIRST 【EN独立】 appears
        BEFORE the first English line (used to convert extend -> standalone)

    Marker usage in demo_script_eng.txt:

    1. Split extend into standalone (【EN独立】 before any English):
         Chinese extend line
         【EN独立】
         English translation

    2. Split one dialogue into multiple English lines:
         Chinese dialogue line
         English part 1
         【EN独立】
         English part 2

    Stage directions, choices, and markers stay in Chinese.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    translations = {}
    standalone_lines = set()
    choice_translations = {}
    i = 0
    next_is_standalone = False

    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # Detect 【EN独立】 marker - flags the next English line as standalone
        if line == '【EN独立】':
            next_is_standalone = True
            continue

        # Skip stage directions, they don't get translated in script
        if is_stage_direction(line):
            continue

        # Skip section headers
        if is_section_header(line):
            continue

        # Parse choice lines (A:–E:) - extract Chinese text, check for English next
        if is_choice_line(line):
            # Strip prefix (letter + optional 【…】 tags) and suffix （madness+1） etc.
            choice_text = _CHOICE_PREFIX_RE.sub('', line)
            choice_text = re.sub(r'[（(]madness\s*\+?\s*\d+[）)]', '', choice_text).strip()
            # Check if next line is English choice translation
            if i < len(lines):
                next_line = lines[i].strip()
                if is_choice_line(next_line):
                    eng_choice = _CHOICE_PREFIX_RE.sub('', next_line).strip()
                    choice_translations[choice_text] = eng_choice
                    i += 1
            continue

        # Skip title line
        if '疯子的青春期' in line and i <= 2:
            continue

        # This is a content line (dialogue or narration)
        # Check if the character has a dialogue prefix
        char_match = re.match(rf'^({char_pattern})[：:](.*)$', line)
        char_action_match = re.match(rf'^({char_pattern})【(.+?)】[：:](.*)$', line)

        if char_action_match:
            chinese_text = char_action_match.group(3).strip()
        elif char_match:
            chinese_text = char_match.group(2).strip()
        else:
            chinese_text = line

        # Check if next non-empty line is English (not Chinese)
        if i < len(lines):
            next_line = lines[i].strip()

            # Check for 【EN独立】 right before the English line
            if next_line == '【EN独立】':
                next_is_standalone = True
                i += 1
                if i < len(lines):
                    next_line = lines[i].strip()
                else:
                    next_is_standalone = False
                    continue

            if _is_english_line(next_line):
                eng_text = _strip_eng_char_prefix(next_line)
                eng_parts = [eng_text]
                if next_is_standalone:
                    standalone_lines.add(chinese_text)
                    next_is_standalone = False
                i += 1

                # Look ahead for 【EN独立】 + more English lines (split single line)
                while i < len(lines):
                    peek = lines[i].strip()
                    if peek == '【EN独立】' and i + 1 < len(lines):
                        peek_next = lines[i + 1].strip()
                        if _is_english_line(peek_next):
                            eng_parts.append(_strip_eng_char_prefix(peek_next))
                            i += 2
                            continue
                    break

                translations[chinese_text] = eng_parts
            else:
                next_is_standalone = False
        else:
            next_is_standalone = False

    return translations, standalone_lines, choice_translations


def _format_tl_line(indent, prefix, eng_text):
    """Format a single translation line with proper quoting."""
    if '"' in eng_text or '\u201c' in eng_text or '\u201d' in eng_text:
        eng_escaped = eng_text.replace("'", "\\'")
        return f"{indent}{prefix}'{eng_escaped}'"
    else:
        eng_escaped = eng_text.replace('"', '\\"')
        return f'{indent}{prefix}"{eng_escaped}"'


def _build_speaker_map(script_path):
    """Return {line_number: speaker_prefix} for a generated .rpy script file.

    For each line number, the value is the most recent non-extend speaker
    above that line in script-execution order. Used by
    fill_dialogue_translation to resolve the correct speaker when converting
    an `extend` to a standalone textbox: file-order tracking in the tl file
    fails when choice branches interleave (e.g. an `ahe "..."` from a B-branch
    appears in the tl file right before a large_narrator's extend, even
    though in the script the ahe line is on a different code path).
    """
    if not os.path.exists(script_path):
        return {}
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    result = {}
    current = ''
    # Speakers we care about. extend / narrator are NOT here — extend doesn't
    # count, and narrator has no name so it can't be the "standalone" target.
    valid_speakers = set(CHAR_VARS.values()) | {
        'large_narrator', 'centered_narrator', 'centered_large_narrator',
        'protag_thought',
    }
    for i, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        # Match speaker at line start (Ren'Py say statement)
        m = re.match(r'^([a-z_][a-z0-9_]*)\s+["\']', stripped)
        if m:
            speaker = m.group(1)
            if speaker in valid_speakers:
                current = speaker + ' '
        result[i] = current
    return result


def fill_dialogue_translation(filepath, translations, standalone_lines=None, source_script_path=None):
    """
    Fill in a Ren'Py dialogue translation file.

    Format:
        # comment with original
        speaker "Chinese text"  ->  speaker "English text"
    or:
        # comment with original
        extend "\\nChinese text"  ->  extend "\\nEnglish text"

    If a line is in standalone_lines, extend is replaced with the last
    seen speaker (e.g. large_narrator, wangshuang), making it a new
    standalone textbox instead of appending to the previous one.

    If a translation has multiple parts (from 【EN独立】 splits), multiple
    speaker statements are output in the same translate block.
    """
    if standalone_lines is None:
        standalone_lines = set()

    # Build {line_number: speaker} map from the source script for
    # script-execution-order speaker resolution (see _build_speaker_map docs).
    speaker_map = _build_speaker_map(source_script_path) if source_script_path else {}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    output = []
    changes = 0
    last_speaker = ''  # File-order fallback if speaker_map lookup misses.
    last_source_line = None  # Line number from the latest "# game/scripts/...:N" comment.

    i = 0
    while i < len(lines):
        line = lines[i]

        # Track the most recent file:line comment so we can look up the
        # correct script-context speaker for the next translate block.
        src_match = re.match(r'^#\s*game/scripts/\S+:(\d+)\s*$', line.strip())
        if src_match:
            last_source_line = int(src_match.group(1))

        # Look for the pattern: comment line followed by translation line
        # Comment: "    # speaker "Chinese text""
        # Translation: "    speaker "Chinese text""
        comment_match = re.match(r'^(\s+)# (.+)$', line)
        if comment_match and i + 1 < len(lines):
            next_line = lines[i + 1]
            comment_text = comment_match.group(2)

            # Match: speaker "text" or extend "text" or "text"
            # Use a simpler regex: capture everything before the first quote as prefix
            tl_match = re.match(r'^(\s+)((?:\w+ )?)"(.+)"\s*$', next_line)
            if not tl_match:
                tl_match = re.match(r"^(\s+)((?:\w+ )?)'(.+)'\s*$", next_line)

            if tl_match:
                tl_indent = tl_match.group(1)
                # Use the COMMENT-line speaker (the script's truth), not the
                # translation-line speaker — same reason as is_extend above.
                speaker_prefix = ''  # placeholder; set right after we parse the comment

                # Extract Chinese text from the COMMENT line (always has original Chinese)
                comment_tl = re.match(r'^(?:\w+ )?["\'](.+)["\']', comment_text)
                if not comment_tl:
                    output.append(line)
                    i += 1
                    continue
                chinese_text = comment_tl.group(1)

                # is_extend (and the actual speaker_prefix used for output) must
                # come from the ORIGINAL-script COMMENT, not from the
                # translation line — otherwise a previous bad fill (e.g. an
                # `ahe ...` line that should have been a standalone
                # large_narrator extend) makes is_extend False and the
                # standalone-substitution branch never runs.
                comment_speaker_match = re.match(r'^((?:\w+ )?)["\']', comment_text)
                speaker_prefix = (comment_speaker_match.group(1)
                                  if comment_speaker_match else '')
                is_extend = speaker_prefix.strip() == 'extend'

                lookup_text = chinese_text
                if is_extend and lookup_text.startswith('\\n'):
                    lookup_text = lookup_text[2:]  # Remove \n prefix

                # Track last non-extend speaker
                if not is_extend and speaker_prefix.strip():
                    last_speaker = speaker_prefix

                # Look up translation. 直接命中不了时，试分段命中：问询段的
                # 「——选项回显\n——首条响应」被转换器并成了一条 extend（中间是
                # 字面 \n），逐段查表后重新拼回去。
                eng_parts = translations.get(lookup_text)
                if eng_parts is None and '\\n' in lookup_text:
                    segs = lookup_text.split('\\n')
                    if all(s in translations for s in segs):
                        eng_parts = ['\\n'.join(translations[s][0] for s in segs)]
                if eng_parts is not None:

                    # Determine the speaker prefix to use
                    if is_extend and lookup_text in standalone_lines:
                        # Extend -> standalone: prefer the script-context
                        # speaker (correct under choice branches) and fall
                        # back to file-order last_speaker if missing.
                        script_speaker = (speaker_map.get(last_source_line, '')
                                          if last_source_line else '')
                        use_prefix = (script_speaker or last_speaker
                                      or speaker_prefix)
                    elif is_extend:
                        use_prefix = speaker_prefix
                    else:
                        use_prefix = speaker_prefix

                    # Output comment line
                    output.append(line)

                    # Output first part
                    first_text = eng_parts[0]
                    if is_extend and lookup_text not in standalone_lines:
                        first_text = '\\n' + first_text
                    output.append(_format_tl_line(tl_indent, use_prefix, first_text))

                    # Output additional parts as standalone speaker lines
                    for extra_part in eng_parts[1:]:
                        output.append(_format_tl_line(tl_indent, use_prefix, extra_part))

                    changes += 1
                    i += 2
                    continue

        output.append(line)
        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    return changes


def fill_string_translations(filepath, string_translations):
    """
    Fill in Ren'Py string translation blocks.

    Format:
        old "Chinese"
        new "Chinese"  ->  new "English"
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    output = []
    changes = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for "old" line
        old_match = re.match(r'^(\s+)old "(.+)"$', line)
        if old_match and i + 1 < len(lines):
            chinese = old_match.group(2)
            next_line = lines[i + 1]
            new_match = re.match(r'^(\s+)new "(.+)"$', next_line)

            if new_match and chinese in string_translations:
                eng = string_translations[chinese]
                eng_escaped = eng.replace('"', '\\"')
                indent = new_match.group(1)
                output.append(line)
                output.append(f'{indent}new "{eng_escaped}"')
                changes += 1
                i += 2
                continue

        output.append(line)
        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    return changes


# 转换器会给正文里的专有名词加 {i}…{/i}（见 convert_script.py PROPER_NOUNS），
# 但 demo_script_eng.txt 里两边都是素文本 —— 查表键必须匹配转换后的文本。
# 这里为每个含专有名词的条目补一份「斜体键 → 斜体值」，中英各自斜体化。
_PROPER_NOUN_PAIRS = [('尤里娅', 'Julia'), ('KAS', 'KAS')]


def _italicize(text, nouns):
    for noun in nouns:
        if noun in text and '{i}' + noun + '{/i}' not in text:
            text = text.replace(noun, '{i}' + noun + '{/i}')
    return text


def augment_translations(translations, choice_translations):
    """派生条目：
    1. 问询段回显：转换器把玩家所选以「——选项文本」回显进框（可与响应并成一条
       extend）——为每个选项合成 '——中文' → '——英文' 条目，供分段命中。
    2. 斜体键：正文里的 尤里娅/KAS 会被转换器包成 {i}…{/i}，为含名词的条目补
       斜体化的键值对（英文侧对应 Julia/KAS 同样斜体）。
    3. 问询段逻辑判断行：say 文本是 [interro_*!t] 插值（不来自 eng 剧本），
       在这里直接给出译文。
    """
    for cn, en in choice_translations.items():
        translations.setdefault('——' + cn, ['——' + en])
    cn_nouns = [p[0] for p in _PROPER_NOUN_PAIRS]
    en_nouns = [p[1] for p in _PROPER_NOUN_PAIRS]
    for cn, parts in list(translations.items()):
        cn2 = _italicize(cn, cn_nouns)
        if cn2 != cn and cn2 not in translations:
            translations[cn2] = [_italicize(p, en_nouns) for p in parts]
    translations.setdefault('精神状态：[interro_mental!t]',
                            ['Mental State: [interro_mental!t]'])
    translations.setdefault('人格特质：[interro_trait!t]',
                            ['Personality Trait: [interro_trait!t]'])
    translations.setdefault('污染进程：[interro_pollution!t]',
                            ['Contamination Progress: [interro_pollution!t]'])
    translations.setdefault('建议执行：[interro_verdict!t]',
                            ['Recommended Action: [interro_verdict!t]'])


# 问询段评估结论（variables.rpy interro_evaluate() 里的 __() 字符串）——
# 运行时经 [var!t] 翻译，字符串翻译条目在 tl 的 strings 块里。
INTERRO_LABELS = {
    '平稳': 'Stable',
    '疯狂': 'Deranged',
    '分裂': 'Divided',
    '检测失败': 'Detection Failed',
    '冷静': 'Composed',
    '对抗': 'Adversarial',
    '幻觉': 'Hallucination',
    '死亡': 'Death',
    '幻灭': 'Disillusion',
    '无污染': 'Uncontaminated',
    '记忆消除并释放': 'Memory erasure and release',
    '记忆消除和无限期监禁': 'Memory erasure and indefinite detention',
    '脑白质切除、记忆消除并释放': 'Lobotomy, memory erasure and release',
    '脑白质切除、记忆消除并无限期监禁': 'Lobotomy, memory erasure and indefinite detention',
}


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    eng_script = os.path.join(base_dir, 'demo_script_eng.txt')
    tl_dir = os.path.join(base_dir, 'game', 'tl', 'english')

    # Step 1: Parse bilingual script
    print("Parsing bilingual script...")
    translations, standalone_lines, choice_translations = parse_bilingual_script(eng_script)
    augment_translations(translations, choice_translations)
    print(f"  Found {len(translations)} Chinese->English mappings")
    print(f"  Found {len(choice_translations)} choice translations")
    if standalone_lines:
        print(f"  Found {len(standalone_lines)} EN独立 (standalone) markers")

    # Debug: show first few
    for cn, en_parts in list(translations.items())[:5]:
        print(f"    '{cn[:30]}...' -> '{en_parts[0][:30]}...'")

    # Step 2: Fill dialogue translation files
    # Pass the source script path (game/scripts/) so fill_dialogue_translation
    # can resolve the script-context speaker — needed for correct
    # standalone-extend conversion under choice branches.
    source_scripts_dir = os.path.join(base_dir, 'game', 'scripts')
    for script_file in ['prologue.rpy', 'route1.rpy']:
        filepath = os.path.join(tl_dir, 'scripts', script_file)
        source_path = os.path.join(source_scripts_dir, script_file)
        if os.path.exists(filepath):
            changes = fill_dialogue_translation(
                filepath, translations, standalone_lines,
                source_script_path=source_path)
            print(f"  {script_file}: {changes} lines translated")

    # Step 3: Fill UI string translations
    ui_translations = {
        # Quick menu
        '历史': 'History',
        '跳过': 'Skip',
        '自动': 'Auto',
        '存档': 'Save',
        '读档': 'Load',
        '快存': 'Q.Save',
        '快读': 'Q.Load',
        '设置': 'Settings',
        # Main menu
        '开始游戏': 'Start',
        '读取数据': 'Load Game',
        '删除存档': 'Delete Saves',
        '清除进度': 'Clear Progress',
        '音乐鉴赏': 'Music Room',
        '历史记录': 'History',
        '结束回放': 'End Replay',
        '标题画面': 'Main Menu',
        '关于': 'About',
        '退出': 'Quit',
        '返回': 'Return',
        # Save/Load
        '第 {} 页': 'Page {}',
        '自动存档': 'Auto Save',
        '快速存档': 'Quick Save',
        '空存档位': 'Empty Slot',
        '删除': 'Delete',
        # Preferences
        '显示模式': 'Display',
        '窗口': 'Window',
        '全屏': 'Fullscreen',
        '跳过设置': 'Skip',
        '未读文本': 'Unseen Text',
        '选项后继续': 'After Choices',
        '过场后继续': 'After Transitions',
        '文字速度': 'Text Speed',
        '自动前进时间': 'Auto-Forward Time',
        '音乐音量': 'Music Volume',
        '音效音量': 'Sound Volume',
        '测试': 'Test',
        '存档管理': 'Save Management',
        '删除所有存档': 'Delete All Saves',
        # History
        '暂无历史记录。': 'No history yet.',
        # Music room
        '停止播放': 'Stop',
        # About
        '版本 [config.version!t]\n': 'Version [config.version!t]\n',
        '在此处添加游戏介绍...\n': 'Game description goes here...\n',
        '制作人员：\n': 'Credits:\n',
        '- 策划：\n- 程序：\n- 美术：\n- 音乐：\n': '- Planning:\n- Programming:\n- Art:\n- Music:\n',
        # Demo end card + filled credits (game/screens.rpy)
        '感谢游玩本Demo！\n请务必在正作继续下潜~\n':
            'Thanks for playing the demo!\nBe sure to keep diving with us in the full release~\n',
        ('- 制作人：Jerrix\n- 剧本：Jerrix\n- 美术：Gara、Mermo\n'
         '- 音乐：Kevin Qiyuan Wang, audionautix.com, FabienC@RustedMusicStudio\n'
         '- 音效：Sirderf，soundscalpel.com，rrehl, chewiesmissus, gravitysound.studio\n'
         '- 编辑：倪佼佼\n- 程序：Jerrix\n'):
            ('- Producer: Jerrix\n- Script: Jerrix\n- Art: Gara, Mermo\n'
             '- Music: Kevin Qiyuan Wang, audionautix.com, FabienC@RustedMusicStudio\n'
             '- Sound: Sirderf, soundscalpel.com, rrehl, chewiesmissus, gravitysound.studio\n'
             '- Editing: Ni Jiaojiao\n- Programming: Jerrix\n'),
        # Confirm
        '确定': 'OK',
        '取消': 'Cancel',
        # Skip indicator
        '快进中': 'Skipping',
        # 文字墙（screens.rpy text_wall）
        '对不起…': "I'm sorry…",
    }

    # Fill screens.rpy
    screens_path = os.path.join(tl_dir, 'screens.rpy')
    if os.path.exists(screens_path):
        changes = fill_string_translations(screens_path, ui_translations)
        print(f"  screens.rpy: {changes} UI strings translated")

    # Fill choice strings in route1.rpy
    route1_path = os.path.join(tl_dir, 'scripts', 'route1.rpy')
    if os.path.exists(route1_path):
        changes = fill_string_translations(route1_path, choice_translations)
        print(f"  route1.rpy choices: {changes} strings translated")

    # Fill 问询段评估结论 string stubs（__() 字符串的 old/new 块；stub 落在哪个
    # tl 文件取决于 Ren'Py 生成器，这里对可能的落点都过一遍，没有条目就是 0）。
    for rel in ['scripts/variables.rpy', 'scripts/route1.rpy', 'screens.rpy', 'common.rpy']:
        p = os.path.join(tl_dir, rel)
        if os.path.exists(p):
            changes = fill_string_translations(p, INTERRO_LABELS)
            if changes:
                print(f"  {rel}: {changes} interro labels translated")

    print("\nTranslation fill complete!")


if __name__ == '__main__':
    main()

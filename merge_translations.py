# -*- coding: utf-8 -*-
"""
Rebuild demo_script_eng.txt against the (new) demo_script.txt.

Walks the new Chinese script line-by-line. For each content line:
  - exact-match lookup in the old bilingual file's (Chinese → English) map
  - normalized-match fallback (strips common drift: trailing/spaced punctuation,
    stylistic 的/了/啊 additions, 全角 vs 半角)
  - if still no hit, leaves a [[TODO]] sentinel for manual fill-in

Stage directions (【...】), choice markers (A:/B:/C:), section headers, blank
lines, and the title line all pass through unchanged — they are never paired
with an English line in the bilingual file.

Output overwrites demo_script_eng.txt. Run a git diff afterward to review.
"""
import difflib
import re
import shutil
from pathlib import Path

PROJECT = Path(__file__).parent
NEW_ZH = PROJECT / "demo_script.txt"
OLD_BILINGUAL = PROJECT / "demo_script_eng.txt"
OUT_BILINGUAL = OLD_BILINGUAL  # overwrite

# Character names recognized at line start (e.g., "王霜：" or "王霜【...】：")
CHAR_NAMES = ['王霜（？）', '王霜', '阿鹤', '尸首', '路人甲', '路人乙', '路人丙',
              '路人丁', '杰罗瓦', '米姐', '尤里娅']
CHAR_NAMES.sort(key=len, reverse=True)
CHAR_PAT = '|'.join(re.escape(n) for n in CHAR_NAMES)


def is_stage_direction(line):
    return line.startswith('【') and line.endswith('】')


def is_choice_line(line):
    return bool(re.match(r'^[ABC][：:]\s*.+$', line))


def is_section_header(line):
    return bool(re.match(r'^[一二三四五六七八九十]+周目', line))


def is_chinese(text):
    return bool(re.search(r'[一-鿿]', text))


def is_english(text):
    """Looks like an English content line: contains Latin letters, no Chinese chars."""
    if not text:
        return False
    if is_stage_direction(text) or is_choice_line(text) or is_section_header(text):
        return False
    if re.match(rf'^({CHAR_PAT})', text):
        return False
    if is_chinese(text):
        return False
    # Must contain at least one Latin letter (lines starting with — / "(" / etc.
    # are still English if they have words in them, e.g. "——But 'Everything' is...").
    return bool(re.search(r'[A-Za-z]', text))


def strip_speaker_prefix(line):
    """Strip "char_name【action】：" or "char_name：" prefix; return the content."""
    m = re.match(rf'^({CHAR_PAT})【.+?】[：:](.*)$', line)
    if m:
        return m.group(2).strip()
    m = re.match(rf'^({CHAR_PAT})[：:](.*)$', line)
    if m:
        return m.group(2).strip()
    return line


def normalize(s):
    """Normalize Chinese line for fuzzy matching.

    Drops whitespace, normalizes 全角/半角 punctuation, strips trailing punctuation
    that often drifts (。, ，, 。。。, ... etc), and removes common stylistic
    particles that get added/removed without changing meaning.
    """
    s = s.strip()
    # Unify quote/punctuation variants
    s = s.translate(str.maketrans({
        '，': ',',  # ，
        '。': '.',  # 。
        '？': '?',  # ？
        '！': '!',  # ！
        '：': ':',  # ：
        '；': ';',  # ；
        '“': '"',  # “
        '”': '"',  # ”
        '‘': "'",  # ‘
        '’': "'",  # ’
        '（': '(',  # （
        '）': ')',  # ）
        '　': ' ',  # ideographic space
    }))
    # Collapse whitespace and ellipses
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'\.{2,}', '...', s)
    # Drop trailing punctuation entirely (drift is common at line ends)
    s = re.sub(r'[\.,!?:;…]+$', '', s)
    return s


def parse_bilingual(path):
    """Read old bilingual file → translation maps + choice translations.

    The 【EN独立】 marker has two semantic uses in this file (per fill_translations.py):
      1. Before the very first English line after a Chinese line — signals that
         the Chinese was an `extend` but should render as a STANDALONE textbox
         in English.
      2. Between two English lines under the same Chinese line — splits one
         Chinese line into multiple English textboxes.
    We capture both so the regenerated bilingual preserves the meaning.

    Returns three maps. Each dialogue value is a dict:
      {"standalone": bool, "parts": [str, ...]}
    """
    with path.open(encoding='utf-8') as f:
        lines = [ln.rstrip('\n') for ln in f]

    zh_to_en = {}
    zh_to_en_normalized = {}
    choice_zh_to_en = {}  # key: "算了"  →  value: "Nah" (no prefix/suffix)
    # A 【EN独立】 marker sitting BETWEEN the previous pair's English and the
    # current Chinese line semantically attaches to the *next* Chinese's
    # English (extend → standalone). Carry that forward in pending_standalone.
    pending_standalone = False
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Handle standalone 【EN独立】 marker BEFORE the generic stage-direction
        # skip below, so the flag isn't silently lost.
        if line == '【EN独立】':
            pending_standalone = True
            i += 1
            continue
        if not line or is_stage_direction(line) or is_section_header(line):
            i += 1
            continue
        # Choice line — look for the parallel English choice on the next line
        if is_choice_line(line):
            zh_choice = _strip_choice_decoration(line)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_choice_line(lines[j].strip()):
                en_choice = _strip_choice_decoration(lines[j].strip())
                if zh_choice and en_choice:
                    choice_zh_to_en.setdefault(zh_choice, en_choice)
                i = j + 1
            else:
                i += 1
            continue
        # If this is Chinese, look ahead for English (possibly preceded by
        # 【EN独立】 or split across multiple parts by interspersed 【EN独立】).
        if is_chinese(line):
            content_zh = strip_speaker_prefix(line)
            # Pattern A (marker before the Chinese): carried in pending_standalone.
            # Pattern B (marker after the Chinese, before its English): handled
            # by the walk-forward block right below.
            standalone = pending_standalone
            pending_standalone = False
            # Walk forward skipping blanks; if we hit 【EN独立】 BEFORE any
            # English, set the standalone flag.
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() == '【EN独立】':
                standalone = True
                j += 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
            # First English part
            if j < len(lines) and is_english(lines[j].strip()):
                parts = [lines[j].strip()]
                j += 1
                # Look ahead for repeated 【EN独立】 → English pairs (case #2)
                while j < len(lines):
                    k = j
                    while k < len(lines) and not lines[k].strip():
                        k += 1
                    if k < len(lines) and lines[k].strip() == '【EN独立】':
                        # next non-empty after the marker
                        kk = k + 1
                        while kk < len(lines) and not lines[kk].strip():
                            kk += 1
                        if kk < len(lines) and is_english(lines[kk].strip()):
                            parts.append(lines[kk].strip())
                            j = kk + 1
                            continue
                    break
                value = {"standalone": standalone, "parts": parts}
                zh_to_en.setdefault(content_zh, value)
                zh_to_en_normalized.setdefault(normalize(content_zh), value)
                i = j
                continue
        i += 1

    return zh_to_en, zh_to_en_normalized, choice_zh_to_en


def _strip_choice_decoration(line):
    """Remove A:/B:/C: prefix and (madness+N) suffix from a choice line."""
    s = re.sub(r'^[ABC][：:]\s*', '', line)
    s = re.sub(r'[（(]madness\s*\+?\s*\d+[）)]', '', s)
    return s.strip()


def merge():
    if not OLD_BILINGUAL.exists():
        raise SystemExit(f"Missing {OLD_BILINGUAL}")
    if not NEW_ZH.exists():
        raise SystemExit(f"Missing {NEW_ZH}")

    # Backup old bilingual just in case
    backup = OLD_BILINGUAL.with_suffix('.txt.before_merge')
    shutil.copy2(OLD_BILINGUAL, backup)

    zh_to_en, zh_to_en_norm, choice_zh_to_en = parse_bilingual(OLD_BILINGUAL)
    print(f"Old bilingual: {len(zh_to_en)} exact Chinese→English pairs, "
          f"{len(choice_zh_to_en)} choice pairs "
          f"({len(zh_to_en_norm)} dialogue keys after normalization)")
    # Precompute normalized-key list for fuzzy fallback
    norm_keys = list(zh_to_en_norm.keys())

    with NEW_ZH.open(encoding='utf-8') as f:
        new_lines = [ln.rstrip('\n') for ln in f]

    out = []
    matched_exact = matched_normalized = matched_fuzzy = unmatched = 0
    choice_matched = choice_unmatched = 0

    for raw in new_lines:
        line = raw.strip()

        # Pass through stage directions, section headers, blanks
        if not line or is_stage_direction(line) or is_section_header(line):
            out.append(raw)
            continue

        # Choice line — emit Chinese, then attach the parallel English choice
        # if we have it. Preserves the A/B/C prefix from the new line and
        # plugs the translated choice text into the same slot (without
        # (madness+N) — Ren'Py adds that from the converter, not the bilingual).
        if is_choice_line(line):
            out.append(raw)
            zh_choice = _strip_choice_decoration(line)
            if zh_choice in choice_zh_to_en:
                # Reuse the new line's A:/B:/C: prefix so the English choice
                # sits in the right slot (fill_translations.py keys by Chinese
                # without prefix, but the bilingual file uses the prefix).
                prefix_match = re.match(r'^([ABC][：:])\s*', line)
                prefix = prefix_match.group(1) + ' ' if prefix_match else ''
                out.append(f'{prefix}{choice_zh_to_en[zh_choice]}')
                choice_matched += 1
            else:
                out.append('[[TODO: translate choice]]')
                choice_unmatched += 1
            continue

        # Title-ish first line: pass through
        if not is_chinese(line):
            out.append(raw)
            continue

        # Content line — emit Chinese, then attempt to attach English.
        out.append(raw)
        content_zh = strip_speaker_prefix(line)
        value = None
        if content_zh in zh_to_en:
            value = zh_to_en[content_zh]
            matched_exact += 1
        else:
            norm = normalize(content_zh)
            if norm in zh_to_en_norm:
                value = zh_to_en_norm[norm]
                matched_normalized += 1
            else:
                # Fuzzy: catch larger drift — author often rewrites a line by
                # dropping a clause while keeping the spine. cutoff=0.6 catches
                # e.g. "王霜：不用紧张，阿鹤，你可以畅所欲言。" ↔
                #      "王霜：不用紧张，阿鹤，这里是绝对安全的，你可以畅所欲言。"
                # while still rejecting truly distinct lines (those rate <0.4).
                close = difflib.get_close_matches(norm, norm_keys, n=1, cutoff=0.6)
                if close:
                    value = zh_to_en_norm[close[0]]
                    matched_fuzzy += 1
        if value is None:
            out.append('[[TODO: translate]]')
            unmatched += 1
            continue
        # Emit English part(s), preserving 【EN独立】 markers from the original:
        #   - if standalone=True, 【EN独立】 goes BEFORE the first English part
        #   - between successive parts, 【EN独立】 splits one Chinese into
        #     multiple English textboxes (case #2 in fill_translations.py)
        if value["standalone"]:
            out.append('【EN独立】')
        for idx, part in enumerate(value["parts"]):
            if idx > 0:
                out.append('【EN独立】')
            out.append(part)

    OUT_BILINGUAL.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f"Wrote {OUT_BILINGUAL.name}:")
    print(f"  dialogue: {matched_exact} exact, {matched_normalized} normalized, "
          f"{matched_fuzzy} fuzzy, {unmatched} TODO")
    print(f"  choices : {choice_matched} matched, {choice_unmatched} TODO")
    print(f"Backup of pre-merge file saved at {backup.name}")


if __name__ == "__main__":
    merge()

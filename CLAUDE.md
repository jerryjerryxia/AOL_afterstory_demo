# Endless Summer Syndrome Demo - Ren'Py Visual Novel

「以第一性原理！从原始需求和问题本质出发，不从惯例或模板出发。
1. 不要假设我清楚自己想要什么。动机或目标不清晰时，停下来讨论。
2. 目标清晰但路径不是最短的，直接告诉我并建议更好的办法。
3. 遇到问题追根因，不打补丁。每个决策都要能回答"为什么"。
4. 输出说重点，砍掉一切不改变决策的信息。」

**IMPORTANT: Always work directly in `X:\GameDev\Endless Summer Syndrome Demo`. Do NOT use git worktrees - the game can only be launched from the main location.**

## Quick Reference

**Build scripts:** `python convert_script.py` - Converts `main_script_raw.txt` → route `.rpy` files

**Main files:**
- `main_script_raw.txt` - Source of truth for story content
- `convert_script.py` - Script converter
- `game/screens.rpy` - All UI screens
- `game/scripts/variables.rpy` - Game variables and helper functions

## Raw Script Format

```
王霜：Character dialogue
阿鹤：Another character
Plain text is narration
【Stage direction → becomes comment】
A: Choice A text
B: Choice B text（madness+1）
【选项分线到此结束】
【展示一周目分屏"Title"】
【Bad End 1：Ending name】
```

**Characters in converter:** `王霜`→`wangshuang`, `阿鹤`→`ahe`, `尸首`→`shishou`

## Key Implementation Details

1. **Choices keep dialogue visible** using `extend ""` in menu blocks

2. **Delete saves** uses `renpy.list_slots()` + `renpy.unlink_save()` (not file operations)

3. **Route progression:** `get_current_route()` in variables.rpy determines which route to play

4. **Variables:**
   - `default X` = resets each playthrough
   - `default persistent.X` = survives across saves
   - `define X` = constant

5. **Init order:** gui.rpy (-2) → screens.rpy (-1) → others (0)

## Adding Content

**New character:**
1. Add `define newchar = Character("名字", color="#hex")` in characters.rpy
2. Add to char_var dict in convert_script.py
3. Run converter

**New ending:**
1. Add `default persistent.new_end_unlocked = False` in variables.rpy
2. Add case to `unlock_ending()` function
3. Use `【Bad End N：name】` in raw script

## Testing Workflow

**Before letting the user test, run `/preflight`.** This runs all QA checks in sequence:
orphaned .rpyc scan → kill zombies → lint → test suite → cleanup → traceback check.

Only hand off for playtesting when preflight reports **READY**.

**Manual steps (if needed):**

1. **Ren'Py Lint:**
   ```
   X:\RenPy\renpy-8.5.0-sdk\renpy.exe "X:\GameDev\Endless Summer Syndrome Demo" lint
   ```
   - Fix any "Unreachable Statements" (usually missing `【选项分线到此结束】` markers)
   - Fix any undefined labels or variables

2. **Check traceback.txt:**
   ```
   X:\GameDev\Endless Summer Syndrome Demo\traceback.txt
   ```
   - If exists, read and fix the error
   - Delete after confirming fix

3. **Regenerate scripts after raw script changes:**
   ```
   python convert_script.py
   ```

**Google Docs Sync:**
- `python sync_gdocs.py pull` - Download from Google Docs. note that this is usually not used. do not use unless specifically asked to. 
- `python sync_gdocs.py push` - Upload to Google Docs. 

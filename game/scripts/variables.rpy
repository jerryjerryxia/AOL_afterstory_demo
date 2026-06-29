## variables.rpy
## 游戏变量和标记 / Game Variables and Flags

################################################################################
## 测试模式 - Test Mode
## 设为 True 可以快进未读文本，用于测试多周目流程
################################################################################

define config.developer = False  # 正式发布：关闭开发者模式
default persistent.test_mode = True  # 测试模式开关

## 玩家是否进入过游戏（用于判断 game→menu 回流时要不要强制重启 polyhedron channel）。
## 用 persistent 是因为 MainMenu() action 会清掉普通的游戏变量但保留 persistent。
default persistent.polyhedron_started_game = False

## "当前周目里有没有存档" —— 旧设计，保留 default 以兼容老 persistent；screen 不再读。
default persistent.has_save_in_run = False

## 最近一次通关时间戳。主菜单按钮按 max(slot_mtime) > 该值 决定 Continue 还是 Start，
## 不是简单"有没有存档"。这样通关后旧存档还在但 Continue 不显示，
## 新周目玩家再存档时 mtime 比通关时间晚，Continue 又自动出现。
default persistent.last_route_completion_time = 0.0

init python:
    import time
    import re

    ## 主菜单 Continue 按钮和 load_most_recent_save 都用这个白名单。
    ## 必须用白名单不能用 "exclude auto-" 黑名单 —— Ren'Py 还会留下
    ## _reload-1（每次重启都更新 mtime，会盖掉真正的存档）、_quit-1 等
    ## 内部用 slot，黑名单全漏掉。匹配 `N-N`（玩家手动存档）和 `quick-N`
    ## （玩家按 Q 触发的快存），其它全不算。
    _CONTINUABLE_RE = re.compile(r"^(\d+|quick)-\d+$")

    def _continuable_slots():
        """玩家"主动"做的存档 —— 排除 autosave、_reload-* 等内部 slot。
        Continue 应该 = "玩家自己最后一次保存的位置"，不是 = "上次玩到哪"。"""
        return [s for s in renpy.list_slots() if _CONTINUABLE_RE.match(s)]

    def has_continuable_save():
        """是否有"通关之后"做的存档（决定主菜单显示 Continue 还是 Start）。"""
        slots = _continuable_slots()
        if not slots:
            return False
        latest = max((renpy.slot_mtime(s) or 0) for s in slots)
        return latest > (persistent.last_route_completion_time or 0)

init python:
    # 测试模式：允许跳过未读文本
    if persistent.test_mode:
        config.allow_skipping = True
        _preferences.skip_unseen = True

################################################################################
## 持久化数据（跨存档保存）
################################################################################

## Demo版：无结局解锁和周目追踪

## 音乐解锁状态（用于音乐鉴赏）
default persistent.music_unlocked = set()

################################################################################
## 游戏内变量（每次游戏重置）
################################################################################

## 当前路线
default current_route = None

## madness 值 - 根据选择增加
default madness = 0

## 关键选择记录
default choice_flags = {}

## 当前场景音乐 ID（由 set_scene_music 设置；after_load 用它恢复音乐）
default current_music_scene = None

################################################################################
## 存档加载后恢复音乐
################################################################################

label after_load:
    if current_music_scene is not None:
        $ set_scene_music(current_music_scene)
    ## 同 `label start`：进游戏(任何方式，包括 load save)都要标记 polyhedron
    ## 在下次回到主菜单时强制重启 channel。否则 load → 玩 → 回菜单又会破。
    $ persistent.polyhedron_started_game = True
    ## load 进游戏说明肯定有存档可继续（兼容老 flag，新逻辑用 last_route_completion_time）
    $ persistent.has_save_in_run = True
    ## 强制重新应用当前语言的 translate python 块。
    ## 否则：玩家在主菜单切到英文 → 点 Continue → load 后 wangshuang.name 等
    ## Character mutation 没有重新跑，名字框还是中文。
    ## force=True 即使语言没变也重跑一遍 translate python，把 .name 全部刷成英文。
    $ renpy.change_language(_preferences.language, force=True)
    return

################################################################################
## 辅助函数
################################################################################

init python:
    def unlock_music(track_name):
        """解锁音乐鉴赏中的曲目"""
        if track_name not in persistent.music_unlocked:
            persistent.music_unlocked.add(track_name)

    def is_music_unlocked(track_name):
        """检查曲目是否已解锁"""
        return track_name in persistent.music_unlocked

    def get_music_room_tracks():
        """音乐鉴赏的曲目列表，从 scene_music 推导（单一数据源）。
        按场景定义顺序去重 —— 每个场景固定一首，正好是玩家在剧情里听到曲子的先后
        顺序。在 screen 显示时（运行时）才调用，所以不受 init offset 顺序影响。"""
        seen = set()
        result = []
        for scene_id in scene_music:
            for track in scene_music[scene_id]["tracks"]:
                if track["id"] not in seen:
                    seen.add(track["id"])
                    result.append(track)
        return result

    def unlock_ending(ending_id):
        """Demo版：无操作"""
        pass

    def demo_reboot_after_route():
        """Demo 通关后整个游戏 reboot 一次，让 polyhedron channel 状态干净，
        第二次 Start 不会渲染成 checker board。persistent 不会被清。

        但自动化测试（renpy ... test）时绝不 reboot —— utter_restart 会重启整个
        引擎，让测试进程在跑完全部用例、打印 PASSED 之后仍无法退出（表现为"测试
        到最后卡死、要等很久"）。测试模式下直接跳过，正常游玩照常 reboot。"""
        if getattr(renpy.game.args, "command", None) == "test":
            return
        renpy.utter_restart()

    import wave as _wave
    _sfx_dur_cache = {}
    _sfx_end_time = [0.0]   # 最近一次音效的预计结束时刻（绝对游戏时钟，秒）

    def _sfx_duration(path):
        """读 wav 头算时长（秒），缓存。读不到就当 0（不阻塞）。"""
        if path not in _sfx_dur_cache:
            d = 0.0
            try:
                f = renpy.open_file(path)
                w = _wave.open(f)
                d = w.getnframes() / float(w.getframerate())
                w.close()
            except Exception:
                d = 0.0
            _sfx_dur_cache[path] = d
        return _sfx_dur_cache[path]

    def play_sfx(path):
        """播放音效（sound 声道，受音效音量控制），并记下预计结束时刻供 wait_sfx 用。
        转换器在音效标记处发 `$ play_sfx(...)`，在下一句正文前发 `$ wait_sfx()`。"""
        renpy.sound.play(path)
        _sfx_end_time[0] = time.time() + _sfx_duration(path)

    def hard_pause(t):
        """不可点击快进的暂停（长黑场过渡用）。和 wait_sfx 一样，自动化测试里跳过 ——
        否则 5s+ 的 hard 暂停会吃满 `advance until` 的超时预算。正常游玩照常等。"""
        if getattr(renpy.game.args, "command", None) == "test":
            return
        renpy.pause(t, hard=True)

    def wait_sfx():
        """阻塞到最近一次音效播完，再放行下一句正文（point 3）。用「剩余时长」做**单次
        有界** hard 暂停：自动结束（绝不卡死），中间转场已耗掉的时间会自动扣除，所以
        音效与碎裂等转场仍同步、转场之后的正文才补等剩余部分。hard=True → 等待期间
        点击/快进都跳不过，「音效播完前不出现下段文字」。"""
        ## 自动化测试（renpy ... test）里 hard 暂停无法被 advance 跳过，会吃满
        ## `advance until` 的超时预算 → 直接跳过等待。正常游玩照常等。
        if getattr(renpy.game.args, "command", None) == "test":
            return
        remaining = _sfx_end_time[0] - time.time()
        if remaining > 0:
            renpy.pause(remaining, hard=True)

    def unlock_route(route_num):
        """Demo版：通关时记下 last_route_completion_time，主菜单按钮回到 Start —— 旧存档
        虽然还在，但 mtime 早于 completion_time，has_continuable_save() 会返回 False。"""
        persistent.has_save_in_run = False  # 兼容老 persistent
        persistent.last_route_completion_time = time.time()

    def get_current_route():
        """Demo版：始终返回1"""
        return 1

    def load_most_recent_save():
        """Continue button 用：按 mtime 找最近一次玩家主动存档并 load 进游戏。
        排除 autosave —— 详见 _continuable_slots 注释。"""
        slots = _continuable_slots()
        if not slots:
            return
        latest = max(slots, key=lambda s: renpy.slot_mtime(s) or 0)
        renpy.load(latest)

    def exit_main_menu_to_game():
        """主菜单退场动画跑完后调用：通关后做的存档 → Continue；否则新开。
        Continue 不武装 _intro_fade_pending（玩家不在序章首句），新开才武装。
        和 screen 用同一个判断 (has_continuable_save)，避免按钮和动作不一致。"""
        if has_continuable_save():
            load_most_recent_save()
            return
        renpy.store._intro_fade_pending = True
        renpy.jump_out_of_context("start")

    ##########################################################################
    ## 场景音乐
    ##########################################################################

    def set_scene_music(scene_id):
        """设置当前场景音乐并播放（每个场景固定一首）。

        if_changed=True：若该曲已在播放则不重启 —— 这样主菜单的 kevin_openning
        能无缝续进序章（序章首曲也是 kevin_openning），玩家点"开始游戏"前后不断。
        """
        global current_music_scene
        store.current_music_scene = scene_id

        if scene_id not in scene_music:
            return

        tracks = scene_music[scene_id]["tracks"]
        if not tracks:
            return

        track = tracks[0]
        ## 玩家第一次听到这首曲子 → 在音乐鉴赏里解锁它。
        unlock_music(track["id"])
        renpy.music.play("audio/bgm/" + track["file"],
                         fadeout=1.0, fadein=1.0, if_changed=True)

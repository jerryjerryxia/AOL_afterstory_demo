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

## 当前环境音路径（由 play_ambient 设置；after_load 用它恢复。不存这个的话，
## 在沙漠里存档再读档就是一片死寂——和音乐一样的问题，一样的解法）
default current_ambient = None

## 上一次 【音乐停】 时音乐播到的位置（秒）。music_config 里标了 "resume": True
## 的曲子从这里接着放，而不是从头开始。见 stash_music_pos / music_track_spec。
default music_resume_pos = 0.0

## 「不分句」开关：转换器在 Extended 大文本框「不分句」块前后置 True/False，
## 期间 add_click_pauses 直接放行——该块每行整句一次点击展示，不在句中插 {w}。
default no_click_split = False

################################################################################
## 存档加载后恢复音乐
################################################################################

label after_load:
    if current_music_scene is not None:
        $ set_scene_music(current_music_scene)
    if current_ambient is not None:
        ## fadein=0：读档瞬间环境音就该在场，2 秒渐入会让开场几句显得突兀。
        $ play_ambient(current_ambient, fadein=0.0)
    ## 如果这份存档正停在多面体场景上，要在这里重启视频 channel：主菜单现在
    ## mount 时会把 channel 停掉（sea.png 背景，视频没人看），不重启的话
    ## load 进来 Movie 没有帧源，渲染成黑屏/checker board。
    ## 只在场景真的显示这个 Movie 时才播 —— 其他场景没必要白解一路 webm。
    if renpy.showing("bg_polyhedron_video"):
        python:
            try:
                renpy.music.stop(channel="polyhedron_video")
            except Exception:
                pass
            renpy.music.play(
                "images/bg/polyhedron.webm",
                channel="polyhedron_video", loop=True)
    ## flag 语义已废弃，只是保持置位（老逻辑兼容）。
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
        # reboot 后主菜单整屏从黑淡入一次（否则 utter_restart 落地很生硬）。
        # renpy.session 跨 utter_restart 存活、真正退出才清 —— 见 screens.rpy main_menu。
        renpy.session["_demo_return_fade"] = True
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

    ## ★每个音效的相对音量★——想单独调某个音效响度就改这里的数字（1.0 = 文件原始
    ## 响度，乘在"音效音量"滑条之上）。键 = audio/sfx/ 下的文件基名（不含 .wav）；
    ## 未列出的音效默认 1.0。>1.0 会放大，但超过文件本身的余量会削波失真——括号内是
    ## 各文件峰值到 0dBFS 的安全上限（用峰值算的粗略值）：
    SFX_GAIN = {
        "Bubbles_10":             1.8,  # 泡泡：头出水面 / 水底上浮（原 -9.5dBFS，偏轻）→调响；安全上限约 ×3.0
        "face-down-bubble":       1.0,  # 脸入水冒泡（原 -3.0dBFS，已较响）；安全上限仅约 ×1.4
        "glass-smash-normalized": 1.0,  # 玻璃破碎（原 -15.4dBFS）；安全上限约 ×5.9
    }

    def play_sfx(path):
        """播放音效（sound 声道，受音效音量控制），并记下预计结束时刻供 wait_sfx 用。
        转换器在音效标记处发 `$ play_sfx(...)`，在下一句正文前发 `$ wait_sfx()`。
        每个音效的单独响度见上面的 SFX_GAIN（relative_volume）。"""
        import os as _os
        base = _os.path.splitext(_os.path.basename(path))[0]
        renpy.sound.play(path, relative_volume=SFX_GAIN.get(base, 1.0))
        _sfx_end_time[0] = time.time() + _sfx_duration(path)

    ## ★环境音相对音量★——键 = audio/sfx/ 下的文件基名。同 SFX_GAIN 的用法。
    ##
    ## 沙漠长风现在播的是限幅重制版 desert_wind_bed.ogg：-23.0 LUFS、峰 -1.3 dBFS，
    ## 已经在文件里配平好，所以这里是 1.0（不列出即 1.0）。
    ##
    ## 为什么必须重制而不是继续在这里推增益：原始素材 -30.1 LUFS 但峰值 -0.11 dBFS，
    ## 波峰因数 30 dB（中位数才 -24.8 dBFS，只有孤立阵风摸到顶）—— 平均响度低、
    ## 峰值却没余量，纯增益一过 1.0 阵风就削顶，天花板卡死在 +2.9 dB。限幅把那些
    ## 尖峰按下去（最大压缩 10.3 dB，释放 800ms），腾出的余量整体抬起来，净得 +7 dB。
    ## 顺带也让铺底不再有 30 dB 起伏 —— 垫在对白底下的环境音本来就不该忽大忽小。
    ## 现在离 0 dBFS 还剩 1.3 dB，想再微调可以在这里给到 1.15 上下，别超过。
    AMBIENT_GAIN = {
    }

    def play_ambient(path, fadein=2.0):
        """环境音铺底：在 ambient 声道上循环播放（声道注册见 videos.rpy）。
        与 play_sfx 的区别是「一直响」而不是「响一下」，所以不进 _sfx_end_time，
        后面的正文不会等它 —— 一段 4 分半的长风等完游戏就没法玩了。

        if_changed=True：同一段环境音重复触发不重头开始。剧本在黑屏前后各标了三次
        【沙漠长风音效】，中间不该出现接缝。

        单独响度见上面的 AMBIENT_GAIN（relative_volume）。"""
        import os as _os
        base = _os.path.splitext(_os.path.basename(path))[0]
        store.current_ambient = path
        renpy.music.play(path, channel="ambient", loop=True,
                         fadein=fadein, if_changed=True,
                         relative_volume=AMBIENT_GAIN.get(base, 1.0))

    def stop_ambient(fadeout=2.0):
        """停掉环境音。current_ambient 置 None，读档不会把它恢复回来。"""
        store.current_ambient = None
        renpy.music.stop(channel="ambient", fadeout=fadeout)

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

    def stash_music_pos():
        """记下音乐停下那一刻的播放位置，供之后标了 "resume" 的场景接着放。
        转换器在每个 【音乐停】 的 stop 之前发这一行 —— 必须在 stop 之前，
        stop 之后 get_pos 就拿不到了。

        注意语义：记的是**声道**的播放位置，不是某一首曲子自己的播放进度。
        route1_horror2 是 N2-14 播完接 N2-07 循环，所以到 route1_horror3 之前那次
        音乐停时，台上的很可能已经是 N2-07 —— 于是 horror3 的 N2-14 会从"N2-07 当时
        走到的秒数"接上。这正是剧本要的效果（不重头开始 / 接着往下走），而且无论
        停在哪一首都有确定行为；反过来若按"N2-14 自己的进度"记，一旦它已经播完，
        进度就在结尾，接上去等于立刻回到 0 —— 恰好是剧本不要的那种重头开始。"""
        t = renpy.music.get_pos(channel="music")
        store.music_resume_pos = t if t else 0.0

    def music_track_spec(track, start=None):
        """把 music_config 里的一条 track 拼成带音频前缀的播放路径。

        单一数据源：剧情播放（set_scene_music）和音乐鉴赏（music_room screen）都
        走这里，所以两边的响度/循环点必然一致。以前音乐鉴赏直接播裸文件名，没有
        <volume> 前缀，同一首曲子在鉴赏里比游戏里响（glitter 差 10dB 以上）。

        可选无缝循环（秒）：loop=回跳点，end=每遍结束点（切掉尾部静音，避免回跳爆 pop）。
        响度匹配增益（线性）见 music_config.rpy 的 volume 注释。

        start：起播位置（秒）。给 "resume" 曲子用 —— 拼成 `from START loop 0`：
        Ren'Py 解析音频前缀时，第一遍用 from、之后每一遍循环改用 loop
        （renpy/audio/audio.py: `if (loop is not None) and looped: start = loop`）。
        所以效果是"这一遍从 START 接着放，放完之后整曲从头循环"，而不是
        永远只播 START 之后那一段。track 自己写了 "loop" 时以 track 的为准。

        clause 顺序（to → loop → volume）不能改：glitter 拼出的前缀必须与
        config.main_menu_music 逐字一致，否则 if_changed 认作两首曲子、
        主菜单→序章会重启这首。（from 只在 resume 曲子上出现，glitter 不受影响。）
        """
        filename = "audio/bgm/" + track["file"]
        clauses = []
        if start:
            clauses.append("from %s" % round(start, 3))
        if "end" in track:
            clauses.append("to %s" % track["end"])
        if "loop" in track:
            clauses.append("loop %s" % track["loop"])
        elif start:
            clauses.append("loop 0")
        if "volume" in track:
            clauses.append("volume %s" % track["volume"])
        if clauses:
            filename = "<%s>%s" % (" ".join(clauses), filename)
        return filename

    def set_scene_music(scene_id):
        """设置当前场景音乐并播放。

        一个场景的音乐是一个**序列**：tracks 按顺序各播一遍，最后一首无限循环。
        绝大多数场景是长度 1 的序列 = 单曲循环（和以前完全一样）。route1_horror2
        是长度 2 的序列：N2-14 完整播一遍，然后 N2-07 循环到场景结束。
        没有单独的"intro 曲"开关 —— 循环点就是序列末尾，不需要额外概念。

        track 上标 "resume": True 时，这首从上次 【音乐停】 的位置接着放
        （route1_horror3）。只对序列第一首有意义 —— 后面几首是接在前一首之后的，
        本来就没有"从哪儿接上"的问题。

        if_changed=True：若该曲已在播放则不重启 —— 这样主菜单的 glitter_in_the_dark
        能无缝续进序章（序章首曲也是它），玩家点"开始游戏"前后不断。
        """
        global current_music_scene
        store.current_music_scene = scene_id

        if scene_id not in scene_music:
            return

        tracks = scene_music[scene_id]["tracks"]
        if not tracks:
            return

        ## 玩家第一次听到这些曲子 → 在音乐鉴赏里解锁。
        for t in tracks:
            unlock_music(t["id"])

        ## 序列只有一首时 loop=True（=以前的行为）；有后续时第一首只播一遍，
        ## 由下面的 queue 接上。
        head_start = music_resume_pos if tracks[0].get("resume") else None
        renpy.music.play(music_track_spec(tracks[0], start=head_start),
                         fadeout=1.0, fadein=1.0, if_changed=True,
                         loop=(len(tracks) == 1))
        for i, t in enumerate(tracks[1:], start=1):
            ## clear_queue=False 是必须的：play() 已经清过队列，而 queue() 的
            ## clear_queue=True 会连 play() 刚入队、还没开始播的第一首一起抹掉
            ## （Channel.dequeue 直接截断 self.queue），结果就是跳过 N2-14 直接放 N2-07。
            renpy.music.queue(music_track_spec(t),
                              loop=(i == len(tracks) - 1), clear_queue=False)

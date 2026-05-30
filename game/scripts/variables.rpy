## variables.rpy
## 游戏变量和标记 / Game Variables and Flags

################################################################################
## 测试模式 - Test Mode
## 设为 True 可以快进未读文本，用于测试多周目流程
################################################################################

define config.developer = True  # 启用开发者模式
default persistent.test_mode = True  # 测试模式开关
default persistent.dev_mode = False  # 设置里的"开发者模式"开关，控制场景/音乐参考叠层

## 玩家是否进入过游戏（用于判断 game→menu 回流时要不要强制重启 polyhedron channel）。
## 用 persistent 是因为 MainMenu() action 会清掉普通的游戏变量但保留 persistent。
default persistent.polyhedron_started_game = False

## "当前周目里有没有存档" 标志。决定主菜单显示 "开始游戏" 还是 "继续游戏"。
## - start label / after_load 进游戏 → True
## - 通关一周目时 → False (unlock_route 重置)，主菜单回到"开始游戏"
## - 删存档时 → False (delete_all_saves 重置)
## screen 那边除了 flag 还另外查 renpy.list_slots()，没存档就不显示 Continue。
## 这也顺带绕开了 Movie/channel lifecycle 在 prologue 首场景重新 mount 时
## 容易出 checker board 的坑 —— Continue 直接 load 跳到存档点，不走那一段。
default persistent.has_save_in_run = False

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

## 开发者音乐选择（场景ID -> 曲目ID）
default persistent.scene_music_selections = {}

################################################################################
## 游戏内变量（每次游戏重置）
################################################################################

## 当前路线
default current_route = None

## madness 值 - 根据选择增加
default madness = 0

## 关键选择记录
default choice_flags = {}

## 当前场景转场信息（开发者用）
default current_scene_name = None  # 场景名称，如 "两座冰雕2"
default current_scene_desc = None  # 场景描述

################################################################################
## 存档加载后恢复音乐
################################################################################

label after_load:
    if current_music_scene is not None:
        $ set_scene_music(current_music_scene)
    ## 同 `label start`：进游戏(任何方式，包括 load save)都要标记 polyhedron
    ## 在下次回到主菜单时强制重启 channel。否则 load → 玩 → 回菜单又会破。
    $ persistent.polyhedron_started_game = True
    ## load 进游戏说明肯定有存档可继续，主菜单按钮保持"继续游戏"
    $ persistent.has_save_in_run = True
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

    def unlock_ending(ending_id):
        """Demo版：无操作"""
        pass

    def unlock_route(route_num):
        """Demo版：通关时把 has_save_in_run 清掉，主菜单回到"开始游戏"。"""
        persistent.has_save_in_run = False

    def get_current_route():
        """Demo版：始终返回1"""
        return 1

    def load_most_recent_save():
        """Continue button 用：按 mtime 找最近一次存档并 load 进游戏。"""
        slots = renpy.list_slots()
        if not slots:
            return
        latest = max(slots, key=lambda s: renpy.slot_mtime(s) or 0)
        renpy.load(latest)

    def exit_main_menu_to_game():
        """主菜单退场动画跑完后调用：有存档就 Continue，没存档就新开。
        Continue 不武装 _intro_fade_pending（玩家不在序章首句），新开才武装。
        和 screen 用同一个判断（renpy.list_slots()），避免 button 显示和实际
        动作不一致。"""
        if renpy.list_slots():
            load_most_recent_save()
            return
        renpy.store._intro_fade_pending = True
        renpy.jump_out_of_context("start")

    ##########################################################################
    ## 开发者音乐选择器函数
    ##########################################################################

    def select_and_play_music(scene_id, track_id):
        """选择并播放场景音乐"""
        if scene_id not in scene_music:
            return

        # Save selection
        persistent.scene_music_selections[scene_id] = track_id

        # Find track and play
        for track in scene_music[scene_id]["tracks"]:
            if track["id"] == track_id:
                renpy.music.play("audio/bgm/" + track["file"], fadeout=1.0, fadein=1.0)
                break

    def set_scene_music(scene_id):
        """设置当前场景音乐并自动播放"""
        global current_music_scene
        store.current_music_scene = scene_id

        if scene_id not in scene_music:
            return

        tracks = scene_music[scene_id]["tracks"]
        if not tracks:
            return

        # Check if we have a saved selection for this scene
        saved_track_id = persistent.scene_music_selections.get(scene_id)

        if saved_track_id:
            # Play the saved selection
            for track in tracks:
                if track["id"] == saved_track_id:
                    renpy.music.play("audio/bgm/" + track["file"], fadeout=1.0, fadein=1.0)
                    return

        # No saved selection - play first track
        renpy.music.play("audio/bgm/" + tracks[0]["file"], fadeout=1.0, fadein=1.0)

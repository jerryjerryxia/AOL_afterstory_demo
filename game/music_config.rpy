## music_config.rpy
## Maps each scene to its single background-music track.
## (The developer track-selector was removed for release; one track per scene.)

init python:
    # Scene music configuration
    # Each scene ID maps to a label and its single track.
    # "file" should match files in game/audio/bgm/

    ## "volume"：响度配平用的线性增益（乘在采样幅度上，经 <volume> 音频前缀播放）。
    ## 无损：只在播放时调音量，不重编码。改这里即可重新配平。
    ## 基线是把积分响度对到 -16 LUFS，但积分 LUFS 低估低频，所以按耳朵微调：
    ##   Glitter -16.5 / Beautiful -16 LUFS（听感刚好）；
    ##   420 -18 LUFS —— 低音很重，配到 -16 听感过响；
    ##   Endless -12.5 LUFS —— 配到 -16 听感过轻。
    ## 真峰全部 < -0.8 dBTP（顺带修掉 Glitter/Beautiful 原本 >0 dBTP 的削波）。
    scene_music = {
        "prologue_1": {
            "label": "序章 - 深海场景",
            "tracks": [
                ## id 保持 "polyhedron" 稳定 —— 它是 persistent.music_unlocked 的解锁键。
                ## volume 0.737 必须与 options.rpy 的 config.main_menu_music 前缀一致，
                ## 否则 if_changed 认作两首曲子、主菜单→序章会重启这首（破坏无缝续播）。
                {"id": "polyhedron", "name": "Glitter in the Dark", "file": "glitter_in_the_dark.ogg", "volume": 0.737},
            ]
        },
        "route1_scene1": {
            "label": "一周目 场景1 - 沙滩（夏日对视）",
            "tracks": [
                ## loop 115→230s：230s 处波形与 115s 逐样本一致（ncc=1.0），无缝。
                ## end=230 让每遍在 230s 收尾，不播到 232s 的静音尾巴（否则回跳会爆 pop）。
                ## -12.5 LUFS（≈原生）—— 配到 -16 听感过轻。
                {"id": "beach_v3", "name": "Endless Summer Time", "file": "endless_summer_time.ogg", "loop": 115.0, "end": 230.0, "volume": 0.995},
            ]
        },
        "route1_scene2": {
            "label": "一周目 对话场景",
            "tracks": [
                ## -18 LUFS（+1dB）—— 低音重，配到 -16 听感过响，压到 -18 刚好。
                {"id": "420", "name": "420", "file": "420.ogg", "volume": 1.118},
            ]
        },
        "route1_hallucination": {
            "label": "一周目 幻视场景",
            "tracks": [
                {"id": "beautiful_daughter", "name": "Beautiful Daughter", "file": "Beautiful_Daughter.mp3", "volume": 0.438},
            ]
        },
    }

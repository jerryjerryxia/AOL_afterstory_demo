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
    ##   DeepSpace -18 / Stranger Files -16.5 —— 见各自注释，都是"再往上就削波"的上限；
    ##   N2-07 与 N2-14 -15.5 —— 恐怖段刻意压过基线，也是这对曲子的削波上限。
    ## 真峰全部 < -0.8 dBTP（顺带修掉 Glitter/Beautiful 原本 >0 dBTP 的削波），
    ## 唯一例外是 N2-14：为了把恐怖段推到 -15.5，容忍 0.004% 采样越顶（见那条注释）。
    scene_music = {
        "prologue_1": {
            "label": "序章 - 深海场景",
            "tracks": [
                ## id 保持 "polyhedron" 稳定 —— 它是 persistent.music_unlocked 的解锁键。
                ## volume 0.3 必须与 options.rpy 的 config.main_menu_music 前缀一致，
                ## 否则 if_changed 认作两首曲子、主菜单→序章会重启这首（破坏无缝续播）。
                ## （0.3：序章首曲刻意压得较轻；原 0.737≈-16.5 LUFS。）
                {"id": "polyhedron", "name": "Glitter in the Dark", "file": "glitter_in_the_dark.ogg", "volume": 0.3},
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
        "route1_deepspace": {
            "label": "一周目 深空场景（粉红屏）",
            "tracks": [
                ## 原生 -20.1 LUFS / 峰 -3.7 dBFS。配到 -18 LUFS（gain 1.271，峰 -1.6 dBFS）：
                ##   1) 配到 -16 需 gain 1.60，峰会冲到 +0.4 dBFS 削波，物理上不允许；
                ##   2) 这是一整段漂浮/失重的独白铺底，本来就该比对话场景更靠后一层。
                {"id": "deepspace", "name": "DeepSpace", "file": "DeepSpace.mp3", "volume": 1.271},
            ]
        },
        "route1_desert": {
            "label": "一周目 沙漠场景",
            "tracks": [
                ## 原生 -14.9 LUFS，但峰已经是 +0.13 dBFS（母带就削了）。压到 -16.5 LUFS
                ## （gain 0.827）顺带把峰拉回 -1.5 dBFS，削波消失。
                ##
                ## 无缝循环点：找过了，不存在。以 4s 窗穷举 (回跳点, 收尾点) 全组合，
                ## 最高归一化互相关只有 0.19（endless_summer_time 那条是 1.0 = 逐样本
                ## 重复）—— 这首是通谱写作，段落之间波形不复现，任何中途剪接都会听出来。
                ## 所以整曲循环：0-17s 是安静的引子，17s 起进主体，125s 后自然衰减到静音，
                ## 本来就是"一首曲子完整放完再放一遍"的形状，回到开头不突兀。
                ## end=128.0 只切掉最后 1.3s 的死寂（那段已经在 -50 dBFS 以下，听不见），
                ## 让下一遍不用干等；衰减尾巴本身保留。切点幅度 0.002，不会爆 pop。
                {"id": "stranger_files", "name": "Stranger Files", "file": "Stranger_Files.ogg", "end": 128.0, "volume": 0.827},
            ]
        },
        "route1_horror1": {
            "label": "一周目 恐怖1 - 尤里娅现身",
            "tracks": [
                ## horror1 / horror2 / horror3 共用 -15.5 LUFS：horror2 播完 N2-14 接回
                ## N2-07、horror3 又续 N2-14，三段是一条线，两首必须等响，否则接缝处
                ## 音量跳变。比全局基线（-16）还高半格 —— 这是尸首登场的追逐段，
                ## 本来就该压过别处。
                ## -15.5 是这对曲子的实际上限：N2-14 原生峰 -0.13 dBFS，配到 -15.5 需
                ## gain 1.093，只有 0.004%（约 275 个）采样越顶、被削 0.6 dB 以内，散在
                ## 74 秒里听不出来；再往上 -15.0 就是 0.017%、-14.0 是 0.08%，开始脏了。
                ## N2-07 峰 -2.55 dBFS 余量充足，gain 1.017 完全不削。
                ## 想让这段再响就只能像沙漠长风那样对 N2-14 做限幅重制。
                {"id": "n2_07", "name": "N2-07", "file": "N2-07.mp3", "volume": 1.017},
            ]
        },
        "route1_horror2": {
            "label": "一周目 恐怖2 - 尸首登场 / 沙漠奔逃",
            ## 一个场景的音乐是一个**序列**：按顺序播完，最后一首无限循环
            ## （见 variables.rpy 的 set_scene_music）。这里 = N2-14 完整播一遍，
            ## 然后切到 N2-07 循环到场景结束。单曲场景就是长度 1 的序列。
            "tracks": [
                {"id": "n2_14", "name": "N2-14", "file": "N2-14.mp3", "volume": 1.093},
                {"id": "n2_07", "name": "N2-07", "file": "N2-07.mp3", "volume": 1.017},
            ]
        },
        "route1_horror3": {
            "label": "一周目 恐怖3 - 沙砾里的眼珠",
            "tracks": [
                ## 剧本：「N2-14 - 从上次音乐停的位置继续播放，不要重头开始」。
                ## resume=True 让它从上一次 【音乐停】 记下的声道位置起播，放完这一遍
                ## 之后整曲从头循环（见 variables.rpy 的 music_track_spec / stash_music_pos）。
                ## 响度和 horror1/horror2 一致，-15.5 LUFS —— 它就是 horror2 那首的续演。
                {"id": "n2_14", "name": "N2-14", "file": "N2-14.mp3", "volume": 1.093, "resume": True},
            ]
        },
    }

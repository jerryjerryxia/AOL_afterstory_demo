## music_config.rpy
## Maps each scene to its single background-music track.
## (The developer track-selector was removed for release; one track per scene.)

init python:
    # Scene music configuration
    # Each scene ID maps to a label and its single track.
    # "file" should match files in game/audio/bgm/

    scene_music = {
        "prologue_1": {
            "label": "序章 - 深海场景",
            "tracks": [
                {"id": "polyhedron", "name": "Polyhedron", "file": "1_polyhedron_loop.ogg"},
            ]
        },
        "route1_scene1": {
            "label": "一周目 场景1 - 沙滩（夏日对视）",
            "tracks": [
                ## loop 115→230s：230s 处波形与 115s 逐样本一致（ncc=1.0），无缝。
                ## end=230 让每遍在 230s 收尾，不播到 232s 的静音尾巴（否则回跳会爆 pop）。
                {"id": "beach_v3", "name": "Beach v3", "file": "2_beach_loop@01.55_q8.ogg", "loop": 115.0, "end": 230.0},
            ]
        },
        "route1_scene2": {
            "label": "一周目 对话场景",
            "tracks": [
                {"id": "420", "name": "420", "file": "420.ogg"},
            ]
        },
        "route1_hallucination": {
            "label": "一周目 幻视场景",
            "tracks": [
                {"id": "beautiful_daughter", "name": "Beautiful Daughter", "file": "Beautiful_Daughter.mp3"},
            ]
        },
    }

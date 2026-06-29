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
                {"id": "kevin_openning", "name": "Kevin Opening", "file": "kevin_openning.wav"},
            ]
        },
        "route1_scene1": {
            "label": "一周目 场景1 - 沙滩（夏日对视）",
            "tracks": [
                {"id": "beach_v3", "name": "Beach v3", "file": "2_beach_v3_trimmed_final.wav"},
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

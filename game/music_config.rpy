## music_config.rpy
## Developer music selector configuration
## Maps scene IDs to available background music tracks

init python:
    # Scene music configuration
    # Each scene ID maps to a label and list of candidate tracks
    # "file" should match files in game/audio/bgm/

    scene_music = {
        "prologue_1": {
            "label": "序章 - 深海场景",
            "tracks": [
                {"id": "kevin_openning", "name": "Kevin Opening", "file": "kevin_openning.wav"},
                {"id": "gaidankousetsu", "name": "Gaidankousetsu", "file": "Gaidankousetsu.mp3"},
                {"id": "electric_sea", "name": "Electric Sea", "file": "ElectricSea.mp3"},
                {"id": "padmasana", "name": "Padmasana", "file": "Padmasana.mp3"},
                {"id": "doutokutosetsu", "name": "Doutokutosetsu", "file": "Doutokutosetsu.mp3"},
                {"id": "shinsou_no_reijou", "name": "Shinsou no reijou", "file": "Shinsou_no_reijou.mp3"},
            ]
        },
        "route1_scene1": {
            "label": "一周目 场景1 - 沙滩",
            "tracks": [
                {"id": "shianchu", "name": "Shianchu", "file": "Shianchu.mp3"},
                {"id": "jellyfish", "name": "Jellyfish", "file": "Jellyfish.mp3"},
                {"id": "shine_of_silver_thaw", "name": "Shine of Silver Thaw", "file": "Shine_of_Silver_Thaw.mp3"},
                {"id": "sunflower_of_night", "name": "The sunflower of the night", "file": "The_sunflower_of_the_night.mp3"},
                {"id": "running_waters", "name": "Running Waters", "file": "RunningWaters.mp3"},
            ]
        },
        "route1_scene2": {
            "label": "一周目 对话场景",
            "tracks": [
                {"id": "420", "name": "420", "file": "420.ogg"},
                {"id": "moonlit_reverie", "name": "Moonlit Reverie", "file": "Moonlit_Reverie.mp3"},
                {"id": "hoyoku", "name": "Hoyoku", "file": "Hoyoku.mp3"},
                {"id": "sutekimeppou", "name": "Sutekimeppou", "file": "Sutekimeppou.mp3"},
            ]
        },
        "route1_hallucination": {
            "label": "一周目 幻视场景",
            "tracks": [
                {"id": "beautiful_daughter", "name": "Beautiful Daughter", "file": "Beautiful_Daughter.mp3"},
            ]
        },
    }

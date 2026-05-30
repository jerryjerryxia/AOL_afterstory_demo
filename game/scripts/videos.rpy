## videos.rpy
## 视频播放通道与共享 Movie 资源。

init python:
    ## 无色透明多面体循环用的独立 channel。movie=True 是必须的，否则不能给 Movie() 取帧。
    ## mixer="music" 让它跟 BGM 共用音量条；clip 本身没有音轨。loop=True 让 channel 循环。
    renpy.music.register_channel(
        "polyhedron_video",
        mixer="music",
        loop=True,
        stop_on_mute=False,
        movie=True,
    )

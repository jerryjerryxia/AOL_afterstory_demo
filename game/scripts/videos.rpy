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

    ## 环境音铺底（长循环，如沙漠长风）。为什么要单开一条声道：
    ##   - 挂 music 不行 —— 沙漠段落里 BGM 起停好几次（desert → horror1 → horror2
    ##     → 音乐停），风必须从头吹到尾，不能跟着 BGM 一起被掐掉；
    ##   - 挂 sound 不行 —— 那是一次性音效声道，下一个音效就把它顶掉，而且不循环。
    ## mixer="sfx"：玩家心智里风就是环境音效，跟着"音效音量"滑条走。
    renpy.music.register_channel(
        "ambient",
        mixer="sfx",
        loop=True,
    )

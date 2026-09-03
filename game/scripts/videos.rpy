## videos.rpy
## 视频播放通道与共享 Movie 资源。

## ★init -50★：下面这个函数被 game/images/bg/placeholder.rpy 里的 `image ... = Movie(...)`
## 在 init 期直接调用。image 语句跑在 init 0，而按文件名排序 images/bg/ 排在
## scripts/ 前面 —— helper 若也放 init 0 就来不及定义了。
init -50 python:

    def intro_then_loop(intro, loop):
        """Movie 的 play_callback：整段播一次 intro，播完接 loop 无限循环。

        剧本写法：【转场：X。播放一次之后开始播放Y】。

        为什么用音频队列而不是"pause 若干秒再换 image"：交接点由队列在 intro
        真正播完的那一帧决定，不用把素材时长抄进代码（素材一改就得跟着改），
        快进或掉帧时也不会错位。play(loop=False) 先把 intro 独占地放上去，
        紧接着的 queue(loop=True) 只把 loop 那条设成"队尾循环项" —— 循环的
        只有 loop，intro 不会再回来。
        （queue 默认 clear_queue=True 不会误伤刚 play 的 intro：enqueue 会把
        keep_queue 加 1，dequeue 只清它后面的。见 renpy/audio/audio.py。）

        channel 用 new.channel 而不是写死 "movie"：Movie(play=...) 默认走
        config.auto_movie_channel，真正的声道是运行时分配的 _movie_N。
        """

        def callback(old, new):
            renpy.music.play(intro, channel=new.channel, loop=False, synchro_start=True)
            renpy.music.queue(loop, channel=new.channel, loop=True, tight=True)

        return callback


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
    ## 两条：铺底要和脉冲同时响（沙漠的风底下压着狂跳的心脏），一条声道装不下。
    ##   ambient       —— 场所的声音：沙漠长风、呼吸 ambience
    ##   ambient_pulse —— 身体的声音：心跳
    ## 分开还有个好处：换场时可以只掐掉其中一条。
    renpy.music.register_channel(
        "ambient",
        mixer="sfx",
        loop=True,
    )
    renpy.music.register_channel(
        "ambient_pulse",
        mixer="sfx",
        loop=True,
    )

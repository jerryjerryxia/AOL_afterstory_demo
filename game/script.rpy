## script.rpy
## 游戏入口和主脚本 / Main Script Entry Point

################################################################################
## 闪屏 - 确保主菜单显示
################################################################################

label splashscreen:
    ## 这个 label 在游戏启动时运行，确保主菜单正常显示
    ## return 后 Ren'Py 会自动显示 main_menu 屏幕
    $ renpy.music.play("images/bg/polyhedron.webm", channel="polyhedron_video", loop=True)
    return

################################################################################
## 游戏开始
################################################################################

## 主菜单的海面背景。定义在这里（init offset 0）而不是 screens.rpy（offset -1），
## 因为要用到 options.rpy 里的 config.screen_width/height —— screens.rpy 跑得比
## options.rpy 早，那时候读到的还是引擎默认分辨率。
## main_menu screen 和 label start 都引用这一个名字，保证进游戏时铺到 master 层上的
## 画面和主菜单上看到的逐像素一致，切换那一帧才看不出破绽。
image bg_menu_sea = Fixed(
    Solid("#000000"),
    Transform("images/ui/menu_background/sea.png",
              xysize=(config.screen_width, config.screen_height),
              fit="contain", xalign=0.5, yalign=0.5),
    ## 压暗层：主菜单的标题图和左侧按钮压在海面上，不压暗亮部会吃掉白字。
    ## 比 game_menu 的 #00000080 轻一档 —— 主菜单文字少，画面留得开一点。
    Solid("#00000066"),
    xysize=(config.screen_width, config.screen_height))

label start:
    ## 初始化变量
    $ madness = 0
    $ choice_flags = {}

    ## 标记 polyhedron 需要在下次回到 main_menu 时强制重启 channel。
    ## 走过游戏一遭后 Movie/channel lifecycle 会乱，必须 stop+play 才能让
    ## bg_polyhedron_video 重新正常渲染（否则就是 checker board）。
    $ persistent.polyhedron_started_game = True

    ## 同 after_load：进游戏后回主菜单时应该是"继续游戏"。flag 配合 screen
    ## 里 renpy.list_slots() 一起判断 —— flag True 但还没存档时仍然回退到
    ## "开始游戏"，玩家真正存档后下次回主菜单才变 Continue。
    $ persistent.has_save_in_run = True

    ## ── 涟漪过场·游戏侧接力（时间轴见 screens.rpy 的"涟漪过场"注释）──────
    ## 玩家点击"开始游戏"的瞬间，主菜单侧的 menu_ripple 已经开始整屏荡漾；
    ## 这里要做的是接住它：
    ## 1) 把主菜单那张海面原样铺到 master 层。主菜单是 screen，jump_out_of_context
    ##    之后它连同背景全没了 —— 不铺这一层，序章首个 scene 的转场就是"从纯黑
    ##    渐入"，看着跟直接切黑没区别（最早那版就是这个毛病）。
    ##    with None：这一步本身不能有转场，它要看起来像"什么都没发生"。
    scene bg_menu_sea with None

    ## 2) 从菜单侧中断的进度处（RIPPLE_T0）续跑同一场涟漪。用 camera 而不是
    ##    show layer —— scene 语句会清掉 layer_at_list，而序章下一句正好就是
    ##    scene，用 show layer 的话涟漪会当场被抹掉。详见 shaders.rpy 的注释。
    camera master at screen_ripple(RIPPLE_T0)

    ## 3) 到点自动摘掉 camera transform（不摘会一直多跑一遍全屏 mesh）。
    show screen ripple_intro_fx

    ## 跳转到序章。序章首个 scene 带 ripple_reveal，在荡漾进行中交叉溶解进来。
    jump prologue

## script.rpy
## 游戏入口和主脚本 / Main Script Entry Point

################################################################################
## 闪屏 - 确保主菜单显示
################################################################################

label splashscreen:
    ## 这个 label 在游戏启动时运行，确保主菜单正常显示
    ## return 后 Ren'Py 会自动显示 main_menu 屏幕
    ## （这里以前 play polyhedron_video —— 那是给旧的视频主菜单预热用的。
    ## 现在主菜单是 sea.png，channel 统一在 label start 里、Movie 即将显示前
    ## 才启动，此处不再碰。）
    return

################################################################################
## 游戏开始
################################################################################

## 主菜单的海面背景。定义在这里（init offset 0）而不是 screens.rpy（offset -1），
## 因为要用到 options.rpy 里的 config.screen_width/height —— screens.rpy 跑得比
## options.rpy 早，那时候读到的还是引擎默认分辨率。
## main_menu screen 和 label start 都引用这一个名字，保证进游戏时铺到 master 层上的
## 画面和主菜单上看到的逐像素一致，切换那一帧才看不出破绽。
##
## 镜头缓移：保持原有 contain 构图（整幅横条 + 上下黑边），只把横条轻微变焦
## 1.06 后 15 秒从左缓移到右定格 —— 幅度与游戏内场景的镜头缓移一致（全程约
## 115px，~8px/s，细微可感）。黑边是背后的 Solid，不参与缓移，纹丝不动。
## 位置不是 ATL 时间轴而是**墙钟的纯函数**（_menu_sea_pan_tick）：菜单 screen 和
## label start 的 master 各自实例化这个 transform 时钟都一样，所以玩家在缓移中途
## 点"开始游戏"，master 接住的画面照样逐像素一致、并继续同步漂移。
## _menu_pan_t0 是 default 变量：从游戏退回主菜单时 store 重置 → 缓移重新来一遍；
## 主菜单 ⇄ 设置/存读档（同一 store）则共用时钟，镜头连续不跳。
define MENU_PAN_SECONDS = 15.0
define MENU_PAN_ZOOM = 1.06

default _menu_pan_t0 = None

init python:
    import time as _time_mod

    def _menu_sea_pan_tick(trans, st, at):
        if store._menu_pan_t0 is None:
            store._menu_pan_t0 = _time_mod.time()
        p = min((_time_mod.time() - store._menu_pan_t0) / MENU_PAN_SECONDS, 1.0)
        trans.xalign = 1.0 - (1.0 - p) ** 2   # easeout：减速滑入右端定格
        return 0 if p < 1.0 else None          # 定格后停止每帧重算

transform menu_sea_pan:
    subpixel True
    zoom MENU_PAN_ZOOM
    yalign 0.5
    function _menu_sea_pan_tick

## 海面层（黑底 + 缓移横条，无压暗）：main_menu 经 bg_menu_sea 用，
## game_menu（设置/存读档）直接 add —— 两边共享同一个缓移时钟。
## contain 盒的上下留白是透明的，变焦溢出的只是透明区，横条永远完整可见；
## 黑边由背后的 Solid 提供，静止。
image menu_sea_panorama = Fixed(
    Solid("#000000"),
    At(Transform("images/ui/menu_background/sea.png",
                 xysize=(config.screen_width, config.screen_height),
                 fit="contain", xalign=0.5, yalign=0.5),
       menu_sea_pan),
    xysize=(config.screen_width, config.screen_height))

image bg_menu_sea = Fixed(
    "menu_sea_panorama",
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

    ## 4) 重启 polyhedron channel —— 必须在 Movie 即将显示前做，这是它唯一可靠
    ##    的时机。历史教训：走过一轮游戏后 channel 状态会坏（显示 playing 但
    ##    Movie 渲染成 checker board / 黑屏），唯一有效的修法是 stop+play 重启。
    ##    旧版把重启放在主菜单 mount 时，那时主菜单本身显示着这个 Movie、channel
    ##    有消费者，一直被消费到序章所以有效；换成 sea.png 主菜单后 mount 时重启
    ##    的 channel 没有任何 Movie 在取帧，到第二次进序章时又是坏的。
    ##    所以挪到这里：紧贴着序章的 `scene bg_polyhedron_video` 之前。
    ##    首帧解码需要几十毫秒，被 2.5s 的 ripple_reveal 溶解完全盖住。
    python:
        try:
            renpy.music.stop(channel="polyhedron_video")
        except Exception:
            pass
        renpy.music.play(
            "images/bg/polyhedron.webm",
            channel="polyhedron_video", loop=True)

    ## 跳转到序章。序章首个 scene 带 ripple_reveal，在荡漾进行中交叉溶解进来。
    jump prologue

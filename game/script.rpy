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

    ## 跳转到序章
    jump prologue

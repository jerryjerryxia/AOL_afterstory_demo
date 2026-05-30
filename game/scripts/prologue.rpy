## prologue.rpy
## 序章 / Prologue - AUTO-GENERATED

label prologue:
    ## 根据进度跳转到对应周目
    $ route = get_current_route()

    if route == 1:
        jump route1_prologue
    elif route == 2:
        jump route2_start
    else:
        jump route3_start

################################################################################
## 一周目序章 - 只在第一次游戏时播放
################################################################################

label route1_prologue:
    $ set_scene_music("prologue_1")
    ## 场景音乐参考：Electric Sea (Buckethead), Padmasana (Buckethead)，Doutokutosetsu，Shinsou no reijou，Gaidankousetsu
    ## 转场：无色透明多面体
    scene bg_polyhedron_video with None
    $ current_scene_name = "无色透明多面体"
    $ current_scene_desc = "一颗无色透明的多面体在无垠的黑暗中幽幽地闪着冷光。"
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "一颗无色透明的多面体在无垠黑暗中幽幽地闪着冷光。"
    extend "\n你感到心平气和，脑海里没有任何多余的问题，只是冷静地观察着你眼前唯一的光源。"
    extend "\n里面装着另一个世界么？"
    extend "\n亦或是另一个人？"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "周身黑暗暖得让人毛骨悚然——不知多久以前，你一定来过这里。"
    extend "\n究竟是多久以前呢？"
    extend "\n很久很久以前。"
    extend "\n是当太阳还只是一团翩翩起舞的灰烬与气体时？"
    ## Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "疯子。"
    ## 居中大字文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "你只记得这个字眼。"
    extend "\n它既关于你，也关于别人，关于所有人。"
    extend "\n关于一切。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "——可‘一切’是个懒散的字眼。"
    extend "\n——一句在词穷时用来欲盖弥彰的空话。"
    extend "\n——但在此刻，‘一切’是精确的。"
    extend "\n——无需争论。"
    extend "\n——自然无需争论！"
    extend "\n——在这里，“一切”都无需争论。"
    extend "\n——完整是无需争论的。"
    extend "\n——无言以对。"
    extend "\n——不如顺便移开目光，看看别处。"
    extend "\n——无可奉告。"
    extend "\n——真是无聊啊。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "…"
    extend "\n……"
    extend "\n………"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "——没想到，这么快就找到你了。"
    extend "\n——我以为这种事对于现在的你来说易如反掌。"
    extend "\n——当然。只是一想到又要见到你那臭脸，我就下意识地多做了点心理准备。"
    extend "\n——心理准备？你？"
    extend "\n——毕竟做了“伤天害理”的事情。"
    extend "\n——哦。歉意，你能感受到那种东西？"
    extend "\n——不能。但能演给你看，要看吗？"
    extend "\n——看来你也挺无聊。"
    extend "\n——是咯。所以想不想出去溜达溜达？"
    extend "\n——向一个不具备意志的人征求认可又是何苦？彰显你那虚伪的开明？"
    extend "\n——那就当你同意了。"
    extend "\n——请自便吧。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "…"
    extend "\n……"
    extend "\n………"
    ## Extended大文本框结束
    ## 转场：黑屏
    scene black with scene_soft
    $ current_scene_name = "黑屏"
    $ current_scene_desc = "就是黑屏。"
    ## 头出水面后大吸一口气音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "仿佛完成了一场亘古的潜行，你轻轻浮出水面。"
    extend "\n可眼前只有一片黑暗，比你所熟知的海底更加幽深。"
    extend "\n世界本就是海，海平面以上自然一无所有。"
    extend "\n你模糊地记得这一点。"
    ## Extended大文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "失望之余，你肆意俯身漂浮，不再试图活动任何肌肉，只是慵懒地咪着双眼。你想，也许能从水下那幽暗世界里看出些什么。"
    extend "\n但终究是什么都没有。"
    extend "\n在长久的漂浮中，你渐渐忘记了消逝的体温，忘记了静脉里潺潺流动的暗红血液，忘记了你究竟为什么来到这里。"
    extend "\n你忘记了呼吸。"
    ## Extended大文本框结束
    ## 水底泡泡上浮音效
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "都说远道而来的友人要以热情相迎。"
    extend "\n本该是这样的。"
    extend "\n但你累了，实在是太累了。长时间保持不动竟是一件如此令人疲惫的事。"
    extend "\n每一寸肌肉都从黑夜中啜饮势能，苦苦等待爆发的那一刻——终究不会到来的那一刻。"
    extend "\n你在永恒的凝滞中被倦意填满。"
    extend "\n然而来者终归要到来——应你之邀而来。"
    extend "\n自己种下了树，就必要咽下它结的果。"
    ## Extended大文本框结束
    ## 居中大字文本框开始 - centered large font textbox
    centered_large_narrator "逃避吧！"
    ## 居中大字文本框结束
    ## Extended大文本框开始 - accumulating large textbox
    large_narrator "虽然早就无路可逃，但移开目光就能解燃眉之急，如此便利之事又有什么推脱的借口？"
    extend "\n于是就这样，你纹丝不动地在闪着微光的海面上漂浮，宛如一段朽木。"
    extend "\n假装一切都没有发生。"
    ## Extended大文本框结束

    ## 一周目序章结束，跳转到一周目正式开始
    jump route1_start
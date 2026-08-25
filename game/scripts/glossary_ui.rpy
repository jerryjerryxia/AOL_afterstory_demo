## glossary_ui.rpy
## 行内注释抽屉：正文里标蓝的概念（{a=gloss:id}，由转换器从剧本
## 【注释：…】 标记生成）点击后，从屏幕右侧滑出抽屉展示该概念的解释。
## 词典数据在 glossary.rpy（AUTO-GENERATED），此文件是手写 UI。

init python:
    import time as _gloss_time

    def _gloss_open(gid):
        """gloss: 协议的超链接处理器。只弹抽屉，不推进对话。"""
        if gid in GLOSSARY:
            renpy.session["_gloss_open_t"] = _gloss_time.time()
            renpy.show_screen("gloss_drawer", gid=gid)
            renpy.restart_interaction()

    config.hyperlink_handlers["gloss"] = _gloss_open

    GLOSS_SLIDE_SECONDS = 0.35
    GLOSS_SLIDE_DIST = 700

    def _gloss_slide_fn(trans, st, at):
        """滑入动画用挂钟时间驱动，不用 ATL 的 st：本作里 hover/焦点变化会
        restart_interaction 把屏幕 st 清零（见 quick_menu 的注释），靠 st 的
        ATL 会在鼠标移动时反复重播滑入——表现为抽屉不停抽搐。挂钟不受交互
        重启影响，动画只完整走一遍，之后静止。"""
        t = _gloss_time.time() - renpy.session.get("_gloss_open_t", 0.0)
        if t >= GLOSS_SLIDE_SECONDS:
            trans.xoffset = 0
            return None          # 动画完成，不再逐帧调度
        p = t / GLOSS_SLIDE_SECONDS
        trans.xoffset = GLOSS_SLIDE_DIST * (1.0 - p) * (1.0 - p)   # ease-out
        return 0.0               # 下一帧继续


## 抽屉：右侧滑入/滑出。modal 挡住底下的对话推进。
screen gloss_drawer(gid):
    zorder 200
    modal True

    ## 点击任意处关闭。dismiss 专为模态关闭设计：不参与 hover 样式变化，
    ## 不像全屏 button 那样制造焦点/重渲染噪声。
    dismiss action Hide("gloss_drawer")

    frame at _gloss_slide:
        xalign 1.0
        yfill True
        xsize 620
        padding (54, 72, 54, 72)
        background "#05050aeb"

        ## 左缘细线：抽屉与画面的分界
        add Solid("#8fc7ff66", xsize=3, ysize=1080, xpos=-54, ypos=-72)

        vbox:
            spacing 30
            ## 术语标题（运行时翻译；GLOSSARY 值已用 _() 标记进抽取）
            text _(GLOSSARY[gid][0]):
                size 44
                color "#ffffff"
                outlines gui.text_outlines
            add Solid("#ffffff40", xsize=512, ysize=2)
            ## 解释正文
            text _(GLOSSARY[gid][1]):
                size 30
                color "#e8e8e8"
                line_spacing 12
                xsize 512
                outlines gui.text_outlines
            null height 8
            text _("——录自逝乐园百科"):
                size 24
                color "#9a9aa4"
                xalign 1.0

## 滑入由 _gloss_slide_fn（挂钟）驱动；滑出仍用 ATL —— 收起过程很短，
## 即使被交互重启重播一次也看不出来。
transform _gloss_slide:
    on show:
        function _gloss_slide_fn
    on hide:
        easein 0.30 xoffset 700

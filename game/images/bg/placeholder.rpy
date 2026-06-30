## placeholder.rpy
## 占位符背景定义 / Placeholder Background Definitions

## 主背景占位符 - 深灰色
image bg_placeholder = Solid("#2a2a2a", xsize=1920, ysize=1080)

## 备用背景占位符 - 深蓝色
image bg_placeholder_alt = Solid("#1a2a3a", xsize=1920, ysize=1080)

## 黑屏
image black = Solid("#000000", xsize=1920, ysize=1080)

## 白屏
image white = Solid("#ffffff", xsize=1920, ysize=1080)

## 更多占位背景 - 按需添加
image bg_room = Solid("#3a3a3a", xsize=1920, ysize=1080)
image bg_outdoor = Solid("#2a3a2a", xsize=1920, ysize=1080)
image bg_night = Solid("#1a1a2a", xsize=1920, ysize=1080)

################################################################################
## 正式背景图 / Real background images (transplanted from full repo)
################################################################################

image bg_summergaze = Transform("images/bg/summergaze.png", xysize=(1920, 1080), fit="cover")
image bg_sungaze = Transform("images/bg/sungaze.png", xysize=(1920, 1080), fit="cover")
image bg_desert = Transform("images/bg/desert.png", xysize=(1920, 1080), fit="cover")

## 无色透明多面体：WebM (VP9) 循环视频，共享 channel polyhedron_video。
## channel 在 game/scripts/videos.rpy 注册，splashscreen 启动播放。
## 主菜单和序章首场景都从同一个 channel 取帧，跨 scene 不重新开始 ——
## 配合 prologue 首场景的 with None 做到主菜单→序章无缝衔接。
##
## demo 特有问题：通关后再回主菜单+第二次 Start 时 Movie/channel lifecycle
## 状态会乱，渲染成 checker board。修复方案：demo 通关时不 return 回菜单，
## 而是 renpy.utter_restart() 重新 boot 整个游戏 —— channel 完全重置，主菜单
## polyhedron 也是干净的。converter 在 demo 的 route1 末尾插这一行。
image bg_polyhedron_video = Movie(
    channel="polyhedron_video",
    size=(1920, 1080)
)

## 甜品店对视 1-8 + 6.51：dessert-shop 场景渐进。
## 1-3 暖色（团子吃法递进），4-6 转入蓝色调幻视（波纹由弱到强、王霜由实体到融入背景），
## 6.51 过渡，7 阿鹤呕吐导致色彩复原，8 碎裂进入黑屏。
## 源图均已 resize 到 3840x2160 以避开 GPU 4096 像素纹理限制。
image bg_dessertgaze1 = Transform("images/bg/dessertgaze1.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze2 = Transform("images/bg/dessertgaze2.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze3 = Transform("images/bg/dessertgaze3.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze4 = Transform("images/bg/dessertgaze4.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze5 = Transform("images/bg/dessertgaze5.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze6 = Transform("images/bg/dessertgaze6.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze6_51 = Transform("images/bg/dessertgaze6_51.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze7 = Transform("images/bg/dessertgaze7.png", xysize=(1920, 1080), fit="cover")
image bg_dessertgaze8 = Transform("images/bg/dessertgaze8.png", xysize=(1920, 1080), fit="cover")

## 旧实验：甜品店 + 水面波纹 shader。当前没有场景引用，留作以后复用。
## shader 注册和 _ripple_tick callback 见 game/scripts/shaders.rpy。
image bg_dessertshop:
    Transform("images/bg/dessertgaze6_50.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 1.5
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    function _ripple_tick

################################################################################
## 白屏 / 黑屏 视频背景（循环）。master 在 bg/_video_masters/，游戏用 webm。
## Movie(play=...) 在 show 时自动在 movie channel 播放、scene 走时停止；二者
## 不会同时出现，共用默认 channel。转场 白屏/黑屏 由 SCENE_BG_MAP 指到这里。
################################################################################
image bg_white_video = Movie(play="images/bg/white_screen.webm", size=(1920, 1080))
image bg_black_video = Movie(play="images/bg/black_screen.webm", size=(1920, 1080))

################################################################################
## 表情差分（全图 / 透明叠层）。转换器在 王霜【表情】 处切换：
##   full 场景（夏日对视 / 甜品店1-3）：scene <差分> —— 整图已含人物，默认图==bg。
##   overlay 场景（虚空对视）：scene black + show <差分> —— 差分是透明人物立绘。
## 文件在 images/bg/expression_variations/<场景>/。
################################################################################
## 夏日对视（full）
image summergaze_default   = Transform("images/bg/expression_variations/summergaze/summergaze_default.png",   xysize=(1920, 1080), fit="cover")
image summergaze_mutter    = Transform("images/bg/expression_variations/summergaze/summergaze_mutter.png",    xysize=(1920, 1080), fit="cover")
image summergaze_blank     = Transform("images/bg/expression_variations/summergaze/summergaze_blank.png",     xysize=(1920, 1080), fit="cover")
image summergaze_laugh     = Transform("images/bg/expression_variations/summergaze/summergaze_laugh.png",     xysize=(1920, 1080), fit="cover")
image summergaze_surprised = Transform("images/bg/expression_variations/summergaze/summergaze_surprised.png", xysize=(1920, 1080), fit="cover")
## 甜品店（full）
image dessert1_default = Transform("images/bg/expression_variations/dessert/dessert1_default.png", xysize=(1920, 1080), fit="cover")
image dessert1_smirk   = Transform("images/bg/expression_variations/dessert/dessert1_smirk.png",   xysize=(1920, 1080), fit="cover")
image dessert1_pout    = Transform("images/bg/expression_variations/dessert/dessert1_pout.png",    xysize=(1920, 1080), fit="cover")
image dessert1_puzzled = Transform("images/bg/expression_variations/dessert/dessert1_puzzled.png", xysize=(1920, 1080), fit="cover")
image dessert2_default = Transform("images/bg/expression_variations/dessert/dessert2_default.png", xysize=(1920, 1080), fit="cover")
image dessert2_pout    = Transform("images/bg/expression_variations/dessert/dessert2_pout.png",    xysize=(1920, 1080), fit="cover")
image dessert3_default = Transform("images/bg/expression_variations/dessert/dessert3_default.png", xysize=(1920, 1080), fit="cover")
image dessert3_excited = Transform("images/bg/expression_variations/dessert/dessert3_excited.png", xysize=(1920, 1080), fit="cover")
image dessert3_pout    = Transform("images/bg/expression_variations/dessert/dessert3_pout.png",    xysize=(1920, 1080), fit="cover")
## 虚空对视（overlay，透明立绘叠在 black 上）。共用 tag "void" → 表情用 show 互换。
image void default   = Transform("images/bg/expression_variations/void/void_default.png",   xysize=(1920, 1080), fit="cover")
image void surprised = Transform("images/bg/expression_variations/void/void_surprised.png", xysize=(1920, 1080), fit="cover")

################################################################################
## 资源替换说明
##
## 当美术资源准备好后，将此文件中的 Solid() 替换为实际图片路径：
##
## 例如:
##   image bg_placeholder = "images/bg/main_bg.png"
##   image bg_room = "images/bg/room.png"
##
## 或者直接删除此文件，将 PNG/JPG 文件放入 images/bg/ 目录，
## Ren'Py 会自动识别（文件名即为 image 名称）
################################################################################

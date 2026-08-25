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
## 4→5→6→6.51→7：水面波纹（水面波纹 shader，见 shaders.rpy）。4 起幻视、微弱入场，
## 5→6 渐强，6.51 顶峰，7 呕吐复原后留极微弱残留。振幅 u_ripple_strength 是主要"动态
## 强度"旋钮，speed 顺带略升加剧。想调强弱就改各自的 strength / speed。
image bg_dessertgaze4:
    Transform("images/bg/dessertgaze4.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.1   # 微弱入场
    u_ripple_speed 0.5
    u_ripple_scale 12.0
    function _ripple_tick
image bg_dessertgaze5:
    Transform("images/bg/dessertgaze5.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.2   # 非常微弱
    u_ripple_speed 0.9
    u_ripple_scale 12.0
    function _ripple_tick
image bg_dessertgaze6:
    Transform("images/bg/dessertgaze6.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.5   # 加强
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    function _ripple_tick
image bg_dessertgaze6_51:
    Transform("images/bg/dessertgaze6_51.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.9   # 顶峰
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    function _ripple_tick
image bg_dessertgaze7:
    Transform("images/bg/dessertgaze7.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.1   # 极微弱残留
    u_ripple_speed 0.5
    u_ripple_scale 12.0
    function _ripple_tick
image bg_dessertgaze8 = Transform("images/bg/dessertgaze8.png", xysize=(1920, 1080), fit="cover")
## 瘾：幻视高潮的转场卡（【转场：瘾。】，对视4→5 之间）——被瘾扭曲的甜品店。
## 波纹与前后场景（4 的 0.1 → 5 的 0.2）衔接，取略强的 0.25 作为这一拍的顶点。
image bg_addiction:
    Transform("images/bg/dessertshop_addiction.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.25
    u_ripple_speed 0.9
    u_ripple_scale 12.0
    function _ripple_tick

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
## start_image/image：视频首帧解码前显示纯色，避免 ctrl 快进时 Movie 冷启动
## 闪出棋盘格占位纹理（资源多、解码有压力时尤其明显）。
image bg_white_video = Movie(play="images/bg/white_screen.webm", size=(1920, 1080), start_image="white", image="white")
image bg_black_video = Movie(play="images/bg/black_screen.webm", size=(1920, 1080), start_image="black", image="black")

## 静帧黑屏：从 black_screen.webm 里截的一帧（t=5.5s），不走 Movie。
## 用在"灯灭一下"的段落节拍上——剧本里裸写 【黑屏】 的那两处（详见 convert_script.py）。
## 挑这一帧的理由：全片 18 帧candidates里它峰值最低（max 48，别的到 90+）、
## 均值 3.66 又贴着全片均值 3.57 —— 静止画面上一个亮斑会变成固定污点，动图里则看不出来。
## 保持源分辨率 1280x720 交给 Transform 放大，和 Movie(size=(1920,1080)) 走同一条缩放路径，
## 这样静帧和视频之间切换看不出画质差别。
image bg_black_still = Transform("images/bg/black_screen_still.png", xysize=(1920, 1080), fit="cover")

## 粉红屏 / 灰屏（★临时版★ —— 正式素材做好后替换掉这两条 image，
## convert_script.py 的 SCENE_BG_MAP 不用动）。
##
## 粉红屏：没有专门素材，先拿白屏视频蒙一层粉色滤镜。
## TintMatrix 是逐通道相乘：白色底(1,1,1) 乘出来正好是染色本身，而白屏视频里
## 那些细微的明暗起伏会按比例保留下来 —— 所以出来的是"会呼吸的粉雾"，
## 不是一块死的纯色。start_image/image 的 white 也一并被染，冷启动不会闪白。
##
## ↓ 调色就改这一个值。偏冷/偏紫往 #f0a0d0，偏肉粉往 #ffb0a8。
define PINK_SCREEN_TINT = "#ffa3c4"

## 灰屏（★临时版★）：同一招，但多乘一个 SaturationMatrix(0.0)。
## 多这一步是照着正文来的 ——「任何色彩倾泻其中，都只能归零的灰」：白屏视频里
## 那些残影本身带着暖/冷色偏，只染灰的话它们会透出淡淡的颜色，正好和这句话打架。
## 先去饱和再染灰 = 色彩真的归零，只剩明暗起伏在动。（顺序同 Ren'Py 自带的
## SepiaMatrix：TintMatrix(...) * SaturationMatrix(0.0)。）
##
## ↓ 调明暗就改这一个值。更亮往 #b2b2b2，更压抑往 #6e6e6e。
define GREY_SCREEN_TINT = "#9a9a9a"

## 两块屏幕的颜色矩阵写成同一个结构：TintMatrix(...) * SaturationMatrix(...)。
## 粉红那层的 SaturationMatrix(1.0) 是恒等矩阵、对画面没有任何影响，存在的唯一
## 理由是"结构相同"——Ren'Py 只在前后两个 matrixcolor 同类型、同乘法顺序时才
## 逐参数插值；结构不同就直接在第一帧跳到终点（官方文档 Structural Similarity）。
## 下面 bg_pink_video 的 10 秒褪色全靠这一点。
define PINK_SCREEN_MATRIX = TintMatrix(PINK_SCREEN_TINT) * SaturationMatrix(1.0)
define GREY_SCREEN_MATRIX = TintMatrix(GREY_SCREEN_TINT) * SaturationMatrix(0.0)

## 粉红屏 → 灰屏：不是换背景，是同一块屏幕自己慢慢褪色。
## 剧本里 【转场：灰屏】 那一行只表示"褪色开始"（转换器在那里发
## `$ pink_to_grey_started = True`，见 convert_script.py 的 IN_PLACE_SCENES），
## 之后 PINK_TO_GREY_SECONDS 秒里玩家照常点字推进，画面在背后自己走完。
##
## 为什么不用 `scene bg_grey_video with Dissolve(10)`：转场是阻塞的，玩家
## 点第一下就会把它一次性拍到终点，而且这十秒里没法推文字。
## 为什么不换成另一个 image：换 image = 换一个 Movie 实例 = 白屏视频从头重放，
## 褪色刚起步就"啪"地跳一下残影，正好毁掉要的那份丝滑。
## 所以只留粉红屏这一个 displayable，让它挂着 ATL 等信号：
##   _pink_to_grey_gate 每帧问一次标志位 —— 没起跑就原地待命（返回 0 = 下一帧
##   再问），起跑了返回 None 放行进 ease 褪色。（同 screens.rpy 的
##   _wait_for_main_menu_exit：ATL 轮询状态变量是这个项目里通用的"等信号"写法。）
## warper 用 ease 而不是 linear：起步和收尾都软，玩家察觉不到"开始变了"这一帧。
##
## 存档/读档：ATL 状态不进存档。褪色途中存档、读回来时画面回到粉红、标志位仍是
## True，于是重跑一遍完整褪色 —— 比读出来卡在半路或直接是灰更好看，不值得为它
## 记时间戳。
define PINK_TO_GREY_SECONDS = 10.0
default pink_to_grey_started = False

init python:
    def _pink_to_grey_gate(trans, st, at):
        return None if pink_to_grey_started else 0

image bg_pink_video:
    Movie(play="images/bg/white_screen.webm", size=(1920, 1080),
          start_image="white", image="white")
    matrixcolor PINK_SCREEN_MATRIX
    function _pink_to_grey_gate
    ease PINK_TO_GREY_SECONDS matrixcolor GREY_SCREEN_MATRIX

## 纯灰屏：现在没有场景用它（灰屏是由粉红屏褪过去的，见上）。留着当"直接就是灰"
## 的备用入口，也让褪色的终点长什么样有一处可直接看的定义。
image bg_grey_video = Transform(
    Movie(play="images/bg/white_screen.webm", size=(1920, 1080),
          start_image="white", image="white"),
    matrixcolor=GREY_SCREEN_MATRIX)

## 红屏（★临时版★）：同粉红屏的做法。取暗红而不是警报红，两个理由 ——
## 正文写的是"血液暗红"；而且这一段要挂着放二十几句旁白，一整屏高饱和亮红
## 顶着看眼睛受不了。
##
## ↓ 调色就改这一个值。要更刺目往 #ff3b30，要更偏橙往 #e0483a。
define RED_SCREEN_TINT = "#a81f1f"
image bg_red_video = Transform(
    Movie(play="images/bg/white_screen.webm", size=(1920, 1080),
          start_image="white", image="white"),
    matrixcolor=TintMatrix(RED_SCREEN_TINT))

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
## 虚空对视：旧的 void_default/void_surprised 占位整图已弃用 —— 现在用
## images/sprites/ 下的王霜立绘（sprites.rpy，转换器自动生成），由剧本里的
## 【姿势，表情】 标记驱动。expression_variations/void/ 下的 png 可以删了。

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

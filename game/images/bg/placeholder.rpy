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
## 无月版：第二段跑动 sequence 前的转场（【转场：银白色沙漠，无月】）。
image bg_desert_moonless = Transform("images/bg/desert_moonless.png", xysize=(1920, 1080), fit="cover")

## 跑动 sequence（尸首追逐段，剧本标记【跑动sequence开始…】）。
## 奔跑错觉三件套：
##   1. 递进景深轮播（美术方案）：从无月沙漠原图（4305x2430）的三个不同景深
##      位置截 16:9 帧，硬切轮播 —— 每一切都像冲进新的一片沙地，地形不断
##      "扑面而来"。截无月图：月亮是固定地标，会在帧间跳位穿帮。
##      截取框（原图像素 x, y, w, h；按美术标注的 1→2→3 顺序）在下面三条
##      bg_desert_run_f* 里，改框只改 crop 即可。
##   2. desert_run 光流 shader（shaders.rpy）：向前涌动感。
##   3. 奔跑节奏的颠簸/摇摆 ATL（向前+颤抖）。
## 两档递进：run 起跑、run2 更快更狂（配心跳渐强）——run2 轮播/颠簸都更快，
## 光流幅度从上一档的目标值 ease 入场（"入场继承 + 场内渐变"原则）。
## zoom 放大 + 居中：给颠簸/摇摆留边，不露黑边。
## 颠簸 repeat 循环顺带充当 shader 的每帧重绘驱动（u_time 才会推进）。
image bg_desert_run_f1 = Transform("images/bg/desert_moonless.png", crop=(1683, 955, 2622, 1475), xysize=(1920, 1080))
image bg_desert_run_f2 = Transform("images/bg/desert_moonless.png", crop=(0, 730, 2488, 1400), xysize=(1920, 1080))
image bg_desert_run_f3 = Transform("images/bg/desert_moonless.png", crop=(1653, 275, 2643, 1487), xysize=(1920, 1080))
image bg_desert_run:
    "bg_desert_run_f1"
    ## mesh True：源图 4305 宽超 GPU 4096 纹理上限会被切块，截取框又横跨切缝
    ## —— 不压平的话 shader 在两块纹理上各算各的 uv，缝两侧光流错位。
    mesh True
    shader "game.desert_run"
    u_run_vp (0.5, 0.42)    # 消失点（屏幕比例，略高于中心 = 地平线）
    u_run_ground 1.4        # 地面光流加成
    u_run_speed 0.55        # 循环速率
    u_run_amp 0.0           # 入场 = 静止（从静止沙漠甩头/溶解过来）
    zoom 1.07
    xalign 0.5
    yalign 0.5
    subpixel True
    parallel:
        ease 2.0 u_run_amp 0.12   # 起跑：光流两秒内涌到位
    parallel:
        # 递进景深轮播：硬切，每帧 0.8s（约两个跨步周期）。
        block:
            "bg_desert_run_f1"
            pause 0.8
            "bg_desert_run_f2"
            pause 0.8
            "bg_desert_run_f3"
            pause 0.8
            repeat
    parallel:
        block:
            easeout 0.17 yoffset -13
            easein 0.15 yoffset 5
            repeat
    parallel:
        block:
            ease 0.61 xoffset -8
            ease 0.61 xoffset 8
            repeat
image bg_desert_run2:
    "bg_desert_run_f1"
    mesh True   # 理由见 bg_desert_run
    shader "game.desert_run"
    u_run_vp (0.5, 0.42)
    u_run_ground 1.4
    u_run_speed 0.8         # 第二段更快
    u_run_amp 0.12          # 入场 = run 的目标值
    zoom 1.07
    xalign 0.5
    yalign 0.5
    subpixel True
    parallel:
        ease 1.5 u_run_amp 0.2    # 冲向更狂的档位
    parallel:
        # 轮播更急促（0.55s/帧）——狂奔档。
        block:
            "bg_desert_run_f1"
            pause 0.55
            "bg_desert_run_f2"
            pause 0.55
            "bg_desert_run_f3"
            pause 0.55
            repeat
    parallel:
        block:
            easeout 0.14 yoffset -16
            easein 0.12 yoffset 6
            repeat
    parallel:
        block:
            ease 0.5 xoffset -10
            ease 0.5 xoffset 10
            repeat

## 一头扎进沙地（【一头扎进沙地sequence，并在完成前锁定点击】）：第一人称，
## 按真实运动拆成两段 —— 人不可能直线把脸怼进地里，是**先跪倒、再前扑**：
##   跪倒（0.7s，ease 软塌）：视线高度下降 —— 视窗沿画面下滑（yanchor
##   0.5→0.65）+ 中等放大（1.0→1.55，地面凑近），随后膝盖着地一记顿挫
##   （yoffset 快速下沉回弹）；
##   前扑（0.45s，easeout 慢起加速）：上身前倾、头朝下栽 —— 视线加速扫向
##   脚下沙地（yanchor→0.88）+ 猛放大（→4.2），旋转到底即扎入；
##   末段 0.3s 乘性压黑（沙子灌满视野），接剧本紧随的 【转场：图片黑屏】。
## 全程轻微横抖（失衡感）。锚点轨迹经过校验：任一时刻视窗都不越出图像
## 下缘（不露黑边）。总时长 1.35s —— 转换器的 hard_pause（SAND_DIVE_SECONDS）
## 必须与此一致，改一处要改另一处。
## 首帧与静止沙漠 bg 完全一致（同源图同 cover），scene ... with None 无缝切入；
## 有月/无月各一版，转换器按当前沙漠形态（_DESERT_RETURN）选。
image bg_sand_dive:
    Transform("images/bg/desert.png", xysize=(1920, 1080), fit="cover")
    subpixel True
    matrixcolor TintMatrix("#ffffff")
    xanchor 0.5
    xpos 960
    yanchor 0.5
    ypos 540
    zoom 1.0
    parallel:
        ease 0.7 zoom 1.55 yanchor 0.65
        easein 0.08 yoffset 16
        easeout 0.10 yoffset 0
        pause 0.02
        easeout 0.45 zoom 4.2 yanchor 0.88
    parallel:
        pause 1.05
        linear 0.3 matrixcolor TintMatrix("#000000")
    parallel:
        block:
            linear 0.05 xoffset -5
            linear 0.05 xoffset 5
            repeat
image bg_sand_dive_moonless:
    Transform("images/bg/desert_moonless.png", xysize=(1920, 1080), fit="cover")
    subpixel True
    matrixcolor TintMatrix("#ffffff")
    xanchor 0.5
    xpos 960
    yanchor 0.5
    ypos 540
    zoom 1.0
    parallel:
        ease 0.7 zoom 1.55 yanchor 0.65
        easein 0.08 yoffset 16
        easeout 0.10 yoffset 0
        pause 0.02
        easeout 0.45 zoom 4.2 yanchor 0.88
    parallel:
        pause 1.05
        linear 0.3 matrixcolor TintMatrix("#000000")
    parallel:
        block:
            linear 0.05 xoffset -5
            linear 0.05 xoffset 5
            repeat

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
## 4→瘾卡→5→6→6.51→7→8：水面波纹（水面波纹 shader，见 shaders.rpy）。4 起幻视，
## 瘾卡小顶点，5 微退，6 加强，6.51 顶峰，7 呕吐复原后平息到极微弱残留，
## 8 保持残留直到碎裂黑屏。
## ★整条链继承动态★：u_time 是全帧共享的全局时基，speed/scale 相同的两张图
## 扰动场逐像素一致 —— 全链 speed=1.0、scale=12.0 统一，交叉溶解期间波纹原样
## 延续，换掉的只有底图。每张图的 strength 都【从上一张的目标值起步、入场后
## ease 到自己的目标值】，振幅也无跳变；4 从 0 起步 = 水面从静止慢慢晃起来，
## 与无 shader 的 3 无缝衔接。
## ★speed 不能参与 ease、也不能各图各设★：波形相位 = u_time × speed，u_time
## 可能已累计很大，speed 一变相位会整体回卷、波纹倒着狂奔。强弱只调 strength。
## ease 时长按各场停留节奏取：瘾卡/5 只有一两拍，取短，玩家快速点过也只差
## 百分位的振幅（不可见）；6/6.51 各两大段文本，7 是长释放。
image bg_dessertgaze4:
    Transform("images/bg/dessertgaze4.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.0   # 入场 = 3 的静止水面
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    ease 4.0 u_ripple_strength 0.1   # 幻视起：水面慢慢晃起来，微弱
    function _ripple_tick
image bg_dessertgaze5:
    Transform("images/bg/dessertgaze5.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.25  # 入场 = 瘾卡的小顶点
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    ease 2.0 u_ripple_strength 0.2   # 过了那一拍，微退
    function _ripple_tick
image bg_dessertgaze6:
    Transform("images/bg/dessertgaze6.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.2   # 入场 = 5 的目标值
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    ease 4.0 u_ripple_strength 0.5   # 加强
    function _ripple_tick
image bg_dessertgaze6_51:
    Transform("images/bg/dessertgaze6_51.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.5   # 入场 = 6 的目标值
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    ease 4.0 u_ripple_strength 0.9   # 涌向顶峰
    function _ripple_tick
image bg_dessertgaze7:
    Transform("images/bg/dessertgaze7.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.9   # 入场 = 6.51 的顶峰值
    u_ripple_speed 1.0      # 必须 == 6.51 的 speed（继承动态的前提，见上）
    u_ripple_scale 12.0
    ease 8.0 u_ripple_strength 0.1   # 随色彩还原逐渐平息到极微弱残留
    function _ripple_tick
image bg_dessertgaze8:
    Transform("images/bg/dessertgaze8.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.1   # 延续 7 的残留强度，无升降
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    function _ripple_tick
## 瘾：幻视高潮的转场卡（【转场：瘾。】，对视4→5 之间）——被瘾扭曲的甜品店。
## 链上的小顶点：从 4 的 0.1 起步，短 ease 涌到 0.25（这一拍是 window hide +
## pause，停留短，ease 取 1.5 保证点得快也基本到位）。
image bg_addiction:
    Transform("images/bg/dessertshop_addiction.png", xysize=(1920, 1080), fit="cover")
    shader "game.water_ripple"
    u_ripple_strength 0.1   # 入场 = 4 的目标值
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    ease 1.5 u_ripple_strength 0.25  # 瘾的小顶点
    function _ripple_tick

## 地下 1-8：沙漠地下（头埋进沙里）恐怖段的场景渐进（【转场：地下N】）。
## 1 初见沙砾 → 2-4 逐步细看（沙砾=多面体=眼珠）→ 5-6 眼珠注意到你 →
## 7 目光刺穿 → 8 眼珠爆裂。1 从图片黑屏黑场淡入，2-8 交叉溶解（同一视野的
## 递进拍，与甜品店 1-8 同一处理，见 convert_script.py CROSS_DISSOLVE_SCENES）。
image bg_underground1 = Transform("images/bg/underground1.png", xysize=(1920, 1080), fit="cover")
image bg_underground2 = Transform("images/bg/underground2.png", xysize=(1920, 1080), fit="cover")
image bg_underground3 = Transform("images/bg/underground3.png", xysize=(1920, 1080), fit="cover")
image bg_underground4 = Transform("images/bg/underground4.png", xysize=(1920, 1080), fit="cover")
image bg_underground5 = Transform("images/bg/underground5.png", xysize=(1920, 1080), fit="cover")
image bg_underground6 = Transform("images/bg/underground6.png", xysize=(1920, 1080), fit="cover")
image bg_underground7 = Transform("images/bg/underground7.png", xysize=(1920, 1080), fit="cover")
image bg_underground8 = Transform("images/bg/underground8.png", xysize=(1920, 1080), fit="cover")

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

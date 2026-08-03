## transitions.rpy
## 场景转场效果定义 / Scene Transition Definitions
##
## 在此统一调整全游戏的转场手感。route .rpy 由 convert_script.py 生成，
## 转场与特效处会引用下面这些名字。

## 默认场景转场 —— 经过黑场的淡入淡出（淡出 0.4s / 黑场停留 0.1s / 淡入 0.5s）
## 比纯溶解更明确：无论前后背景多相似，黑场都能让"换场"被清楚感知。
define scene_soft = Fade(0.4, 0.1, 0.5)

## 白屏 → 甜品店：较长的"屏幕逐渐黑下来"过渡。淡出到黑 1.5s / 黑场停留 0.3s /
## 淡入 0.8s。比 scene_soft 更慢更重，给"光褪去、世界沉入黑暗再浮现"的感觉。
define fade_to_black_long = Fade(1.5, 0.3, 0.8)

## 同场景渐变 —— 直接交叉淡入淡出，不经过黑场。
## 用于"同一地点、同一时刻"内的视觉渐变（甜品店对视 1→2→3...），让画面像
## 时间慢慢流过去那样彼此过渡，而不是每次都"切走又切回来"。
define scene_dissolve = Dissolve(0.8)

## 涟漪转场 —— 主菜单"开始游戏"进序章专用（配合 script.rpy 的 label start）。
## 从画面中心向外交叉溶解：中心先换成序章，边缘最后换，方向和涟漪扩散一致。
## 控制图 ripple_wipe.png 由 generate_ripple_assets.py 生成。ImageDissolve 是
## 白先黑后（SDK transition.py："white pixels will dissolve in first"），所以
## 控制图是中心白 → 四角黑，并烘焙了正弦环 —— 推进的边界是一圈圈水波而不是
## 一个干净的几何圆。
## ramplen 给到 255（上限）= 灰度斜坡拉到最软，看起来接近整体溶解、只是带方向感，
## 不会出现一条能看清的推进边 —— 要的就是"顺滑"，不是"扫过去"。
define ripple_reveal = ImageDissolve("images/ui/fx/ripple_wipe.png", RIPPLE_DISSOLVE, ramplen=255)

## 戏剧性瞬间的特效转场（由舞台提示关键词触发，见 convert_script.py 的 SPECIAL_FX）
define fx_glitch = hpunch    ## 故障 / glitch —— 横向震动
define fx_shock = vpunch     ## 惊吓 / 冲击 —— 纵向震动

## 电视机关机 —— CRT 断电：画面纵向塌成一条亮线，亮线横向收成一个光点，光点熄灭。
## 作用在整个 master 图层上（`show layer master at crt_shutdown`），所以塌陷的是
## 画面本身，不是盖一层遮罩。
##
## ★时间轴是照着 tv_off 音效的波形对的，改任何一段都要重新对★
## 音效 dragon-studio-tv-shutdown-386167.mp3 实测：
##   0.00-0.06s 起振 → 0.06-0.08s 瞬态峰 → 0.08-0.80s 延音衰减 → 0.80s 骤降到 -56 dBFS
## 对应：
##   0.00-0.07  纵向塌陷（塌到位正好压在瞬态峰上，"啪"的那一下画面同时没了）
##   0.07-0.10  亮线保持
##   0.10-0.55  横向收成光点（对着延音段）
##   0.55-0.80  光点熄灭（0.80 到黑，音效同时掉到听不见）
## 总长 0.80s，与 hard_pause 的时长必须一致（见 convert_script.py 的转场发射）。
transform crt_shutdown:
    align (0.5, 0.5)
    matrixcolor BrightnessMatrix(0.0)
    linear 0.07 yzoom 0.006 matrixcolor BrightnessMatrix(0.55)
    pause 0.03
    linear 0.45 xzoom 0.015
    linear 0.25 alpha 0.0

## 文字墙（"对不起"那面墙）的演出：堆满 → 抖动 → 一路放大 → 收场，总长 10.8 秒。
##
## 拆成两层是必要的，不能写成一个 transform：
##   揭开用 crop，而 crop 会改变显示物的尺寸；放大要从画面中心长出来，就得 align
##   到中心。两者放在同一层的话，揭开过程中"半高的内容"会被 align 拽到屏幕中间，
##   看起来是文字在往下滑而不是在原地一行行堆满。所以内层只管揭开，外层只管抖和放大。
##
## 为什么不用逐字打字实现"堆满"：打字速度受 text_cps 影响，而那是玩家能在设置里
## 改的偏好 —— 演出时长会跟着变，和 10 秒的 hard_pause 对不上。裁切与偏好无关。

## 完整时间轴（改这里必须同步 convert_script.py 的 TEXT_WALL_SECONDS）：
##   0.0 - 4.0    揭开：文字一行行堆满屏幕
##   4.0 - 10.8   放大：铺满的那一刻立刻接上，一路推到 3.8 倍、中途不停 ——
##                收场时它还在放大，所以是"越压越近然后被切走"，不是"停住再切"
##   全程         逐字颤动，幅度随放大一起渐强（见下面的 _wall_jitter）
##   10.0- 10.35  收场：白闪一下、黑底褪去，露出下面的红屏
##
## ★逐字四散坠落试过两版，都没成，别再走同一条路★
## (a) 把屏幕切成矩形碎片各自飞散；(b) 每个字各自抛出、旋转、加速坠落。
## 两版的表现都是"到点后文字瞬间消失"。在 scratchpad/walltest 最小复现工程里
## 逐帧截图查过：
##   (a) 原因明确：靠 screen 变量切 if/else 换渲染内容，会导致父级 fixed 被重建，
##       挂在它上面的 text_wall_reveal 跟着重启，crop 回到高度 0 —— 整块被裁没。
##   (b) 改成不切分支、由同一个逐字函数从抖动平滑过渡到坠落：文字会在约 1.7 秒后
##       整体停止渲染，不抛异常、无 traceback，干净重写后稳定复现。
##       已排除的方向：分支切换、字数规模（减到 120 字同样失败）、函数内异常。
## (c) 又试过"对半分开"：两半各渲染一份完整文本再各自平移。它在最小复现工程里能
##     跑完整程，但搬进正片直接卡死到没法看 —— 复现工程只有这一个屏幕，正片还带着
##     整套素材，逐字 displayable 从 528 翻到 1056 就过线了。
## 结论：墙只能是**一份**文本。任何"拆成 N 块各自动"的方案都会撞同一堵墙。
## 收场就用放大 + 白闪 + 黑底褪去，不要再加分块动画。
define WALL_SHATTER_AT = 10.0

## 内层：文本一次性排好版，自上而下揭开（0→4s）
## 揭完立刻把 crop 撤掉。crop 是硬裁剪，留着的话后面炸开时飞出原始矩形的字会被
## 直接切掉；撤掉的那一刻画面没有任何变化（此时 crop 本来就是完整矩形）。
transform text_wall_reveal:
    crop_relative True
    crop (0.0, 0.0, 1.0, 0.0)
    linear 4.0 crop (0.0, 0.0, 1.0, 1.0)
    crop None

## 外层：只管放大。起点 4.0 = 揭开结束的那一刻，铺满与开始变大之间不留空档。
## 抖动不在这里 —— 整块一起位移太糙，改成每个字单独抖，见下面的 _wall_jitter。
## 放大一路开到演出结束（6.8s = 从 4.0 到 hard_pause 的 10.8），中途不停顿 ——
## 收场那一下它还在往前压，观感是"被切走"而不是"停住了再切"。
transform text_wall_anim:
    align (0.5, 0.5)
    pause 4.0
    linear 6.8 zoom 3.8

## 每个字单独抖，而且随着放大越抖越凶。
##
## ★为什么不用 ATL 而用 function★
## 要"幅度随时间增长"，ATL 只能写成若干段 block+repeat 的阶梯（而且每个相位变体
## 都要各写一遍，4×3=12 段），既啰嗦又只能是台阶式跳变。一个 function 回调每帧
## 按 st 算一次位移，就能连续渐强，参数也集中在一处。
##
## ★相位必须逐字不同★
## screens.rpy 里原有的 {shake} 让所有字共用一个 transform、同时启动、同向位移 ——
## 那和整块一起抖在观感上没有区别（"好刻薄"只有三个字所以看不出来）。
## 这里用黄金比例给每个字分一个互不相关的相位，才是真正的"各抖各的"。
##
## 注意幅度是**放大前**的数值：外层最终放到 3.8 倍，上屏还要再乘这个倍数。
## 所以 1.5 → 8.0 的增长，实际观感是 ±5px 涨到 ±30px。
init python:
    import math as _math

    ## 渐强区间与放大同步：4.0s 开始（正是铺满、开始放大的那一刻），6 秒涨满。
    WALL_JITTER_FROM = 4.0
    WALL_JITTER_RAMP = 6.0
    WALL_JITTER_AMP0, WALL_JITTER_AMP1 = 1.5, 8.0      # 幅度 px（放大前）
    WALL_JITTER_FREQ0, WALL_JITTER_FREQ1 = 5.0, 13.0   # 频率，越大抖得越密

    def _wall_jitter(phase):
        def f(trans, st, at):
            k = (st - WALL_JITTER_FROM) / WALL_JITTER_RAMP
            k = 0.0 if k < 0.0 else (1.0 if k > 1.0 else k)
            amp = WALL_JITTER_AMP0 + (WALL_JITTER_AMP1 - WALL_JITTER_AMP0) * k
            freq = WALL_JITTER_FREQ0 + (WALL_JITTER_FREQ1 - WALL_JITTER_FREQ0) * k
            ## x/y 用不同的频率倍数，轨迹才不是一条斜线来回蹭
            trans.xoffset = amp * _math.sin(st * freq + phase)
            trans.yoffset = amp * _math.cos(st * freq * 1.37 + phase * 1.7)
            return 0
        return f

    def wall_tremble(phase):
        return Transform(function=_wall_jitter(phase), subpixel=True)

    def wall_char_phase(n):
        """按字序给相位。黄金比例递增 —— 邻字相差最远，看不出周期性。"""
        return (n * 0.6180339887) % 1.0 * 6.2831853

## 黑底：到点褪去，让下面的红屏透出来 —— 这就是"转回一般的红屏"。
transform wall_backdrop:
    alpha 1.0
    pause WALL_SHATTER_AT
    linear 0.35 alpha 0.0

## 收场瞬间的白闪，一下就收。它和黑底褪去一起构成"墙被冲掉、露出红屏"那一下。
transform wall_flash:
    alpha 0.0
    pause WALL_SHATTER_AT
    linear 0.06 alpha 0.7
    linear 0.30 alpha 0.0

## 【屏幕震动】专用的"剧烈版"屏幕震动（阿鹤惨叫处，见 convert_script.py）。
## 想调整剧烈程度就改这一行：
##   - 前两个点 (±X, ±Y) 是位移幅度：X 横向、Y 纵向，越大抖得越凶（vpunch 是纯纵向 10）。
##   - 第 3 个参数是单次位移时长，越小抖得越快越密。
##   - delay 是总时长，越大抖得越久。
## 现在是斜向对角抖动，同时含横向+纵向分量（想要更横就把 X 调大、Y 调小）。
define fx_quake = Move((28, 36), (-28, -36), .04, bounce=True, repeat=True, delay=.55)

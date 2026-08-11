## shaders.rpy
## GLSL 着色器与对应 transform。
## 在 ATL 中通过 `at <transform>` 应用，或在 image 块里直接 `shader "..."` 内嵌。

## 水面波纹着色器：通过三层正弦波叠加扰动 UV，模拟流动的水面。
## 关键细节：
##   1. fragment_300（而非 200）—— renpy.texture 在 fragment_200 写 gl_FragColor =
##      texture2D(tex0, v_tex_coord, ...)；如果我们也在 fragment_200，两边谁后写谁赢，
##      顺序未定义。上一版静态画面就是被 renpy.texture 的未扰动采样覆盖了。
##      用 fragment_300 保证我们晚于 renpy.texture，又早于 matrixcolor/alpha（它们是乘）。
##   2. tex0 / v_tex_coord / u_lod_bias 已由 renpy.texture 声明，复用不重声明。
##      但 u_time 是个"魔法"名 —— Ren'Py 见到就会自动每帧注入当前时间，但前提是
##      你必须自己声明它。所以 u_time 仍要写在 variables 里。
##   3. 重绘驱动：自定义 uniform 不能 `linear u_time` 动；`pause 0.0; repeat` 也不触发重绘。
##      用 ATL function callback _ripple_tick 每 ~1/60 s 触发一次回调，让自动 u_time 推进。
init python:
    def _ripple_tick(trans, st, at):
        return 1.0 / 60.0

    renpy.register_shader("game.water_ripple",
        variables="""
            uniform float u_time;
            uniform float u_ripple_strength;
            uniform float u_ripple_speed;
            uniform float u_ripple_scale;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;

            // 多层正弦波叠加，模拟水面波纹
            float wave1 = sin(uv.x * u_ripple_scale + u_time * u_ripple_speed) * u_ripple_strength;
            float wave2 = sin(uv.y * u_ripple_scale * 0.8 + u_time * u_ripple_speed * 1.3) * u_ripple_strength * 0.7;
            float wave3 = sin((uv.x + uv.y) * u_ripple_scale * 0.6 + u_time * u_ripple_speed * 0.9) * u_ripple_strength * 0.5;

            vec2 distorted_uv = uv + vec2(wave1 + wave3, wave2 + wave3) * 0.02;

            gl_FragColor = texture2D(tex0, distorted_uv, u_lod_bias);
        """
    )

## 全屏径向涟漪：往画面中心"丢了一滴水"，把整个画面拉扯变形。
## 用在主菜单 → 序章的过场上（见 script.rpy 的 label start）。
##
## 透视：不是把圆压扁成椭圆的仿射近似，而是真的做一次针孔相机 ↔ 水面平面的
## 投影往返 —— 把每个像素反投影到一张虚拟水面上，在**平面真实距离**上算波形，
## 在平面空间里做位移，再投影回屏幕采样。于是透视是免费送的、而且是对的：
##   * 上半屏（远处）的圈圈彼此挤紧（波长约压到 1/4），下半屏（近处）摊开；
##   * 同一圈波纹在屏幕上不是同心椭圆 —— 远弧更贴近地平线方向；
##   * 远处的位移幅度被投影自动缩小（除以深度），近处的晃动大。
## 相机参数：俯仰 RIPPLE_PITCH（30°）、焦距 RIPPLE_FOCAL、离水面高 RIPPLE_HEIGHT。
## 地平线在 η = focal·tan(pitch) ≈ 0.81，屏幕上缘是 0.5 —— 永远在画外，
## 反投影不会除零（着色器里再加 max 兜底）。
##
## 波形模型按真实水滴涟漪的物理来（gravity–capillary ring wave packet）：
##   * 扰动是一圈**环形波包**：包络中心 R(t) 沿平面向外推进，包内水面回平
##     （quiescent center / caustic），包外还没被扰动；
##   * 波峰相速 > 波包群速：波峰从包络后缘冒出、向前穿过、在前缘消失；
##   * 色散：外圈波长更长（chirp 相位），波包缓慢展宽（low diffusion）；
##   * 能量摊在越来越大的圆周上 → 振幅 ~1/sqrt(ρ) 几何衰减；
##   * 落点：小半径、高强度、衰减极快的中心"扑通"（crater/rebound）；
##     回落水柱再激起一圈更小更弱、迟一拍出发的次波包（rebound jet ring）；
##   * 角向不均：±15% 低频角向调制，不是完美等幅的圆。
##
## fragment_300 / 复用 tex0、v_tex_coord、u_lod_bias / 自定义 uniform 要自己声明，
## 同上面 water_ripple 的注意事项。不用 u_time：进度全部由 u_ripple_t ∈ [0,1] 驱动
## （ATL 插值自动触发重绘），整个波形是 t 的纯函数 —— 这是主菜单侧和游戏侧
## 能无缝接力的前提（两边只要 t 衔接，画面就衔接）。
init python:
    renpy.register_shader("game.screen_ripple",
        variables="""
            uniform float u_ripple_t;
            uniform float u_ripple_amp;
            uniform float u_ripple_freq;
            uniform float u_ripple_phspeed;
            uniform float u_ripple_r0;
            uniform float u_ripple_gspeed;
            uniform float u_ripple_w0;
            uniform float u_ripple_spread;
            uniform float u_ripple_impr;
            uniform float u_ripple_impamp;
            uniform float u_ripple_irreg;
            uniform float u_ripple_aspect;
            uniform float u_ripple_pitch;
            uniform float u_ripple_focal;
            uniform float u_ripple_height;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_ripple_t;

            float sn = sin(u_ripple_pitch);
            float cs = cos(u_ripple_pitch);
            float fo = u_ripple_focal;
            float hh = u_ripple_height;

            // ---- 屏幕 → 水面平面（反投影）-----------------------------------
            // 屏幕坐标：η 向上、屏幕半高 = 0.5；ξ 横向、按宽高比展开。
            float xi  = (uv.x - 0.5) * u_ripple_aspect;
            float eta = 0.5 - uv.y;

            // 过该像素的视线（相机被俯仰 pitch）与水面 y = -height 求交。
            // dy 必是负的（整屏都在地平线以下），max 只是除零兜底。
            float dy = eta * cs - fo * sn;
            float dz = eta * sn + fo * cs;
            float tt = hh / max(-dy, 0.0001);
            float X  = xi * tt;
            float Z  = dz * tt;

            // 落点 = 屏幕中心那条视线落在水面上的点。
            float Z0 = hh * cs / sn;
            vec2  q   = vec2(X, Z - Z0);
            float rho = length(q);      // 水面上到落点的真实平面距离

            // ---- 主波包 ----------------------------------------------------
            // 包络：高斯环，中心从 r0（落点大小）向外推进，宽度随行进展宽。
            // 后缘 sigma 放大 1.9 倍（波包后拖尾比前沿长），前缘相对干脆。
            float R = u_ripple_r0 + u_ripple_gspeed * t;
            float w = u_ripple_w0 * (1.0 + u_ripple_spread * t);
            float dr = rho - R;
            float sig = (dr > 0.0) ? w : (w * 1.9);
            // birth 门控：t=0 时主波包必须严格为 0（菜单待机时 t 停在 0，
            // 不门控的话包络叠着非零载波，主菜单中心会有一块静态的凹陷）。
            float birth = smoothstep(0.0, 0.08, t);
            float env = exp(-dr * dr / (2.0 * sig * sig)) * birth;

            // 载波：chirp 相位 ρ/(1+0.55ρ) → 外圈波长长（色散）。
            // phspeed 定得比群速对应值高 → 波峰比包络跑得快，从后缘冒出、
            // 前缘消失，正是真实波包的看相。
            float chirp = rho / (1.0 + 0.55 * rho);
            float wave = sin(u_ripple_freq * chirp - u_ripple_phspeed * t);

            // ---- 次波包（回落水柱激起的第二圈）------------------------------
            float t2 = max(t - 0.22, 0.0) / 0.78;
            float R2 = u_ripple_r0 + u_ripple_gspeed * 0.85 * t2;
            float w2 = u_ripple_w0 * (1.0 + u_ripple_spread * t2) * 0.7;
            float dr2 = rho - R2;
            float env2 = exp(-dr2 * dr2 / (2.0 * w2 * w2))
                       * smoothstep(0.22, 0.30, t) * 0.45;
            float wave2 = sin(u_ripple_freq * 1.25 * chirp - u_ripple_phspeed * 0.9 * t2);

            // ---- 幅度调制 ---------------------------------------------------
            // 能量摊薄 ~1/sqrt(ρ)（0.3 平面单位处开始显著）。
            float geo = inversesqrt(1.0 + rho / 0.3);

            // 角向不均：三个低频谐波，±15%；末项带 ρ 让花纹随半径演化。
            float ang = atan(q.y, q.x);
            float irr = 1.0 + u_ripple_irreg * (0.5 * sin(ang * 3.0 + 1.7)
                                              + 0.3 * sin(ang * 5.0 - 0.8)
                                              + 0.2 * sin(ang * 9.0 + rho * 7.0));

            // 整体回平：临近结束加速归零，t=1 位移严格为 0（之后摘 camera）。
            float settle = 1.0 - t * t;

            // ---- 中心冲击：凹坑 → 回弹冲高 → 余摆 ----------------------------
            // 真实落水的中心不是一味乱颤：先砸出凹坑（水面下陷），涟漪出发，
            // 然后回弹水柱冲**高过水面**，再一次小回落归平。三段正弦，相接处
            // 都过零（无跳变），t=0 严格为 0（菜单待机不动）。
            // 采样语义：ia > 0 = 径向向外采样 → 画面被"吸"向四周 = 下陷；
            //           ia < 0 = 向内采样 → 中心放大凸起 = 鼓起冒头。
            // 回弹做得比凹坑更强(1.3×)更慢(T2>T1) —— "冒出水面"要看得清。
            float T1 = 0.07;
            float T2 = 0.16;
            float T3 = 0.20;
            float ia = 0.0;
            if (t < T1) {
                ia = sin(3.14159265 * t / T1);                     // 凹坑
            } else if (t < T1 + T2) {
                ia = -1.3 * sin(3.14159265 * (t - T1) / T2);       // 回弹冲高
            } else if (t < T1 + T2 + T3) {
                ia = 0.3 * sin(3.14159265 * (t - T1 - T2) / T3);   // 余摆
            }
            // 回弹的水柱比凹坑窄（0.6×半径）；相接处 ia=0，半径切换无缝。
            float ir = u_ripple_impr * ((ia < 0.0) ? 0.6 : 1.0);
            float domeg = exp(-rho * rho / (2.0 * ir * ir));
            // 径向分量在正中心归零（rho→0 方向未定义）；竖直抬升不受此限。
            float plop = domeg * ia * u_ripple_impamp
                       * smoothstep(0.0, 0.015, rho);

            // ---- 平面空间位移 → 投影回屏幕 -----------------------------------
            // 位移沿平面上的径向（从落点向外），单位是平面单位；重投影会自动
            // 把远处的位移在屏幕上缩小 —— 这就是"近大远小"的透视本体。
            float W = ((wave * env + wave2 * env2) * geo * irr + plop)
                    * u_ripple_amp * settle;
            vec2 dirP = q / max(rho, 0.0001);
            float Xp = X + dirP.x * W;
            float Zp = Z + dirP.y * W;

            float wc  = hh * sn + Zp * cs;          // 相机空间深度
            float xip = fo * Xp / wc;
            float etp = fo * (Zp * sn - hh * cs) / wc;
            vec2 suv = vec2(0.5 + xip / u_ripple_aspect, 0.5 - etp);

            // 回弹期的竖直抬升：水柱是垂直运动，纯径向位移表现不出"冒出水面"。
            // 向下偏移采样点 = 内容在屏幕上向上抬。只在 ia<0（回弹）时生效，
            // 幅度跟着回弹包络走，中心最强、随 domeg 高斯衰减。
            suv.y += max(-ia, 0.0) * domeg * u_ripple_amp * u_ripple_impamp
                   * 0.15 * settle;

            gl_FragColor = texture2D(tex0, suv, u_lod_bias);
        """
    )

## 涟漪 shader 参数 —— 单一数据源。
## 游戏侧 screen_ripple（本文件）和菜单侧 menu_ripple（screens.rpy）都引用这些
## define，两边必然一致，接力才无缝。改任何一个只改这里。
## 长度类参数（R0/W0/IMP_R/GSPEED 等）的单位都是"水面平面单位"：
## 屏幕下缘 ≈ ρ 0.55、左右缘 ≈ 0.79、上缘 ≈ 2.34、上角 ≈ 3.13（由相机参数决定）。
define RIPPLE_AMP     = 0.048    ## 位移幅度（平面单位；近处约合 50px，远处被透视自动缩小）
define RIPPLE_FREQ    = 60.0     ## 载波密度（chirp 前的基准波数）
define RIPPLE_PHSPEED = 190.0    ## 波峰相位推进速度（≈1.6×群速的效果：波峰穿过波包）
define RIPPLE_R0      = 0.05     ## 落点半径 = 波包出发位置（"中心冲击的大小"就是它）
define RIPPLE_GSPEED  = 3.8      ## 波包推进速度：t≈0.81 时包络中心扫过最远的上角(ρ≈3.13)
define RIPPLE_W0      = 0.08     ## 波包初始半宽 —— 环带一开始有多"窄"
define RIPPLE_SPREAD  = 2.2      ## 波包展宽率（行进中环带慢慢变宽）
define RIPPLE_IMP_R   = 0.10     ## 中心"扑通"的作用半径
define RIPPLE_IMP_AMP = 3.6      ## 中心"扑通"的强度（相对主波，落点必须明显比涟漪猛）
define RIPPLE_IRREG   = 0.15     ## 角向不均匀度（0 = 完美同心圆，太大会破相）
define RIPPLE_ASPECT  = 1.7778   ## 屏幕宽高比（16:9）
define RIPPLE_PITCH   = 0.5236   ## 相机俯仰角（弧度）。0.5236 = 30°：越小越贴水面、
                                 ## 透视越夸张（地平线 focal·tan(pitch) 必须 > 0.5，
                                 ## 否则地平线进画，上缘反投影发散）
define RIPPLE_FOCAL   = 1.4      ## 焦距（视场越窄透视越缓）
define RIPPLE_HEIGHT  = 0.625    ## 相机离水面高度（控制整体缩放：落点附近 1 平面单位
                                 ## ≈ 半个屏高）。改相机三参记得同步 generate_ripple_
                                 ## assets.py 的同名常量（转场控制图用同一套投影）。

## 挂在整个 master 层上（script.rpy 用 `camera master at screen_ripple(RIPPLE_T0)`）。
## mesh True 是让 fragment shader 能作用在整层渲染结果上的前提。
##
## t0 = 起点进度：主菜单侧的孪生 transform（screens.rpy 的 menu_ripple）在玩家
## 点击"开始游戏"时从 0 起跑，跑到 MENU_EXIT_DELAY 秒离开菜单；游戏侧从
## t0 = RIPPLE_T0 = MENU_EXIT_DELAY / RIPPLE_DURATION 处接着跑完剩下的 —— 波形是
## t 的纯函数，t 衔接画面就衔接。
##
## 为什么是 `camera` 而不是 `show layer`：`scene` 语句会把 layer_at_list 清掉
## （见 SDK scenelists.py 的 clear()，受 config.scene_clears_layer_at_list 控制），
## 而序章第一句正好就是 `scene bg_polyhedron_video` —— 用 show layer 的话涟漪会
## 在转场那一刻被抹掉。camera_list 不受 clear() 影响，所以能撑过整个转场。
transform screen_ripple(t0=0.0):
    mesh True
    shader "game.screen_ripple"
    u_ripple_amp RIPPLE_AMP
    u_ripple_freq RIPPLE_FREQ
    u_ripple_phspeed RIPPLE_PHSPEED
    u_ripple_r0 RIPPLE_R0
    u_ripple_gspeed RIPPLE_GSPEED
    u_ripple_w0 RIPPLE_W0
    u_ripple_spread RIPPLE_SPREAD
    u_ripple_impr RIPPLE_IMP_R
    u_ripple_impamp RIPPLE_IMP_AMP
    u_ripple_irreg RIPPLE_IRREG
    u_ripple_aspect RIPPLE_ASPECT
    u_ripple_pitch RIPPLE_PITCH
    u_ripple_focal RIPPLE_FOCAL
    u_ripple_height RIPPLE_HEIGHT
    u_ripple_t t0
    linear (RIPPLE_DURATION * (1.0 - t0)) u_ripple_t 1.0

################################################################################
## 按钮悬停特效 —— 鼠标停在任何按钮上时，**这颗按钮自己的矩形里** glitch 一下，
## 同时按钮四周浮出一圈会荡的水框。
################################################################################
## 挂在整个 screens 图层上（config.layer_transforms，见本节末尾），所以它扭的是
## **界面本身**（按钮上的字），不是在上面盖一个画好的特效图。
##
## 作用范围 = renpy.focus_coordinates() 给的那个焦点矩形，一个像素都不外溢：
## 特效讲的是"这颗按钮的信号坏了"，不是"光标周围有个特效球"。所以形状必然是
## 矩形（按钮本来就是矩形），也不需要知道光标在按钮里的哪个点 —— 矩形定一切。
## 撕裂会把矩形外的像素横着拽进矩形内，那是 datamosh 该有的样子，仍然不出框。
##
## 为什么是 screens 层而不是连 master 一起：
##   * 菜单/选项/快捷菜单全在 screens 层，"所有菜单选项"这个需求正好等于这一层；
##   * master 层上已经挂着别的整层特效（camera screen_ripple、crt_shutdown），
##     再叠一层只会互相打架，而且要多跑一遍全屏 mesh。
##
## 为什么用轮询而不是按钮的 hovered/unhovered：全游戏几十个 textbutton 都要挂，
## 而且 hovered 给不出按钮的矩形。focus_coordinates() 一次给全，再问一次指针坐标
## 就能区分"鼠标悬停"和"键盘选中"（键盘选中不该起特效）。
##
## ★空闲时不要每帧回调★ 回调返回 0 = 每帧强制重绘整屏。没悬停时按 0.05 轮询
## （20Hz，够快到察觉不出延迟），悬停期间才返回 0 走满帧。
##
## ★水不扭字，水是按钮四周那一圈会荡的框★
## screens 层上，按钮矩形里除了那几个字**什么都没有**（按钮 background None）——
## 任何"扭曲"能扭的只有字本身，水波再小也在推着字游，字就读不清。所以水这一半
## 完全不碰像素，改成 shader 自己**画**出来的一圈线：沿按钮外沿一周的矩形描边，
## 描边到按钮的距离被两列正弦调制着上下起伏，波沿周长跑 —— 看起来就是这颗按钮
## 被水面圈住、水面在荡。字一个像素都没被推动。
##
## 实现要点：
##   * 用矩形 SDF（signed distance field）而不是画四条边：一个 d 就包含"离边框
##     多远"，加个 wob 位移就是"边框在荡"，四个角自动是连续的圆角，不用拼接。
##   * 波的相位取**归一化空间里的极角** atan(p.y/hs.y, p.x/hs.x)：这样长边短边
##     上的波长看起来差不多。★bump 数必须取整数★ —— θ 在左边中点绕回 ±π，
##     只有整数倍频的 sin 在那里才接得上，否则框上会有一道明显的接缝。
##   * 两列不同频率、不同方向的波叠加，看起来才像水面而不像跑马灯。
## glitch 仍然作用在字上（撕裂/马赛克/通道错位都是采样位移），那是要的"坏掉"感。
define HOVER_WAVE   = 0.85      ## 画框整体不透明度（0 = 不画框）
define HOVER_FRAME_PAD = 0.005  ## 框离按钮矩形多远（uv）≈ 5px
define HOVER_FRAME_W = 0.0016   ## 线宽（uv）≈ 1.7px。太粗就变成"选中底框"了
define HOVER_WOB    = 0.0038    ## 荡幅：框离按钮的距离起伏多少（uv）≈ 4px
define HOVER_BUMPS  = 8.0       ## 主波：绕框一周几个起伏。★必须是整数★
define HOVER_BUMPS2 = 13.0      ## 副波：另一个整数，与主波互质才不同步
define HOVER_SPEED  = 3.2       ## 波沿框跑的速度
define HOVER_GLOW   = 0.005     ## 线外侧的柔光衰减距离（uv）；0.0 = 硬线不发光
define HOVER_TINT   = (0.62, 0.85, 1.0)   ## 线的颜色（偏冷的水光）
define HOVER_EDGE   = 0.0015    ## glitch 矩形边缘羽化（uv）≈ 2px，为了不出锯齿
define HOVER_ASPECT = 1.7778    ## 16:9。框的圆角与波长要匀，x 必须按宽高比换算
define HOVER_FADE   = 0.12      ## 淡入/淡出秒数（进出按钮不能"啪"地开关）

## glitch 的几个随机变体。每次**新的一次悬停**（换按钮也算）随机换一个，
## 整体感觉一致（都是"这块界面信号坏了"），只是坏法不同。
## 不写成 shader 里的 if 分支：四种坏法本来就是同一套数学的不同权重，
## 让 Python 填不同的 uniform 就行 —— 加一个变体 = 加一行表，shader 不用动。
##   tear  条带撕裂的最大横移量（uv）    bands 横向条带密度（整屏高分多少条）
##   split RGB 三通道错位量              block 方块马赛克中招比例（0 = 不马赛克）
##   cells 马赛克格子密度（整屏高分多少格，越大格子越小）
define HOVER_GLITCH_MODES = [
    ## 撕裂：横向条带整条错位，最"录像带"的一种
    {"tear": 0.018, "bands": 220.0, "split": 0.0012, "block": 0.00, "cells": 90.0},
    ## 块损：细密小方块马赛克，字被啃掉一块块
    {"tear": 0.004, "bands": 160.0, "split": 0.0010, "block": 0.22, "cells": 150.0},
    ## 错位：三通道分家为主，位移很小但色边很凶
    {"tear": 0.006, "bands": 120.0, "split": 0.0024, "block": 0.00, "cells": 90.0},
    ## 细纹：极细的高频条带抖动，像信号里混了噪声
    {"tear": 0.010, "bands": 460.0, "split": 0.0016, "block": 0.12, "cells": 190.0},
]

init python:
    ## 纯 UI 装饰用的随机源。**不用 renpy.random** —— 那个的状态进存档、参与
    ## 回滚，在渲染回调里摇它会污染剧情用的随机序列。
    import random as _ui_random

    ## 透镜状态：只在渲染回调里读写，不进存档、不参与 rollback。
    ## 这个 dict 是唯一的事实来源，每帧整套推给 trans —— ★不能只在"变了"的时候推★：
    ## 层 transform 每次交互重建时会退回 ATL 里写的静态初值（u_hover_rect 退成
    ## 全 0 = 遮罩恒为 0 = 特效整个消失），而缓存里的矩形没变、就再也不会补写。
    ## 症状是"悬停时好时坏"，而且只有在某次交互之后才犯 —— 极难查，别再改回去。
    _hover_lens = {"amount": 0.0, "st": 0.0, "rect": None,
                   "uv": (0.0, 0.0, 0.0, 0.0), "seed": 0.0,
                   "mode": HOVER_GLITCH_MODES[0]}

    def _hover_lens_tick(trans, st, at):
        x, y = renpy.get_mouse_pos()
        fx, fy, fw, fh = renpy.focus_coordinates()
        ## 焦点矩形存在**且指针确实在里面** —— 键盘选中的按钮不该自己坏给你看。
        on = (fx is not None
              and fx <= x < fx + fw
              and fy <= y < fy + fh)

        ## dt 用 st 差分。screen 重启时 ATL 会被重建、st 归零，此时 dt<0，
        ## 这一帧不推进（下一帧就正常了）；掉帧太久也夹住，免得一步跳完。
        dt = st - _hover_lens["st"]
        _hover_lens["st"] = st
        if dt < 0.0 or dt > 0.25:
            dt = 0.0

        amount = _hover_lens["amount"]
        step = dt / HOVER_FADE
        amount = min(amount + step, 1.0) if on else max(amount - step, 0.0)
        _hover_lens["amount"] = amount

        rect = (fx, fy, fw, fh) if on else None
        if on and rect != _hover_lens["rect"]:
            ## 换了按钮（或刚开始悬停）：换矩形、换种子、换一个 glitch 变体。
            ## 排除上一次那个，理由同 glitch_fx —— 连着抽中同一个就看不出是随机的。
            w = float(config.screen_width)
            h = float(config.screen_height)
            _hover_lens["uv"] = (fx / w, fy / h, (fx + fw) / w, (fy + fh) / h)
            ## 种子由按钮矩形算出来：每颗按钮的花纹互不相同，且同一颗每次都一样。
            _hover_lens["seed"] = (fx * 13.7 + fy * 7.1) % 100.0
            pool = [m for m in HOVER_GLITCH_MODES
                    if m is not _hover_lens["mode"]] or HOVER_GLITCH_MODES
            _hover_lens["mode"] = _ui_random.choice(pool)
        ## 淡出期间 uv/seed/mode 都保持不变 —— 特效留在刚离开的那颗按钮上淡掉。
        _hover_lens["rect"] = rect

        mode = _hover_lens["mode"]
        trans.u_hover_rect = _hover_lens["uv"]
        trans.u_hover_seed = _hover_lens["seed"]
        trans.u_hover_tear = mode["tear"]
        trans.u_hover_bands = mode["bands"]
        trans.u_hover_split = mode["split"]
        trans.u_hover_block = mode["block"]
        trans.u_hover_cells = mode["cells"]
        trans.u_hover_amount = amount

        return 0 if (on or amount > 0.0) else 0.05

    renpy.register_shader("game.hover_lens",
        variables="""
            uniform float u_time;
            uniform vec4 u_hover_rect;
            uniform float u_hover_amount;
            uniform float u_hover_wave;
            uniform float u_hover_frame_pad;
            uniform float u_hover_frame_w;
            uniform float u_hover_wob;
            uniform float u_hover_bumps;
            uniform float u_hover_bumps2;
            uniform float u_hover_speed;
            uniform float u_hover_glow;
            uniform vec3 u_hover_tint;
            uniform float u_hover_bands;
            uniform float u_hover_tear;
            uniform float u_hover_split;
            uniform float u_hover_block;
            uniform float u_hover_cells;
            uniform float u_hover_edge;
            uniform float u_hover_aspect;
            uniform float u_hover_seed;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;

            // ---- 矩形遮罩：只有按钮自己那一块会坏 ----
            // 四条边各羽化 u_hover_edge（≈2px）纯粹是为了不出锯齿，形状仍是矩形。
            // 乘 u_hover_amount 把淡入淡出也吃进来 —— amount=0 时下面所有位移
            // 都恰好是 0、亮环强度也是 0，画面与不挂这个 shader 逐像素相同。
            float e = u_hover_edge;
            float mask = smoothstep(u_hover_rect.x - e, u_hover_rect.x + e, uv.x)
                       * (1.0 - smoothstep(u_hover_rect.z - e, u_hover_rect.z + e, uv.x))
                       * smoothstep(u_hover_rect.y - e, u_hover_rect.y + e, uv.y)
                       * (1.0 - smoothstep(u_hover_rect.w - e, u_hover_rect.w + e, uv.y))
                       * u_hover_amount;

            float tick = floor(u_time * 12.0);

            // ---- glitch（作用在字上）：横向条带撕裂 ----
            // step(0.76, h)：只有约四分之一的条带会撕，全撕就糊成一团噪声了。
            float band = floor(uv.y * u_hover_bands);
            float h = fract(sin(band * 91.7 + tick * 37.3 + u_hover_seed) * 43758.5453);
            vec2 disp = vec2(step(0.76, h) * (h - 0.88) * u_hover_tear * mask, 0.0);

            // ---- glitch：方块马赛克（block 模式才开）----
            // 硬切换（step）而不是渐变：采样点连续漂移会变成"糊"，不是"坏了一块"。
            vec2 grid = vec2(u_hover_cells * u_hover_aspect, u_hover_cells);
            vec2 cell = floor(uv * grid);
            float hb = fract(sin(cell.x * 41.3 + cell.y * 289.1
                                + tick * 13.1 + u_hover_seed) * 43758.5453);
            float hit = step(1.0 - u_hover_block, hb) * step(0.5, mask);
            vec2 quv = (floor(uv * grid * 2.0) + 0.5) / (grid * 2.0);
            vec2 suv = mix(uv, quv, hit) + disp;

            // ---- 采样 + RGB 三通道横向错位（信号不稳的色边）----
            float split = (0.35 + 0.65 * h) * u_hover_split * mask;
            vec4 c = texture2D(tex0, suv, u_lod_bias);
            float cr = texture2D(tex0, suv + vec2(split, 0.0), u_lod_bias).r;
            float cb = texture2D(tex0, suv - vec2(split, 0.0), u_lod_bias).b;
            // 预乘 alpha：任何颜色通道都不能超过该点的 alpha，否则错位处会烧出白斑。
            vec3 rgb = min(vec3(cr, c.g, cb), vec3(c.a));
            float a = c.a;

            // ---- 水：按钮四周那一圈会荡的框（不碰任何像素，纯画上去）----
            // 全部在"等高比"空间里算：x 乘 aspect，于是 1.0 = 一个屏高，
            // 圆角和波长在横竖两个方向上才是一致的。
            vec2 ctr = vec2((u_hover_rect.x + u_hover_rect.z) * 0.5,
                            (u_hover_rect.y + u_hover_rect.w) * 0.5);
            vec2 hs = vec2((u_hover_rect.z - u_hover_rect.x) * 0.5 * u_hover_aspect,
                           (u_hover_rect.w - u_hover_rect.y) * 0.5);
            vec2 p = vec2((uv.x - ctr.x) * u_hover_aspect, uv.y - ctr.y);

            // 矩形 SDF：d = 到"按钮外扩 pad"那个矩形边界的带符号距离（外正内负）
            vec2 qd = abs(p) - (hs + vec2(u_hover_frame_pad));
            float d = length(max(qd, vec2(0.0))) + min(max(qd.x, qd.y), 0.0);

            // 相位 = 归一化空间里的极角。整数 bump 数保证 ±π 处接得上（无接缝）。
            float th = atan(p.y / max(hs.y, 0.0001), p.x / max(hs.x, 0.0001));
            float wob = (sin(th * u_hover_bumps - u_time * u_hover_speed) * 0.65
                       + sin(th * u_hover_bumps2 + u_time * u_hover_speed * 0.73) * 0.35)
                      * u_hover_wob;

            // 线本体 + 外侧柔光；亮度也跟着波走，波峰处更亮，像水面反光。
            float dd = abs(d - wob);
            float line = 1.0 - smoothstep(0.0, u_hover_frame_w, dd);
            float glow = exp(-dd / max(u_hover_glow, 0.0001)) * 0.45;
            float shine = 0.72 + 0.28 * sin(th * u_hover_bumps - u_time * u_hover_speed);
            float g = min(line + glow, 1.0) * shine * u_hover_wave * u_hover_amount;

            // source-over 一层自带 alpha 的水光：空白处也画得出来，字不会被推动。
            rgb = u_hover_tint * g + rgb * (1.0 - g);
            a = g + a * (1.0 - g);

            gl_FragColor = vec4(rgb, a);
        """
    )

transform hover_lens:
    mesh True
    shader "game.hover_lens"
    u_hover_rect (0.0, 0.0, 0.0, 0.0)
    u_hover_amount 0.0
    u_hover_seed 0.0
    u_hover_tear 0.018
    u_hover_bands 220.0
    u_hover_split 0.0012
    u_hover_block 0.0
    u_hover_cells 90.0
    u_hover_wave HOVER_WAVE
    u_hover_frame_pad HOVER_FRAME_PAD
    u_hover_frame_w HOVER_FRAME_W
    u_hover_wob HOVER_WOB
    u_hover_bumps HOVER_BUMPS
    u_hover_bumps2 HOVER_BUMPS2
    u_hover_speed HOVER_SPEED
    u_hover_glow HOVER_GLOW
    u_hover_tint HOVER_TINT
    u_hover_edge HOVER_EDGE
    u_hover_aspect HOVER_ASPECT
    function _hover_lens_tick

## 挂到 screens 图层。用 config.layer_transforms 而不是 renpy.show_layer_at：
## 后者是每个 context 各自的状态（主菜单、游戏、game menu 是不同 context），
## 得在每处入口都调一遍还容易漏；config 是全局的，一处生效处处生效。
define config.layer_transforms = {"screens": [hover_lens]}

## 可独立 `at water_effect` 使用的 transform；image 块内嵌时也可直接复用这套参数。
## 参数解释：
##   u_ripple_strength —— 波纹振幅，数值越大扰动越明显
##   u_ripple_speed    —— 时间推进速度，越大波动越快
##   u_ripple_scale    —— 波纹密度，越大波纹越细
## 用 function _ripple_tick 强制每帧重绘，让自动 u_time 跑起来。
transform water_effect:
    shader "game.water_ripple"
    u_ripple_strength 1.5
    u_ripple_speed 1.0
    u_ripple_scale 12.0
    function _ripple_tick

################################################################################
## 视觉 glitch 五连 —— 每记 glitch 音效随机配一记画面故障。
################################################################################
## 五个变体：抽搐 / 三通道错位 / 条带撕裂 / 垂直失锁 / 块状损坏。
## 随机挑选在 transitions.rpy 的 glitch_fx()（剧本侧只认那一个名字）。
##
## 形式是 **ATL 转场**（transform 带 new_widget/old_widget 参数 + delay 属性，
## 见 Ren'Py 文档 Transitions > ATL Transitions），而不是"挂在某一层上的 transform"：
##   * 转场作用在"整屏这一帧"上，master + screens 一起扭 —— 故障是信号层面的，
##     不该只扭背景不扭文字框；
##   * 用完即弃，不留任何常驻状态，不像层 transform 那样要记得撤下来；
##   * 剧本里原本就写 `with fx_glitch`，换成 `with glitch_fx()` 一行到位。
## 只引用 new_widget（前后两帧通常是同一画面，glitch 不是"换场"而是"这一帧坏了"）。
##
## 时间轴统一用 u_glitch_t 0→1 线性推进（uniform 插值会自动触发重绘），
## 每个 shader 自己按 t 算包络：前半程满强度，后半程收干净 —— 尾巴留着会显脏。
## u_glitch_seed 让同一个变体每次的花纹都不一样（连着触发不会看出是同一记）。
define GLITCH_FX_SECONDS = 0.32

init python:
    import math as _math

    ## ① 抽搐：整屏按格跳动。没有 shader —— 纯位移的"硬跳"本身就是最像
    ## 数字丢帧的一种故障，用 GPU 去做反而多余。
    ## 每 1/26 秒重掷一次偏移（不是平滑摇晃：平滑的是"震动"，跳变的才是"故障"）。
    def _glitch_stutter(seed, duration):
        def f(trans, st, at):
            k = st / duration
            env = 1.0 - max(0.0, (k - 0.5) / 0.5)
            tick = _math.floor(st * 26.0)
            hx = _math.sin(tick * 12.9898 + seed) * 43758.5453
            hy = _math.sin(tick * 78.2330 + seed) * 43758.5453
            trans.xoffset = (hx - _math.floor(hx) - 0.5) * 64.0 * env
            trans.yoffset = (hy - _math.floor(hy) - 0.5) * 20.0 * env
            return 0 if st < duration else None
        return f

    ## ② 三通道错位：R/B 通道左右分家 + 起手两格白闪。最"电子"的一种。
    renpy.register_shader("game.glitch_rgb",
        variables="""
            uniform float u_glitch_t;
            uniform float u_glitch_seed;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_glitch_t;
            float env = 1.0 - smoothstep(0.5, 1.0, t);

            // 分成 9 格，每格一个错位量 —— 连续滑动看起来是"重影"，跳变才是"故障"
            float tick = floor(t * 9.0);
            float h = fract(sin(tick * 12.9898 + u_glitch_seed) * 43758.5453);
            float sp = (h - 0.5) * 0.020 * env;

            vec4 c = texture2D(tex0, uv, u_lod_bias);
            float cr = texture2D(tex0, uv + vec2(sp, 0.0), u_lod_bias).r;
            float cb = texture2D(tex0, uv - vec2(sp, 0.0), u_lod_bias).b;

            // 预乘 alpha：通道值不能超过该点 alpha，否则错位处会烧白
            vec3 rgb = min(vec3(cr, c.g, cb), vec3(c.a));
            rgb = min(rgb + c.a * step(tick, 1.5) * 0.18 * env, vec3(c.a));
            gl_FragColor = vec4(rgb, c.a);
        """
    )

    ## ③ 条带撕裂：横切 26 条，其中三成整条横移，移出去的从另一边卷回来。
    renpy.register_shader("game.glitch_slice",
        variables="""
            uniform float u_glitch_t;
            uniform float u_glitch_seed;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_glitch_t;
            float env = 1.0 - smoothstep(0.55, 1.0, t);

            float band = floor(uv.y * 26.0);
            float tick = floor(t * 7.0);
            float h = fract(sin(band * 91.7 + tick * 37.3 + u_glitch_seed) * 43758.5453);

            // step(0.6, h)：只有靠上的四成条带会撕；全撕就糊成一团噪声了
            float hit = step(0.6, h);
            float amt = hit * (h - 0.8) * 0.35 * env;
            vec4 c = texture2D(tex0, vec2(fract(uv.x + amt), uv.y), u_lod_bias);

            // 撕开的条带压暗一档，边界才看得清是"错位"而不是"糊了"
            gl_FragColor = vec4(c.rgb * (1.0 - 0.25 * hit * env), c.a);
        """
    )

    ## ④ 垂直失锁：整屏上下乱跳 + 一条同步亮带扫过 + 扫描线。CRT 掉同步的样子。
    renpy.register_shader("game.glitch_roll",
        variables="""
            uniform float u_glitch_t;
            uniform float u_glitch_seed;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_glitch_t;
            float env = 1.0 - smoothstep(0.6, 1.0, t);

            float tick = floor(t * 11.0);
            float h = fract(sin(tick * 7.7 + u_glitch_seed) * 43758.5453);
            float off = (h - 0.5) * 0.10 * env;
            vec4 c = texture2D(tex0, vec2(uv.x, fract(uv.y + off)), u_lod_bias);
            vec3 rgb = c.rgb;

            // 同步亮带：一条横带自上而下扫过（fract 让它循环，abs(...-0.5) 是环绕距离）
            float bandpos = fract(u_glitch_seed * 0.01 + t * 1.7);
            float bd = 1.0 - smoothstep(0.0, 0.05, abs(fract(uv.y - bandpos + 0.5) - 0.5));
            rgb = min(rgb + c.a * bd * 0.22 * env, vec3(c.a));

            // 扫描线：隔行压暗
            rgb *= 1.0 - 0.30 * step(0.5, fract(uv.y * 200.0)) * env;
            gl_FragColor = vec4(rgb, c.a);
        """
    )

    ## ⑤ 块状损坏：细密小方块被啃成马赛克，一部分整块被搬走，最坏的一批反色/掉黑。
    ## 格子给到 64x36（≈30px 见方），马赛克再细分到 1/4 格（≈7px）—— 块要小要多，
    ## 大格子看起来像"打了个码"，小格子才像数据在烂。
    renpy.register_shader("game.glitch_block",
        variables="""
            uniform float u_glitch_t;
            uniform float u_glitch_seed;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_glitch_t;
            float env = 1.0 - smoothstep(0.5, 1.0, t);

            vec2 grid = vec2(64.0, 36.0);
            vec2 cell = floor(uv * grid);
            float tick = floor(t * 8.0);
            float h = fract(sin(cell.x * 41.3 + cell.y * 289.1
                              + tick * 13.1 + u_glitch_seed) * 43758.5453);

            // 马赛克用 step 硬切换：采样点连续漂移会变成"糊"，不是"块坏了"
            float hit = step(0.62, h) * step(0.5, env);
            vec2 quv = (floor(uv * grid * 4.0) + 0.5) / (grid * 4.0);

            // 一部分中招的格子整块横向搬走 —— 单纯打码不吓人，"内容跑到别处"才吓人
            float h2 = fract(sin(cell.y * 77.7 + cell.x * 13.9
                               + tick * 5.3 + u_glitch_seed) * 24634.6345);
            vec2 shift = vec2((h2 - 0.5) * 0.10 * step(0.55, h2) * hit, 0.0);
            vec4 c = texture2D(tex0, mix(uv, quv, hit) + shift, u_lod_bias);

            // 反色：预乘 alpha 下就是 a - rgb。只给最坏的一成方块。
            vec3 rgb = mix(c.rgb, c.a - c.rgb, step(0.88, h) * env * 0.9);
            // 再一小撮直接掉成黑洞
            rgb *= 1.0 - step(0.965, h) * env;
            gl_FragColor = vec4(rgb, c.a);
        """
    )

transform gl_stutter(duration=GLITCH_FX_SECONDS, seed=0.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    subpixel True
    function _glitch_stutter(seed, duration)

transform gl_rgb(duration=GLITCH_FX_SECONDS, seed=0.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    mesh True
    shader "game.glitch_rgb"
    u_glitch_seed seed
    u_glitch_t 0.0
    linear duration u_glitch_t 1.0

transform gl_slice(duration=GLITCH_FX_SECONDS, seed=0.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    mesh True
    shader "game.glitch_slice"
    u_glitch_seed seed
    u_glitch_t 0.0
    linear duration u_glitch_t 1.0

transform gl_roll(duration=GLITCH_FX_SECONDS, seed=0.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    mesh True
    shader "game.glitch_roll"
    u_glitch_seed seed
    u_glitch_t 0.0
    linear duration u_glitch_t 1.0

transform gl_block(duration=GLITCH_FX_SECONDS, seed=0.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    mesh True
    shader "game.glitch_block"
    u_glitch_seed seed
    u_glitch_t 0.0
    linear duration u_glitch_t 1.0

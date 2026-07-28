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

            // ---- 中心冲击 ---------------------------------------------------
            float plop = exp(-rho * rho / (2.0 * u_ripple_impr * u_ripple_impr))
                       * sin(t * 55.0) * exp(-t * 9.0)
                       * u_ripple_impamp * smoothstep(0.0, 0.015, rho);

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

            gl_FragColor = texture2D(tex0, suv, u_lod_bias);
        """
    )

## 涟漪 shader 参数 —— 单一数据源。
## 游戏侧 screen_ripple（本文件）和菜单侧 menu_ripple（screens.rpy）都引用这些
## define，两边必然一致，接力才无缝。改任何一个只改这里。
## 长度类参数（R0/W0/IMP_R/GSPEED 等）的单位都是"水面平面单位"：
## 屏幕下缘 ≈ ρ 0.55、左右缘 ≈ 0.79、上缘 ≈ 2.34、上角 ≈ 3.13（由相机参数决定）。
define RIPPLE_AMP     = 0.03     ## 位移幅度（平面单位；近处约合 30px，远处被透视自动缩小）
define RIPPLE_FREQ    = 60.0     ## 载波密度（chirp 前的基准波数）
define RIPPLE_PHSPEED = 190.0    ## 波峰相位推进速度（≈1.6×群速的效果：波峰穿过波包）
define RIPPLE_R0      = 0.05     ## 落点半径 = 波包出发位置（"中心冲击的大小"就是它）
define RIPPLE_GSPEED  = 3.8      ## 波包推进速度：t≈0.81 时包络中心扫过最远的上角(ρ≈3.13)
define RIPPLE_W0      = 0.06     ## 波包初始半宽 —— 环带一开始有多"窄"
define RIPPLE_SPREAD  = 2.2      ## 波包展宽率（行进中环带慢慢变宽）
define RIPPLE_IMP_R   = 0.07     ## 中心"扑通"的作用半径
define RIPPLE_IMP_AMP = 2.6      ## 中心"扑通"的强度（相对主波，落点必须明显比涟漪猛）
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

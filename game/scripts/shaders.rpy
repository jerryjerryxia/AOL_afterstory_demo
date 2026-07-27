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
## 波形模型按真实水滴涟漪的物理来（gravity–capillary ring wave packet）：
##   * 扰动是一圈**环形波包**，不是铺满全盘的正弦：包络中心 R(t) 向外走，
##     包络以内的水面回归平静（文献里叫 quiescent center / caustic），
##     包络以外还没被扰动 —— 老版本整个圆盘一起震，就是"太均匀"的病根。
##   * 波峰的相速 > 波包的群速：单个波峰从包络后缘"长出来"、向前穿过波包、
##     在前缘消失（"amplitudes grow at the trailing edge, diminish at the
##     leading edge"）。表现为圈圈不断从内侧冒出、往外追。
##   * 色散：外圈波长更长（chirp 相位），波包缓慢展宽（low diffusion）。
##   * 能量摊在越来越大的圆周上 → 振幅 ~1/sqrt(r) 几何衰减。
##   * 落点本身：小半径、高强度、衰减极快的中心"扑通"（crater/rebound）；
##     回落水柱再激起一圈更小更弱、迟一拍出发的次波包（rebound jet ring）。
##   * 角向不均：真实涟漪不是完美等幅的圆 —— 加一点低频角向调制（±15% 左右）。
##
## fragment_300 / 复用 tex0、v_tex_coord、u_lod_bias / 自定义 uniform 要自己声明，
## 同上面 water_ripple 的注意事项。不用 u_time：进度全部由 u_ripple_t ∈ [0,1] 驱动
## （ATL 插值自动触发重绘），所以整个波形是 t 的纯函数 —— 这是主菜单侧和游戏侧
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
            uniform float u_ripple_tilt;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            float t = u_ripple_t;

            // 以画面中心为原点。x 乘宽高比让"等距离"成为正圆；y 再乘 tilt
            // （= 1/sin(视角)）把圆压成横椭圆 —— 斜视角看水面的投影。
            vec2 d = uv - vec2(0.5, 0.5);
            d.x *= u_ripple_aspect;
            d.y *= u_ripple_tilt;
            float r = length(d);

            // ---- 主波包 ----------------------------------------------------
            // 包络：高斯环，中心从 r0（落点大小）向外推进，宽度随行进展宽。
            // 后缘 sigma 放大 1.9 倍（波包后拖尾比前沿长），前缘相对干脆。
            float R = u_ripple_r0 + u_ripple_gspeed * t;
            float w = u_ripple_w0 * (1.0 + u_ripple_spread * t);
            float dr = r - R;
            float sig = (dr > 0.0) ? w : (w * 1.9);
            // birth 门控：t=0 时主波包必须严格为 0（菜单待机时 t 停在 0，
            // 不门控的话包络叠着非零载波，主菜单中心会有一块静态的凹陷）。
            // 0.08 内快速淡入 —— 物理上冲击后环圈本来也要一瞬间才成形。
            float birth = smoothstep(0.0, 0.08, t);
            float env = exp(-dr * dr / (2.0 * sig * sig)) * birth;

            // 载波：chirp 相位 r/(1+0.55r) → 外圈波长长（色散）。
            // phspeed 定得比群速对应值高 → 波峰比包络跑得快，从后缘冒出、
            // 前缘消失，正是真实波包的看相。
            float chirp = r / (1.0 + 0.55 * r);
            float wave = sin(u_ripple_freq * chirp - u_ripple_phspeed * t);

            // ---- 次波包（回落水柱激起的第二圈）------------------------------
            // 迟 0.22 出发、更小（群速 0.85×）、更窄（0.7×）、更弱（0.45×）、
            // 波长更短（频率 1.25×）。smoothstep 淡入避免突然出现。
            float t2 = max(t - 0.22, 0.0) / 0.78;
            float R2 = u_ripple_r0 + u_ripple_gspeed * 0.85 * t2;
            float w2 = u_ripple_w0 * (1.0 + u_ripple_spread * t2) * 0.7;
            float dr2 = r - R2;
            float env2 = exp(-dr2 * dr2 / (2.0 * w2 * w2))
                       * smoothstep(0.22, 0.30, t) * 0.45;
            float wave2 = sin(u_ripple_freq * 1.25 * chirp - u_ripple_phspeed * 0.9 * t2);

            // ---- 幅度调制 ---------------------------------------------------
            // 能量摊在越来越大的圆周上：~1/sqrt(r) 几何衰减（0.25 处开始摊薄）。
            float geo = inversesqrt(1.0 + r / 0.25);

            // 角向不均：三个低频谐波叠加，±15% 左右；最后一项带 r，
            // 让不均匀的"花纹"随半径旋转而不是一张静态贴图。
            float ang = atan(d.y, d.x);
            float irr = 1.0 + u_ripple_irreg * (0.5 * sin(ang * 3.0 + 1.7)
                                              + 0.3 * sin(ang * 5.0 - 0.8)
                                              + 0.2 * sin(ang * 9.0 + r * 7.0));

            // 整体回平：前段几乎不衰减（能量靠 geo 摊薄），临近结束加速归零，
            // 保证 t=1 时位移严格为 0（之后 camera transform 会被摘掉）。
            float settle = 1.0 - t * t;

            // ---- 中心冲击 ---------------------------------------------------
            // 落点"扑通"：小半径高斯 × 快速衰减的一两下振荡（砸下去→弹回来）。
            // smoothstep 把 r→0 的位移收到 0（正中心方向未定义，不该有位移）。
            float plop = exp(-r * r / (2.0 * u_ripple_impr * u_ripple_impr))
                       * sin(t * 55.0) * exp(-t * 9.0)
                       * u_ripple_impamp * smoothstep(0.0, 0.015, r);

            // ---- 合成 -------------------------------------------------------
            vec2 dir = d / max(r, 0.0001);
            dir.x /= u_ripple_aspect;
            dir.y /= u_ripple_tilt;

            float amp = u_ripple_amp * settle;
            vec2 offset = dir * ((wave * env + wave2 * env2) * geo * irr + plop) * amp;

            gl_FragColor = texture2D(tex0, uv + offset, u_lod_bias);
        """
    )

## 涟漪 shader 参数 —— 单一数据源。
## 游戏侧 screen_ripple（本文件）和菜单侧 menu_ripple（screens.rpy）都引用这些
## define，两边必然一致，接力才无缝。改任何一个只改这里。
define RIPPLE_AMP     = 0.022    ## 位移幅度（uv 单位；0.022 ≈ 42px @1920，经 geo/env 调制后实际远小）
define RIPPLE_FREQ    = 60.0     ## 载波密度（chirp 前的基准波数）
define RIPPLE_PHSPEED = 100.0    ## 波峰相位推进速度（定成 ≈2×群速的效果：波峰穿过波包）
define RIPPLE_R0      = 0.05     ## 落点半径 = 波包出发位置（"中心冲击的大小"就是它）
define RIPPLE_GSPEED  = 1.5      ## 波包（包络）向外推进速度：t=0.86 时包络中心扫过四角(r≈1.34)
define RIPPLE_W0      = 0.045    ## 波包初始半宽 —— 环带一开始有多"窄"
define RIPPLE_SPREAD  = 2.2      ## 波包展宽率（行进中环带慢慢变宽）
define RIPPLE_IMP_R   = 0.07     ## 中心"扑通"的作用半径
define RIPPLE_IMP_AMP = 2.6      ## 中心"扑通"的强度（相对主波，落点必须明显比涟漪猛）
define RIPPLE_IRREG   = 0.15     ## 角向不均匀度（0 = 完美同心圆，太大会破相）
define RIPPLE_ASPECT  = 1.7778   ## 屏幕宽高比（16:9）
define RIPPLE_TILT    = 2.0      ## 斜视角系数 = 1/sin(视角)。2.0 ≈ 30° 俯视。
                                 ## 改这个记得同步 generate_ripple_assets.py 的 WIPE_TILT。

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
    u_ripple_tilt RIPPLE_TILT
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

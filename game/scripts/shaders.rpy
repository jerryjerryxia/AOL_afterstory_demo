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

## 全屏径向涟漪：从画面中心扩散的一圈圈水波，把整个画面拉扯变形。
## 用在主菜单 → 序章的过场上（见 script.rpy 的 label start）。
##
## 和上面 water_ripple 的区别：那个是"整片水面持续晃"，这个是"往中心丢了块石头"
## —— 有明确的波前、向外推进，振幅随时间衰减，最后归于平静。
##
## 同样的三条注意事项适用（fragment_300 / 复用 tex0、v_tex_coord、u_lod_bias /
## 自定义 uniform 要自己声明）。区别是这里不用 u_time：进度由 ATL 的
## `linear ... u_ripple_t 1.0` 推，自定义 uniform 被 ATL 插值时会自动触发重绘，
## 所以不需要 _ripple_tick 那种手动驱动。
init python:
    renpy.register_shader("game.screen_ripple",
        variables="""
            uniform float u_ripple_t;
            uniform float u_ripple_amp;
            uniform float u_ripple_freq;
            uniform float u_ripple_speed;
            uniform float u_ripple_aspect;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;

            // 以画面中心为原点。x 乘宽高比，让"等距离"是真正的圆而不是椭圆。
            vec2 d = uv - vec2(0.5, 0.5);
            d.x *= u_ripple_aspect;
            float r = length(d);

            // 波前：只有被波扫过的区域才起伏。1.15 保证进度到 1 时连四角都扫到。
            float front = smoothstep(0.0, 0.10, u_ripple_t * 1.15 - r);

            // 振幅平方衰减 —— 水面慢慢平复，而不是到点突然停。
            float decay = (1.0 - u_ripple_t) * (1.0 - u_ripple_t);

            float wave = sin(r * u_ripple_freq - u_ripple_t * u_ripple_speed);

            // 位移方向是径向的。dir.x 要除回宽高比，换算回原始 uv 尺度。
            vec2 dir = d / max(r, 0.0001);
            dir.x /= u_ripple_aspect;

            vec2 offset = dir * wave * u_ripple_amp * decay * front;

            gl_FragColor = texture2D(tex0, uv + offset, u_lod_bias);
        """
    )

## 挂在整个 master 层上（script.rpy 用 `camera master at screen_ripple(RIPPLE_T0)`）。
## mesh True 是让 fragment shader 能作用在整层渲染结果上的前提。
##
## t0 = 起点进度：主菜单侧的孪生 transform（screens.rpy 的 menu_ripple）在玩家
## 点击"开始游戏"时从 0 起跑，跑到 MENU_EXIT_DELAY 秒离开菜单；游戏侧从
## t0 = RIPPLE_T0 = MENU_EXIT_DELAY / RIPPLE_DURATION 处接着跑完剩下的 —— 两边
## 参数一致 + 进度衔接，玩家看到的就是同一场涟漪没停过。改参数必须两边一起改。
##
## 为什么是 `camera` 而不是 `show layer`：`scene` 语句会把 layer_at_list 清掉
## （见 SDK scenelists.py 的 clear()，受 config.scene_clears_layer_at_list 控制），
## 而序章第一句正好就是 `scene bg_polyhedron_video` —— 用 show layer 的话涟漪会
## 在转场那一刻被抹掉。camera_list 不受 clear() 影响，所以能撑过整个转场。
##
## 参数：
##   u_ripple_amp    位移幅度（uv 单位；0.015 ≈ 29px @1920）。调大更"晃"，太大会晕。
##   u_ripple_freq   波纹密度，越大圈越密。
##   u_ripple_speed  波往外推的速度。
transform screen_ripple(t0=0.0):
    mesh True
    shader "game.screen_ripple"
    u_ripple_amp 0.015
    u_ripple_freq 46.0
    u_ripple_speed 26.0
    u_ripple_aspect 1.7778
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

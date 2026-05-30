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

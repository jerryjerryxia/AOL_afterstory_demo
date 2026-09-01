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

            // 边缘衰减（按轴分离）：出界风险只来自"指向那条边"的位移分量 ——
            // x 位移只需在左右边缘归零，y 位移只需在上下边缘归零。两轴合用一个
            // 衰减系数会把贴边的另一轴起伏也掐死，波浪线在边缘窄带里被硬掰直，
            // 看起来像一条断层缝（实测可见）。margin 0.08 按最大位移
            // 0.03×strength 反推，覆盖到 strength≈2.3，且过渡平缓。
            vec2 edge_dist = min(uv, 1.0 - uv);
            vec2 edge_fade = smoothstep(vec2(0.0), vec2(0.08), edge_dist);
            vec2 distorted_uv = uv + vec2(wave1 + wave3, wave2 + wave3) * 0.02 * edge_fade;

            // 保险丝：万一将来 strength 超出 margin 覆盖范围，出界采样按镜面
            // 反射折回，兜底成不显眼的镜像而不是 clamp 色条。正常参数下不触发。
            distorted_uv = 1.0 - abs(1.0 - abs(distorted_uv));

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
## 沙漠奔跑（跑动 sequence，尸首追逐段）：单张背景做"不断向前跑"的错觉。
## 原理 = 光流位移 + 双层半相位交叉淡化：
##   * 位移场从消失点 u_run_vp 向四周发散，幅度随"离消失点的距离"和地面权重
##     （消失点以下越低越大）增长 —— 这正是第一人称前进时的视网膜光流分布：
##     正前方几乎不动，脚下和两侧飞速后掠；
##   * 每层采样点随相位 p∈[0,1) 向消失点回退 → 画面内容被持续"推向四周"，
##     读作向前冲；p 回卷的跳变靠两层相差半周期的采样交叉淡化隐藏 ——
##     哪层跳变哪层恰好全透明，循环无缝；
##   * 代价是轻微的双重曝光感 —— 在"奔跑+世界崩解"的语境里是加分项。
## 与 water_ripple 相同：fragment_300、复用 tex0/v_tex_coord/u_lod_bias、
## u_time 要自己声明；重绘由挂载图的奔跑颠簸 ATL 循环驱动（见 placeholder.rpy），
## 不需要 _ripple_tick。
################################################################################
init python:
    renpy.register_shader("game.desert_run",
        variables="""
            uniform float u_time;
            uniform float u_run_amp;
            uniform float u_run_speed;
            uniform vec2 u_run_vp;
            uniform float u_run_ground;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            vec2 rel = uv - u_run_vp;

            // 光流权重：径向距离 + 地面加成 + 底数（消失点处也留一丝呼吸感）
            float w = length(rel) * 0.6
                    + max(uv.y - u_run_vp.y, 0.0) * u_run_ground
                    + 0.15;
            vec2 d = rel * (w * u_run_amp);

            // 两层相差半周期；采样向消失点回退（uv - d*p），内容外扩 = 前冲
            float t = u_time * u_run_speed;
            float p1 = fract(t);
            float p2 = fract(t + 0.5);
            vec4 c1 = texture2D(tex0, uv - d * p1, u_lod_bias);
            vec4 c2 = texture2D(tex0, uv - d * p2, u_lod_bias);

            // 混合权重 sin^2(pi*p1)：p1=0/1 时恰好全走另一层，回卷不可见
            float b = sin(3.14159265 * p1);
            b = b * b;
            gl_FragColor = c1 * b + c2 * (1.0 - b);
        """
    )

################################################################################
## 按钮悬停特效 —— 鼠标停在任何按钮上时，**这颗按钮自己的矩形里** glitch 一下。
## （按钮四周那圈会荡的水框已关闭但代码保留，见下面 HOVER_WAVE 的注释。）
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
## ★水框当前关闭★（HOVER_WAVE = 0.0）—— 试过圆盘水波、矩形内同心环、四周波动
## 画框三版，都不好看：按钮太小，任何水的形态放进去都只是"多了一圈装饰"。
## 悬停特效现在只留 glitch。代码整套留着（下面那段 SDF 画框是完好的），
## 想再试就把这个值调回 0.4 上下，其余参数不用动。
define HOVER_WAVE   = 0.0       ## 画框整体不透明度（0 = 不画框）
define HOVER_FRAME_PAD = 0.005  ## 框离按钮矩形多远（uv）≈ 5px
define HOVER_FRAME_W = 0.0009   ## 线宽（uv）≈ 1px。太粗就变成"选中底框"了
define HOVER_WOB    = 0.0026    ## 荡幅：框离按钮的距离起伏多少（uv）≈ 3px
define HOVER_BUMPS  = 8.0       ## 主波：绕框一周几个起伏。★必须是整数★
define HOVER_BUMPS2 = 13.0      ## 副波：另一个整数，与主波互质才不同步
define HOVER_SPEED  = 3.2       ## 波沿框跑的速度
define HOVER_GLOW   = 0.0030    ## 线外侧的柔光衰减距离（uv）；0.0 = 硬线不发光
define HOVER_TINT   = (0.62, 0.85, 1.0)   ## 线的颜色（偏冷的水光）
define HOVER_EDGE   = 0.0015    ## glitch 矩形边缘羽化（uv）≈ 2px，为了不出锯齿
define HOVER_ASPECT = 1.7778    ## 16:9。框的圆角与波长要匀，x 必须按宽高比换算
define HOVER_FADE   = 0.12      ## 淡入/淡出秒数（进出按钮不能"啪"地开关）
##
## 试过一版"从左往右滑出的蓝色背景板"代替 glitch，回滚了：背景板一旦成为按钮的
## 底就属于 screens 这一层，而 glitch 是对整层已合成像素做采样位移的，板子会跟着
## 被撕 —— 两者不能共存，二选一之后还是 glitch 更像这个游戏。（那一版在 git 里。）

## glitch 的几个随机变体。每次**新的一次悬停**（换按钮也算）随机换一个，
## 整体感觉一致（都是"这块界面信号坏了"），只是坏法不同。
## 不写成 shader 里的 if 分支：四种坏法本来就是同一套数学的不同权重，
## 让 Python 填不同的 uniform 就行 —— 加一个变体 = 加一行表，shader 不用动。
##   tear  条带撕裂的最大横移量（uv）    bands 横向条带密度（整屏高分多少条）
##   split RGB 三通道错位量
define HOVER_GLITCH_MODES = [
    ## 撕裂：横向条带整条错位，最"录像带"的一种
    {"tear": 0.018, "bands": 220.0, "split": 0.0012},
    ## 错位：三通道分家为主，位移很小但色边很凶
    {"tear": 0.006, "bands": 120.0, "split": 0.0024},
    ## 细纹：极细的高频条带抖动，像信号里混了噪声
    {"tear": 0.010, "bands": 460.0, "split": 0.0016},
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
        ## 滑块（bar / slider）排除在外：那是要一边拖一边盯着数值走的控件，
        ## 画面在手底下"坏掉"会让人不确定自己拖到哪了。glitch 只给"按一下"的
        ## 东西，不给"连续调节"的东西。
        on = (fx is not None
              and fx <= x < fx + fw
              and fy <= y < fy + fh
              and not isinstance(renpy.display.focus.get_focused(),
                                 renpy.display.behavior.Bar))

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

        ## ★取整★ 焦点矩形是浮点的，弹窗入场那点亚像素位移会让它每帧都"变"，
        ## 用原始浮点比相等的话滑入进度会被反复清零 —— 表现是蓝板闪一下就没了。
        ## 取整之后只有真的换了按钮才重滑。
        rect = (int(fx + 0.5), int(fy + 0.5),
                int(fw + 0.5), int(fh + 0.5)) if on else None
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

            vec2 suv = uv + disp;

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
            float glow = exp(-dd / max(u_hover_glow, 0.0001)) * 0.30;
            float shine = 0.55 + 0.45 * sin(th * u_hover_bumps - u_time * u_hover_speed);
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
## 视觉 glitch —— 每记 glitch 音效随机配一记画面故障。
################################################################################
## 四个变体：抽搐 / 三通道错位 / 条带撕裂 / 垂直失锁。
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

################################################################################
## 甩头转场（whip pan）—— 剧本【转头】：第一视角猛回头就跑。
## 用在跑动 sequence 起手的 scene 切换上（convert_script.py 的 run_start 分支）。
##
## 单 widget 方案（只引用 new_widget，同 glitch 转场家族）：新画面横向整圈
## wrap（fract 采样），easeout —— t=0 就是最大速度，首帧即烂糊拖影，正好掩住
## 新旧画面的硬切；随后减速、模糊收干净，稳稳落在奔跑画面上。前后两个场景
## 都是同一片沙漠，整圈横甩读作"原地猛回头"，不需要真的两段式新旧交接。
## 模糊 = 沿甩动方向的 13 tap 均值，宽度正比于瞬时速度 —— 方向性运动模糊，
## 不是均匀糊掉。
init python:
    renpy.register_shader("game.whip_pan",
        variables="""
            uniform float u_whip_t;
            uniform float u_whip_dir;
        """,
        fragment_300="""
            float inv = 1.0 - u_whip_t;
            float p = 1.0 - inv * inv;      // easeout：起手最快，减速停住
            float speed = 2.0 * inv;        // dp/dt，驱动模糊宽度
            float base = v_tex_coord.x + u_whip_dir * p;
            float spread = 0.22 * speed;
            // per-pixel 抖动错开采样相位：不加的话高对比元素（月亮）会拖出
            // 一排离散残影（tap 间距在屏幕上有几十像素），加了就化成连续涂抹。
            float jit = fract(sin(dot(v_tex_coord, vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
            vec4 acc = vec4(0.0);
            for (int i = 0; i < 17; i++) {
                float o = ((float(i) + jit) / 16.0 - 0.5) * spread;
                acc += texture2D(tex0, vec2(fract(base + o), v_tex_coord.y));
            }
            gl_FragColor = acc / 17.0;
        """
    )

transform whip_pan(duration=0.5, direction=1.0, *, new_widget=None, old_widget=None):
    delay duration
    new_widget
    mesh True
    shader "game.whip_pan"
    u_whip_dir direction
    u_whip_t 0.0
    linear duration u_whip_t 1.0

################################################################################
## 黑红混沌 vignette —— 尤里娅对峙段的"混沌死亡"滤镜。
## 剧本标记：【场景滤镜：黑红混沌，逐渐加深】/【停止场景滤镜：…】（见 convert_script.py）。
##
## 形态：画面边缘被黑雾吞噬，吞噬前沿透一圈淤血红；雾的边界不是干净的圆 ——
## 两层 fbm 噪声让它持续翻涌、向画面内伸出触手。u_chaos 0→1 驱动"逐渐加深"：
## 侵蚀半径向中心收缩 + 整体不透明度上升；CHAOS_RAMP_SECONDS 后到顶，之后 ATL
## 循环让 u_chaos 在 1.0↔CHAOS_PULSE_LOW 之间缓慢呼吸。呼吸不只是演出：u_chaos
## 永远在插值 = 每帧都触发重绘，u_time 的翻涌才动得起来（文件头注意事项 3 ——
## 自定义 uniform 不动就没有重绘，翻涌会冻住）。
##
## 挂载：master 层，压在立绘之下（2026-09-01 从独立 "chaos" 图层搬下来的）。
## 作者要求雾不能遮住人物 —— 而图层是严格分层的：只要雾在 master 之上，就必然
## 连立绘一起盖。背景和立绘又都在 master 上，所以雾只能进 master、排在立绘前面。
##   * 排序：靠 `show chaos_vignette behind ws, yl`（同 zorder 内插到立绘之前）。
##     立绘换表情是 re-show 同一个 tag，索引不变，所以这个次序一次定终身；
##     scene 之后新 show 的立绘会追加到顶端，同样在雾之上。
##   * scene 会清空 master 的所有内容，雾也在内 —— 由 config.scene_callbacks 里的
##     _chaos_rescene 自动补回（见下），转换器和剧本都不用管。
##   * 代价：master 上的 camera 会连雾一起变换。本段窗口内只有 route1.rpy:1360 那个
##     已经走完的静态 zoom 1.06（1806 行复位），雾被等比放大 6%、中心左移约 3%——
##     湍流本身的形变远大于此，肉眼无差。★若以后在这段里加【镜头】缓移，雾会跟着
##     一起移★，那时要么把镜头挪出窗口，要么接受。
##   * 对话框在 screens 层，永远压在雾上面，文字不受影响。
## 纯 procedural：不采样底下的画面（Solid 黑底只是 mesh 的载体），输出预乘 alpha
## 直接叠在场景合成结果上。
##
## 时钟：强度和翻涌都不再吃 ATL 的 st，改由 chaos_t0（墙钟）驱动 —— 因为 scene 之后
## 的补发会重建 displayable、st 归零，吃 st 的话每次转场雾都缩回画外重来一遍
## （这一段有 5 次 scene，斜坡总长 80 秒，等于整条渐进作废）。
init python:
    ## 老存档里可能还有内容挂在这个图层上，留着别删 —— 现在不往上面 show 任何东西。
    renpy.add_layer("chaos", above="master")

    renpy.register_shader("game.chaos_vignette",
        variables="""
            uniform float u_ctime;
            uniform float u_chaos;
        """,
        fragment_functions="""
            float cvg_hash(vec2 q) {
                return fract(sin(dot(q, vec2(127.1, 311.7))) * 43758.5453);
            }
            float cvg_noise(vec2 q) {
                vec2 i = floor(q);
                vec2 f = fract(q);
                f = f * f * (3.0 - 2.0 * f);
                float a = cvg_hash(i);
                float b = cvg_hash(i + vec2(1.0, 0.0));
                float c = cvg_hash(i + vec2(0.0, 1.0));
                float d = cvg_hash(i + vec2(1.0, 1.0));
                return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
            }
            float cvg_fbm(vec2 q) {
                float v = 0.0;
                v += 0.500 * cvg_noise(q);
                v += 0.250 * cvg_noise(q * 2.03 + 19.7);
                v += 0.125 * cvg_noise(q * 4.11 - 7.3);
                return v / 0.875;
            }
        """,
        fragment_300="""
            vec2 p = (v_tex_coord - vec2(0.5)) * vec2(1.7778, 1.0);
            float r = length(p);
            ## u_ctime 而不是内置 u_time：内置的是 displayable 的 st，scene 之后
            ## 补发会归零、翻涌图案跳变；u_ctime 走墙钟，补发前后完全连续。
            float t = u_ctime * 0.55;
            // 域扭曲（domain warp）：先算一个涡流场，再用它揉皱采样坐标 ——
            // 黑与红不再各占一环，而是被搅成互相咬合的大理石乱流。
            vec2 w = vec2(cvg_fbm(p * 3.1 + vec2(t * 1.3, -t)),
                          cvg_fbm(p * 3.1 - vec2(t, t * 0.8) + 47.0));
            vec2 q = p + (w - 0.5) * 0.55;
            // 三层反向漂移的 fbm：轮廓翻涌 + 碎触手 + 高频渣滓。
            float n1 = cvg_fbm(q * 2.6 + vec2(t * 0.9, -t * 0.7));
            float n2 = cvg_fbm(q * 6.4 + vec2(-t * 0.5, t * 1.4) + 31.4);
            float n3 = cvg_fbm(p * 11.0 + vec2(t * 2.2, t * 1.7) + 8.8);
            float wob = (n1 - 0.5) * (0.36 + 0.42 * u_chaos)
                      + (n2 - 0.5) * 0.20 + (n3 - 0.5) * 0.08;
            float rr = r + wob;
            // 侵蚀前沿的半径：u_chaos=0 时在画面外（1.05 > 屏角 1.02），滤镜不可见；
            // 加深过程就是这个半径向中心收缩（0.34 = 满强度时中心留一小片清明）。
            float inner = mix(1.05, 0.34, u_chaos);
            float g = smoothstep(inner, inner + 0.30, rr);
            // 血脉：域扭曲 fbm 的高值脊线 —— 淤血红的脉络贯穿整个黑雾深处，
            // 随涡流不断重新排布（不是贴着前沿的一条环带）。
            float veins = smoothstep(0.52, 0.78,
                                     cvg_fbm(q * 4.8 - vec2(t * 1.6, t * 1.2) + 77.7));
            // 越往深处脉络略沉（角落仍以黑为主，但始终有红在里面蠕动）。
            veins *= 1.0 - 0.4 * smoothstep(inner + 0.35, inner + 0.95, rr);
            // 抽搐频闪：按环带量化的时域噪声 —— 整片乱流一格一格地痉挛。
            float flick = 0.72 + 0.28 * cvg_noise(vec2(t * 6.0, floor(rr * 6.0)));
            // 前沿撕裂带：被 n2 打碎，不再是干净的圆环。
            float front = clamp(smoothstep(inner - 0.10, inner + 0.10, rr)
                              - smoothstep(inner + 0.08, inner + 0.30, rr), 0.0, 1.0)
                        * (0.3 + 0.7 * n2);
            // 颜色 = 黑底 + 血红大理石纹 + 前沿撕裂，整体随频闪痉挛。
            vec3 red = vec3(0.34, 0.015, 0.042);
            vec3 col = red * veins * (0.5 + 0.5 * n1);
            col += vec3(0.22, 0.012, 0.02) * front;
            col *= (0.55 + 0.45 * flick);
            // 不透明度：雾体外缘接近全黑（亮背景也压得住）；前沿有自己的实度，
            // 否则在亮背景上血红会被冲成粉色。透明度也跟着频闪轻微搏动。
            float a = g * mix(0.72, 1.0, u_chaos) * (0.90 + 0.10 * flick);
            a = max(a, front * 0.9 * u_chaos);
            a = min(a, 0.985);
            gl_FragColor = vec4(col * a, a);
        """
    )

define CHAOS_ATTACK_SECONDS = 20.0 ## 起手时长。整段加深绑的是墙钟时间，玩家点击速度
                                   ## 不定 —— 起手太慢的话，快速读者会在滤镜可见之前
                                   ## 就走到停止点。
                                   ## ★warper 必须是 easein（前快后慢）★：低强度时雾
                                   ## 还在画面外、肉眼看不见，S 型 ease 的中段增速会
                                   ## 让它在某一秒"突然冒出来"；easein 让角落几秒内
                                   ## 就开始渗、之后减速软着陆，可见过程摊满整段。
define CHAOS_ATTACK_LEVEL = 0.60   ## 起手到达的强度（边缘明显被黑红侵入的程度；
                                   ## 白色沙漠背景会吃掉半透明雾，低于 0.6 存在感不足）
define CHAOS_RAMP_SECONDS = 60.0   ## 起手之后慢慢爬到满强度的时长
define CHAOS_PULSE_LOW = 0.87      ## 到顶后呼吸的下限
define CHAOS_PULSE_SECONDS = 3.2   ## 呼吸半周期（缓慢的濒死喘息感）

## 起雾时刻（绝对墙钟）；None = 没有雾。用 store 变量而不是 ATL 的 st ——
## scene 之后 _chaos_rescene 会把雾重新 show 一遍，st 归零而这个不归零，
## 于是强度和翻涌都接着走，玩家看不出中间被补发过。
default chaos_t0 = None

init python:
    ## 直接借 Ren'Py 自己的 warper，保证曲线与原来的 easein / ease 逐帧一致。
    _CHAOS_EASEIN = renpy.atl.warpers["easein"]
    _CHAOS_EASE = renpy.atl.warpers["ease"]

    def chaos_start():
        """【场景滤镜：黑红混沌】—— 打时钟。转换器发在 show 那一行前面。"""
        store.chaos_t0 = renpy.display.core.get_time()

    def chaos_level(t):
        """起雾 t 秒后的 u_chaos。与原 ATL 同形：easein 20s 到 0.60，
        ease 60s 到 1.0，之后在 1.0↔0.87 之间以 3.2s 半周期呼吸。"""
        if t <= 0.0:
            return 0.0
        if t < CHAOS_ATTACK_SECONDS:
            return CHAOS_ATTACK_LEVEL * _CHAOS_EASEIN(t / CHAOS_ATTACK_SECONDS)
        t -= CHAOS_ATTACK_SECONDS
        if t < CHAOS_RAMP_SECONDS:
            return (CHAOS_ATTACK_LEVEL
                    + (1.0 - CHAOS_ATTACK_LEVEL) * _CHAOS_EASE(t / CHAOS_RAMP_SECONDS))
        t = (t - CHAOS_RAMP_SECONDS) % (2.0 * CHAOS_PULSE_SECONDS)
        if t < CHAOS_PULSE_SECONDS:
            return 1.0 + (CHAOS_PULSE_LOW - 1.0) * _CHAOS_EASE(t / CHAOS_PULSE_SECONDS)
        return (CHAOS_PULSE_LOW + (1.0 - CHAOS_PULSE_LOW)
                * _CHAOS_EASE((t - CHAOS_PULSE_SECONDS) / CHAOS_PULSE_SECONDS))

    def _chaos_tick(trans, st, at):
        """每帧把强度和翻涌时钟喂给 shader。`return 0` 同时是重绘驱动
        （文件头注意事项 3：自定义 uniform 不动就没有重绘，翻涌会冻住）——
        和 _ripple_tick / _hover_lens_tick 同一个路子。
        预测阶段也会被调，所以只读 store 不写。"""
        t0 = getattr(store, "chaos_t0", None)
        dt = 0.0 if t0 is None else (renpy.display.core.get_time() - t0)
        trans.u_chaos = chaos_level(dt)
        trans.u_ctime = dt
        return 0

    ## 转场之后的补发不走 config.scene_callbacks —— 那个回调在 renpy.scene()
    ## 内部触发，此时新背景还没 show 上来，雾会落到背景「底下」（实测 master 次序
    ## 变成 ['chaos_vignette', 'bg_desert_moonless', 'yl', 'ws']，雾完全看不见）。
    ## 而且雾一旦已在层里，再 show 同一个 tag 只是原地替换、不会因为 behind 移位，
    ## 补救不回来。改由转换器在每条 scene 之后补一行 show（见 convert_script.py
    ## _insert_chaos_rescene）。

transform chaos_vignette_fx:
    mesh True
    shader "game.chaos_vignette"
    u_chaos 0.0            ## 只是首帧默认值，随后每帧被 _chaos_tick 覆写
    u_ctime 0.0
    function _chaos_tick

image chaos_vignette = At(Solid("#000"), chaos_vignette_fx)


################################################################################
## 立绘信号故障（sprite_glitch）：横向条带撕裂 + RGB 通道错位 + 行丢失。
## 面部 glitch 的出现/复原动效、尤里娅的异常消失与异变演出共用这一个 shader，
## 用法全部是"挂在 image ATL / at transform 上、由 ATL ease 驱动 uniform"：
##   u_sg_amp      撕裂强度 0..1。出现 = 1→0（扭曲着成形，落定成静帧）；
##                 消失/异变 = 0→1（越撕越碎）。
##   u_sg_top/bot  作用带（纹理 Y 比例，带缘 smoothstep 羽化）。面部动效只罩
##                 头部（王霜/尤里娅的脸都在立绘顶部 ~20%），全身演出取 0..1。
##   u_sg_dropout  行丢失阈值 0..1：随机顺序整行消失，1 = 全部丢完。行序随机
##                 但不随时间跳（丢掉的行保持丢失）—— 消失读作"信号被逐行掐断"
##                 而不是闪烁。面部动效恒 0。
## 重绘驱动：这些 uniform 全程在 ATL ease 里，动画期间每帧重绘、u_time 自动
## 推进；ease 结束后画面静止，不再耗重绘（面部动效落定后 shader 等效直通）。
## fragment_300 / 复用 tex0、v_tex_coord、u_lod_bias 的理由同 water_ripple。
init python:
    renpy.register_shader("game.sprite_glitch",
        variables="""
            uniform float u_time;
            uniform float u_sg_amp;
            uniform float u_sg_top;
            uniform float u_sg_bot;
            uniform float u_sg_dropout;
        """,
        fragment_300="""
            vec2 uv = v_tex_coord.xy;
            // 作用带（带缘羽化），带外像素完全不动
            float band = smoothstep(u_sg_top - 0.05, u_sg_top, uv.y)
                       * (1.0 - smoothstep(u_sg_bot, u_sg_bot + 0.05, uv.y));
            float amp = u_sg_amp * band;

            // 条带撕裂：行量化 + 每行伪随机横移，随时间跳变（撕裂在重排自己）
            float row = floor(uv.y * 90.0);
            float tick = floor(u_time * 18.0);
            float n1 = fract(sin(row * 127.1 + tick * 311.7) * 43758.5453);
            // 三成"重灾行"位移翻倍 —— 全等幅像百叶窗，不像坏掉（同离线生成器）
            float heavy = 1.0 + step(0.7, fract(n1 * 7.13)) * 1.2;
            vec2 suv = vec2(uv.x + (n1 - 0.5) * 0.11 * amp * heavy, uv.y);

            // RGB 错位：R/B 左右分家，轮廓外侧留红青边
            float ca = 0.014 * amp;
            vec4 cr = texture2D(tex0, vec2(suv.x + ca, suv.y), u_lod_bias);
            vec4 cg = texture2D(tex0, suv, u_lod_bias);
            vec4 cb = texture2D(tex0, vec2(suv.x - ca, suv.y), u_lod_bias);
            vec4 col = vec4(cr.r, cg.g, cb.b, max(cg.a, max(cr.a, cb.a)));

            // 行丢失：行序伪随机但与时间无关 —— 丢掉的行保持丢失
            float n2 = fract(sin(row * 269.5 + 7.7) * 12043.77);
            col *= step(u_sg_dropout * band, n2);

            gl_FragColor = col;
        """
    )

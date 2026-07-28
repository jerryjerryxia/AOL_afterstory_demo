"""Generate the ripple-transition control art for the main-menu → game 过场.

Pure math — tune by editing the constants below and re-running:

    python generate_ripple_assets.py

Outputs (game/images/ui/fx/):
    ripple_wipe.png  ImageDissolve 的控制图：白=先出现、黑=后出现（SDK
                     transition.py 原话 "white pixels will dissolve in first"）。
                     落点白 → 远处黑的斜坡 + 正弦环：新画面从落点向外揭开，
                     方向、透视都和涟漪 shader 一致。
                     （整屏"荡漾"本身是 GLSL shader —— 见 game/scripts/shaders.rpy
                     的 game.screen_ripple —— 不吃这里的任何图。）

透视：和 shader 同一套针孔相机 ↔ 水面平面投影 —— 每个像素反投影到虚拟水面，
斜坡/正弦环都定义在**平面真实距离** ρ 上。于是揭开的等值线在屏幕上自带
近大远小：上半屏的环挤紧、下半屏的环摊开，跟涟漪的圈圈严格同一族曲线。
CAM_* 三个常量必须和 shaders.rpy 的 RIPPLE_PITCH / RIPPLE_FOCAL / RIPPLE_HEIGHT
保持一致，改一边必须同步另一边。
"""

import math
import os

from PIL import Image

OUT_DIR = os.path.join("game", "images", "ui", "fx")

## 画布尺寸 = 游戏分辨率（见 options.rpy 的 config.screen_width/height）。
## ImageDissolve 的控制图必须和转场区域同尺寸，否则会被拉伸、波纹间距失真。
SCREEN_W, SCREEN_H = 1920, 1080
ASPECT = SCREEN_W / SCREEN_H

## 相机参数 —— 与 shaders.rpy 的 RIPPLE_PITCH / RIPPLE_FOCAL / RIPPLE_HEIGHT 逐字一致。
CAM_PITCH = 0.5236   # 俯仰 30°（弧度）
CAM_FOCAL = 1.4      # 焦距
CAM_HEIGHT = 0.625   # 相机离水面高度

## ripple_wipe 的波纹：AMP 是环形起伏的幅度（占归一化斜坡的比例），
## WAVELENGTH 是相邻两圈波峰的间距（平面单位）。AMP 调大 = 揭开边缘更"皱"。
WIPE_RIPPLE_AMP = 0.045
WIPE_RIPPLE_WAVELENGTH = 0.30


def _write(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    print("  %-16s %s" % (name, img.size))
    return path


def _plane_rho(uv_x, uv_y, sn, cs):
    """屏幕 uv → 水面平面上到落点的距离 ρ。和 shader 里的反投影逐式对应。"""
    xi = (uv_x - 0.5) * ASPECT
    eta = 0.5 - uv_y
    dy = eta * cs - CAM_FOCAL * sn          # 恒为负（地平线在画外上方）
    dz = eta * sn + CAM_FOCAL * cs
    tt = CAM_HEIGHT / max(-dy, 1e-4)
    x_p = xi * tt
    z_p = dz * tt
    z0 = CAM_HEIGHT * cs / sn               # 落点（屏幕中心视线的落水点）
    return math.hypot(x_p, z_p - z0)


def make_wipe():
    """落点白 → 远处黑的 ρ 斜坡（透视度量），叠加正弦环。

    归一化用四个角里最大的 ρ（上两角最远）—— 保证转场收尾时最后消失的就是
    最远的角，不会有哪块因为斜坡被截断而时序错乱。
    """
    w, h = SCREEN_W, SCREEN_H
    sn, cs = math.sin(CAM_PITCH), math.cos(CAM_PITCH)

    max_rho = max(
        _plane_rho(0.0, 0.0, sn, cs), _plane_rho(1.0, 0.0, sn, cs),
        _plane_rho(0.0, 1.0, sn, cs), _plane_rho(1.0, 1.0, sn, cs))

    img = Image.new("L", (w, h))
    px = img.load()

    for y in range(h):
        uv_y = (y + 0.5) / h
        for x in range(w):
            rho = _plane_rho((x + 0.5) / w, uv_y, sn, cs)
            v = rho / max_rho
            v += WIPE_RIPPLE_AMP * math.sin(rho / WIPE_RIPPLE_WAVELENGTH * math.tau)
            ## 1-v：ImageDissolve 白先黑后，落点要最先出现所以落点必须是白。
            px[x, y] = max(0, min(255, int((1.0 - v) * 255.0)))

    return _write(img, "ripple_wipe.png")


def main():
    if not os.path.isdir("game"):
        raise SystemExit("run this from the project root (X:\\GameDev\\EndlessSummerSyndromeDemo)")

    os.makedirs(OUT_DIR, exist_ok=True)
    print("writing to %s/" % OUT_DIR.replace("\\", "/"))
    make_wipe()
    print("done")


if __name__ == "__main__":
    main()

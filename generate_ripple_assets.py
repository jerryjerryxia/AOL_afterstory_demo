"""Generate the ripple-transition control art for the main-menu → game 过场.

Pure math — tune by editing the constants below and re-running:

    python generate_ripple_assets.py

Outputs (game/images/ui/fx/):
    ripple_wipe.png  ImageDissolve 的控制图：白=先出现、黑=后出现（SDK
                     transition.py 原话 "white pixels will dissolve in first"）。
                     中心白 → 四角黑的径向斜坡 + 正弦环：新画面从中心向外揭开，
                     方向和涟漪扩散一致，揭开的边缘是带波纹的水圈而不是几何圆。
                     （整屏"荡漾"本身是 GLSL shader —— 见 game/scripts/shaders.rpy
                     的 game.screen_ripple —— 不吃这里的任何图。）
"""

import math
import os

from PIL import Image

OUT_DIR = os.path.join("game", "images", "ui", "fx")

## 画布尺寸 = 游戏分辨率（见 options.rpy 的 config.screen_width/height）。
## ImageDissolve 的控制图必须和转场区域同尺寸，否则会被拉伸、波纹间距失真。
SCREEN_W, SCREEN_H = 1920, 1080

## ripple_wipe 的波纹：AMP 是边缘起伏的幅度（占半径的比例），
## WAVELENGTH 是相邻两圈波峰的像素间距。AMP 调大 = 边缘更"皱"。
WIPE_RIPPLE_AMP = 0.045
WIPE_RIPPLE_WAVELENGTH = 130.0

## 斜视角系数 = 1/sin(视角)。必须和 shader 侧的 u_ripple_tilt（shaders.rpy 的
## screen_ripple + screens.rpy 的 menu_ripple）一致：荡漾的椭圆和转场揭开的
## 椭圆要是同一套，2.0 = 约 30° 俯视（纵向压成一半）。
WIPE_TILT = 2.0

def _write(img, name):
    path = os.path.join(OUT_DIR, name)
    img.save(path)
    print("  %-16s %s" % (name, img.size))
    return path


def make_wipe():
    """中心白 → 四角黑的径向斜坡（斜视角椭圆度量），叠加正弦环。

    dy 乘 WIPE_TILT = 等值线是纵向压扁的椭圆，跟 shader 里的涟漪同一套投影。
    归一化用的是"中心到角"的距离（同一椭圆度量）而不是到边的距离 —— 用后者的
    话四个角永远到不了纯黑，斜坡在角上被截断，转场收尾时角落的时序会不一致。
    """
    w, h = SCREEN_W, SCREEN_H
    cx, cy = w / 2.0, h / 2.0
    max_r = math.hypot(cx, cy * WIPE_TILT)

    img = Image.new("L", (w, h))
    px = img.load()

    for y in range(h):
        dy = (y - cy) * WIPE_TILT
        for x in range(w):
            r = math.hypot(x - cx, dy)
            v = r / max_r
            v += WIPE_RIPPLE_AMP * math.sin(r / WIPE_RIPPLE_WAVELENGTH * math.tau)
            ## 1-v：ImageDissolve 白先黑后，中心要最先出现所以中心必须是白。
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

# -*- coding: utf-8 -*-
"""
把一张立绘/背景加工成"电视信号失稳"的 glitch 版本。

算法是游戏里那几个 shader 的离线复刻（game/scripts/shaders.rpy）：
  gl_slice  条带撕裂  —— 横切成若干条，一部分整条横移、移出去的从另一边卷回来
  gl_rgb    三通道错位 —— R/B 通道左右分家，边缘留下红青色边
  gl_roll   垂直失锁  —— 若干条带上下错位 + 一条同步亮带扫过 + 隔行扫描线
  （块状损坏没做——那一路已经从游戏里移除了）
再加两样只有静帧才需要的东西：重影（stutter 的定格版）和信号丢失的透明断行。

★透明立绘的处理★ 全程在**预乘 alpha** 空间里算。通道错位如果直接在直通 alpha 上
做，透明区域那些"没有颜色的颜色"会被拽进画面，边缘糊成一圈脏灰；预乘之后
alpha=0 的地方 rgb 恒为 0，错位出去的就是干净的色边。最后再反预乘写回 PNG。

用法：
    python generate_glitch_art.py 输入.png -o 输出目录 --variants 3
    python generate_glitch_art.py 输入.png -o 输出.png --seed 7 --strength 1.4
"""
import argparse
import os

import numpy as np
from PIL import Image


def _load_premultiplied(path):
    """读 PNG → float32 预乘 alpha 数组 (h, w, 3) + alpha (h, w)，值域 0..1。"""
    im = Image.open(path).convert("RGBA")
    arr = np.asarray(im).astype(np.float32) / 255.0
    a = arr[..., 3]
    rgb = arr[..., :3] * a[..., None]
    return rgb, a


def _save_unpremultiplied(rgb, a, path):
    """反预乘写回 PNG。alpha=0 处直接写 0，避免除零放大出噪点。"""
    safe = np.maximum(a, 1e-6)[..., None]
    out_rgb = np.clip(rgb / safe, 0.0, 1.0)
    out = np.concatenate([out_rgb, np.clip(a, 0.0, 1.0)[..., None]], axis=-1)
    Image.fromarray((out * 255.0 + 0.5).astype(np.uint8), "RGBA").save(path)


def _roll_x(a, dx):
    return np.roll(a, dx, axis=1)


def slice_tear(rgb, a, rng, strength):
    """gl_slice：横切成条，约四成整条横移，移出画面的从另一边卷回来。

    条带高度不等（真实的信号撕裂不会是等分的），并且留少数几条"重灾条"——
    位移大一个数量级。全等幅的位移看起来像百叶窗，不像坏掉。
    """
    h, w = a.shape
    y = 0
    while y < h:
        band = int(rng.integers(8, 120))
        y1 = min(y + band, h)
        if rng.random() < 0.26:
            heavy = rng.random() < 0.10
            amp = 0.17 if heavy else 0.055
            dx = int(rng.normal(0.0, amp * w * strength))
            if dx:
                rgb[y:y1] = _roll_x(rgb[y:y1], dx)
                a[y:y1] = _roll_x(a[y:y1], dx)
                # 撕开的条略压暗，边界才看得出是"错位"而不是"糊了"
                rgb[y:y1] *= 0.86
        y = y1
    return rgb, a


def channel_split(rgb, a, rng, strength):
    """gl_rgb：R 往一边、B 往另一边，G 留在原地。

    alpha 取三者的最大值 —— 于是错位出去的通道在轮廓外侧留下红/青边，
    正是信号串扰的样子；如果 alpha 只取原图，色边会被自己的轮廓裁掉。
    """
    dr = int(rng.integers(6, 17) * strength)
    db = -int(rng.integers(6, 17) * strength)
    dy = int(rng.integers(-4, 5))

    r = np.roll(np.roll(rgb[..., 0], dr, axis=1), dy, axis=0)
    b = np.roll(rgb[..., 2], db, axis=1)
    ar = np.roll(np.roll(a, dr, axis=1), dy, axis=0)
    ab = np.roll(a, db, axis=1)

    out = np.stack([r, rgb[..., 1], b], axis=-1)
    return out, np.maximum(np.maximum(ar, a), ab)


def vertical_desync(rgb, a, rng, strength):
    """gl_roll：几条带子上下错位。垂直失锁比横向撕裂少见，所以只给两三条。"""
    h, w = a.shape
    for _ in range(int(rng.integers(2, 4))):
        y = int(rng.integers(0, h))
        band = int(rng.integers(40, 200))
        y1 = min(y + band, h)
        dy = int(rng.normal(0.0, 26.0 * strength))
        if dy:
            rgb[y:y1] = np.roll(rgb[y:y1], dy, axis=0)
            a[y:y1] = np.roll(a[y:y1], dy, axis=0)
    return rgb, a


def sync_band(rgb, a, rng, strength):
    """一条正在扫过的同步亮带：带内整体提亮，上下缘各一条更亮的细线。"""
    h, w = a.shape
    y = int(rng.integers(0, h - 60))
    band = int(rng.integers(26, 90))
    y1 = min(y + band, h)
    # 预乘空间里"提亮"= 往 rgb 加 alpha 的倍数，加完不会超过 alpha（不烧白）
    rgb[y:y1] += a[y:y1][..., None] * (0.16 * strength)
    for edge in (y, y1 - 2):
        rgb[edge:edge + 2] += a[edge:edge + 2][..., None] * (0.30 * strength)
    return rgb, a


def dropout_rows(rgb, a, rng, strength):
    """信号丢失：几条极窄的行整条消失（alpha 归零）。"""
    h, w = a.shape
    for _ in range(int(rng.integers(2, 5))):
        y = int(rng.integers(0, h - 12))
        band = int(rng.integers(2, 11))
        a[y:y + band] = 0.0
        rgb[y:y + band] = 0.0
    return rgb, a


def ghost(rgb, a, rng, strength):
    """重影：一份低透明度的副本压在下面，模拟余辉/串台。"""
    dx = int(rng.integers(24, 64) * strength) * (1 if rng.random() < 0.5 else -1)
    dy = int(rng.integers(-10, 11))
    ga = np.roll(np.roll(a, dx, axis=1), dy, axis=0) * 0.15
    grgb = np.roll(np.roll(rgb, dx, axis=1), dy, axis=0) * 0.15
    # source-over：原图在上，重影在下
    out_a = a + ga * (1.0 - a)
    out_rgb = rgb + grgb * (1.0 - a[..., None])
    return out_rgb, out_a


def scanlines(rgb, a, pitch=3, depth=0.22):
    """隔行压暗。只乘 rgb 不动 alpha —— 透明处本来就没有东西可压。"""
    rgb = rgb.copy()
    rgb[::pitch] *= (1.0 - depth)
    return rgb, a


def glitch(path, seed=0, strength=1.0):
    rng = np.random.default_rng(seed)
    rgb, a = _load_premultiplied(path)

    rgb, a = ghost(rgb, a, rng, strength)
    rgb, a = slice_tear(rgb, a, rng, strength)
    rgb, a = vertical_desync(rgb, a, rng, strength)
    rgb, a = channel_split(rgb, a, rng, strength)
    rgb, a = sync_band(rgb, a, rng, strength)
    rgb, a = dropout_rows(rgb, a, rng, strength)
    rgb, a = scanlines(rgb, a)

    # 预乘空间的硬约束：任何通道都不能超过 alpha，否则反预乘时会烧成白斑
    rgb = np.minimum(rgb, a[..., None])
    return np.clip(rgb, 0.0, 1.0), np.clip(a, 0.0, 1.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--out", required=True,
                    help="输出文件（单张）或输出目录（--variants > 1 时）")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--variants", type=int, default=1)
    args = ap.parse_args()

    base = os.path.splitext(os.path.basename(args.input))[0]

    for i in range(args.variants):
        seed = args.seed + i
        rgb, a = glitch(args.input, seed=seed, strength=args.strength)
        if args.variants > 1 or os.path.isdir(args.out):
            os.makedirs(args.out, exist_ok=True)
            out = os.path.join(args.out, "%s_glitch%d.png" % (base, seed))
        else:
            out = args.out
        _save_unpremultiplied(rgb, a, out)
        # ascii-safe：Windows 控制台常是 GBK/cp1252，中文文件名直接 print 会崩
        line = "%s  (seed=%d strength=%.2f)" % (out, seed, args.strength)
        print(line.encode("ascii", "backslashreplace").decode("ascii"))


if __name__ == "__main__":
    main()

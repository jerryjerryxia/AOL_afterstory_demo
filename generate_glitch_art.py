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
from PIL import Image, ImageFilter


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


# ---------------------------------------------------------------------------
# 面部恐怖模式（--face）：只毁脸，不碰身体。
# 剧本【…表情上蒙了glitch】的字面意图是【王霜面部开始出现glitch】——要的是
# "脸坏掉了"的恐怖感，不是全身电视串台。三个种子各自生成不同的扭曲，
# 游戏里 0.12s 轮播 —— 脸在不停地重新排列自己。
#
# 效果栈（全部限制在自动检测的脸部椭圆内，边缘羽化）：
#   melt   低频位移场热熔，带向下偏置 —— 五官糊开、下坠
#   tears  脸内横向错位条 —— 眼睛和嘴从中间错开
#   ghost  半透明的第二张脸错位叠影 —— "脸后面还有一张脸"
#   decay  尸斑污渍 + 灰紫尸色 + 眼窝发黑
# ---------------------------------------------------------------------------

def detect_face_box(path, top_frac=0.16, pad=0.20):
    """自动定位脸：立绘不透明包围盒的顶部 top_frac 高度内找肤色像素
    （r-b 明显为正的暖色 —— 头发是蓝的、衣服是白的，只有皮肤是暖的），
    取其 2~98 百分位包围盒外扩 pad。返回 (x0, y0, x1, y1)。"""
    rgb, a = _load_premultiplied(path)
    h, w = a.shape
    rows = np.where(a.max(axis=1) > 0.05)[0]
    by0 = int(rows[0]) if len(rows) else 0
    by1 = int(rows[-1]) if len(rows) else h
    win_y1 = by0 + int((by1 - by0) * top_frac)
    safe = np.maximum(a, 1e-6)
    r, g, b = (rgb[..., i] / safe for i in range(3))
    warm = (a > 0.5) & (r - b > 0.06) & (r > 0.55) & (r - g > 0.015)
    warm[win_y1:] = False
    ys, xs = np.where(warm)
    if len(ys) < 400:
        raise SystemExit("face detect failed: %s (warm px=%d)" % (path, len(ys)))
    x0, x1 = np.percentile(xs, 2), np.percentile(xs, 98)
    y0, y1 = np.percentile(ys, 2), np.percentile(ys, 98)
    fw, fh = x1 - x0, y1 - y0
    x0 -= fw * pad; x1 += fw * pad
    y0 -= fh * pad * 1.4; y1 += fh * pad          # 额头多留一点（刘海压着脸）
    return (int(max(0, x0)), int(max(0, y0)),
            int(min(w, x1)), int(min(h, y1)))


def _smooth_noise(rng, h, w, scale):
    """低频平滑噪声：低分辨率高斯噪声双线性放大到 (h, w)，值域约 ±1。"""
    gh, gw = max(2, h // scale), max(2, w // scale)
    g = rng.standard_normal((gh, gw)).astype(np.float32)
    return np.asarray(Image.fromarray(g, "F").resize((w, h), Image.BILINEAR),
                      dtype=np.float32)


def _bilinear(img, my, mx):
    """按浮点坐标图采样（位移场用）。img 可为 (h,w) 或 (h,w,3)。"""
    h, w = img.shape[:2]
    y0 = np.clip(np.floor(my).astype(np.int32), 0, h - 1)
    x0 = np.clip(np.floor(mx).astype(np.int32), 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    fy, fx = my - y0, mx - x0
    if img.ndim == 3:
        fy, fx = fy[..., None], fx[..., None]
    top = img[y0, x0] * (1 - fx) + img[y0, x1] * fx
    bot = img[y1, x0] * (1 - fx) + img[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def _contour_mask(face, fa, fh, fw):
    """追踪面庞轮廓的掩膜（--face-contour）：框内肤色检测 → 闭运算把眼/嘴等
    非肤色五官并进脸内 → 高斯羽化。椭圆掩膜在瓜子脸+乱发的立绘上会盖出一块
    明显的"椭圆图章"（尤里娅），轮廓掩膜只毁脸皮所在的形状，压着脸的发丝
    保持干净。阈值按"皮肤是画面里唯一偏暖的浅色"取，需要比自动检测宽松
    （极浅肤色 r-b 只有 0.01~0.06）。"""
    safe = np.maximum(fa, 1e-6)[..., None]
    sc = face / safe
    r, g, b = sc[..., 0], sc[..., 1], sc[..., 2]
    skin = (fa > 0.5) & (r - b > 0.012) & (r - g > 0.004) & (r > 0.55)
    m = Image.fromarray((skin * 255).astype(np.uint8), 'L')
    # 1/12 缩略图上做闭运算（Max 后 Min）：眼睛/嘴是脸内几十像素的"洞"，
    # 缩略图上 4 像素半径的膨胀就能糊拢，再腐蚀回轮廓；顺带抹掉孤立噪点。
    sw, sh = max(2, fw // 12), max(2, fh // 12)
    small = m.resize((sw, sh), Image.BILINEAR)
    small = small.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    small = small.filter(ImageFilter.GaussianBlur(2))
    mask = np.asarray(small.resize((fw, fh), Image.BILINEAR), np.float32) / 255.0
    # 收紧半透明边缘：0.35 以下当背景，0.75 以上算全脸，中间线性羽化。
    mask = np.clip((mask - 0.35) / 0.40, 0.0, 1.0)
    # 宽松椭圆先验压框角：肤色阈值放得很宽（不然极浅肤色捕不全），暖白的
    # 衣料/发丝在框角会被零星误捕、闭运算再连成条。椭圆取得比脸大一圈
    # （1.0~1.25 才开始衰减），脸心不受影响，只掐掉角落的误检。
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    ny = (yy - fh / 2) / (fh / 2)
    nx = (xx - fw / 2) / (fw / 2)
    d = np.sqrt(nx * nx + ny * ny)
    return mask * np.clip((1.25 - d) / 0.25, 0.0, 1.0)


def face_horror(path, seed, strength, tint=(0.72, 0.68, 0.80), box=None,
                contour=False):
    """原图 + 只在脸部掩膜内的毁容效果。身体一个像素都不动。
    tint：decay 步骤的尸色（对亮度的 RGB 乘数）。默认灰紫（王霜）；
    尤里娅用血红（--tint 0.65,0.12,0.10）——同一条毁容管线，只换色调。
    box：手动面部框 (x0, y0, x1, y1)，图像宽高的比例值。自动检测认肤色暖调，
    在极浅肤色/带暖色描边饰物的立绘上会跑偏（尤里娅），这时用 --face-box
    手动指定；None = 自动检测（王霜）。
    contour：True = 掩膜追踪面庞轮廓（_contour_mask，尤里娅）；
    False = 框内切椭圆羽化（王霜沿用）。"""
    rng = np.random.default_rng(seed)
    rgb, a = _load_premultiplied(path)
    if box is not None:
        h, w = a.shape
        x0, y0, x1, y1 = (int(box[0] * w), int(box[1] * h),
                          int(box[2] * w), int(box[3] * h))
    else:
        x0, y0, x1, y1 = detect_face_box(path)
    fh, fw = y1 - y0, x1 - x0
    face = rgb[y0:y1, x0:x1].copy()
    fa = a[y0:y1, x0:x1].copy()

    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    if contour:
        mask = _contour_mask(face, fa, fh, fw)
    else:
        ny = (yy - fh / 2) / (fh / 2)
        nx = (xx - fw / 2) / (fw / 2)
        d = np.sqrt(nx * nx + ny * ny)
        mask = np.clip((1.05 - d) / 0.30, 0.0, 1.0)  # 椭圆内 1，边缘羽化到 0

    # melt：位移场热熔。向下偏置 —— 器官会坠，信号不会。
    sc = max(6, fh // 6)
    dx = _smooth_noise(rng, fh, fw, sc) * 0.11 * fw * strength
    dy = (_smooth_noise(rng, fh, fw, sc) * 0.07 + 0.045) * fh * strength
    my = np.clip(yy + dy * mask, 0, fh - 1)
    mx = np.clip(xx + dx * mask, 0, fw - 1)
    face = _bilinear(face, my, mx)
    fa = _bilinear(fa, my, mx)

    # tears：脸内横向错位条 —— 眼与嘴从中缝错开。
    for _ in range(int(rng.integers(3, 6))):
        yb = int(rng.integers(0, max(1, fh - 20)))
        bh = int(rng.integers(int(fh * 0.05), int(fh * 0.15)))
        dxb = int(rng.uniform(0.06, 0.17) * fw * strength
                  * (1 if rng.random() < 0.5 else -1))
        band = np.zeros((fh, 1), dtype=np.float32)
        band[yb:yb + bh] = 1.0
        bm = (np.broadcast_to(band, (fh, fw)) * mask)[..., None]
        rolled = np.roll(face, dxb, axis=1)
        rolled_a = np.roll(fa, dxb, axis=1)
        face = face * (1 - bm) + rolled * bm * 0.94   # 错位条微暗，读作"断开"
        fa = fa * (1 - bm[..., 0]) + rolled_a * bm[..., 0]

    # ghost：错位的第二张脸，低透明度叠在下层。
    gdx = int(rng.integers(int(fw * 0.05), int(fw * 0.14))) * (1 if rng.random() < 0.5 else -1)
    gdy = int(rng.integers(int(fh * 0.03), int(fh * 0.10)))
    gface = np.roll(np.roll(face, gdx, axis=1), gdy, axis=0)
    face = face + gface * 0.22 * mask[..., None]

    # decay：尸斑污渍 + 灰紫尸色 + 眼窝发黑。
    mottle = np.clip(_smooth_noise(rng, fh, fw, max(4, fh // 12)) * 0.8 + 0.15, 0, 1)
    eyeband = np.exp(-(((yy / fh) - 0.42) / 0.13) ** 2)
    dark = 1.0 - (0.40 * mottle + 0.30 * eyeband) * mask * strength
    face *= np.clip(dark, 0.15, 1.0)[..., None]
    lum = (face[..., 0] * 0.30 + face[..., 1] * 0.59 + face[..., 2] * 0.11)
    corpse = np.stack([lum * tint[0], lum * tint[1], lum * tint[2]], axis=-1)
    t = (0.55 * mask * strength)[..., None]
    face = face * (1 - t) + corpse * t

    out_rgb, out_a = rgb, a
    m3 = mask[..., None]
    out_rgb[y0:y1, x0:x1] = rgb[y0:y1, x0:x1] * (1 - m3) + face * m3
    out_a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - mask) + fa * mask
    out_rgb = np.minimum(out_rgb, out_a[..., None])
    return np.clip(out_rgb, 0.0, 1.0), np.clip(out_a, 0.0, 1.0)


def apply_patches(rgb_g, a_g, path, n, rng):
    """局部 glitch（--patches N）：只在 N 个随机小矩形带里保留 glitch 结果，
    其余像素还原成原图。用于"偶发小范围抽搐"的软 glitch 素材（店员立绘）——
    整帧全身撕裂对复制体太夸张。矩形带限制在立绘不透明区域的包围盒内，
    高 30~110px、宽为立绘宽度的三到七成，随机落点。"""
    rgb_o, a_o = _load_premultiplied(path)
    h, w = a_o.shape
    rows = np.where(a_o.max(axis=1) > 0.05)[0]
    cols = np.where(a_o.max(axis=0) > 0.05)[0]
    y0b, y1b = (int(rows[0]), int(rows[-1])) if len(rows) else (0, h)
    x0b, x1b = (int(cols[0]), int(cols[-1])) if len(cols) else (0, w)
    mask = np.zeros((h, w), dtype=bool)
    for _ in range(n):
        bh = int(rng.integers(30, 110))
        y0 = int(rng.integers(y0b, max(y0b + 1, y1b - bh)))
        bw = max(1, int((x1b - x0b) * rng.uniform(0.3, 0.7)))
        x0 = int(rng.integers(x0b, max(x0b + 1, x1b - bw)))
        mask[y0:y0 + bh, x0:x0 + bw] = True
    m3 = mask[..., None]
    return np.where(m3, rgb_g, rgb_o), np.where(mask, a_g, a_o)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--out", required=True,
                    help="输出文件（单张）或输出目录（--variants > 1 时）")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--variants", type=int, default=1)
    ap.add_argument("--patches", type=int, default=0,
                    help="只在 N 个随机小矩形带里保留 glitch、其余还原原图"
                         "（软 glitch，输出命名 _glitchsoft<seed>）")
    ap.add_argument("--face", action="store_true",
                    help="面部恐怖模式：只毁脸不碰身体（输出命名仍是 _glitch<seed>，"
                         "直接覆盖旧的整身 glitch 帧）")
    ap.add_argument("--tint", default="0.72,0.68,0.80",
                    help="--face 的尸色（亮度 RGB 乘数）。默认灰紫（王霜）；"
                         "血红（尤里娅）用 0.65,0.12,0.10")
    ap.add_argument("--face-box", default=None,
                    help="--face 的手动面部框 x0,y0,x1,y1（图像宽高比例值）。"
                         "自动检测在浅肤色立绘上跑偏时用（尤里娅）")
    ap.add_argument("--face-contour", action="store_true",
                    help="--face 的掩膜追踪面庞轮廓（肤色检测+闭运算），"
                         "而不是框内切椭圆（尤里娅用；王霜沿用椭圆）")
    args = ap.parse_args()
    tint = tuple(float(v) for v in args.tint.split(","))
    face_box = (tuple(float(v) for v in args.face_box.split(","))
                if args.face_box else None)

    base = os.path.splitext(os.path.basename(args.input))[0]
    suffix = "glitchsoft" if args.patches else "glitch"

    for i in range(args.variants):
        seed = args.seed + i
        if args.face:
            rgb, a = face_horror(args.input, seed=seed, strength=args.strength,
                                 tint=tint, box=face_box,
                                 contour=args.face_contour)
        else:
            rgb, a = glitch(args.input, seed=seed, strength=args.strength)
        if args.patches:
            rng = np.random.default_rng(seed + 1000)   # 落点独立于 glitch 内部随机流
            rgb, a = apply_patches(rgb, a, args.input, args.patches, rng)
        if args.variants > 1 or os.path.isdir(args.out):
            os.makedirs(args.out, exist_ok=True)
            out = os.path.join(args.out, "%s_%s%d.png" % (base, suffix, seed))
        else:
            out = args.out
        _save_unpremultiplied(rgb, a, out)
        # ascii-safe：Windows 控制台常是 GBK/cp1252，中文文件名直接 print 会崩
        line = "%s  (seed=%d strength=%.2f)" % (out, seed, args.strength)
        print(line.encode("ascii", "backslashreplace").decode("ascii"))


if __name__ == "__main__":
    main()

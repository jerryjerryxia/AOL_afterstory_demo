# -*- coding: utf-8 -*-
"""
Video transcoder: source masters -> Ren'Py-friendly WebM (VP9 + Opus).

Workflow:
    1. Drop high-quality source video (mp4 / mov / avi / mkv / m4v / prores etc.)
       into game/images/bg/_video_masters/
    2. Run: python convert_videos.py
    3. Each <name>.<ext> in masters becomes <name>.webm in game/images/bg/,
       which Ren'Py can play reliably via the Movie() displayable.

Why this exists:
    Ren'Py's bundled FFmpeg ships without H.264 decoding (patent-encumbered),
    so MP4/H.264 files often render as the magenta-checkerboard placeholder.
    WebM with VP9 video + Opus audio uses only royalty-free codecs and is
    guaranteed to play.

CRF 23 is a high-quality default (visually transparent for most content).
Scale fits within 1920x1080 max while preserving aspect ratio; never upscales.
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
MASTERS_DIR = PROJECT_DIR / "game" / "images" / "bg" / "_video_masters"
OUTPUT_DIR = PROJECT_DIR / "game" / "images" / "bg"

TARGET_W = 1920
TARGET_H = 1080
CRF = 23
AUDIO_BITRATE = "96k"

SOURCE_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".prores"}


def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("imageio-ffmpeg not installed. Run: pip install imageio-ffmpeg")


def has_audio_stream(ffmpeg, src):
    """Cheap probe — ffmpeg writes stream info to stderr."""
    r = subprocess.run([ffmpeg, "-i", str(src)], capture_output=True, text=True)
    return "Audio:" in r.stderr


def transcode(ffmpeg, src, dst, target_fps=None):
    print(f"  encoding -> {dst.name}" + (f"  (interpolated to {target_fps} fps)" if target_fps else ""))
    # Scale: fit within 1920x1080, preserve aspect, never upscale.
    # Trailing scale ensures even dimensions (VP9 requirement).
    vf_parts = [
        f"scale='min({TARGET_W},iw)':'min({TARGET_H},ih)'"
        f":force_original_aspect_ratio=decrease",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
    ]
    if target_fps:
        # Motion-compensated interpolation. Good for slow CG content; can ghost
        # on fast cuts. Skip if the source is already at or above target_fps.
        vf_parts.append(
            f"minterpolate=fps={target_fps}"
            f":mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
        )
    cmd = [
        ffmpeg, "-y", "-i", str(src),
        "-vf", ",".join(vf_parts),
        "-c:v", "libvpx-vp9", "-crf", str(CRF), "-b:v", "0",
        "-row-mt", "1", "-threads", "8",
    ]
    if has_audio_stream(ffmpeg, src):
        # WebM only accepts Vorbis/Opus; re-encode whatever the source has.
        cmd += ["-c:a", "libopus", "-b:a", AUDIO_BITRATE]
    else:
        cmd += ["-an"]
    cmd += [str(dst)]

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAILED (ffmpeg exit {r.returncode}):")
        print(r.stderr[-800:])
        return False

    size_in = src.stat().st_size / 1024 / 1024
    size_out = dst.stat().st_size / 1024 / 1024
    pct = (size_out / size_in * 100) if size_in else 0
    print(f"  {size_in:.1f} MB -> {size_out:.2f} MB  ({pct:.1f}%)")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--fps", type=int, default=None,
        help="Target FPS; motion-interpolate if source is lower. "
             "Common: 60 for smooth bg loops. Omit to keep source FPS."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-encode even if output is newer than source.",
    )
    parser.add_argument(
        "files", nargs="*",
        help="Specific master filenames (relative to _video_masters/) to encode. "
             "Omit to encode every file in _video_masters/.",
    )
    args = parser.parse_args()

    if not MASTERS_DIR.exists():
        MASTERS_DIR.mkdir(parents=True)
        print(f"Created {MASTERS_DIR.relative_to(PROJECT_DIR)}.")
        print("Drop source video masters in there and re-run.")
        return

    if args.files:
        sources = [MASTERS_DIR / f for f in args.files]
        missing = [p for p in sources if not p.exists()]
        if missing:
            sys.exit(f"Not found in masters dir: {[p.name for p in missing]}")
    else:
        sources = sorted(
            p for p in MASTERS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in SOURCE_EXTS
        )
    if not sources:
        print(f"No source videos in {MASTERS_DIR.relative_to(PROJECT_DIR)}.")
        print(f"Accepted extensions: {sorted(SOURCE_EXTS)}")
        return

    ffmpeg = get_ffmpeg()
    print(f"ffmpeg: {ffmpeg}")
    print(f"masters: {MASTERS_DIR.relative_to(PROJECT_DIR)}")
    print(f"output:  {OUTPUT_DIR.relative_to(PROJECT_DIR)}")
    if args.fps:
        print(f"target fps: {args.fps} (motion interpolation)")
    print()

    processed = skipped = failed = 0
    for src in sources:
        dst = OUTPUT_DIR / (src.stem + ".webm")
        print(f"[{src.name}]")
        if not args.force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            print(f"  up-to-date, skipping ({dst.name})  [use --force to re-encode]")
            skipped += 1
            continue
        if transcode(ffmpeg, src, dst, target_fps=args.fps):
            processed += 1
        else:
            failed += 1
        print()

    print(f"Done: {processed} encoded, {skipped} skipped, {failed} failed.")


if __name__ == "__main__":
    main()

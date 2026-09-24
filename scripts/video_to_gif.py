"""
Turn the recorded demo video into docs/demo.gif.

    python scripts/video_to_gif.py demo.webm docs/demo.gif [--fps 8] [--width 1000]

Frames are extracted with any ffmpeg (Playwright's bundled one is enough: it
only needs to decode VP8 and write PNG), then assembled with Pillow. Runs of
identical frames collapse into one longer frame, which keeps a demo full of
pauses small without making the motion choppy.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    bundled = sorted(glob.glob(os.path.join(local, "ms-playwright", "ffmpeg-*", "ffmpeg*.exe")))
    bundled += sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/ffmpeg-*/ffmpeg-linux")))
    if not bundled:
        raise SystemExit("No ffmpeg found. Install it, or run `npx playwright install ffmpeg`.")
    return bundled[-1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("gif")
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--width", type=int, default=1000)
    parser.add_argument("--colors", type=int, default=128)
    parser.add_argument("--noise", type=int, default=10, help="max per-pixel change still counted as unchanged")
    parser.add_argument("--refresh", type=float, default=0.08,
                        help="share of changed pixels above which a frame is taken whole")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [find_ffmpeg(), "-loglevel", "error", "-i", args.video, "-r", str(args.fps),
             "-vf", f"scale={args.width}:-2", os.path.join(tmp, "f%05d.png")],
            check=True,
        )
        paths = sorted(Path(tmp).glob("f*.png"))
        frame_ms = round(1000 / args.fps)
        frames, durations = [], []
        for path in paths:
            image = Image.open(path).convert("RGB")
            if frames:
                # Video compression leaves faint noise everywhere. Keep the previous
                # frame's pixels wherever the change is only noise, so a GIF frame
                # encodes just the region that really moved (a cursor, a typed word).
                diff = ImageChops.difference(frames[-1], image).convert("L")
                changed = diff.point(lambda v: 255 if v > args.noise else 0)
                if not changed.getbbox():
                    durations[-1] += frame_ms
                    continue
                # A scroll or page change moves most of the screen: take the frame
                # whole, or faint borders from the old position would linger as ghosts.
                share = sum(changed.histogram()[255:]) / (changed.width * changed.height)
                if share < args.refresh:
                    image = Image.composite(image, frames[-1], changed.filter(ImageFilter.MaxFilter(7)))
            frames.append(image)
            durations.append(frame_ms)

        # One palette for the whole clip: no per-frame colour shimmer, smaller file.
        palette_source = Image.new("RGB", (args.width, frames[0].height * min(len(frames), 12)))
        step = max(1, len(frames) // 12)
        for i, frame in enumerate(frames[::step][:12]):
            palette_source.paste(frame, (0, i * frames[0].height))
        palette = palette_source.quantize(colors=args.colors, method=Image.Quantize.MEDIANCUT)
        quantized = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

        quantized[0].save(
            args.gif, save_all=True, append_images=quantized[1:], duration=durations,
            loop=0, optimize=True, disposal=1,
        )
    size = os.path.getsize(args.gif) / 1e6
    print(f"{args.gif}: {len(frames)} frames ({len(paths)} before dedupe), "
          f"{sum(durations) / 1000:.1f}s, {size:.1f} MB")


if __name__ == "__main__":
    main()

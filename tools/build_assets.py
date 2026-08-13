#!/usr/bin/env python3
"""
build_assets.py
-------------------------------------------------------------------------------
Apps Script cannot serve image files, so the engagement photos in assets/img are
baked into src/Assets.html as base64 data URIs and exposed as CSS variables.

Run this again any time you swap a photo:

    python3 tools/build_assets.py

Optionally re-optimise the source images first (needs Pillow):

    python3 tools/build_assets.py --optimize
"""

import argparse
import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "assets", "img")
OUT_FILE = os.path.join(ROOT, "src", "Assets.html")

# CSS variable name -> file in assets/img, plus the longest edge used when
# --optimize is passed.
ASSETS = [
    ("--img-hero", "couple-portrait.jpg", 1400),
    ("--img-beach", "couple-beach.jpg", 900),
]

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def optimize(path, max_edge, quality=74):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        sys.exit("--optimize needs Pillow:  pip install Pillow")

    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    im.thumbnail((max_edge, max_edge), Image.LANCZOS)
    im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    return im.size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimize", action="store_true",
                        help="resize and re-compress the source photos in place first")
    args = parser.parse_args()

    blocks = []
    total = 0

    for var, filename, max_edge in ASSETS:
        path = os.path.join(IMG_DIR, filename)
        if not os.path.exists(path):
            sys.exit("Missing image: %s" % path)

        if args.optimize:
            size = optimize(path, max_edge)
            print("optimized %-22s -> %dx%d" % (filename, size[0], size[1]))

        mime = MIME.get(os.path.splitext(filename)[1].lower())
        if not mime:
            sys.exit("Unsupported image type: %s" % filename)

        with open(path, "rb") as fh:
            raw = fh.read()

        encoded = base64.b64encode(raw).decode("ascii")
        total += len(encoded)
        blocks.append('    %s: url("data:%s;base64,%s");' % (var, mime, encoded))
        print("embedded  %-22s %6.0f KB source -> %6.0f KB base64"
              % (filename, len(raw) / 1024, len(encoded) / 1024))

    html = (
        "<!--\n"
        "  Assets.html — GENERATED FILE, do not edit by hand.\n"
        "  Rebuild with:  python3 tools/build_assets.py\n"
        "  Source images live in assets/img/\n"
        "-->\n"
        "<style>\n"
        "  :root {\n"
        + "\n".join(blocks) + "\n"
        "  }\n"
        "</style>\n"
    )

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(html)

    print("\nwrote %s (%.0f KB)" % (os.path.relpath(OUT_FILE, ROOT), len(html) / 1024))


if __name__ == "__main__":
    main()

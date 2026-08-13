#!/usr/bin/env python3
"""
build_assets.py
-------------------------------------------------------------------------------
Apps Script cannot serve files — no images, no scripts, no audio — so everything
the page needs is baked into HTML files it *can* serve:

    media/img/*.jpg          ->  apps-script/Assets.html  (base64 CSS variables)
    vendor/gsap.min.js       ->  apps-script/Gsap.html    (inlined <script>)
    media/audio/*.mp3        ->  apps-script/Audio.html   (base64 data URI)

Run this again after swapping a photo, the song, or the GSAP build:

    python3 tools/build_assets.py

Optionally re-optimise the source images first (needs Pillow):

    python3 tools/build_assets.py --optimize

The GitHub Pages build does not use these files at all — it serves the real
assets from the repository root.
"""

import argparse
import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "media", "img")
AUDIO_DIR = os.path.join(ROOT, "media", "audio")
VENDOR_DIR = os.path.join(ROOT, "vendor")
SRC_DIR = os.path.join(ROOT, "apps-script")

# CSS variable name -> file in assets/img, plus the longest edge used when
# --optimize is passed.
ASSETS = [
    ("--img-hero", "couple-portrait.jpg", 1400),
    ("--img-beach", "couple-beach.jpg", 900),
]

MUSIC_FILE = "wedding-placeholder.mp3"
GSAP_FILE = "gsap.min.js"

MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
        ".ogg": "audio/ogg", ".wav": "audio/wav"}

BANNER = ("<!--\n"
          "  {name} — GENERATED FILE, do not edit by hand.\n"
          "  Rebuild with:  python3 tools/build_assets.py\n"
          "  Source: {source}\n"
          "-->\n")


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


def data_uri(path):
    mime = MIME.get(os.path.splitext(path)[1].lower())
    if not mime:
        sys.exit("Unsupported file type: %s" % os.path.basename(path))
    with open(path, "rb") as fh:
        raw = fh.read()
    return "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii")), len(raw)


def write(name, body, source):
    path = os.path.join(SRC_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(BANNER.format(name=name, source=source) + body)
    print("  %-14s %7.0f KB" % (name, os.path.getsize(path) / 1024))


def build_images(do_optimize):
    blocks = []
    for var, filename, max_edge in ASSETS:
        path = os.path.join(IMG_DIR, filename)
        if not os.path.exists(path):
            sys.exit("Missing image: %s" % path)
        if do_optimize:
            size = optimize(path, max_edge)
            print("  optimized %s -> %dx%d" % (filename, size[0], size[1]))
        uri, raw = data_uri(path)
        blocks.append('    %s: url("%s");' % (var, uri))
        print("  %-14s %7.0f KB source" % (filename, raw / 1024))

    write("Assets.html",
          "<style>\n  :root {\n" + "\n".join(blocks) + "\n  }\n</style>\n",
          "media/img/")


def build_gsap():
    path = os.path.join(VENDOR_DIR, GSAP_FILE)
    if not os.path.exists(path):
        sys.exit("Missing %s — see vendor/README.md" % path)
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    # A stray </script> inside the library would end our tag early. It has never
    # happened, but the failure would be baffling, so check rather than hope.
    if "</script" in source.lower():
        sys.exit("gsap.min.js contains a literal </script> and cannot be inlined")

    write("Gsap.html", "<script>\n" + source.strip() + "\n</script>\n",
          "vendor/" + GSAP_FILE)


def build_audio():
    path = os.path.join(AUDIO_DIR, MUSIC_FILE)
    if not os.path.exists(path):
        print("  no %s — skipping Audio.html" % MUSIC_FILE)
        return
    uri, raw = data_uri(path)
    print("  %-14s %7.0f KB source" % (MUSIC_FILE, raw / 1024))
    write("Audio.html",
          "<script>\n  window.RSVP_MUSIC_SRC = %s;\n</script>\n" % js_string(uri),
          "media/audio/" + MUSIC_FILE)


def js_string(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimize", action="store_true",
                        help="resize and re-compress the source photos in place first")
    args = parser.parse_args()

    print("images:")
    build_images(args.optimize)
    print("animation:")
    build_gsap()
    print("music:")
    build_audio()

    total = sum(os.path.getsize(os.path.join(SRC_DIR, f))
                for f in ("Assets.html", "Gsap.html", "Audio.html")
                if os.path.exists(os.path.join(SRC_DIR, f)))
    print("\ngenerated files total %.0f KB — that is the extra weight the Apps\n"
          "Script build carries. The GitHub Pages site serves real files instead."
          % (total / 1024))


if __name__ == "__main__":
    main()

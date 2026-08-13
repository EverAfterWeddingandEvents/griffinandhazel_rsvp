#!/usr/bin/env python3
"""
build_site.py
-------------------------------------------------------------------------------
Assembles the Apps Script source files into a page.

    # local design preview — form is stubbed, nothing is saved anywhere
    python3 tools/build_site.py preview

    # the live site, written into the repository root for GitHub Pages
    python3 tools/build_site.py pages --endpoint https://script.google.com/macros/s/AKfy.../exec

GitHub Pages serves this repository's root, so `pages` writes exactly these
files there and touches nothing else:

    index.html
    404.html
    favicon.svg
    gsap.min.js
    assets/couple-portrait.jpg
    assets/couple-beach.jpg
    assets/<MUSIC_FILE>.mp3

Commit them and push to main; the site updates within a minute or two.
"""

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_assets import ASSETS, GSAP_FILE, MUSIC_FILE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "apps-script")
IMG_DIR = os.path.join(ROOT, "media", "img")
AUDIO_DIR = os.path.join(ROOT, "media", "audio")
VENDOR_DIR = os.path.join(ROOT, "vendor")
BUILD = os.path.join(ROOT, "build")
PUBLISHED_ASSETS = os.path.join(ROOT, "assets")

PUBLIC_KEYS = (
    "groom", "bride", "monogram", "weddingDateIso", "weddingDateLong",
    "weddingYear", "weddingDateShort", "ceremony", "reception",
    "rsvpDeadlineIso", "rsvpDeadlineLabel", "maxPartySize",
    "invitationLine", "requestLine", "closingNote",
    "animations", "petals", "petalCount", "music",
)

PLACEHOLDER = "PASTE_YOUR_APPS_SCRIPT_WEB_APP_URL_HERE"

# Stands in for Apps Script's google.script.run during local preview.
PREVIEW_STUB = """
<script>
  window.google = {
    script: {
      run: (function () {
        var handlers = {};
        var api = {
          withSuccessHandler: function (fn) { handlers.success = fn; return api; },
          withFailureHandler: function (fn) { handlers.failure = fn; return api; },
          submitRsvp: function (payload) {
            console.log('[preview] submitRsvp', payload);
            setTimeout(function () {
              handlers.success({
                ok: true,
                code: 'GAM-4821',
                name: payload.name,
                attending: payload.attending === 'yes',
                partySize: payload.attending === 'yes' ? parseInt(payload.partySize, 10) : 0,
                updated: false
              });
            }, 600);
          }
        };
        return api;
      })()
    }
  };
</script>
"""


def read(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as fh:
        return fh.read()


def parse_config():
    """Pulls the CONFIG object literal out of Config.gs without running it."""
    text = read("Config.gs")
    match = re.search(r"var CONFIG = (\{.*?\n\};)", text, re.S)
    if not match:
        sys.exit("Could not find the CONFIG literal in Config.gs")

    body = match.group(1).rstrip(";")
    body = re.sub(r"//[^\n]*", "", body)                              # comments
    body = re.sub(r"'((?:[^'\\]|\\.)*)'", r'"\1"', body)              # quotes
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body)   # keys
    body = re.sub(r",(\s*[}\]])", r"\1", body)                        # dangling commas

    cfg = json.loads(body)
    missing = [k for k in PUBLIC_KEYS if k not in cfg]
    if missing:
        sys.exit("Config.gs is missing: %s" % ", ".join(missing))
    return {k: cfg[k] for k in PUBLIC_KEYS}


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="7" fill="#FBF7F1"/>
  <g fill="none" stroke="#C98878" stroke-width="2">
    <circle cx="13" cy="18" r="7"/>
    <circle cx="21" cy="18" r="7"/>
  </g>
</svg>
"""


def social_meta(config, domain):
    """
    Title, description and link-preview cards.

    A wedding link gets pasted into Messenger far more than it gets typed, so
    the preview card is most of what people actually see of this page.
    """
    names = "%s & %s" % (first_name(config["groom"]), first_name(config["bride"]))
    title = "%s — %s" % (names, config["weddingDateShort"])
    description = "%s and %s %s at %s, %s. Kindly reply by %s." % (
        config["groom"], config["bride"], config["requestLine"],
        config["ceremony"]["venue"], config["ceremony"]["city"],
        config["rsvpDeadlineLabel"])

    base = "https://%s" % domain if domain else ""
    image = "%s/assets/%s" % (base, ASSETS[0][1]) if base else ""

    tags = [
        '<meta name="description" content="%s">' % esc(description),
        '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
        '<meta property="og:type" content="website">',
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(description),
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if base:
        tags += [
            '<meta property="og:url" content="%s/">' % base,
            '<meta property="og:image" content="%s">' % image,
            '<meta property="og:image:alt" content="%s on the beach">' % esc(names),
        ]

    return title, "\n  ".join(tags)


def first_name(full):
    return str(full).strip().split()[0] if str(full).strip() else ""


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def read_domain():
    cname = os.path.join(ROOT, "CNAME")
    if os.path.exists(cname):
        with open(cname) as fh:
            return fh.read().strip()
    return ""


def linked_assets_css():
    """CSS pointing at real image files instead of base64."""
    lines = ['    %s: url("assets/%s");' % (var, name) for var, name, _ in ASSETS]
    return "<style>\n  :root {\n" + "\n".join(lines) + "\n  }\n</style>"


def current_endpoint():
    """
    Reads the endpoint out of the index.html already sitting in the root.

    Rebuilding after a copy tweak should not quietly disconnect the form, which
    is exactly what happens if --endpoint has to be remembered every time.
    """
    path = os.path.join(ROOT, "index.html")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        match = re.search(r'var RSVP_ENDPOINT = "([^"]*)"', fh.read())
    if match and match.group(1).startswith("http"):
        return match.group(1)
    return None


def stitch(mode, endpoint):
    page = read("Index.html")

    if mode == "pages":
        # Real files load faster and cache; base64 only exists for Apps Script.
        page = page.replace("<?!= include('Assets'); ?>", linked_assets_css())
        page = page.replace("<?!= include('Gsap'); ?>",
                            '<script src="%s"></script>' % GSAP_FILE)
        page = page.replace(
            "<?!= include('Audio'); ?>",
            '<script>window.RSVP_MUSIC_SRC = %s;</script>'
            % json.dumps("assets/" + MUSIC_FILE))
        head = '<script>\n  var RSVP_ENDPOINT = %s;\n' % json.dumps(endpoint)

        title, tags = social_meta(parse_config(), read_domain())
        page = page.replace("<title>Wedding RSVP</title>",
                            "<title>%s</title>" % esc(title))
        page = page.replace("<!--SOCIAL_META-->", tags)
    else:
        page = page.replace("<?!= include('Assets'); ?>", read("Assets.html"))
        page = page.replace("<?!= include('Gsap'); ?>", read("Gsap.html"))
        page = page.replace("<?!= include('Audio'); ?>", read("Audio.html"))
        head = "<script>\n"

    page = page.replace("<!--SOCIAL_META-->", "")
    page = page.replace("<?!= include('Stylesheet'); ?>", read("Stylesheet.html"))
    page = page.replace(
        "<?!= include('JavaScript'); ?>",
        (PREVIEW_STUB if mode == "preview" else "") + read("JavaScript.html"))
    page = page.replace(
        "<script>\n  var CONFIG = <?!= configJson ?>;\n",
        head + "  var CONFIG = %s;\n" % json.dumps(parse_config(), indent=2))

    leftover = re.findall(r"<\?!?=?.*?\?>", page)
    if leftover:
        sys.exit("Unresolved Apps Script scriptlets: %s" % leftover)
    if "var CONFIG =" not in page:
        sys.exit("CONFIG was not injected — did Index.html change?")

    return page


def not_found_page(config):
    """A wrong turn on a wedding domain should not be a GitHub error page."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(monogram)s &mdash; Page not found</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<style>
  html, body { height: 100%%; margin: 0; }
  body {
    display: flex; align-items: center; justify-content: center; text-align: center;
    background: #FBF7F1; color: #4A3F36; padding: 2rem;
    font-family: 'Jost', 'Avenir Next', 'Segoe UI', Helvetica, Arial, sans-serif;
  }
  .m {
    font-family: 'Cormorant Garamond', 'Hoefler Text', Georgia, serif;
    font-size: 2.4rem; letter-spacing: .06em; margin-bottom: .6rem;
  }
  p { color: #7A6C5D; margin: .4rem 0 1.8rem; }
  a {
    display: inline-block; padding: .9rem 1.8rem; background: #4A3F36; color: #FBF7F1;
    text-decoration: none; font-size: .74rem; letter-spacing: .26em; text-transform: uppercase;
  }
  a:hover { background: #C98878; }
</style>
</head>
<body>
  <div>
    <div class="m">%(monogram)s</div>
    <p>We could not find that page.</p>
    <a href="/">Back to the invitation</a>
  </div>
</body>
</html>
""" % {"monogram": config["monogram"]}


def build_preview():
    page = stitch("preview", PLACEHOLDER)
    out = os.path.join(BUILD, "preview.html")
    os.makedirs(BUILD, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote %s (%.0f KB)" % (os.path.relpath(out, ROOT), len(page) / 1024))
    print("open file://%s" % out)


def build_pages(endpoint):
    config = parse_config()
    page = stitch("pages", endpoint)

    os.makedirs(PUBLISHED_ASSETS, exist_ok=True)
    written = []

    def put(rel, body=None, copy_from=None):
        dest = os.path.join(ROOT, rel)
        if copy_from:
            shutil.copy2(copy_from, dest)
        else:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(body)
        written.append((rel, os.path.getsize(dest)))

    put("index.html", page)
    put("404.html", not_found_page(config))
    put("favicon.svg", FAVICON)
    put(GSAP_FILE, copy_from=os.path.join(VENDOR_DIR, GSAP_FILE))

    for _, name, _ in ASSETS:
        put(os.path.join("assets", name), copy_from=os.path.join(IMG_DIR, name))

    music = os.path.join(AUDIO_DIR, MUSIC_FILE)
    if os.path.exists(music):
        put(os.path.join("assets", MUSIC_FILE), copy_from=music)
    else:
        print("  ! %s is missing — the page will render without music." % MUSIC_FILE)

    # .nojekyll stops GitHub running the site through Jekyll, which is for blogs
    # and would only get in the way here.
    nojekyll = os.path.join(ROOT, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()
        written.append((".nojekyll", 0))

    total = 0
    for rel, size in written:
        print("  %-38s %7.0f KB" % (rel, size / 1024))
        total += size
    print("  %-38s %7.0f KB" % ("total", total / 1024))

    cname = os.path.join(ROOT, "CNAME")
    domain = ""
    if os.path.exists(cname):
        with open(cname) as fh:
            domain = fh.read().strip()

    if endpoint == PLACEHOLDER:
        print("\n  ! No RSVP endpoint set, so the form cannot submit yet.")
        print("    Deploy the Apps Script web app, then rebuild with:")
        print("      python3 tools/build_site.py pages --endpoint <your /exec URL>")
    else:
        print("\n  Endpoint: %s" % endpoint)

    print("\n  Commit and push to main:")
    print("    git add -A && git commit -m 'Rebuild site' && git push")
    if domain:
        print("\n  Live at https://%s within a minute or two." % domain)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preview", "pages"])
    parser.add_argument("--endpoint",
                        help="the Apps Script web app /exec URL. Omit to keep "
                             "whatever the current index.html already uses.")
    args = parser.parse_args()

    if args.mode == "preview":
        build_preview()
        return

    endpoint = args.endpoint or current_endpoint() or PLACEHOLDER

    if endpoint != PLACEHOLDER:
        if not endpoint.startswith("https://"):
            sys.exit("--endpoint must be an https:// URL")
        if not endpoint.endswith("/exec"):
            sys.exit("--endpoint should end in /exec — that is the web app URL, "
                     "not the editor or /dev link")
        if not args.endpoint:
            print("  reusing the endpoint already in index.html\n")

    build_pages(endpoint)


if __name__ == "__main__":
    main()

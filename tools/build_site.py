#!/usr/bin/env python3
"""
build_site.py
-------------------------------------------------------------------------------
Turns the Apps Script source files into a page you can open or upload.

    # local design preview — form is stubbed, nothing is saved anywhere
    python3 tools/build_site.py preview

    # the real thing, for your own domain
    python3 tools/build_site.py static --endpoint https://script.google.com/macros/s/AKfy.../exec

`static` writes build/site/ — upload that folder to Cloudflare Pages, Netlify,
GitHub Pages, or any static host. The page posts replies to the Apps Script web
app, which writes them to your Google Sheet.
"""

import argparse
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_assets import ASSETS  # noqa: E402  (css var, filename, max edge)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
IMG_DIR = os.path.join(ROOT, "assets", "img")
BUILD = os.path.join(ROOT, "build")

PUBLIC_KEYS = (
    "groom", "bride", "monogram", "weddingDateIso", "weddingDateLong",
    "weddingYear", "weddingDateShort", "ceremony", "reception",
    "rsvpDeadlineIso", "rsvpDeadlineLabel", "maxPartySize",
    "invitationLine", "requestLine", "closingNote",
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


def linked_assets_css():
    """CSS pointing at real image files instead of base64, for static hosting."""
    lines = ['    %s: url("assets/%s");' % (var, name) for var, name, _ in ASSETS]
    return "<style>\n  :root {\n" + "\n".join(lines) + "\n  }\n</style>"


def stitch(mode, endpoint):
    page = read("Index.html")

    if mode == "static":
        # Real files load faster and cache; base64 only exists for Apps Script.
        page = page.replace("<?!= include('Assets'); ?>", linked_assets_css())
        head = '<script>\n  var RSVP_ENDPOINT = %s;\n' % json.dumps(endpoint)
    else:
        page = page.replace("<?!= include('Assets'); ?>", read("Assets.html"))
        head = "<script>\n"

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preview", "static"])
    parser.add_argument("--endpoint", default=PLACEHOLDER,
                        help="the Apps Script web app /exec URL (static mode)")
    args = parser.parse_args()

    if args.mode == "static" and args.endpoint != PLACEHOLDER:
        if not args.endpoint.startswith("https://"):
            sys.exit("--endpoint must be an https:// URL")
        if not args.endpoint.endswith("/exec"):
            sys.exit("--endpoint should end in /exec — that is the web app URL, "
                     "not the editor or /dev link")

    page = stitch(args.mode, args.endpoint)

    if args.mode == "preview":
        out = os.path.join(BUILD, "preview.html")
        os.makedirs(BUILD, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(page)
        print("wrote %s (%.0f KB)" % (os.path.relpath(out, ROOT), len(page) / 1024))
        print("open file://%s" % out)
        return

    site = os.path.join(BUILD, "site")
    shutil.rmtree(site, ignore_errors=True)
    os.makedirs(os.path.join(site, "assets"))

    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)

    for _, name, _ in ASSETS:
        shutil.copy2(os.path.join(IMG_DIR, name), os.path.join(site, "assets", name))

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(site) for f in fs)
    print("wrote %s  (index.html %.0f KB, %.0f KB total)"
          % (os.path.relpath(site, ROOT), len(page) / 1024, total / 1024))

    if args.endpoint == PLACEHOLDER:
        print("\n  ! No --endpoint given, so the form cannot submit yet.")
        print("    Deploy the Apps Script web app, then rebuild with:")
        print("      python3 tools/build_site.py static --endpoint <your /exec URL>")
    else:
        print("\n  Upload the contents of build/site/ to your host.")


if __name__ == "__main__":
    main()

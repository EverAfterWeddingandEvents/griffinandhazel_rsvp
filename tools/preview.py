#!/usr/bin/env python3
"""
preview.py
-------------------------------------------------------------------------------
Stitches the Apps Script HTML files into one standalone page you can open in a
browser, with google.script.run stubbed out. Nothing but a design preview — no
data is written anywhere.

    python3 tools/preview.py            # writes build/preview.html
    python3 tools/preview.py --open     # ...and prints the file:// URL
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "build", "preview.html")

STUB = """
<script>
  // Stand-in for Apps Script's google.script.run during local preview.
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
    body = re.sub(r"//[^\n]*", "", body)                 # strip comments
    body = re.sub(r"'((?:[^'\\]|\\.)*)'", r'"\1"', body)  # single -> double quotes
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body)  # quote keys
    body = re.sub(r",(\s*[}\]])", r"\1", body)            # trailing commas

    cfg = json.loads(body)
    public = {k: cfg[k] for k in (
        "groom", "bride", "monogram", "weddingDateIso", "weddingDateLong",
        "weddingYear", "weddingDateShort", "ceremony", "reception",
        "rsvpDeadlineLabel", "maxPartySize", "askForPhone",
        "invitationLine", "requestLine", "closingNote")}
    public["isOpen"] = True
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", action="store_true", help="print a file:// URL when done")
    args = parser.parse_args()

    page = read("Index.html")
    page = page.replace("<?!= include('Assets'); ?>", read("Assets.html"))
    page = page.replace("<?!= include('Stylesheet'); ?>", read("Stylesheet.html"))
    page = page.replace("<?!= include('JavaScript'); ?>", STUB + read("JavaScript.html"))
    page = page.replace("<?!= configJson ?>", json.dumps(parse_config()))

    leftover = re.findall(r"<\?!?=?.*?\?>", page)
    if leftover:
        sys.exit("Unresolved Apps Script scriptlets: %s" % leftover)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)

    print("wrote %s (%.0f KB)" % (os.path.relpath(OUT, ROOT), len(page) / 1024))
    if args.open:
        print("file://" + OUT)


if __name__ == "__main__":
    main()

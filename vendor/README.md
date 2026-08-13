# Vendored libraries

## gsap.min.js

GSAP 3.15.0 — the animation engine behind the hero entrance, the scroll
reveals, the drifting petals and the music button.

- License: Standard "no charge" license — <https://gsap.com/standard-license>
- Home: <https://gsap.com>

It lives here rather than being pulled from a CDN, so the page keeps working
when a CDN is slow or blocked, and so the Apps Script build has something to
inline. To update it:

```bash
npm pack gsap && tar xzf gsap-*.tgz && cp package/dist/gsap.min.js vendor/
python3 tools/build_assets.py
```

Nothing here is loaded over the network at runtime — the static build serves
`gsap.min.js` from your own domain, and the Apps Script build inlines it.

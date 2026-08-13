# Griffin & Hazel — Wedding RSVP

A custom RSVP website backed by a Google Sheet. Guests open a link, reply, and
their answer lands in your spreadsheet instantly — no database, no monthly fee.

It ships in two shapes, from the same source files:

| | URL guests see | Cost |
| --- | --- | --- |
| **A. Your own domain** *(recommended)* | `griffinandhazel.com` | a domain, ~₱600–900/yr |
| **B. Apps Script only** | `script.google.com/macros/s/AKfy…/exec` | free |

**B** is the quickest way to test everything. **A** hosts the page on your own
domain and quietly uses the Apps Script only as the endpoint that writes to your
Sheet, so the Google URL never appears anywhere. Set up **B** first either way —
**A** builds directly on top of it.

**Griffin Paul M. Gamallo & Hazel Jade A. Gamallo**
Saturday, May 8, 2027 · Our Lady of the Most Holy Rosary Cathedral Parish, Dipolog City
Reception to follow at Ariana Hotel · Kindly reply by December 2026

---

## What guests see

A single page built around your engagement photos:

1. **Hero** — the beach portrait, a monogram medallion, your names, the date, and
   a countdown that counts itself up ("268 days until we say I do").
2. **The Celebration** — ceremony and reception cards beside the walking photo.
3. **Kindly Reply** — the form itself.
4. A handwritten-feeling thank-you screen with a confirmation code.

Everything animates in as it is scrolled to, petals drift down the background,
and a floating button in the corner plays your song.

The form collects:

| Field | Required | Notes |
| --- | --- | --- |
| Full name | yes | |
| Joyfully Accepts / Regretfully Declines | yes | |
| Number attending | when accepting | 1 – 10, configurable |
| Names in your party | no | one per line, for place cards |
| A message for Griffin & Hazel | no | up to 1000 characters |

It is open to anyone with the link, and no contact details are collected — just
the name, the answer, and the headcount. Nothing is emailed; everything is
recorded in the spreadsheet only. A hidden honeypot field quietly discards
drive-by bot submissions.

### Guests can change their mind

If someone replies twice, the second reply **updates their existing row** rather
than adding a duplicate.

Because a name is the only thing we collect, that is what the matching uses — so
**two guests who share a name would overwrite each other.** With Filipino naming
being what it is, that is worth a thought. If you would rather never lose a
reply, set `allowEdits: false` in `src/Config.gs`; every submission then lands as
its own row and you tidy up duplicates by eye.

---

## Part B — the Apps Script (about 10 minutes)

Do this first. Option A needs it too.

### 1. Create the spreadsheet

Go to <https://sheets.new>, and name it something like
*Griffin & Hazel — RSVP*.

### 2. Open the script editor

**Extensions → Apps Script**. Rename the project *Wedding RSVP*.

### 3. Add the files

In the script editor, recreate each file from the `src/` folder of this repo.
Use the **+** button next to *Files*:

| Add as | From this repo | Type |
| --- | --- | --- |
| `Config` | `src/Config.gs` | Script |
| `Code` | `src/Code.gs` | Script |
| `Setup` | `src/Setup.gs` | Script |
| `Index` | `src/Index.html` | HTML |
| `Stylesheet` | `src/Stylesheet.html` | HTML |
| `JavaScript` | `src/JavaScript.html` | HTML |
| `Assets` | `src/Assets.html` | HTML |
| `Gsap` | `src/Gsap.html` | HTML |
| `Audio` | `src/Audio.html` | HTML |

Delete the default `Code.gs` contents before pasting, and delete any leftover
`myFunction()`. The names must match exactly — the code looks files up by name.

> `Assets.html`, `Gsap.html` and `Audio.html` are big — about 500 KB between
> them — because Apps Script cannot serve files, so the photographs, the
> animation library and the song are all embedded as text. Select all and
> paste; the editor copes, it just takes a second each.
>
> This is the one real drawback of the Apps Script-only route: guests download
> all of that with the page. The custom-domain build serves them as ordinary
> files instead, so the page itself is only 45 KB.

### 4. Run the setup once

Save, then pick **`setupSpreadsheet`** from the function dropdown and press
**Run**. Google will ask you to authorise the script — choose your account,
click *Advanced → Go to Wedding RSVP (unsafe)*, then *Allow*. That warning is
normal for a script you wrote yourself.

This creates two tabs: **RSVPs** (one row per reply) and **Summary** (live
counts).

### 5. Deploy the form

**Deploy → New deployment → ⚙ → Web app**, then:

- Description: `RSVP v1`
- Execute as: **Me**
- Who has access: **Anyone**

Press **Deploy** and copy the **Web app URL**. It looks like:

```
https://script.google.com/macros/s/AKfycbx7Rk9.../exec
```

Keep that URL — Option A needs it. If you stop here, that link *is* your RSVP
form; share it as a QR code so nobody has to type it. You can find it again from
the spreadsheet menu: **💍 Wedding RSVP → Show RSVP form link**.

### 6. After any change

Editing a file does **not** update the live form on its own. Go to
**Deploy → Manage deployments → ✏️ → Version: New version → Deploy**.

Always use *New version* on the existing deployment. Creating a brand new
deployment mints a **different URL**, which breaks every invitation already
printed.

---

## Part A — putting it on your own domain

The Apps Script URL cannot be renamed or pointed at a custom domain; that ID is
assigned by Google. So instead of dressing it up, we move the page to your
domain and leave Apps Script doing the invisible half — receiving replies and
writing them to your Sheet.

### 1. Build the site

```bash
python3 tools/build_site.py static --endpoint "https://script.google.com/macros/s/AKfy.../exec"
```

Use the `/exec` URL from Part B, step 5. This writes `build/site/`:

```
build/site/index.html                     the whole page, ~45 KB
build/site/gsap.min.js                    the animation library
build/site/assets/*.jpg                   the photographs
build/site/assets/wedding-placeholder.mp3 the song
```

### 2. Buy a domain

Anywhere you like — Namecheap, Cloudflare, Porkbun, GoDaddy. Something such as
`griffinandhazel.com`. Expect roughly ₱600–900 a year.

### 3. Upload it

Any static host works, and the free tiers are more than enough for a wedding.
The simplest is drag-and-drop:

- **Cloudflare Pages** — <https://pages.cloudflare.com> → *Upload assets* → drag
  the **contents** of `build/site/` in → *Deploy*. Then **Custom domains → Set
  up a domain**.
- **Netlify** — <https://app.netlify.com/drop> → drag the `build/site` folder in
  → **Domain settings → Add custom domain**.

Both give free HTTPS. Drag the *contents* of `build/site`, not the folder
itself, on Cloudflare — `index.html` must sit at the top level.

### 4. Test it

Open your domain and send yourself a test RSVP. It should appear in the Sheet
within a second or two. Delete the test row afterwards.

If the form says *"We could not reach the server"*, it is almost always one of:

- the deployment's **Who has access** is not set to **Anyone** (this causes a
  CORS failure, because Google returns a sign-in page instead of your data);
- the endpoint URL ends in `/dev` instead of `/exec` — `/dev` only works while
  you are signed in as the owner;
- the script was edited but not redeployed as a **new version**.

### 5. When you change anything

Edit → redeploy the Apps Script (Part B, step 6) if you touched a `.gs` file →
rebuild with the command in step 1 → re-upload `build/site/`.

---

## Changing the details

Everything you are likely to want to edit lives in **`src/Config.gs`** — names,
date, venues, deadline, maximum party size, the wording on the page. Change it,
save, and redeploy a new version.

A few worth knowing:

```js
rsvpDeadlineIso:  '2026-12-31',   // after this day the form politely closes itself
rsvpDeadlineLabel:'December 2026',// what guests actually read
maxPartySize:     10,             // largest number of seats one reply may claim
allowEdits:       true,           // false records every reply as a new row

animations:       true,           // entrance timeline and scroll reveals
petals:           true,           // drifting petals
petalCount:       14,
music: {
  enabled:        true,
  label:          'Play our song',
  volume:         0.32,
  startOnFirstTap: true           // see "The music" below
}
```

All three of `animations`, `petals` and `music` are skipped automatically for
guests whose device asks for reduced motion.

When the deadline passes, the form is replaced with *"Our guest list has
closed"* — the check also runs on the server, so a stale browser tab cannot
sneak a late reply through.

---

## Swapping the photos

The photographs live in `assets/img/` and are baked into `src/Assets.html` as
base64 text, because Apps Script has nowhere to serve image files from.

```bash
# replace assets/img/couple-portrait.jpg  (wide — the hero)
# replace assets/img/couple-beach.jpg     (tall — the framed photo)

pip install Pillow
python3 tools/build_assets.py --optimize
```

Then paste the regenerated `src/Assets.html` back into the script editor and
redeploy. Drop `--optimize` if your images are already web-sized.

On the static build the photos are served as ordinary files instead, which is
why `build/site/index.html` stays small — just rebuild and re-upload.

---

## The music

The track that ships with this is a **placeholder**: a soft music-box arpeggio
over the Canon in D, synthesised from scratch by `tools/make_music.py`. It is
there so the player has something to play, and so there is nothing to license.
It is meant to be replaced.

### Using your own song

```bash
# drop your file in, keeping the name
cp ~/our-song.mp3 assets/audio/wedding-placeholder.mp3
python3 tools/build_assets.py
```

Then paste the new `src/Audio.html` into the script editor (Apps Script route),
or rebuild and re-upload `build/site/` (custom-domain route).

Two things worth keeping in mind. Trim the file to a minute or two — it is a
background loop, not an album, and every guest downloads it. And it does need
to be a song you have the right to publish; a wedding site is a public web page,
so the usual rules about someone else's recording apply.

### Why it does not just start playing

Every modern browser refuses to play audio until the guest has interacted with
the page. Nothing can be done about that — it is not a bug in this code, and
`autoplay` attributes will not get around it.

So the button waits, gives a small nudge after a couple of seconds, and:

- `startOnFirstTap: true` (the default) starts the song on the guest's first
  tap, click or key press anywhere on the page;
- `startOnFirstTap: false` waits until they press the music button itself.

Either way the button always shows what is happening and lets them stop it, and
its label and `aria-pressed` state stay in step for screen readers.

### Turning the motion down

`animations`, `petals` and `music` in `src/Config.gs` are independent switches.
All of them are ignored anyway for guests whose device asks for reduced motion,
and the page renders perfectly well as a plain static document if GSAP fails to
load for any reason — nothing is hidden that the animation engine is needed to
bring back.

---

## Previewing the design locally

You can see the page in a normal browser without deploying anything:

```bash
python3 tools/build_site.py preview
open build/preview.html      # or just double-click it
```

This stitches the files together and stubs out the submission, so the form
always shows the thank-you screen without saving anywhere. Useful for tweaking
colours and copy quickly.

## Checking the logic

```bash
node tools/test_logic.js     # 38 assertions, no Google account needed
```

Covers field validation, the duplicate-reply matching, confirmation codes, the
deadline cut-off, the honeypot, and the `doPost` endpoint — with the Apps Script
services stubbed out.

---

## Deploying with clasp (optional)

If you prefer the command line to copy-and-paste:

```bash
npm install -g @google/clasp
clasp login
cp .clasp.json.example .clasp.json
# put your script ID in .clasp.json — find it under Project Settings
clasp push
clasp deploy --description "RSVP v1"
```

`.clasp.json` is gitignored so your script ID and credentials stay out of the
repository.

---

## The spreadsheet

**RSVPs** tab — one row per guest:

`Timestamp · Last Updated · Full Name · Attending · Party Size · Guest Names ·
Message to the Couple · Confirmation Code`

*Attending* is colour-coded green for Yes and blush for No. *Last Updated* is
filled in only when someone changed an earlier reply.

**Summary** tab — responses received, accepting, declining, total seats
confirmed, messages left, and days until the wedding. Refresh it from the
**💍 Wedding RSVP** menu if the counts ever look stale.

To get a clean guest list for your coordinator, use
**File → Download → Microsoft Excel** or **PDF**.

---

## Notes

- Writes are wrapped in a script lock, so two guests replying at the same second
  cannot overwrite each other.
- Every field is validated again on the server, not just in the browser — the
  deadline included, so a stale browser tab cannot sneak a late reply through.
- The endpoint is public, exactly like any online form. The honeypot stops
  drive-by bots; it will not stop someone determined. Glance at the Sheet now
  and then and delete anything odd — replies are plain rows, so tidying up is
  just deleting a row.
- The page is responsive, works without JavaScript-heavy frameworks, and
  respects `prefers-reduced-motion`.
- Apps Script web apps run inside an iframe on Google's servers; the fonts come
  from Google Fonts, with system serif and sans-serif fallbacks if they are
  blocked.

## Files

```
src/
  Config.gs         all wedding details in one place — start here
  Code.gs           doGet + doPost, validation, writes to the sheet
  Setup.gs          spreadsheet setup, formatting, summary tab, custom menu
  Index.html        page markup
  Stylesheet.html   the design
  JavaScript.html   form behaviour, animation and the music player
  Assets.html       GENERATED — photos, for Apps Script only
  Gsap.html         GENERATED — the animation library, for Apps Script only
  Audio.html        GENERATED — the song, for Apps Script only
  appsscript.json   project manifest
assets/img/         the source photographs
assets/audio/       the song (placeholder — swap it for your own)
vendor/             gsap.min.js, committed rather than loaded from a CDN
tools/
  build_assets.py   regenerates the three GENERATED files above
  build_site.py     preview | static — builds build/preview.html or build/site/
  make_music.py     synthesises the placeholder track
  test_logic.js     tests the server-side logic without a Google account
```

The page detects where it is running: served by Apps Script it uses
`google.script.run`, and on your own domain it POSTs to `RSVP_ENDPOINT` instead.
One set of source files, both deployments.

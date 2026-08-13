# Griffin & Hazel — Wedding RSVP

A custom RSVP website that runs entirely on a Google Sheet, using Google Apps
Script. No hosting, no domain, no monthly fee — guests open a link, reply, and
their answer lands in your spreadsheet instantly.

**Griffin Paul M. Gamallo & Hazel Jade A. Gamallo**
Saturday, May 8, 2027 · Our Lady of the Most Holy Rosary Cathedral Parish, Dipolog City
Reception to follow at Ariana Hotel · Kindly reply by December 2026

---

## What guests see

A single page built around your engagement photos:

1. **Hero** — the beach portrait, a monogram medallion, your names, the date, and
   a live countdown ("268 days until we say I do").
2. **The Celebration** — ceremony and reception cards beside the walking photo.
3. **Kindly Reply** — the form itself.
4. A handwritten-feeling thank-you screen with a confirmation code.

The form collects:

| Field | Required | Notes |
| --- | --- | --- |
| Full name | yes | |
| Email | no | used to match repeat replies |
| Mobile number | no | hide it with `askForPhone: false` |
| Joyfully Accepts / Regretfully Declines | yes | |
| Number attending | when accepting | 1 – 10, configurable |
| Names in your party | no | one per line, for place cards |
| A message for Griffin & Hazel | no | up to 1000 characters |

It is open to anyone with the link, and **no emails are sent** — everything is
recorded in the spreadsheet only.

### Guests can change their mind

If someone replies twice, the second reply **updates their existing row** rather
than adding a duplicate. Matching is by email when one was given, otherwise by
name. Set `allowEdits: false` in `src/Config.gs` if you would rather keep every
submission as a separate row.

---

## Setting it up (about 10 minutes)

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

Delete the default `Code.gs` contents before pasting, and delete any leftover
`myFunction()`. The names must match exactly — the code looks files up by name.

> `Assets.html` is large (~185 KB) because both photographs are embedded inside
> it as text. Select all of it and paste; the editor handles it fine, it just
> takes a second.

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

Press **Deploy** and copy the **Web app URL**. That link is what you send to
your guests — put it in your invitations, on a QR code, wherever you like.

You can find it again any time from the spreadsheet menu:
**💍 Wedding RSVP → Show RSVP form link**.

### 6. After any change

Editing a file does **not** update the live form on its own. Go to
**Deploy → Manage deployments → ✏️ → Version: New version → Deploy**.

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
askForPhone:      true,           // false hides the mobile number field
allowEdits:       true,           // false records every reply as a new row
```

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

---

## Previewing the design locally

You can see the page in a normal browser without deploying anything:

```bash
python3 tools/preview.py
open build/preview.html      # or just double-click it
```

This stitches the files together and stubs out `google.script.run`, so the form
submits to nothing and always shows the thank-you screen. Useful for tweaking
colours and copy quickly. Nothing is written to any spreadsheet.

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

`Timestamp · Last Updated · Full Name · Email · Phone · Attending · Party Size ·
Guest Names · Message to the Couple · Confirmation Code`

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
- Every field is validated again on the server, not just in the browser.
- The page is responsive, works without JavaScript-heavy frameworks, and
  respects `prefers-reduced-motion`.
- Apps Script web apps run inside an iframe on Google's servers; the fonts come
  from Google Fonts, with system serif and sans-serif fallbacks if they are
  blocked.

## Files

```
src/
  Config.gs         all wedding details in one place — start here
  Code.gs           web app entry point, validation, writes to the sheet
  Setup.gs          spreadsheet setup, formatting, summary tab, custom menu
  Index.html        page markup
  Stylesheet.html   the design
  JavaScript.html   form behaviour
  Assets.html       GENERATED — photos as base64
  appsscript.json   project manifest
assets/img/         the source photographs
tools/
  build_assets.py   regenerates src/Assets.html from assets/img
  preview.py        builds build/preview.html for local viewing
```

#!/usr/bin/env python3
"""
make_music.py
-------------------------------------------------------------------------------
Writes the placeholder background track: a soft music-box arpeggio over the
Canon-in-D progression, synthesised from scratch so there is nothing to license.

It is built to loop seamlessly — note tails that run past the end wrap around
to the beginning, so there is no click or gap when the audio repeats.

    pip install lameenc
    python3 tools/make_music.py

Swap it for the couple's real song by dropping any MP3 in as
assets/audio/wedding-placeholder.mp3 and re-running build_assets.py.
"""

import math
import os
import struct
import sys
import wave

# The brightest partial in this patch lands near 3 kHz, so 22.05 kHz is
# plenty of headroom and lets the encoder spend its bits where they count.
SR = 22050
BPM = 80.0
BEAT = 60.0 / BPM            # 0.75 s
BAR = BEAT * 4               # 3.0 s
BARS = 8                     # 24 s loop

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "audio")
OUT_MP3 = os.path.join(OUT_DIR, "wedding-placeholder.mp3")

# Canon in D — public domain, and about as wedding as a chord progression gets.
# Each bar is four chord tones, low to high, as MIDI note numbers.
PROGRESSION = [
    [50, 54, 57, 62],   # D
    [45, 49, 52, 57],   # A
    [47, 50, 54, 59],   # Bm
    [42, 45, 49, 54],   # F#m
    [43, 47, 50, 55],   # G
    [50, 54, 57, 62],   # D
    [43, 47, 50, 55],   # G
    [45, 49, 52, 57],   # A
]

# Which chord tone each eighth note plays. Up, over, and back down again.
PATTERN = [0, 1, 2, 3, 2, 3, 1, 2]

# A music box is mostly sine, with a couple of slightly inharmonic overtones.
PARTIALS = [(1.0, 1.00, 1.60), (2.0, 0.42, 1.05), (3.01, 0.20, 0.70),
            (4.18, 0.09, 0.45), (5.43, 0.04, 0.30)]


def freq(midi):
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def add_note(buf, start, midi, gain, tau_scale=1.0):
    """Mixes one plucked note in, wrapping its tail around the loop point."""
    n = len(buf)
    f0 = freq(midi)
    length = int(SR * 3.2 * tau_scale)
    attack = int(SR * 0.004)

    for ratio, amp, tau in PARTIALS:
        f = f0 * ratio
        if f > SR / 2.2:
            continue
        w = 2.0 * math.pi * f / SR
        decay = math.exp(-1.0 / (SR * tau * tau_scale))
        env = gain * amp
        phase = 0.0
        for i in range(length):
            e = env
            if i < attack:
                e *= i / attack
            buf[(start + i) % n] += e * math.sin(phase)
            phase += w
            env *= decay
            if env < 1e-5:
                break


def add_pad(buf, start, midi, gain):
    """A quiet sustained tone under the arpeggio, faded in and out so bars blend."""
    n = len(buf)
    f0 = freq(midi)
    length = int(SR * BAR * 1.15)
    w = 2.0 * math.pi * f0 / SR
    w2 = 2.0 * math.pi * (f0 * 2.003) / SR   # a touch of detune for warmth

    for i in range(length):
        x = i / length
        env = gain * math.sin(math.pi * x) ** 1.5
        buf[(start + i) % n] += env * (math.sin(w * i) + 0.30 * math.sin(w2 * i))


def build():
    total = int(SR * BAR * BARS)
    buf = [0.0] * total

    for bar, chord in enumerate(PROGRESSION):
        bar_start = int(SR * BAR * bar)

        add_pad(buf, bar_start, chord[0] - 12, 0.055)

        for step, tone in enumerate(PATTERN):
            at = bar_start + int(SR * BEAT * 0.5 * step)
            accent = 1.0 if step % 4 == 0 else 0.72
            add_note(buf, at, chord[tone], 0.20 * accent)

            # A sparkle an octave up on the downbeat of every other bar.
            if step == 0 and bar % 2 == 1:
                add_note(buf, at, chord[3] + 12, 0.055, tau_scale=0.55)

    peak = max(abs(v) for v in buf) or 1.0
    scale = 0.72 / peak
    return [int(max(-32767, min(32767, v * scale * 32767))) for v in buf]


def main():
    print("synthesising %.0f s of placeholder music..." % (BAR * BARS))
    samples = build()

    os.makedirs(OUT_DIR, exist_ok=True)
    wav_path = os.path.join(OUT_DIR, "_placeholder.wav")
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack("<%dh" % len(samples), *samples))

    try:
        import lameenc
    except ImportError:
        sys.exit("Needs the LAME encoder:  pip install lameenc\n"
                 "(the uncompressed %s was still written)" % wav_path)

    enc = lameenc.Encoder()
    enc.set_bit_rate(64)
    enc.set_in_sample_rate(SR)
    enc.set_channels(1)
    enc.set_quality(2)
    mp3 = enc.encode(struct.pack("<%dh" % len(samples), *samples)) + enc.flush()

    with open(OUT_MP3, "wb") as fh:
        fh.write(bytes(mp3))
    os.remove(wav_path)

    print("wrote %s (%.0f KB, %.1f s loop)"
          % (os.path.relpath(OUT_MP3, ROOT), len(mp3) / 1024, BAR * BARS))


if __name__ == "__main__":
    main()

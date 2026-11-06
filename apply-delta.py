#!/usr/bin/env python3
"""Write a tinted-delta gitconfig with blended diff backgrounds.

Usage: apply-delta.py SCHEME_GITCONFIG [DEST ...]

SCHEME_GITCONFIG is a built file from delta/. Its "tinted-delta-vars" comment
gives the scheme foreground, background, red and green. The plus/minus styles
are rewritten to use the syntax foreground on a background mixed from the
scheme background and red/green. The mix is reduced if needed to keep the
foreground readable, on both dark and light schemes. The result is written to each DEST (default
~/.config/delta/tinty.gitconfig), creating parent directories as needed.
"""

import os
import re
import sys
import tempfile

DEFAULT_DEST = "~/.config/delta/tinty.gitconfig"

# Fraction of red/green mixed into the background. Lowered (down to MIN_MIX)
# when the scheme foreground would fall below MIN_CONTRAST, or below
# KEEP_CONTRAST of its contrast on the plain background if that is lower.
LINE = 0.20
EMPH = 0.40
MIN_MIX = 0.08
STEP = 0.02
MIN_CONTRAST = 4.5
KEEP_CONTRAST = 0.8

VARS_RE = re.compile(r"^;\s*tinted-delta-vars:(.*)$", re.MULTILINE)
HEX_RE = re.compile(r"#?([0-9a-fA-F]{6})")


def parse_vars(text):
    m = VARS_RE.search(text)
    if not m:
        raise ValueError("no 'tinted-delta-vars' line")
    out = {}
    for item in m.group(1).split():
        key, _, value = item.partition("=")
        hm = HEX_RE.fullmatch(value)
        if not hm:
            raise ValueError(f"bad color {item!r}")
        out[key] = hm.group(1).lower()
    missing = {"bg", "red", "green"} - out.keys()
    if missing:
        raise ValueError(f"missing {', '.join(sorted(missing))}")
    return out


def mix(bg, fg, t):
    """Hex color t of the way from bg to fg."""
    a = [int(bg[i : i + 2], 16) for i in (0, 2, 4)]
    b = [int(fg[i : i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def luminance(color):
    """WCAG 2 relative luminance of a hex color."""
    out = []
    for i in (0, 2, 4):
        c = int(color[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def tint(bg, accent, t, fg=None):
    """Mix accent into bg, backing off t while fg would become hard to read."""
    if fg is None:
        return mix(bg, accent, t)
    need = min(MIN_CONTRAST, KEEP_CONTRAST * contrast(fg, bg))
    while t > MIN_MIX and contrast(fg, mix(bg, accent, t)) < need:
        t = max(MIN_MIX, t - STEP)
    return mix(bg, accent, t)


def styles(v):
    bg, fg = v["bg"], v.get("fg")
    out = {}
    for side, accent in (("minus", v["red"]), ("plus", v["green"])):
        line = tint(bg, accent, LINE, fg)
        emph = tint(bg, accent, EMPH, fg)
        out[f"{side}-style"] = f'syntax "#{line}"'
        out[f"{side}-non-emph-style"] = f'syntax "#{line}"'
        out[f"{side}-emph-style"] = f'syntax "#{emph}"'
        out[f"{side}-empty-line-marker-style"] = f'normal "#{line}"'
    return out


def render(text):
    new = styles(parse_vars(text))
    seen = set()

    def repl(m):
        key = m.group(2)
        seen.add(key)
        return f"{m.group(1)}{key} = {new[key]}"

    keys = "|".join(re.escape(k) for k in new)
    pattern = re.compile(rf"^([ \t]*)({keys})[ \t]*=.*$", re.MULTILINE)
    text = pattern.sub(repl, text)
    # Append any style the template did not set, at the end of [delta].
    extra = "".join(f"\t{k} = {v}\n" for k, v in new.items() if k not in seen)
    if not text.endswith("\n"):
        text += "\n"
    return text + extra


def write(path, text):
    path = os.path.expanduser(path)
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return
    except FileNotFoundError:
        pass
    fd, tmp = tempfile.mkstemp(prefix=".tinty.", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    src = argv[1]
    dests = argv[2:] or [DEFAULT_DEST]
    with open(src, encoding="utf-8") as f:
        text = f.read()
    try:
        out = render(text)
    except ValueError as e:
        sys.exit(f"apply-delta: {src}: {e}")
    for dest in dests:
        write(dest, out)


if __name__ == "__main__":
    main(sys.argv)

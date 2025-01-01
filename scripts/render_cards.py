#!/usr/bin/env python3
"""Render the animated hero and the three section tiles at the top of the profile README.

Run from the repo root:  python3 scripts/render_cards.py
Set STATIC=1 to render the final frame only (no animation), for screenshots.

Writes cards/<theme>/hero.svg and cards/<theme>/tile-*.svg; the README picks a theme with <picture>.
The README shows the hero at width="772" (the size it had in the "update" commit), scaling it up evenly.
Tile counts are read from the "Made with" icons in README.md, so they stay in sync with the projects.
Fonts are embedded as base64 WOFF because GitHub shows README SVGs through <img>,
which cannot load external files. CSS keyframes and SMIL both play there.
"""
import base64
import os
import re
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "scripts", "fonts")
OUT = os.path.join(ROOT, "cards")
STATIC = os.environ.get("STATIC") == "1"

# Matches GitHub's own README look: its text colours per theme, and a semibold sans (Geist, embedded,
# close to GitHub's system font). Buttons copy shields.io "for-the-badge" (28px, square, bold caps)
# so they sit well next to the LinkedIn / Gmail badges, in GitHub's neutral charcoal with a brand-coloured logo.
THEMES = {
    # "Mono" heading/subtitle: GitHub's own text colours per theme (near-white on dark, near-black on light).
    "dark": {"HEAD": "#f0f6fc", "SUB": "#9198a1"},    # 17.4:1 / 6.5:1 on #0d1117
    "light": {"HEAD": "#1f2328", "SUB": "#59636e"},   # 15.8:1 / 6.1:1 on #ffffff
}

HEADING = "Hi there,"
TAGLINE = "Would you like to see what I've been building so far?"

# (anchor in README, title, logo in scripts/icons/glyph-*.path, logo colour, button background, button text)
# "Magenta pop" buttons, the same in both themes. Text contrast: 11.4:1, 14.7:1, 5.6:1.
SECTIONS = [
    ("full-stack", "Full-stack & Interfaces", "react", "#61DAFB", "#312e81", "#ffffff"),
    ("backend", "Backend / Systems", "bash", "#4EAA25", "#24292f", "#ffffff"),
    ("game-dev", "Game Development", "unity", "#FFFFFF", "#c0266d", "#ffffff"),
]

FONT_FILES = {"G4": "geist-400.woff", "G6": "geist-600.woff"}

CSS = """
.rise{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
""" + ("*{animation:none!important}\n" if STATIC else "")


def font_css(families):
    out = []
    for fam in families:
        file = FONT_FILES[fam]
        data = base64.b64encode(open(os.path.join(FONTS, file), "rb").read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';src:url(data:font/woff;base64,{data}) format('woff')}}")
    return "\n".join(out)


def text_width(text, fam, size):
    f = TTFont(os.path.join(FONTS, FONT_FILES[fam]))
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else upm / 2 for c in text) * size / upm


def shine(width, base, accent):
    """A highlight band that sweeps across the name every few seconds (SMIL, so it works in <img>)."""
    anim = "" if STATIC else (
        f'<animateTransform attributeName="gradientTransform" type="translate" values="{-width} 0;{width} 0;{width} 0" '
        f'keyTimes="0;0.3;1" dur="6s" begin="1.4s" repeatCount="indefinite"/>')
    return (f'<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{width}" y2="0" '
            f'gradientTransform="translate({-width} 0)"><stop offset="0" stop-color="{base}"/>'
            f'<stop offset=".38" stop-color="{base}"/><stop offset=".5" stop-color="{accent}"/>'
            f'<stop offset=".62" stop-color="{base}"/><stop offset="1" stop-color="{base}"/>{anim}</linearGradient>')


def wrap(text, fam, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, fam, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur] if cur else lines


AVATAR = os.path.join(ROOT, "src", "coding_je_cat.gif")


def render_hero(t):
    # One image: animated avatar on the left; greeting + subtitle sit at its bottom-right corner,
    # the subtitle almost on the bottom edge and the two lines close together.
    from PIL import Image
    MAX_W, H, GAP, SUB, SUB_LH = 880, 160, 8, 16, 22
    aw, ah = Image.open(AVATAR).size
    AVW = round(H * aw / ah)                        # keep the GIF's proportions at full hero height
    tx = AVW + GAP
    head = HEADING
    size = 64
    while tx + text_width(head, "G6", size) > MAX_W:    # as big as fits beside the picture
        size -= 2
    sub_lines = wrap(TAGLINE, "G4", SUB, MAX_W - tx)
    # the image is only as wide as its content, so it doesn't stretch across the README
    W = int(tx + max(text_width(head, "G6", size) - len(head), *(text_width(l, "G4", SUB) for l in sub_lines)) + 4)
    last_y = H - 5                                  # baseline of the last subtitle line (descenders just clear the edge)
    first_sub_y = last_y - (len(sub_lines) - 1) * SUB_LH
    head_y = first_sub_y - 12 - round(size * .22)   # tight gap: clears the heading's descenders
    label = f"{head} {TAGLINE}"
    avatar = base64.b64encode(open(AVATAR, "rb").read()).decode()
    sub = "".join(f'<text class="rise" style="animation-delay:{.4 + i * .08:.2f}s" x="{tx}" y="{first_sub_y + i * SUB_LH}" '
                  f'font-family="G4" font-size="{SUB}" fill="{t["SUB"]}">{escape(line)}</text>'
                  for i, line in enumerate(sub_lines))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label, {chr(34): '&quot;'})}">
<title>{escape(label)}</title>
<style>
{font_css(["G4", "G6"])}
{CSS}</style>
<image class="rise" x="0" y="0" width="{AVW}" height="{H}" href="data:image/gif;base64,{avatar}"/>
<text class="rise" style="animation-delay:.1s" x="{tx - 3}" y="{head_y}" font-family="G6" font-size="{size}" letter-spacing="-1" fill="{t["HEAD"]}">{escape(head)}</text>
{sub}
</svg>
"""

def section_counts(key):
    """(unique tools, projects) for one README section, from its "Made with" icons."""
    readme = open(os.path.join(ROOT, "README.md")).read()
    start = readme.index(f'<a id="{key}"></a>')
    table = readme[start:readme.index("</table>", start)]
    tools = set(re.findall(r'alt="([^"]+)" title="', table))
    return len(tools), table.count('<td width="300"')


def glyph(name, x, y, size, color):
    """Single-colour logo (Simple Icons path, 24x24) for use on a solid button."""
    paths = open(os.path.join(ROOT, "scripts", "icons", f"glyph-{name}.path")).read().strip()
    return f'<g transform="translate({x} {y}) scale({size / 24})" fill="{color}">{paths}</g>'


def render_tile(t, sec, index):
    """Matches the shields.io for-the-badge contact badges: 28px tall, square, bold spaced caps."""
    key, title, icon_name, logo_colour, button_bg, button_fg = sec
    n_tools, n_projects = section_counts(key)
    H, PAD, ICON, SIZE, TRACK = 24, 10, 12, 10, 1.1
    text = title.upper()
    title_x = PAD + ICON + 7
    W = int(title_x + text_width(text, "G6", SIZE) + TRACK * (len(text) - 1) + PAD)
    label = f"{title}: {n_tools} tools across {n_projects} projects"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">
<title>{escape(label)}</title>
<style>
{font_css(["G6"])}
{CSS}</style>
<g class="rise" style="animation-delay:{.8 + index * .12:.2f}s">
  <rect width="{W}" height="{H}" fill="{button_bg}" shape-rendering="crispEdges"/>
  {glyph(icon_name, PAD, (H - ICON) / 2, ICON, logo_colour)}
  <text x="{title_x}" y="{H / 2 + 3.5}" font-family="G6" font-size="{SIZE}" letter-spacing="{TRACK}" fill="{button_fg}">{escape(text)}</text>
</g>
</svg>
"""


def main():
    for name, tokens in THEMES.items():
        os.makedirs(os.path.join(OUT, name), exist_ok=True)
        path = os.path.join(OUT, name, "hero.svg")
        with open(path, "w") as f:
            f.write(render_hero(tokens))
        print(os.path.relpath(path, ROOT))
        for i, sec in enumerate(SECTIONS):
            path = os.path.join(OUT, name, f"tile-{sec[0]}.svg")
            with open(path, "w") as f:
                f.write(render_tile(tokens, sec, i))
            print(os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the profile card: rotating ASCII face on the left, info on the right.

    python3 tools/build_card.py

Reads profile.toml (the text) and assets/face_frames.json (the face, made by
tools/ascii_face.py). Writes assets/card-dark.svg and assets/card-light.svg.
Needs Python 3.11 or newer and nothing else.
"""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent

# ---- layout, in SVG units (the card is shown 940 wide) ----
CARD_W = 940
PAD_X = 28
PAD_Y = 26
FACE_MAX_FONT = 15.5      # largest font size for the face; shrinks to fit wide grids
INFO_X = 470              # where the right half starts
INFO_FONT = 13.0
INFO_CW = INFO_FONT * 0.6
INFO_LINE = 20.0          # distance between info lines
INFO_GAP = 10.0           # extra space above a section rule
INFO_CHARS = 56           # characters per info line
FPS = 12                  # face frames per second
HOLD = 3                  # extra frames to pause at each end of the turn

FONT = ("ui-monospace, 'SF Mono', SFMono-Regular, 'Cascadia Mono', 'JetBrains Mono', "
        "Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace")

COLORS = {
    "dark": {
        "background": "#0d0f14", "border": "#262b36", "face": "#e8eaf0",
        "accent": "#ff4d5e", "section": "#ffd200", "value": "#e6e6e6",
        "dim": "#3d4452", "green": "#5dd68a", "red": "#ff5c7a",
    },
    "light": {
        "background": "#ffffff", "border": "#d0d7de", "face": "#1f2328",
        "accent": "#c8102e", "section": "#8a6400", "value": "#1f2328",
        "dim": "#c4cad1", "green": "#1a7f37", "red": "#cf222e",
    },
}
VALUE_CLASS = {"green": "ok", "red": "bad", "gold": "sec"}


def n(value: float) -> str:
    """Short number for SVG attributes."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def info_lines(profile: dict) -> list[tuple[str, list[tuple[str, str]]]]:
    """Each line is (kind, [(css class, text), ...]). kind 'gap' adds spacing."""
    width = INFO_CHARS
    title = profile["title"]
    lines = [("line", [("acc b", title), ("dim", " " + "─" * (width - len(title) - 1))])]
    problems = []
    for section in profile.get("sections", []):
        name = section.get("name")
        if name:
            lines.append(("gap", []))
            lines.append(("line", [("dim", "─ "), ("sec", name),
                                   ("dim", " " + "─" * (width - len(name) - 3))]))
        for field in section.get("fields", []):
            label, value = field[0], field[1]
            tone = VALUE_CLASS.get(field[2], "val") if len(field) > 2 else "val"
            dots = width - len(label) - len(value) - 3   # "Label: " + dots + " " + value
            if dots < 2:
                problems.append(f'  "{label}": trim {2 - dots} character(s) from "{value}"')
                continue
            lines.append(("line", [("acc", label + ":"), ("dim", " " + "." * dots + " "), (tone, value)]))
    if problems:
        sys.exit("These lines are too long for the card:\n" + "\n".join(problems))
    lines.append(("gap", []))
    lines.append(("prompt", [("acc b", title), ("val", " " + profile.get("prompt", "~ $") + " ")]))
    return lines


def turn_keyframes(count: int, front: int, pitch: float) -> tuple[str, float]:
    """Front, to one side, back through front to the other side, and back."""
    order = (list(range(front, count)) + [count - 1] * HOLD
             + list(range(count - 2, -1, -1)) + [0] * HOLD
             + list(range(1, front)))
    total = len(order)
    steps = []
    for i, frame in enumerate(order):
        steps.append(f"{i * 100 / total:.3f}%{{transform:translateY({n(-frame * pitch)}px)}}")
    steps.append(f"100%{{transform:translateY({n(-front * pitch)}px)}}")
    return "".join(steps), total / FPS


def build(theme: str, profile: dict, face: dict) -> str:
    c = dict(COLORS[theme])
    c.update(profile.get("colors", {}).get(theme, {}))

    rows, cols = face["rows"], face["cols"]
    frames = face[theme]
    # Fit the face into the left half: as large as allowed, never wider than the space.
    room = INFO_X - PAD_X - 14 - PAD_X / 2
    face_cw = min(FACE_MAX_FONT * 0.6, room / cols)
    face_font = face_cw / 0.6
    face_line = face_cw * face["cell_ratio"]
    face_h = rows * face_line
    face_w = cols * face_cw
    info_need = sum(INFO_GAP if kind == "gap" else INFO_LINE for kind, _ in info_lines(profile))
    card_h = round(max(face_h, info_need) + 2 * PAD_Y)
    face_x = PAD_X / 2 + (INFO_X - 14 - PAD_X / 2 - face_w) / 2
    face_y = (card_h - face_h) / 2
    pitch = face_h + 8  # distance between frames on the film strip

    lines = info_lines(profile)
    info_h = sum(INFO_GAP if kind == "gap" else INFO_LINE for kind, _ in lines)
    info_y = (card_h - info_h) / 2 + INFO_LINE * 0.72

    keyframes, seconds = turn_keyframes(len(frames), face["front"], pitch)
    front_shift = n(-face["front"] * pitch)

    label = (f"{profile['title']}: profile card with a rotating ASCII-art portrait. "
             + " ".join(f"{f[0]}: {f[1]}." for s in profile.get("sections", []) for f in s.get("fields", [])))

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {card_h}" width="{CARD_W}" '
        f'height="{card_h}" role="img" aria-label="{escape(label, {chr(34): "&quot;"})}">',
        "<style>",
        f".mono{{font-family:{FONT}}}",
        f".face{{font-size:{n(face_font)}px;font-weight:700;fill:{c['face']}}}",
        f".info{{font-size:{n(INFO_FONT)}px;fill:{c['value']}}}",
        f".acc{{fill:{c['accent']}}}.b{{font-weight:700}}.sec{{fill:{c['section']}}}",
        f".val{{fill:{c['value']}}}.dim{{fill:{c['dim']}}}.ok{{fill:{c['green']}}}.bad{{fill:{c['red']}}}",
        f".strip{{animation:turn {n(seconds)}s step-end infinite}}",
        f".cursor{{fill:{c['accent']};animation:blink 1.1s step-end infinite}}",
        f"@keyframes turn{{{keyframes}}}",
        "@keyframes blink{50%{opacity:0}}",
        "@media (prefers-reduced-motion:reduce){.strip,.cursor{animation:none}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{CARD_W - 1}" height="{card_h - 1}" rx="10" '
        f'fill="{c["background"]}" stroke="{c["border"]}"/>',
        f'<clipPath id="window"><rect x="{n(face_x - 4)}" y="{n(face_y - 2)}" '
        f'width="{n(face_w + 8)}" height="{n(face_h + 4)}"/></clipPath>',
        '<g clip-path="url(#window)">',
        # Without animation (or before it starts) the strip rests on the front frame.
        f'<g class="mono face strip" transform="translate(0,{front_shift})">',
    ]
    for f_index, frame in enumerate(frames):
        top = face_y + f_index * pitch
        for r, text in enumerate(frame):
            stripped = text.lstrip(" ")
            if not stripped:
                continue
            lead = len(text) - len(stripped)
            out.append(
                f'<text x="{n(face_x + lead * face_cw)}" y="{n(top + r * face_line + face_line * 0.8)}" '
                f'textLength="{n(len(stripped) * face_cw)}" xml:space="preserve">{escape(stripped)}</text>')
    out.append("</g></g>")

    out.append('<g class="mono info">')
    y = info_y
    for kind, spans in lines:
        if kind == "gap":
            y += INFO_GAP
            continue
        chars = sum(len(t) for _, t in spans)
        body = "".join(f'<tspan class="{cls}">{escape(t)}</tspan>' for cls, t in spans)
        out.append(f'<text x="{INFO_X}" y="{n(y)}" textLength="{n(chars * INFO_CW)}" '
                   f'xml:space="preserve">{body}</text>')
        if kind == "prompt":
            out.append(f'<rect class="cursor" x="{n(INFO_X + chars * INFO_CW)}" y="{n(y - INFO_FONT * 0.85)}" '
                       f'width="{n(INFO_CW)}" height="{n(INFO_FONT * 1.1)}"/>')
        y += INFO_LINE
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    profile = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
    frames_path = ROOT / "assets" / "face_frames.json"
    if not frames_path.exists():
        sys.exit("assets/face_frames.json is missing. Run tools/ascii_face.py first.")
    face = json.loads(frames_path.read_text(encoding="utf-8"))
    for theme in ("dark", "light"):
        svg = build(theme, profile, face)
        path = ROOT / "assets" / f"card-{theme}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(svg.encode()) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

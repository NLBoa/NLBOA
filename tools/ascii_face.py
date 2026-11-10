#!/usr/bin/env python3
"""Turn a short head-turn video into ASCII-art frames.

    uv run --python 3.12 --with opencv-python-headless --with numpy \
        tools/ascii_face.py path/to/video.mov --start 1.0 --end 3.5

Writes assets/face_frames.json, which tools/build_card.py turns into the
profile card. Run with --demo to use a computer-drawn stand-in head instead
of a video.

The video needs a plain, light wall behind you: the script finds the wall by
its colour, removes it, and frames your head from what is left.

Tuning knobs, in the order you are most likely to need them:
  --start / --end   seconds of the video to keep (one sweep, side to side)
  --zoom            bigger = tighter on the face (default 1.0)
  --shift-x/-y      nudge the crop, as a share of head height (+ = right / down)
  --below           how much chin and neck to keep under the jaw line
                    (default 0.25 of head height; smaller cuts higher)
  --contrast        local contrast boost (default 2.0, 0 turns it off)
  --gamma-light     light card: below 1 puts more shading on bright skin
  --gamma-dark      dark card: above 1 lets dark hair recede (default 1.3)
  --crop x,y,w,h    skip the automatic framing and use this pixel box
  --cols / --rows   size of the character grid (default 50 x 38)
  --full-oval       cut the whole picture to an oval, not just under the chin
  --debug FILE.jpg  save a picture of the crops and wall masks to check them
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# Each character and the share of its cell it fills with ink, measured by
# drawing it in bold Menlo. Darker picture areas get the inkier characters.
INK = {
    " ": 0.000, ".": 0.039, "'": 0.046, ",": 0.060, ":": 0.077, "-": 0.089,
    ";": 0.102, "«": 0.123, "/": 0.124, "\\": 0.125, "+": 0.149, "=": 0.156,
    "*": 0.174, "L": 0.199, "7": 0.204, "T": 0.210, "1": 0.224, "J": 0.225,
    "Y": 0.227, "C": 0.231, "I": 0.246, "F": 0.249, "V": 0.270, "X": 0.275,
    "S": 0.280, "P": 0.283, "Z": 0.286, "A": 0.289, "G": 0.298, "6": 0.300,
    "E": 0.302, "9": 0.304, "U": 0.311, "K": 0.316, "O": 0.322, "H": 0.324,
    "&": 0.324, "D": 0.330, "R": 0.340, "0": 0.342, "N": 0.342, "W": 0.346,
    "M": 0.353, "B": 0.355,
}
TONES = 20  # how many brightness levels the picture is reduced to


def build_palette() -> list[list[str]]:
    """For each tone (0 = no ink, TONES-1 = most ink) the characters that fit."""
    top = max(INK.values())
    chars = sorted(INK, key=INK.get)
    palette = []
    for tone in range(TONES):
        target = tone / (TONES - 1)
        half = 0.5 / (TONES - 1)
        fits = [c for c in chars if abs(INK[c] / top - target) <= half]
        if not fits:
            fits = [min(chars, key=lambda c: abs(INK[c] / top - target))]
        palette.append(fits)
    palette[0] = [" "]
    return palette


def to_text(ink: np.ndarray, keep: np.ndarray, palette: list[list[str]]) -> list[str]:
    """ink: rows x cols array, 0..1 (1 = most ink). keep: False = leave blank."""
    rows, cols = ink.shape
    # A fixed shuffle per cell (same every run) decides which of the fitting
    # characters a cell uses, so a cell whose brightness does not change keeps
    # the same character from frame to frame.
    pick = np.random.default_rng(7).integers(0, 1 << 16, size=(rows, cols))
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            if not keep[y, x]:
                line.append(" ")
                continue
            tone = min(TONES - 1, max(1, int(round(ink[y, x] * (TONES - 1)))))
            fits = palette[tone]
            line.append(fits[int(pick[y, x]) % len(fits)])
        out.append("".join(line).rstrip())
    return out


def oval_mask(rows: int, cols: int, lower_only: bool = False) -> np.ndarray:
    """An oval filling the grid. With lower_only the top half is left square,
    so only the chin and neck are rounded off."""
    ys, xs = np.mgrid[0:rows, 0:cols]
    ny = (ys + 0.5 - rows / 2) / (rows / 2)
    nx = (xs + 0.5 - cols / 2) / (cols / 2)
    inside = nx * nx + ny * ny <= 1.0
    return inside | (ny < 0) if lower_only else inside


def drop_specks(keep: np.ndarray) -> np.ndarray:
    """Blank cells with fewer than three drawn neighbours (stray hairs)."""
    padded = np.pad(keep, 1).astype(int)
    around = sum(padded[1 + dy:padded.shape[0] - 1 + dy, 1 + dx:padded.shape[1] - 1 + dx]
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
    return keep & (around >= 3)


def tame_edges(grid: np.ndarray, keep: np.ndarray) -> np.ndarray:
    """Wispy hair against a bright wall averages out half-bright and shows as
    a halo. Cap each outline cell at the brightness of the cells just inside it."""
    rows, cols = keep.shape
    padded = np.pad(keep, 1)
    interior = keep & padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:]
    out = grid.copy()
    for y, x in zip(*np.nonzero(keep & ~interior)):
        y0, y1, x0, x1 = max(0, y - 1), min(rows, y + 2), max(0, x - 1), min(cols, x + 2)
        inner = interior[y0:y1, x0:x1]
        if inner.any():
            out[y, x] = min(grid[y, x], grid[y0:y1, x0:x1][inner].mean())
    return out


def shrink(img: np.ndarray, rows: int, cols: int) -> np.ndarray:
    """Average the picture down to one value per character cell."""
    h, w = img.shape
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, cols + 1).astype(int)
    out = np.empty((rows, cols), dtype=np.float64)
    for r in range(rows):
        for c in range(cols):
            out[r, c] = img[ys[r]:ys[r + 1], xs[c]:xs[c + 1]].mean()
    return out


# --------------------------------------------------------------------------
# Stand-in head: a shaded egg with hair, eyes, nose and mouth painted on,
# turned from one side to the other. Only used to test the animation.
# --------------------------------------------------------------------------
def demo_frames(count: int, width: int = 360, height: int = 500):
    """Returns (pictures, masks); a mask is 1.0 where the head is, 0.0 for background."""
    ys, xs = np.mgrid[0:height, 0:width]
    px = (xs - width / 2) / (width * 0.40)
    py = (ys - height / 2) / (height * 0.44)
    inside = px * px + py * py < 1.0
    pz = np.sqrt(np.clip(1.0 - px * px - py * py, 0, 1))
    frames = []
    for yaw in np.linspace(-0.8, 0.8, count):
        # surface point in the head's own coordinates (undo the turn)
        hx = px * np.cos(yaw) - pz * np.sin(yaw)
        hz = px * np.sin(yaw) + pz * np.cos(yaw)
        hy = py
        light = np.clip(0.35 + 0.65 * (0.25 * px - 0.35 * py + 0.9 * pz), 0, 1)
        shade = 0.25 + 0.7 * light

        def spot(cx, cy, rx, ry):
            return (((hx - cx) / rx) ** 2 + ((hy - cy) / ry) ** 2 < 1) & (hz > 0)

        hair = (hy < -0.48 + 0.25 * np.abs(hx)) | (hz < -0.15)
        shade = np.where(hair, shade * 0.22, shade)
        for side in (-1, 1):
            shade = np.where(spot(side * 0.36, -0.12, 0.17, 0.07), 0.10, shade)   # eyes
            shade = np.where(spot(side * 0.36, -0.27, 0.22, 0.035), 0.25, shade)  # brows
        shade = np.where(spot(0.0, 0.16, 0.07, 0.20), shade * 1.15 + 0.05, shade)  # nose
        shade = np.where(spot(0.0, 0.50, 0.26, 0.05), 0.22, shade)                 # mouth
        img = np.where(inside, np.clip(shade, 0, 1), 0.96)
        frames.append((img * 255).astype(np.uint8))
    return frames, [inside.astype(np.float64)] * count


# --------------------------------------------------------------------------
# Video: read it, find the wall, frame the head
# --------------------------------------------------------------------------
def read_video(path: Path, start: float, end: float | None, count: int) -> list[np.ndarray]:
    """Evenly spaced colour frames between start and end (seconds)."""
    import cv2

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        sys.exit(f"Could not open the video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    kept = []
    index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = index / fps
        index += 1
        if t < start or (end is not None and t > end):
            continue
        kept.append(frame)
    cap.release()
    if len(kept) < 2:
        sys.exit("No frames found in that time range. Check --start and --end.")
    picks = np.linspace(0, len(kept) - 1, min(count, len(kept))).round().astype(int)
    return [kept[i] for i in picks]


def person_mask(frame: np.ndarray) -> np.ndarray:
    """True where the person is. The wall is whatever is as bright and as
    colourless as the top corners of the picture and reachable from the top
    or side edges without crossing the person."""
    import cv2

    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)
    sat, val = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    h, w = sat.shape
    ph, pw = max(8, h // 12), max(8, w // 8)
    corners = np.r_[0:ph], np.r_[0:pw, w - pw:w]
    wall_sat = np.median(sat[np.ix_(*corners)])
    wall_val = np.median(val[np.ix_(*corners)])
    wall_like = ((sat < wall_sat + 28) & (val > wall_val - 55)).astype(np.uint8)

    count, labels = cv2.connectedComponents(wall_like, connectivity=4)
    edge = np.concatenate([labels[0, :], labels[: int(h * 0.8), 0], labels[: int(h * 0.8), -1]])
    reached = np.zeros(count, dtype=bool)
    reached[np.unique(edge)] = True
    wall = reached[labels] & (wall_like > 0)

    person = (~wall).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    person = cv2.morphologyEx(person, cv2.MORPH_OPEN, kernel)   # drop specks
    person = cv2.morphologyEx(person, cv2.MORPH_CLOSE, kernel)  # fill pinholes
    return person > 0


def neck_row(mask: np.ndarray) -> tuple[int, int] | None:
    """(top of the hair, row of the neck). Going down from the widest part of
    the head, the neck is where the outline stops narrowing and widens again."""
    h, w = mask.shape
    widths = mask.sum(axis=1).astype(float)
    filled = np.nonzero(widths > w * 0.02)[0]
    if not len(filled):
        return None
    top = int(filled[0])
    k = max(3, h // 40) | 1
    smooth = np.convolve(widths, np.ones(k) / k, mode="same")
    widest_y, widest = top, smooth[top]
    for y in range(top, h - k):
        if smooth[y] > widest:
            widest_y, widest = y, smooth[y]
        elif y > widest_y + k and smooth[y] < 0.8 * widest and smooth[y + k] > smooth[y] * 1.03:
            # step to the true bottom of this dip
            return top, y + int(np.argmin(smooth[y:y + k]))
    return top, h - 1


def head_boxes(masks: list[np.ndarray], picture_ratio: float, zoom: float,
               shift_x: float, shift_y: float, below: float) -> tuple[list[tuple[float, float, float, float]], float, float]:
    """One box per frame, shaped like the text grid, running from the top of
    the hair to just under the chin. Every box is the same size; each follows
    its frame's head sideways (smoothed), so the head turns in place.
    Returns the boxes, the row of the neck, and the row to cut clothes off at."""
    tops, necks, centres = [], [], []
    for m in masks:
        found = neck_row(m)
        if found is None:
            sys.exit("Could not find a head against the wall. Give the box yourself with --crop x,y,w,h.")
        top, neck = found
        cols = np.nonzero(m[top:neck].any(axis=0))[0]
        tops.append(top)
        necks.append(neck)
        centres.append((cols[0] + cols[-1]) / 2)
    top, neck = float(np.median(tops)), float(np.median(necks))
    head_h = neck - top
    box_h = head_h * (1.05 + below) / zoom
    box_w = box_h / picture_ratio
    y0 = top - 0.03 * head_h + (1 - 1 / zoom) * 0.4 * head_h + shift_y * head_h
    # Smooth the sideways path so the crop glides instead of jittering.
    padded = np.pad(np.array(centres, dtype=float), 2, mode="edge")
    smooth = np.convolve(padded, np.ones(5) / 5, mode="valid")
    boxes = [(cx + shift_x * head_h - box_w / 2, y0, box_w, box_h) for cx in smooth]
    print(f"hair top at row {top:.0f}, jaw at row {neck:.0f}")
    return boxes, neck, neck + below * head_h


def fill_below(mask: np.ndarray, row: int) -> np.ndarray:
    """Below the neck, light clothes can look like wall. Fill each row there
    from its leftmost to its rightmost person pixel."""
    out = mask.copy()
    for y in range(max(0, row), mask.shape[0]):
        xs = np.nonzero(mask[y])[0]
        if len(xs):
            out[y, xs[0]:xs[-1] + 1] = True
    return out


def cut(img: np.ndarray, box, out_w: int, out_h: int) -> np.ndarray:
    """Cut the box out of the picture (padding with the edge colour if it runs off)."""
    import cv2

    x, y, w, h = box
    src = np.float32([[x, y], [x + w, y], [x, y + h]])
    dst = np.float32([[0, 0], [out_w, 0], [0, out_h]])
    return cv2.warpAffine(img, cv2.getAffineTransform(src, dst), (out_w, out_h),
                          flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?", type=Path)
    ap.add_argument("--demo", action="store_true", help="use the stand-in head instead of a video")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "assets" / "face_frames.json")
    ap.add_argument("--cols", type=int, default=50)
    ap.add_argument("--rows", type=int, default=38)
    ap.add_argument("--cell-ratio", type=float, default=1.56, help="character cell height / width on the card")
    ap.add_argument("--frames", type=int, default=24)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--shift-x", type=float, default=0.0)
    ap.add_argument("--shift-y", type=float, default=0.0)
    ap.add_argument("--below", type=float, default=0.25, help="how far under the jaw to keep, as a share of head height")
    ap.add_argument("--crop", type=str, default=None)
    ap.add_argument("--contrast", type=float, default=2.0)
    ap.add_argument("--gamma-light", type=float, default=1.0)
    ap.add_argument("--gamma-dark", type=float, default=1.3)
    ap.add_argument("--debug", type=Path, default=None)
    ap.add_argument("--full-oval", action="store_true", help="cut the whole picture to an oval")
    args = ap.parse_args()

    rows, cols = args.rows, args.cols
    # Shape of the picture area the grid covers (height / width).
    picture_ratio = rows * args.cell_ratio / cols
    work_w = cols * 8
    work_h = int(round(work_w * picture_ratio))

    if args.demo:
        crops, masks = demo_frames(args.frames, work_w, work_h)
    else:
        if args.video is None:
            ap.error("give a video path, or use --demo")
        import cv2

        frames = read_video(args.video, args.start, args.end, args.frames)
        people = [person_mask(f) for f in frames]
        boxes, neck, collar = head_boxes(people, picture_ratio, args.zoom, args.shift_x, args.shift_y, args.below)
        people = [fill_below(p, int(neck)) for p in people]
        for person in people:
            person[int(collar):] = False  # nothing below the neck: no collar, no shirt
        if args.crop:
            boxes = [tuple(float(v) for v in args.crop.split(","))] * len(frames)
        print(f"crop box of the middle frame (x,y,w,h): {','.join(str(int(v)) for v in boxes[len(boxes) // 2])}")
        crops = [cut(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), b, work_w, work_h) for f, b in zip(frames, boxes)]
        masks = [cut(p.astype(np.uint8) * 255, b, work_w, work_h) / 255.0 for p, b in zip(people, boxes)]
        if args.debug:
            tiles = [np.hstack([c, (m * 255).astype(np.uint8)]) for c, m in zip(crops, masks)]
            show = tiles[:: max(1, len(tiles) // 6)][:6]
            cv2.imwrite(str(args.debug), np.hstack(show))
        if args.contrast > 0:
            boost = cv2.createCLAHE(clipLimit=args.contrast, tileGridSize=(6, 6))
            crops = [boost.apply(c) for c in crops]

    # The demo head is cut to a full oval; a real head keeps its own outline
    # (the wall is already gone) and is only rounded off under the chin.
    oval = oval_mask(rows, cols, lower_only=not args.demo and not args.full_oval)
    # A cell is drawn only if at least half of it is the person, not the wall,
    # and its brightness is averaged over the person's part of it only.
    cover = [shrink(m, rows, cols) for m in masks]
    keep = [drop_specks(oval & (c >= 0.5)) for c in cover]
    grids = [shrink(c.astype(np.float64) / 255.0 * m, rows, cols) / np.maximum(cv, 1e-6)
             for c, m, cv in zip(crops, masks, cover)]

    # One brightness stretch shared by every frame, so the picture does not flicker.
    inside = np.concatenate([g[k] for g, k in zip(grids, keep)])
    lo, hi = np.percentile(inside, [2, 98])
    grids = [np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1) for g in grids]
    grids = [tame_edges(g, k) for g, k in zip(grids, keep)]

    palette = build_palette()
    data = {
        "cols": cols,
        "rows": rows,
        "cell_ratio": args.cell_ratio,
        "front": len(grids) // 2,
        # "light": dark ink on a light card, so dark areas get the dense letters.
        # "dark": light ink on a dark card, so bright areas get the dense letters.
        "light": [to_text((1.0 - g) ** args.gamma_light, k, palette) for g, k in zip(grids, keep)],
        "dark": [to_text(g ** args.gamma_dark, k, palette) for g, k in zip(grids, keep)],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {args.out} ({len(grids)} frames, {cols}x{rows})")
    print("\n".join(data["light"][data["front"]]))


if __name__ == "__main__":
    main()

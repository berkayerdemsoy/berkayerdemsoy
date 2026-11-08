"""Two reaching hands rendered as ASCII layers.

The hands are drawn as labelled vector shapes (each finger, palm and plate gets
its own label), shaded per part, and sampled into a character grid:
the human hand is filled with DNA bases, the robot hand with binary digits,
and the robot joints and cables with ring characters.
Each cell carries a brightness level (1-4) that the SVG maps to opacity.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# design space of the composition and the cropped window that becomes the grid
BOX = (150, 105, 650, 305)
SCALE = 3.4          # raster pixels per design unit
CELL_W, CELL_H = 10, 15
LIGHT = (-0.45, -0.75, 0.5)   # from the upper left, toward the viewer
HUMAN_CHARS = "ACGT"
ROBOT_CHARS = "01"
JOINT_CHARS = "o@"
ROBOT_LABEL = 30     # labels below this value belong to the human hand
JOINT_LABEL = 150    # robot joints and cables, drawn as a separate copper layer


class Scaled:
    """ImageDraw proxy that maps design coordinates into the scaled, cropped canvas."""

    def __init__(self, draw, s, ox, oy):
        self.d, self.s, self.ox, self.oy = draw, s, ox, oy

    def _p(self, p):
        return ((p[0] - self.ox) * self.s, (p[1] - self.oy) * self.s)

    def polygon(self, pts, fill):
        self.d.polygon([self._p(p) for p in pts], fill=fill)

    def ellipse(self, box, fill):
        x0, y0 = self._p(box[:2])
        x1, y1 = self._p(box[2:])
        self.d.ellipse([x0, y0, x1, y1], fill=fill)


def capsule(d, p0, p1, r, fill):
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * r, math.cos(ang) * r
    d.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=fill)
    d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=fill)
    d.ellipse([x1 - r, y1 - r, x1 + r, y1 + r], fill=fill)


def finger(d, pts, r, fill, taper=1.0):
    """Rounded multi-joint finger that narrows toward the tip."""
    n = len(pts) - 1
    for i in range(n):
        r0 = r * (1 - (1 - taper) * i / n)
        r1 = r * (1 - (1 - taper) * (i + 1) / n)
        capsule(d, pts[i], pts[i + 1], (r0 + r1) / 2, fill)


def bar(d, p0, p1, r, fill):
    """Square-ended segment used for the robot parts."""
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * r, math.cos(ang) * r
    d.polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)], fill=fill)


def draw_human(d, ox=-38):
    def P(pts):
        return [(x + ox, y) for x, y in pts]
    # forearm rising from the lower left into a relaxed wrist
    d.polygon(P([(0, 330), (0, 236), (150, 196), (262, 180), (272, 252), (150, 290)]), fill=10)
    # back of the hand
    d.polygon(P([(256, 178), (300, 172), (334, 182), (340, 222), (300, 240), (266, 252)]), fill=11)
    # thumb hanging below
    finger(d, P([(278, 236), (306, 252), (326, 260)]), 11, 12, taper=0.8)
    # pinky and ring: curled
    finger(d, P([(306, 228), (330, 246), (336, 262), (328, 272)]), 9, 13, taper=0.8)
    finger(d, P([(318, 220), (350, 236), (362, 254), (355, 266)]), 10, 14, taper=0.8)
    # middle: half extended, drooping
    finger(d, P([(326, 206), (366, 218), (392, 232), (398, 248)]), 11, 15, taper=0.8)
    # index: extended, slight droop
    finger(d, P([(322, 190), (365, 198), (402, 206), (430, 214)]), 12, 16, taper=0.78)


def draw_robot(d):
    plate = iter(range(ROBOT_LABEL, JOINT_LABEL))
    joint = iter(range(JOINT_LABEL, 256))
    # forearm: two armored plates entering from the upper right
    bar(d, (820, 96), (720, 122), 40, next(plate))
    bar(d, (712, 124), (640, 142), 34, next(plate))
    # cables hanging under the forearm
    bar(d, (700, 150), (628, 176), 4, next(joint))
    bar(d, (716, 158), (640, 190), 3.5, next(joint))
    # wrist joint
    d.ellipse([600, 120, 650, 172], fill=next(joint))
    # back of the hand, palm down, tilted toward the knuckles
    d.polygon([(612, 128), (628, 172), (588, 214), (548, 222), (516, 190), (520, 160), (560, 136)],
              fill=next(plate))
    # fingers: knuckle, phalanx vectors, radius; the index reaches, the rest hang
    fingers = [
        ((520, 168), [(-34, 10), (-28, 7), (-24, 5)], 10.5),
        ((530, 190), [(-30, 18), (-20, 18), (-12, 16)], 10),
        ((548, 206), [(-20, 24), (-10, 22), (-4, 18)], 9.5),
        ((570, 214), [(-8, 26), (-2, 20), (2, 16)], 8.5),
    ]
    for (x, y), segs, r in fingers:
        for i, (dx, dy) in enumerate(segs):
            k = 0.86 if i else 1.0          # shortened phalanx leaves a gap at the joint
            bar(d, (x, y), (x + dx * k, y + dy * k), r * (1 - 0.08 * i), next(plate))
            x, y = x + dx, y + dy
            if i < len(segs) - 1:
                jr = r * 0.62
                d.ellipse([x - jr, y - jr, x + jr, y + jr], fill=next(joint))
    # thumb tucked under the palm
    bar(d, (590, 212), (566, 236), 9, next(plate))
    bar(d, (564, 240), (548, 252), 8, next(plate))


def render_labels():
    x0, y0, x1, y1 = BOX
    img = Image.new("L", (int((x1 - x0) * SCALE), int((y1 - y0) * SCALE)), 0)
    d = Scaled(ImageDraw.Draw(img), SCALE, x0, y0)
    draw_human(d)
    draw_robot(d)
    return img


def _norm(v):
    l = math.sqrt(sum(a * a for a in v))
    return tuple(a / l for a in v)


def _height_map(lab, labels, blur):
    """Each part becomes its own soft dome so neighbouring parts shade separately."""
    hm = Image.new("L", lab.size, 0)
    for v in labels:
        m = lab.point(lambda p, v=v: 255 if p == v else 0)
        if not m.getbbox():
            continue
        dome = ImageChops.multiply(m.filter(ImageFilter.GaussianBlur(blur)), m)
        hm = ImageChops.lighter(hm, dome)
    return hm


def _open_gaps(lab, gap=7):
    """Carve the lower part wherever two parts of the same hand touch."""
    W, H = lab.size
    src = lab.copy().load()
    px = lab.load()
    for y in range(gap * 2, H - gap * 2):
        for x in range(gap, W - gap):
            v = src[x, y]
            if not v:
                continue
            for dx, dy in ((gap, 0), (0, gap * 2), (gap, gap * 2), (gap, -gap * 2)):
                n = src[x + dx, y + dy]
                if n and n > v and (n < ROBOT_LABEL) == (v < ROBOT_LABEL):
                    px[x, y] = 0
                    break


def build(seed=7):
    """Return {"h", "r", "j"} rows (human, robot plates, robot joints).

    Each row is a list of (char, level) with level 0 for empty.
    """
    lab = render_labels()
    W, H = lab.size
    pixels = lab.get_flattened_data() if hasattr(lab, "get_flattened_data") else lab.getdata()
    labels = sorted(set(pixels) - {0})
    hm = {
        "h": _height_map(lab, [v for v in labels if v < ROBOT_LABEL], 9).load(),
        "r": _height_map(lab, [v for v in labels if v >= ROBOT_LABEL], 9).load(),
    }
    _open_gaps(lab)
    px = lab.load()
    light = _norm(LIGHT)
    rnd = random.Random(seed)
    cols, rows = W // CELL_W, H // CELL_H
    out = {"h": [], "r": [], "j": []}
    d = 8
    for r in range(rows):
        hr, rr, jr = [], [], []
        for c in range(cols):
            cnt, n, n_joint = {"h": 0, "r": 0}, 0, 0
            for y in range(r * CELL_H, (r + 1) * CELL_H, 3):
                for x in range(c * CELL_W, (c + 1) * CELL_W, 2):
                    v = px[x, y]
                    n += 1
                    if v:
                        cnt["h" if v < ROBOT_LABEL else "r"] += 1
                        n_joint += v >= JOINT_LABEL
            x, y = c * CELL_W + CELL_W // 2, r * CELL_H + CELL_H // 2
            for k, row in (("h", hr), ("r", rr)):
                cov = cnt[k] / n
                if cov < 0.18:
                    row.append((" ", 0))
                    continue
                h = hm[k]

                def g(xx, yy):
                    return h[min(max(xx, 0), W - 1), min(max(yy, 0), H - 1)] / 255

                gx = (g(x + d, y) - g(x - d, y)) * 6
                gy = (g(x, y + d) - g(x, y - d)) * 6
                nrm = _norm((-gx, -gy, 1.0))
                lum = 0.18 + 0.82 * max(0.0, sum(a * b for a, b in zip(nrm, light)))
                lum *= min(1.0, 0.35 + cov)
                level = max(1, min(4, int(lum * 4.999)))
                if h[x, y] < 40:          # near a part border
                    ch = "."
                else:
                    ch = rnd.choice(HUMAN_CHARS if k == "h" else ROBOT_CHARS)
                row.append((ch, level))
            # robot cells covered mostly by a joint or cable move to the copper layer
            if rr[-1][1] and n_joint * 2 > cnt["r"]:
                jr.append((rnd.choice(JOINT_CHARS), rr[-1][1]))
                rr[-1] = (" ", 0)
            else:
                jr.append((" ", 0))
        out["h"].append(hr)
        out["r"].append(rr)
        out["j"].append(jr)
    # drop empty rows at the top and bottom
    keep = [i for i in range(rows) if any(ch != " " for ch, _ in out["h"][i] + out["r"][i] + out["j"][i])]
    return {k: v[keep[0]:keep[-1] + 1] for k, v in out.items()}


if __name__ == "__main__":
    o = build()
    for rows in zip(o["h"], o["r"], o["j"]):
        print("".join(next((ch for ch, _ in cells if ch != " "), " ") for cells in zip(*rows)).rstrip())

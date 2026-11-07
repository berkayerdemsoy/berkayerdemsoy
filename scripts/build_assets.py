"""Generate the profile README assets (dark and light variants).

    python3 scripts/build_assets.py

Writes into assets/:
    hero-{dark,light}.svg     ASCII hands animation with name and tagline
    arch-{dark,light}.svg     Akissy topology with animated traffic
    btn-<name>-{dark,light}.svg  link buttons

Requires Pillow. All animation is CSS/SMIL inside the SVG, so it plays in a
README <img> without scripts.
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape

import hands_ascii

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'

THEMES = {
    "dark": dict(bg="#0d1117", panel="#161b22", border="#30363d", human="#f2b38a", robot="#5fd3ff",
                 text="#e6edf3", dim="#7d8590", accent="#ffe4a3", glow="#fff3d1"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", border="#d0d7de", human="#b0542a", robot="#0577a8",
                  text="#1f2328", dim="#656d76", accent="#c26a00", glow="#ffb84d"),
}

# ---------------------------------------------------------------------------
# hero
# ---------------------------------------------------------------------------
T = 14.0                       # loop length in seconds
CW, CH = hands_ascii.CELL_W, hands_ascii.CELL_H
PAD_X = 40
TOP = 96                       # y where the art starts
LEVEL_OPACITY = {1: 0.28, 2: 0.5, 3: 0.75, 4: 1.0}

PROMPT = "berkay@erdemsoy:~$ ./connect --human --machine"
NAME = "BERKAY ERDEMSOY"
SUBTITLE = "software engineer  ·  java / spring  ·  systems & architecture"
QUOTE = "> one is greater than zero."


def pct(t):
    return f"{100 * t / T:.2f}%"


def fingertips(o):
    """Rightmost human cell, and leftmost robot cell in the upper-left area of the robot layer."""
    h_tip = max(((c, r) for r, row in enumerate(o["h"]) for c, (ch, _) in enumerate(row) if ch not in " ."))
    r_tip = min(((c, r) for r, row in enumerate(o["r"]) for c, (ch, _) in enumerate(row)
                 if ch not in " ." and r < len(o["r"]) * 0.6 and c < len(row) * 0.7))
    return h_tip, r_tip


def layer_text(rows, cls, cols):
    """One <text> per row and brightness level; spaces keep the grid aligned."""
    out = []
    for r, row in enumerate(rows):
        y = TOP + r * CH + 12
        for lv in (1, 2, 3, 4):
            s = "".join(ch if (ch != " " and l == lv) else " " for ch, l in row)
            if s.strip():
                out.append(f'<text class="{cls} l{lv} r{r}" x="{PAD_X}" y="{y}" textLength="{cols * CW}" '
                           f'lengthAdjust="spacing">{escape(s)}</text>')
    return "\n".join(out)


def typed(id_, x, y, text, size, cls, t0, t1, bg):
    """Text revealed left to right by a background-coloured cover that slides in steps."""
    n = len(text)
    w = n * size * 0.6
    svg = (f'<g class="{cls}"><text x="{x:.0f}" y="{y}" style="font-size:{size}px" textLength="{w:.0f}" '
           f'lengthAdjust="spacing">{escape(text)}</text>'
           f'<rect class="cov cov-{id_}" x="{x - 2:.0f}" y="{y - size}" width="{w + 24:.0f}" '
           f'height="{size * 1.4:.0f}" fill="{bg}"/></g>')
    css = (f'.cov-{id_}{{animation:cov-{id_} {T}s infinite}}'
           f'@keyframes cov-{id_}{{0%,{pct(t0)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}'
           f'{pct(t1)},100%{{transform:translateX({w + 24:.0f}px)}}}}')
    return svg, css


def hero(th, art):
    rows, cols = len(art["h"]), len(art["h"][0])
    (hx, hy), (rx, ry) = fingertips(art)
    W = PAD_X * 2 + cols * CW
    art_h = rows * CH
    H = TOP + art_h + 170
    css = []

    # timeline (seconds)
    t_scan0, t_scan1 = 1.6, 3.6       # rows appear top to bottom
    t_meet = 6.4                      # hands finish drifting together
    t_sp0, t_sp1 = 6.3, 13.0          # spark window
    t_fade0, t_fade1 = 13.2, 13.8     # scene fades before the loop restarts

    for r in range(rows):
        t = t_scan0 + (t_scan1 - t_scan0) * r / rows
        css.append(f'.r{r}{{animation:r{r} {T}s infinite}}'
                   f'@keyframes r{r}{{0%,{pct(t)}{{visibility:hidden}}{pct(t + 0.01)},100%{{visibility:visible}}}}')
    css.append(f'.scan{{animation:scan {T}s infinite linear}}'
               f'@keyframes scan{{0%,{pct(t_scan0)}{{transform:translateY(0);opacity:0}}'
               f'{pct(t_scan0 + 0.05)}{{opacity:1}}{pct(t_scan1)}{{transform:translateY({art_h}px);opacity:1}}'
               f'{pct(t_scan1 + 0.2)},100%{{transform:translateY({art_h}px);opacity:0}}}}')
    drift = 7 * CW
    for name, sign in (("human", -1), ("robot", 1)):
        css.append(f'.{name}{{animation:{name} {T}s infinite}}'
                   f'@keyframes {name}{{0%,{pct(t_scan0)}{{transform:translateX({sign * drift}px);'
                   f'animation-timing-function:cubic-bezier(.45,0,.2,1)}}{pct(t_meet)},100%{{transform:translateX(0)}}}}')

    # spark: a few random three-row frames cycled quickly between the fingertips
    gx0 = PAD_X + (hx + 1) * CW
    gx1 = PAD_X + rx * CW
    gy = TOP + ((hy + ry) / 2) * CH + 8
    cx = (gx0 + gx1) / 2
    gap_cols = max(3, rx - hx - 1)
    rnd = random.Random(3)
    n_frames, step = 6, 0.09
    spark = []
    for i in range(n_frames):
        lines = []
        for dy, pool, density in ((-1, "·.'*+", 0.25), (0, "-~=*+~-", 1.0), (1, "·.,*+", 0.25)):
            s = "".join(rnd.choice(pool) if rnd.random() < density else " " for _ in range(gap_cols))
            lines.append(f'<text x="{gx0}" y="{gy + dy * CH:.0f}" textLength="{gap_cols * CW}" '
                         f'lengthAdjust="spacing">{escape(s)}</text>')
        spark.append(f'<g class="sp sp{i}">' + "".join(lines) + '</g>')
        css.append(f'.sp{i}{{animation:sp{i} {n_frames * step:.2f}s infinite steps(1,end);animation-delay:-{step * i:.2f}s}}'
                   f'@keyframes sp{i}{{0%{{opacity:1}}{100 / n_frames:.2f}%,100%{{opacity:0}}}}')
    css.append(f'.spark{{animation:spark {T}s infinite}}'
               f'@keyframes spark{{0%,{pct(t_sp0)}{{opacity:0}}{pct(t_sp0 + 0.15)}{{opacity:1}}'
               f'{pct(t_sp1)}{{opacity:1}}{pct(t_sp1 + 0.3)},100%{{opacity:0}}}}')
    css.append(f'.glow{{animation:glow {T}s infinite}}'
               f'@keyframes glow{{0%,{pct(t_sp0)}{{opacity:0;transform:scale(.4)}}'
               f'{pct(t_sp0 + 0.25)}{{opacity:1;transform:scale(1.25)}}{pct(t_sp0 + 1.2)}{{opacity:.55;transform:scale(1)}}'
               f'{pct(10.0)}{{opacity:.8}}{pct(t_sp1)}{{opacity:.55}}{pct(t_sp1 + 0.3)},100%{{opacity:0}}}}')
    css.append(f'.scene{{animation:scene {T}s infinite}}'
               f'@keyframes scene{{0%,{pct(t_fade0)}{{opacity:1}}{pct(t_fade1)},100%{{opacity:0}}}}')

    name_y = TOP + art_h + 62
    texts = [
        typed("p", PAD_X, 52, PROMPT, 22, "prompt", 0.2, 1.4, th["bg"]),
        typed("n", PAD_X, name_y, NAME, 44, "name", 7.0, 7.9, th["bg"]),
        typed("s", PAD_X, name_y + 40, SUBTITLE, 20, "sub", 8.0, 9.2, th["bg"]),
        typed("q", W - PAD_X - len(QUOTE) * 20 * 0.6, name_y + 40, QUOTE, 20, "quote", 9.6, 10.6, th["bg"]),
    ]
    css += [c for _, c in texts]

    lv_css = "".join(f'.l{k}{{fill-opacity:{v}}}' for k, v in LEVEL_OPACITY.items())
    hidden_still = ",".join(f".sp{i}" for i in range(1, n_frames))
    style = (f'text{{font-family:{FONT};white-space:pre;font-size:16.6px}}'
             f'.h{{fill:{th["human"]}}}.r{{fill:{th["robot"]}}}{lv_css}'
             f'.prompt text{{fill:{th["dim"]}}}.name text{{fill:{th["text"]};font-weight:700}}'
             f'.sub text{{fill:{th["dim"]}}}.quote text{{fill:{th["accent"]}}}'
             f'.sp text{{fill:{th["accent"]};font-weight:700}}'
             + "".join(css) +
             f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.cov,.scan,{hidden_still}{{display:none}}}}')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Berkay Erdemsoy</title>
<desc id="d">ASCII art of two reaching hands: a human hand made of DNA letters and a robot hand made of binary digits, with a spark between the fingertips.</desc>
<defs>
<radialGradient id="g"><stop offset="0" stop-color="{th["glow"]}" stop-opacity=".9"/><stop offset=".35" stop-color="{th["glow"]}" stop-opacity=".35"/><stop offset="1" stop-color="{th["glow"]}" stop-opacity="0"/></radialGradient>
<linearGradient id="sb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["robot"]}" stop-opacity="0"/><stop offset="1" stop-color="{th["robot"]}" stop-opacity=".35"/></linearGradient>
<clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
</defs>
<style>{style}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{th["bg"]}" stroke="{th["border"]}"/>
<g class="scene" clip-path="url(#card)">
{texts[0][0]}
<g class="human">
{layer_text(art["h"], "h", cols)}
</g>
<g class="robot">
{layer_text(art["r"], "r", cols)}
</g>
<rect class="scan" x="{PAD_X}" y="{TOP - 24}" width="{cols * CW}" height="24" fill="url(#sb)"/>
<g class="glow" style="transform-origin:{cx:.0f}px {gy - 5:.0f}px"><ellipse cx="{cx:.0f}" cy="{gy - 5:.0f}" rx="{(gx1 - gx0) * 0.9:.0f}" ry="46" fill="url(#g)"/></g>
<g class="spark">
{chr(10).join(spark)}
</g>
{texts[1][0]}
{texts[2][0]}
{texts[3][0]}
</g>
</svg>
''', W


# ---------------------------------------------------------------------------
# architecture
# ---------------------------------------------------------------------------
# service names shown in the diagram; edit to match the real services
SERVICES = ("service-a", "service-b", "service-c")


def arch(th, W):
    H = 560
    f = 28
    css = (f'text{{font-family:{FONT};white-space:pre}}'
           f'.lbl{{fill:{th["text"]};font-size:{f}px}}.dim{{fill:{th["dim"]};font-size:22px}}'
           f'.box{{fill:{th["panel"]};stroke:{th["border"]};stroke-width:2}}'
           f'.bus{{fill:{th["panel"]};stroke:{th["human"]};stroke-width:2}}'
           f'.reg{{fill:{th["panel"]};stroke:{th["dim"]};stroke-width:2;stroke-dasharray:6 6}}'
           f'.ln{{stroke:{th["border"]};stroke-width:2;fill:none}}'
           f'.hb{{stroke:{th["dim"]};stroke-width:2;stroke-dasharray:4 8;fill:none}}'
           f'.sync{{fill:{th["robot"]}}}.async{{fill:{th["human"]}}}.beat{{fill:{th["dim"]}}}'
           f'.live{{fill:{th["accent"]}}}'
           f'.pulse{{animation:pulse 2s infinite}}@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}'
           f'@media (prefers-reduced-motion:reduce){{.pulse{{animation:none}}.pkt{{display:none}}}}')

    def box(x, y, w, h, label, cls="box"):
        return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>'
                f'<text class="lbl" x="{x + w / 2:.0f}" y="{y + h / 2 + 8:.0f}" text-anchor="middle">{escape(label)}</text>')

    def packet(path, cls, dur, begin, travel=0.35, r=6):
        """A dot that travels the path in the first `travel` share of each cycle, then hides."""
        kt = f"0;{travel};1"
        return (f'<circle class="pkt {cls}" r="{r}" opacity="0">'
                f'<animateMotion path="{path}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite" '
                f'keyPoints="0;1;1" keyTimes="{kt}" calcMode="linear"/>'
                f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{travel};{travel + 0.001};1" '
                f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/></circle>')

    sy, sh, sw = 250, 64, 280                    # service row
    sx = [720, 1080, 1440]
    mid = sy + sh / 2
    parts = [
        box(40, sy, 200, sh, "client"),
        box(300, sy, 340, sh, "traefik · gateway"),
        box(720, 100, 1000, 56, "eureka · service registry", "reg"),
        box(720, 430, 1000, 56, "kafka · event bus", "bus"),
    ]
    parts += [box(x, sy, sw, sh, name) for x, name in zip(sx, SERVICES)]

    a_x, b_x, c_x = (x + sw / 2 for x in sx)
    lines = [
        f'M240 {mid} H300', f'M640 {mid} H720',            # client -> gateway -> service-a
        f'M{sx[0] + sw} {mid} H{sx[1]}',                     # a -> b (sync)
        f'M{a_x} {sy + sh} V430', f'M{c_x} 430 V{sy + sh}',  # a -> kafka -> c (async)
    ]
    parts.insert(0, "".join(f'<path class="ln" d="{d}"/>' for d in lines))
    parts.insert(0, "".join(f'<path class="hb" d="M{x} {sy} V156"/>' for x in (a_x, b_x, c_x)))
    parts += [
        f'<text class="dim" x="{(sx[0] + sw + sx[1]) / 2:.0f}" y="{mid - 14:.0f}" text-anchor="middle">REST</text>',
        f'<text class="dim" x="{a_x + 14:.0f}" y="{(sy + sh + 430) / 2 + 6:.0f}">publish</text>',
        f'<text class="dim" x="{c_x + 14:.0f}" y="{(sy + sh + 430) / 2 + 6:.0f}">consume</text>',
    ]

    cyc = 6
    pk = [
        # request: client -> gateway -> service-a, then service-a <-> service-b
        packet(f'M240 {mid} H300', "sync", cyc, 0, 0.06),
        packet(f'M640 {mid} H{sx[0]}', "sync", cyc, 0.5, 0.06),
        packet(f'M{sx[0] + sw} {mid} H{sx[1]}', "sync", cyc, 1.1, 0.08),
        packet(f'M{sx[1]} {mid} H{sx[0] + sw}', "sync", cyc, 1.7, 0.08),
    ]
    # events: service-a publishes, they travel along the top of the bus, service-c consumes
    bus_path = f'M{a_x} {sy + sh} V442 H{c_x} V{sy + sh}'
    pk += [packet(bus_path, "async", cyc, t, 0.55) for t in (2.2, 2.7, 3.2)]
    pk += [packet(f'M{x} {sy} V156', "beat", 3, i * 0.9, 0.3, 4) for i, x in enumerate((a_x, b_x, c_x))]

    legend_y = H - 30
    legend = (f'<circle class="sync" cx="52" cy="{legend_y - 6}" r="6"/><text class="dim" x="66" y="{legend_y}">sync request</text>'
              f'<circle class="async" cx="292" cy="{legend_y - 6}" r="6"/><text class="dim" x="306" y="{legend_y}">async event</text>'
              f'<circle class="beat" cx="522" cy="{legend_y - 6}" r="4"/><text class="dim" x="536" y="{legend_y}">registry heartbeat</text>')
    header = (f'<text class="dim" x="40" y="52" style="font-size:24px">berkay@erdemsoy:~$ akissy --topology</text>'
              f'<circle class="live pulse" cx="{W - 40 - 17 * 24 * 0.6 - 18:.0f}" cy="45" r="7"/>'
              f'<text class="dim" x="{W - 40}" y="52" text-anchor="end" style="font-size:24px">live · akissy.com</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Akissy topology</title>
<desc id="d">Requests enter through the Traefik gateway; services call each other over REST, publish events to Kafka, and register with Eureka.</desc>
<style>{css}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{th["bg"]}" stroke="{th["border"]}"/>
{header}
{"".join(parts)}
{"".join(pk)}
{legend}
</svg>
'''


# ---------------------------------------------------------------------------
# buttons
# ---------------------------------------------------------------------------
BUTTONS = ("portfolio", "akissy", "linkedin", "medium")


def button(th, label):
    f, h = 15, 36
    text = f"~/{label}"
    w = int(len(text) * f * 0.6 + 2 * 16 + 22)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(label)}">
<style>text{{font-family:{FONT};font-size:{f}px;white-space:pre}}</style>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="{th["panel"]}" stroke="{th["border"]}"/>
<text x="16" y="{h / 2 + 5:.0f}"><tspan fill="{th["accent"]}">~/</tspan><tspan fill="{th["text"]}">{escape(label)}</tspan></text>
<text x="{w - 16}" y="{h / 2 + 5:.0f}" text-anchor="end" fill="{th["dim"]}">↗</text>
</svg>
'''


def main():
    OUT.mkdir(exist_ok=True)
    art = hands_ascii.build()
    for name, th in THEMES.items():
        svg, W = hero(th, art)
        (OUT / f"hero-{name}.svg").write_text(svg)
        (OUT / f"arch-{name}.svg").write_text(arch(th, W))
        for label in BUTTONS:
            (OUT / f"btn-{label}-{name}.svg").write_text(button(th, label))
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()

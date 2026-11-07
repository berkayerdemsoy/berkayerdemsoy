"""Generate the profile README assets (dark and light variants).

    python3 scripts/build_assets.py

Writes into assets/:
    hero-{dark,light}.svg     ASCII hands animation with name and tagline
    arch-{dark,light}.svg     Akissy topology with animated traffic
    card-<section>-{dark,light}.svg  static section cards (text lives in CARDS)
    btn-<name>-{dark,light}.svg   icon link buttons

Requires Pillow and fontTools. Display text is drawn as glyph outlines (see fonts.py). All animation is CSS/SMIL inside the SVG, so it plays in a
README <img> without scripts.
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape

import fonts
import hands_ascii
from fonts import MONO

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = MONO

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
NAME = "Berkay Erdemsoy"
SUBTITLE = "software engineer  ·  java / spring  ·  systems & architecture"
QUOTE = "“One is greater than zero.”"


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


def typed(id_, x, y, text, size, cls, t0, t1, bg, face=None, ts=None):
    """Text revealed left to right by a background-coloured cover that slides in steps.

    Without `face` the text is monospace <text>; with `face` it is drawn as outlines via `ts`.
    """
    n = len(text)
    if face:
        content, w = ts.run(face, text, x, y, size)
    else:
        w = n * size * 0.6
        content = (f'<text x="{x:.0f}" y="{y}" style="font-size:{size}px" textLength="{w:.0f}" '
                   f'lengthAdjust="spacing">{escape(text)}</text>')
    svg = (f'<g class="{cls}">{content}'
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

    ts = fonts.Typesetter()
    name_y = TOP + art_h + 84
    q_size = 36
    q_w = fonts.SERIF_ITALIC.width(QUOTE, q_size)
    texts = [
        typed("p", PAD_X, 52, PROMPT, 22, "prompt", 0.2, 1.4, th["bg"]),
        typed("n", PAD_X, name_y, NAME, 80, "name", 7.0, 7.9, th["bg"], fonts.SERIF_REG, ts),
        typed("s", PAD_X, name_y + 46, SUBTITLE, 20, "sub", 8.0, 9.2, th["bg"]),
        typed("q", W - PAD_X - q_w, name_y, QUOTE, q_size, "quote", 9.6, 10.6, th["bg"], fonts.SERIF_ITALIC, ts),
    ]
    css += [c for _, c in texts]

    lv_css = "".join(f'.l{k}{{fill-opacity:{v}}}' for k, v in LEVEL_OPACITY.items())
    hidden_still = ",".join(f".sp{i}" for i in range(1, n_frames))
    style = (f'text{{font-family:{FONT};white-space:pre;font-size:16.6px}}'
             f'.h{{fill:{th["human"]}}}.r{{fill:{th["robot"]}}}{lv_css}'
             f'.prompt text{{fill:{th["dim"]}}}.name{{fill:{th["text"]}}}'
             f'.sub text{{fill:{th["dim"]}}}.quote{{fill:{th["accent"]}}}'
             f'.sp text{{fill:{th["accent"]};font-weight:600}}'
             + "".join(css) +
             f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.cov,.scan,{hidden_still}{{display:none}}}}')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Berkay Erdemsoy</title>
<desc id="d">ASCII art of two reaching hands: a human hand made of DNA letters and a robot hand made of binary digits, with a spark between the fingertips.</desc>
<defs>
<radialGradient id="g"><stop offset="0" stop-color="{th["glow"]}" stop-opacity=".9"/><stop offset=".35" stop-color="{th["glow"]}" stop-opacity=".35"/><stop offset="1" stop-color="{th["glow"]}" stop-opacity="0"/></radialGradient>
<linearGradient id="sb" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{th["robot"]}" stop-opacity="0"/><stop offset="1" stop-color="{th["robot"]}" stop-opacity=".35"/></linearGradient>
<clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="14"/></clipPath>
{ts.defs()}
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
# section cards
# ---------------------------------------------------------------------------
# Block kinds: ("p", text) paragraph, ("li", text) bullet, ("kv", key, value) aligned row,
# ("gap",) vertical space. **text** renders emphasised.
CARDS = {
    "about": dict(cmd="cat about.md", title="About Me", blocks=[
        ("p", "I am a Computer Engineering student and Software Developer driven by a deep curiosity for "
              "**System Architectures**. In every structure I encounter, I strive to go deeper by asking the "
              "\"why\" and \"how\" behind the technology. My journey has taught me that successful engineering "
              "is more than just writing code; it's about managing real-world use cases and maintaining "
              "effective communication at the heart of every solution."),
        ("gap",),
        ("p", "My primary focus is the **Java** and **Spring Boot** ecosystem, where I enjoy building scalable "
              "and optimized systems. I am highly passionate about **Software Architecture** and **DevOps** "
              "principles, aiming to create sustainable value for products and teams by implementing modern "
              "best practices and robust cloud infrastructures."),
    ]),
    "now": dict(cmd="cat now.md", title="What I'm Working On", blocks=[
        ("p", "**Akissy (Live Event Management System):** I am currently developing and maintaining a scalable, "
              "secure microservices-based platform, actively live at **akissy.com**."),
        ("gap",),
        ("li", "**Architecture:** Utilizing **Eureka** for service discovery, **Apache Kafka** for event-driven "
               "messaging, and **Traefik** for boundary security and API gateway management."),
        ("li", "**Communication:** Implementing both **synchronous and asynchronous** communication patterns "
               "between services to ensure high availability and resilience."),
        ("li", "**Goal:** Building a high-performance system that handles complex event flows while maintaining "
               "strict security standards in a production environment."),
    ]),
    "stack": dict(cmd="cat stack.md", title="Tech Stack", blocks=[
        ("kv", "backend", "Java, Spring Boot, Microservices, C/C++, Python"),
        ("kv", "cloud & devops", "Docker, AWS (EC2, S3), Jenkins, Linux (Ubuntu), Git"),
        ("kv", "messaging & security", "Apache Kafka, Redis, Keycloak (OAuth2/OIDC)"),
        ("kv", "database", "PostgreSQL, MySQL, Liquibase, QueryDSL"),
        ("kv", "frontend", "Angular, Vue.js"),
    ]),
    "experience": dict(cmd="cat experience.md", title="Experience & Projects", blocks=[
        ("li", "**HAVELSAN (Long-term Intern):** Worked within the KOVAN adaptation projects team, resolving "
               "issues in live production systems and managing containerization with Docker Compose."),
    ]),
}


def _rich_words(text):
    """Split **marked** text into words; each word is a list of (text, emphasised) segments.

    A segment that follows a marker without whitespace (e.g. punctuation after an
    emphasised phrase) is glued to the previous word.
    """
    words, prev_open = [], False   # prev_open: previous part ended without whitespace
    for i, part in enumerate(text.split("**")):
        if not part:
            continue
        b = i % 2 == 1
        toks = part.split()
        if words and prev_open and not part[0].isspace() and toks:
            words[-1].append((toks.pop(0), b))
        words += [[(t, b)] for t in toks]
        prev_open = not part[-1].isspace()
    return words


def _word_width(w, size):
    return sum((fonts.SANS_BOLD if b else fonts.SANS_REG).width(t, size) for t, b in w)


def _wrap(words, max_w, size):
    space = fonts.SANS_REG.width(" ", size)
    lines, cur, n = [], [], 0.0
    for w in words:
        ww = _word_width(w, size)
        add = ww + (space if cur else 0)
        if cur and n + add > max_w:
            lines.append(cur)
            cur, n, add = [], 0.0, ww
        cur.append(w)
        n += add
    if cur:
        lines.append(cur)
    return lines


def _tspans(line):
    """Render a wrapped line; adjacent segments with equal emphasis share a tspan."""
    segs = []

    def put(t, b):
        if segs and segs[-1][1] == b:
            segs[-1][0] += t
        else:
            segs.append([t, b])

    for i, w in enumerate(line):
        if i:
            put(" ", False)
        for t, b in w:
            put(t, b)
    return "".join(f'<tspan class="em">{escape(t)}</tspan>' if b else escape(t) for t, b in segs)


def card(th, W, spec):
    pad, f = 64, 29
    lh = round(f * 1.65)
    max_w = W - 2 * pad
    ts = fonts.Typesetter()
    y = 64
    body = [f'<text class="cmd" x="{pad}" y="{y}">berkay@erdemsoy:~$ {escape(spec["cmd"])}</text>']
    y += 92
    body.append(ts.run(fonts.SERIF_REG, spec["title"], pad, y, 64, "title")[0])
    y += 28
    body.append(f'<rect class="bar" x="{pad}" y="{y}" width="64" height="3" rx="1.5"/>')
    y += 24
    key_f = 24
    key_w = max((len(b[1]) * key_f * 0.6 for b in spec["blocks"] if b[0] == "kv"), default=0) + 48
    indent = 34
    space = fonts.SANS_REG.width(" ", f)
    for b in spec["blocks"]:
        kind = b[0]
        if kind == "gap":
            y += lh // 2
            continue
        if kind == "kv":
            y += lh
            body.append(f'<text class="key" x="{pad}" y="{y}">{escape(b[1])}</text>')
            body.append(ts.run(fonts.SANS_REG, b[2], pad + key_w, y, f)[0])
            continue
        dx = indent if kind == "li" else 0
        for i, line in enumerate(_wrap(_rich_words(b[1]), max_w - dx, f)):
            y += lh
            if kind == "li" and i == 0:
                body.append(ts.run(fonts.SANS_BOLD, "›", pad, y, f, "mark")[0])
            x = pad + dx
            for j, word in enumerate(line):
                if j:
                    x += space
                for t, em in word:
                    svg, w = ts.run(fonts.SANS_BOLD if em else fonts.SANS_REG, t, x, y, f, "em" if em else None)
                    body.append(svg)
                    x += w
    H = y + 56
    css = (f'text{{font-family:{MONO};white-space:pre}}'
           f'.cmd{{fill:{th["dim"]};font-size:22px}}.key{{font-size:{key_f}px;fill:{th["human"]}}}'
           f'.body{{fill:{th["text"]}}}.bar{{fill:{th["human"]}}}'
           f'.em{{fill:{th["robot"]}}}.mark{{fill:{th["human"]}}}')
    plain = " ".join(" ".join(blk[1:]) for blk in spec["blocks"] if len(blk) > 1).replace("**", "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">\n'
            f'<title id="t">{escape(spec["title"])}</title>\n<desc id="d">{escape(plain)}</desc>\n'
            f'<defs>{ts.defs()}</defs>\n<style>{css}</style>\n'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{th["bg"]}" stroke="{th["border"]}"/>\n'
            f'<g class="body">\n' + "\n".join(body) + "\n</g>\n</svg>\n")


# ---------------------------------------------------------------------------
# icon buttons
# ---------------------------------------------------------------------------
# 24x24 icons; brand marks are simplified shapes
ICONS = {
    # globe
    "portfolio": '<g fill="none" stroke="{fg}" stroke-width="1.8" stroke-linecap="round">'
                 '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/>'
                 '<path d="M3.6 9h16.8M3.6 15h16.8"/></g>',
    # event ticket
    "akissy": '<g fill="none" stroke="{fg}" stroke-width="1.8" stroke-linejoin="round">'
              '<path d="M3 7.5A1.5 1.5 0 0 1 4.5 6h15A1.5 1.5 0 0 1 21 7.5V10a2 2 0 0 0 0 4v2.5a1.5 1.5 0 0 1-1.5 1.5h-15'
              'A1.5 1.5 0 0 1 3 16.5V14a2 2 0 0 0 0-4z"/><path d="M14.5 6.5v11" stroke-dasharray="1.6 2"/></g>',
    "linkedin": '<rect x="2.5" y="2.5" width="19" height="19" rx="3" fill="{fg}"/>'
                '<g fill="{bg}"><circle cx="7.6" cy="7.4" r="1.55"/><rect x="6.3" y="9.8" width="2.6" height="8" rx=".3"/>'
                '<path d="M11 9.8h2.45V11c.5-.85 1.45-1.4 2.7-1.4 2 0 3.05 1.25 3.05 3.55v4.65h-2.6v-4.2c0-1.1-.45-1.7-1.35-1.7'
                '-.95 0-1.65.65-1.65 1.85v4.05H11z"/></g>',
    "medium": '<g fill="{fg}"><ellipse cx="7.2" cy="12" rx="5.6" ry="5.6"/><ellipse cx="16.2" cy="12" rx="2.8" ry="5.3"/>'
              '<ellipse cx="20.7" cy="12" rx="1.05" ry="4.8"/></g>',
}
BUTTONS = tuple(ICONS)


def button(th, name):
    s = 52
    icon = ICONS[name].replace("{fg}", th["text"]).replace("{bg}", th["panel"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s} {s}" width="{s}" height="{s}" '
            f'role="img" aria-label="{escape(name)}">\n<title>{escape(name)}</title>\n'
            f'<rect x="0.5" y="0.5" width="{s - 1}" height="{s - 1}" rx="12" fill="{th["panel"]}" stroke="{th["border"]}"/>\n'
            f'<g transform="translate(13 13) scale(1.083)">{icon}</g>\n</svg>\n')


def main():
    OUT.mkdir(exist_ok=True)
    art = hands_ascii.build()
    for name, th in THEMES.items():
        svg, W = hero(th, art)
        (OUT / f"hero-{name}.svg").write_text(svg)
        (OUT / f"arch-{name}.svg").write_text(arch(th, W))
        for key, spec in CARDS.items():
            (OUT / f"card-{key}-{name}.svg").write_text(card(th, W, spec))
        for btn in BUTTONS:
            (OUT / f"btn-{btn}-{name}.svg").write_text(button(th, btn))
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()

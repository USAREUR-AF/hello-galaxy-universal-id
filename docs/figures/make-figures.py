"""Draw the repository's figures from the tree.

    python3 -I docs/figures/make-figures.py           # write docs/figures/*.svg
    python3 -I docs/figures/make-figures.py --check   # exit 1 if a committed figure is out of date

Each figure is written twice, `<name>-light.svg` and `<name>-dark.svg`, for a
`<picture>` element. Every value in `one-record` is computed here the way
bin/demo computes it: the seeded registry, the reorg (lib/registry.retask), and
the three platforms in platforms/, at the demo's pinned times. Standard
library only; the output is deterministic.
"""

# ---- Hello Galaxy figure kit (shared by the series; standard library only) ----
# One visual language for every Hello Galaxy figure: the token palette, type
# sizes, boxes, stage dots and arrows below. Each figure is written twice,
# <name>-light.svg and <name>-dark.svg, for a <picture> element; each file is
# self-contained (its colors are declared inside it; no remote font).

import os
import sys
from xml.sax.saxutils import escape

THEMES = {
    "light": "--ink:#191c22; --quiet:#555c68; --rule:#dde1e6; --line:#878f9c; --paper:#ffffff; "
             "--panel:#f5f6f8; --accent:#0b5a72; --accent-soft:#e2f0f4; --on-accent:#ffffff; "
             "--good:#2a6a35; --good-bg:#e4f3e6; --warn:#875200; --warn-bg:#fcf0d7; --info:#285d9e; "
             "--info-bg:#e6eff9; --crit:#b0261d; --crit-bg:#fbeae8; --mute:#5a606a; --mute-bg:#efeeeb;",
    "dark": "--ink:#e7e9ec; --quiet:#a5acb7; --rule:#30363e; --line:#7b8592; --paper:#121417; "
            "--panel:#1a1d21; --accent:#6cc3da; --accent-soft:#14303a; --on-accent:#121417; "
            "--good:#6fc480; --good-bg:#1b2e20; --warn:#e2b04e; --warn-bg:#32291a; --info:#86b3ea; "
            "--info-bg:#1a2636; --crit:#f08b80; --crit-bg:#3a1f1f; --mute:#9ba2ac; --mute-bg:#24262b;",
}
SANS = "'Helvetica Neue',Helvetica,Arial,'Liberation Sans',sans-serif"
MONO = "Menlo,Consolas,'Liberation Mono',monospace"
CLASSES = """
.t{fill:var(--ink)} .tq{fill:var(--quiet)} .ta{fill:var(--accent)} .tg{fill:var(--good)}
.tw{fill:var(--warn)} .ti{fill:var(--info)} .tc{fill:var(--crit)} .tm{fill:var(--mute)} .ton{fill:var(--on-accent)}
.bx{fill:var(--paper);stroke:var(--line);stroke-width:1.25} .bxp{fill:var(--panel);stroke:var(--rule);stroke-width:1.25}
.bxa{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.25} .bxg{fill:var(--good-bg);stroke:var(--good);stroke-width:1.25}
.bxw{fill:var(--warn-bg);stroke:var(--warn);stroke-width:1.25} .bxi{fill:var(--info-bg);stroke:var(--info);stroke-width:1.25}
.bxc{fill:var(--crit-bg);stroke:var(--crit);stroke-width:1.25} .bxm{fill:var(--mute-bg);stroke:var(--mute);stroke-width:1.25}
.bxd{fill:var(--paper);stroke:var(--line);stroke-width:1.25;stroke-dasharray:5 4}
.bxz{fill:none;stroke:var(--accent);stroke-width:1.25;stroke-dasharray:6 4}
.ln{stroke:var(--line);stroke-width:1.5;fill:none} .lna{stroke:var(--accent);stroke-width:2.25;fill:none}
.lng{stroke:var(--good);stroke-width:2;fill:none} .lnw{stroke:var(--warn);stroke-width:2;fill:none}
.lnc{stroke:var(--crit);stroke-width:2;fill:none} .lnx{stroke:var(--crit);stroke-width:2;fill:none;stroke-dasharray:4 5}
.lnd{stroke:var(--line);stroke-width:1.25;fill:none;stroke-dasharray:6 5} .lnr{stroke:var(--rule);stroke-width:1;fill:none}
.fa{fill:var(--accent)} .fg{fill:var(--good)} .fl{fill:var(--line)} .fw{fill:var(--warn)} .fi{fill:var(--info)}
.fc{fill:var(--crit)} .fm{fill:var(--mute)} .fp{fill:var(--panel)} .fs{fill:var(--accent-soft)} .fpaper{fill:var(--paper)}
.mono{font-family:%s}
""" % MONO
HEAD = {"ln": "fl", "lna": "fa", "lng": "fg", "lnw": "fw", "lnc": "fc", "lnx": "fc", "lnd": "fl"}

TITLE = 20      # the finding, top left
LABEL = 15      # a box's name
SUB = 15        # the line under the title
BODY = 14       # everything else; never smaller


def n(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def tw(s, size, mono=False, bold=False):
    """Text width estimate for a system sans; generous on purpose."""
    if mono:
        return len(s) * size * 0.62
    w = 0.0
    for c in s:
        if c in "il.,:;|!'`·1 ":
            w += 0.30
        elif c in "ft()[]/-":
            w += 0.37
        elif c in "mwMW@%":
            w += 0.88
        elif c.isupper() or c in "0123456789≤≥→←":
            w += 0.66
        else:
            w += 0.56
    return w * size * (1.07 if bold else 1.0)


def wrap(s, width, size, mono=False, bold=False):
    out, line = [], ""
    for word in s.split(" "):
        t = word if not line else line + " " + word
        if tw(t, size, mono, bold) <= width or not line:
            line = t
        else:
            out.append(line)
            line = word
    if line:
        out.append(line)
    return out


class Fig:
    def __init__(self, w, h, title, alt):
        self.w, self.h, self.alt, self.parts = w, h, alt, []
        self.text(24, 38, title, TITLE, bold=True, role="title")

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=BODY, cls="t", anchor="start", bold=False, mono=False, role=None):
        if not mono and size < 13:
            raise SystemExit("text under 13 units: %r" % s)
        a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
        b = ' font-weight="700"' if bold else ""
        r = ' data-role="%s"' % role if role else ""
        c = cls + (" mono" if mono else "")
        self.add('<text x="%s" y="%s" class="%s" font-size="%s"%s%s%s>%s</text>'
                 % (n(x), n(y), c, n(size), a, b, r, escape(s)))

    def sub(self, s):
        """The line under the title."""
        if tw(s, SUB) > self.w - 48:
            raise SystemExit("subtitle too long: %r" % s)
        self.text(24, 66, s, SUB, "tq")

    def lines(self, x, y, rows, size=BODY, lead=1.45, **kw):
        for i, r in enumerate(rows):
            self.text(x, y + i * size * lead, r, size, **kw)
        return y + len(rows) * size * lead

    def rect(self, x, y, w, h, cls="bx", rx=8):
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" class="%s"/>'
                 % (n(x), n(y), n(w), n(h), n(rx), cls))

    def box(self, x, y, w, h, cls, name, rows=(), name_cls="t", mono_rows=False, pad=14, center=False):
        """A box with a bold name and quiet rows under it."""
        self.rect(x, y, w, h, cls)
        cx = x + w / 2 if center else x + pad
        anc = "middle" if center else "start"
        self.text(cx, y + pad + LABEL * 0.8, name, LABEL, name_cls, anc, bold=True)
        yy = y + pad + LABEL * 0.8 + BODY * 1.5
        for r in rows:
            self.text(cx, yy, r, BODY, "tq", anc, mono=mono_rows)
            yy += BODY * 1.45

    def circle(self, x, y, r, cls):
        self.add('<circle cx="%s" cy="%s" r="%s" class="%s"/>' % (n(x), n(y), n(r), cls))

    def dot(self, x, y, label, cls="fa"):
        """A numbered stage dot, as in every Hello Galaxy figure."""
        self.circle(x, y, 15, cls)
        self.text(x, y + 4.6, str(label), 13, "ton", "middle", bold=True)

    def path(self, d, cls="ln"):
        self.add('<path d="%s" class="%s"/>' % (d, cls))

    def arrow(self, pts, cls="ln", head=True, size=10):
        """A polyline through pts, with a filled head at the last point."""
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        if head:
            dx, dy = x2 - x1, y2 - y1
            L = (dx * dx + dy * dy) ** 0.5 or 1
            ux, uy = dx / L, dy / L
            bx, by = x2 - ux * size, y2 - uy * size
            pts = pts[:-1] + [(bx + ux, by + uy)]
            px, py = -uy * size * 0.5, ux * size * 0.5  # 10 long by 10 wide
            self.add('<path d="M%s %sL%s %sL%s %sz" class="%s"/>'
                     % (n(x2), n(y2), n(bx + px), n(by + py), n(bx - px), n(by - py), HEAD.get(cls, "fl")))
        d = "M" + "L".join("%s %s" % (n(x), n(y)) for x, y in pts)
        self.path(d, cls)

    def tick(self, x, y, cls="fg"):
        """A filled check mark disc."""
        self.circle(x, y, 10, cls)
        self.add('<path d="M%s %sl3.6 3.6l6.4-7.2" style="stroke:var(--paper);stroke-width:2.4;fill:none;'
                 'stroke-linecap:round;stroke-linejoin:round"/>' % (n(x - 5), n(y)))

    def cross(self, x, y, cls="fc"):
        """A filled cross disc."""
        self.circle(x, y, 10, cls)
        self.add('<path d="M%s %sl8 8M%s %sl-8 8" style="stroke:var(--paper);stroke-width:2.4;'
                 'stroke-linecap:round"/>' % (n(x - 4), n(y - 4), n(x + 4), n(y - 4)))

    def render(self, theme):
        style = "svg{%s font-family:%s}%s" % (THEMES[theme], SANS, CLASSES)
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%s" height="%s" '
                'role="img" aria-label="%s"><style>%s</style>\n%s\n</svg>\n'
                % (n(self.w), n(self.h), n(self.w), n(self.h), escape(self.alt, {'"': "&quot;"}),
                   style, "\n".join(self.parts)))


def write_all(figures, here, argv):
    """figures: {name: Fig}. Write <name>-light/-dark.svg, or with --check report drift."""
    check = "--check" in argv
    stale = []
    for name, fig in figures.items():
        for theme in ("light", "dark"):
            path = os.path.join(here, "%s-%s.svg" % (name, theme))
            body = fig.render(theme)
            if check:
                try:
                    with open(path, encoding="utf-8") as f:
                        if f.read() != body:
                            stale.append(path)
                except FileNotFoundError:
                    stale.append(path)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(body)
                print("wrote", os.path.relpath(path, os.path.dirname(os.path.dirname(here))))
    if check:
        for p in stale:
            print("out of date:", p, file=sys.stderr)
        if stale:
            print("run: python3 -I docs/figures/make-figures.py", file=sys.stderr)
            return 1
        print("figures up to date")
    return 0
# ---- end of the Hello Galaxy figure kit ----


from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
from lib import descriptor, registry  # noqa: E402
from platforms import platform_a, platform_b, platform_c  # noqa: E402

# the pinned times of bin/demo
BEFORE_AT = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
T = "2026-06-12T12:00:00Z"
NOW = datetime(2026, 6, 18, 0, 0, tzinfo=timezone.utc)
E = datetime(2026, 6, 5, 9, 0, tzinfo=timezone.utc)


def org(urn):
    return urn.split("org=")[-1] if urn else "none"


def run():
    before = registry.seed_before()
    after = registry.retask(before, registry.CONDOR, at=T)
    if descriptor.uuid(after) != descriptor.uuid(before):
        raise SystemExit("one-record: the reorg changed the uuid; the figure's claim no longer holds")
    out = {"uuid": descriptor.uuid(after), "alias": after["attributes"].get("alias", "raven-03"),
           "old": org(descriptor.resolve_parent(before, as_of=BEFORE_AT)),
           "new": org(descriptor.resolve_parent(after, as_of=NOW)),
           "audit": org(descriptor.resolve_parent(after, as_of=E)), "rows": []}
    for d, t in ((before, BEFORE_AT), (after, NOW)):
        out["rows"].append([platform_a.decision(d, t), platform_b.authorize(d, "sensor-feeds", t),
                            platform_c.releasable(d, t)])
    return out


def cell(res, uuid):
    """The decision in a few words, taken from the platform's own result line."""
    r = res["result"]
    if r.startswith("write-namespace "):
        return "write " + r.split(" ", 1)[1].replace(uuid, uuid[:8] + "…")
    if "as role " in r:
        return r.split("as role ", 1)[1]
    if r.startswith("releasable"):
        return "releasable: " + r.split("): ", 1)[1].split(" ")[0]
    raise SystemExit("one-record: unknown result line %r" % r)


def fig_one_record():
    D = run()
    names = ["A: Zenoh fabric", "B: analytics service", "C: partner C2"]
    rows = []
    for i in range(3):
        b, a = D["rows"][0][i], D["rows"][1][i]
        rows.append((names[i], b["binds_to"], cell(b, D["uuid"]), cell(a, D["uuid"]), cell(b, D["uuid"]) != cell(a, D["uuid"])))
    flipped = [r[0][3:] for r in rows if r[4]]
    f = Fig(880, 448, "A reorg is a registry edit: the identity stays, one platform's answer changes",
            "One identity record for %s (uuid %s…) is read by three platforms. Its parent moves from %s "
            "to %s by a registry edit, with no new certificate. The uuid does not change; the Zenoh "
            "fabric's write namespace and the analytics service's role decision stay the same; the "
            "partner C2's releasability changes from no to YES. Asked about an audit event before the "
            "reorg, the record still answers %s."
            % (D["alias"], D["uuid"][:8], D["old"], D["new"], D["audit"]))
    f.sub("python3 bin/demo: one record, three platforms that share nothing else, "
                   "one reorg.")

    # the record
    RX, RY, RW, RH = 20, 98, 284, 330
    f.rect(RX, RY, RW, RH, "bxp", rx=12)
    f.text(RX + 16, RY + 28, D["alias"] + ".descriptor.json", BODY, "t", bold=True, mono=True)
    f.rect(RX + 16, RY + 46, RW - 32, 84, "bx")
    f.text(RX + 30, RY + 72, "spine", LABEL, "t", bold=True)
    f.text(RX + 82, RY + 72, "born-as, in the cert", BODY, "tq")
    f.text(RX + 30, RY + 96, "uuid " + D["uuid"][:8] + "…", BODY, "t", mono=True)
    f.text(RX + 30, RY + 117, "never changes", BODY, "tg")
    f.rect(RX + 16, RY + 144, RW - 32, 160, "bx")
    f.text(RX + 30, RY + 170, "edges", LABEL, "t", bold=True)
    f.text(RX + 84, RY + 170, "currently-is, registry", BODY, "tq")
    f.text(RX + 30, RY + 196, "parent " + D["old"], BODY, "tq", mono=True)
    f.text(RX + 30, RY + 216, "closed at T", BODY, "tq")
    f.text(RX + 30, RY + 248, "parent " + D["new"], BODY, "ta", bold=True, mono=True)
    f.text(RX + 30, RY + 268, "open from T", BODY, "tq")
    f.text(RX + 30, RY + 290, "T: a registry edit, no new cert", BODY, "t")

    # the three platforms, before and after
    TX, TR = RX + RW + 24, 860
    cols = [(TX + 14, "platform"), (TX + 210, "before T"), (TX + 380, "after T")]
    hy = RY + 18
    for x, h in cols:
        f.text(x, hy, h, BODY, "tq", bold=True)
    y = hy + 14
    for name, reads, b, a, changed in rows:
        f.rect(TX, y, TR - TX, 66, "bxw" if changed else "bx")
        f.text(cols[0][0], y + 27, name, BODY, "t", bold=True)
        f.text(cols[0][0], y + 49, "reads " + reads, BODY, "tq")
        f.text(cols[1][0], y + 27, b, BODY, "t")
        f.text(cols[2][0], y + 27, a, BODY, "tw" if changed else "t", bold=changed)
        f.text(cols[2][0], y + 49, "changed" if changed else "unchanged", BODY, "tw" if changed else "tg")
        y += 76
    # the audit question
    f.rect(TX, y, TR - TX, RY + RH - y, "bxa")
    f.text(cols[0][0], y + 28, "Who was the parent at an audit event before T?", BODY, "t", bold=True)
    f.text(cols[0][0], y + 50, "The same record answers " + D["audit"] + ", not the current parent.", BODY, "tq")
    if flipped != ["partner C2"]:
        raise SystemExit("one-record: the platforms that change are now %s" % flipped)
    return f


def main(argv):
    return write_all({"one-record": fig_one_record()}, HERE, argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

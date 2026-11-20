# Figures

`make-figures.py` draws every figure in this directory from the tree. Nothing in
a figure is typed by hand. Each figure is written in a light and a dark variant
for a `<picture>` element; each SVG holds its own colors and uses system fonts.

```sh
python3 -I docs/figures/make-figures.py           # write the SVG files
python3 -I docs/figures/make-figures.py --check   # exit 1 if a committed file is out of date
```

| Figure | Shows | Data |
|---|---|---|
| `one-record` | one descriptor read by three platforms across one reorg: the spine that stays, the edge that moves, each platform's decision before and after, and the as-of answer for an audit event | computed with `lib/` and `platforms/` at the pinned times of `bin/demo` |

The drawing code at the top of `make-figures.py` is shared by the Hello Galaxy
series, so the figures of every repository in it read alike. Text is at least
13 units on an 880-unit canvas. Both variants were rendered in headless Chromium
as an `<img>` at 830 px and 400 px wide and inspected.

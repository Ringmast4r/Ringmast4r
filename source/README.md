# How the profile page is made

Everything the page shows in `../assets/` is built by the scripts here. Nothing is drawn by hand.

| File | What it does |
|:--|:--|
| `hero.html`, `hero.js` | The 3D top hat (three.js r180 in `vendor/`): black velvet crown and brim, three red satin bands edged with three-strand gold rope, gold skull studs, a gold fringe, turning under a spotlight. Proportions measured from the brand photo of the hat. |
| `render_hero.py`, `type.html` | Renders the 120-frame loop in headless Chromium (Playwright), adds the stage, the floor reflection and the name, writes `../assets/hero.webp`. |
| `prep_tiles.py` | Lists the public repositories that are not forks (not this one), by stars, and gathers each tile's picture into `media/` and its text into `tiles.json`. Pictures are only ones the repo's own README already shows, or its public live page. |
| `tiles.html`, `capture_tiles.py` | One tile per project (every repo is its own act), the footer and the marquee; writes `../assets/tiles/`, `../assets/foot.webp`, `../assets/marquee.webp`, and the tiles into `../README.md` between the `ACTS` markers. |

The repo list in the fold-out under the acts, the language badges and the profile cards are kept
up to date by the workflows in `../.github/` on their own.

## Rebuild

```sh
cd source
py -3.13 prep_tiles.py              # after a repo is added, renamed or made public (--fresh retakes pictures)
py -3.13 capture_tiles.py           # tiles, footer, marquee, README block
py -3.13 render_hero.py --stills 0 0.3 0.6   # only if the hat changes: look first (frames/)
py -3.13 render_hero.py --frames 120         # a few minutes: run it in the background
```

Needs Python 3.13 with Playwright (Chromium installed) and Pillow, and `gh` signed in.

"""Make one tile per project (../assets/tiles/<repo>.webp) and the footer (../assets/foot.webp), then
write the tiles into ../README.md between <!-- ACTS:START --> and <!-- ACTS:END -->.

Reads tiles.json (made by prep_tiles.py). Two tiles per row on the page, each linked to its repo.
Transparent page background, so the rounded corners stay rounded on GitHub's light theme too.
Served through Playwright routing from this folder; fonts come from Google Fonts at build time.

  py -3.13 capture_tiles.py
"""
import io
import json
import mimetypes
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "tiles"
ORIGIN = "https://rm-tiles.invalid"
USER = "Ringmast4r"


def readme_block(tiles):
    rows = []
    for i in range(0, len(tiles), 2):
        pair = tiles[i:i + 2]
        cells = [f'<a href="https://github.com/{USER}/{t["repo"]}"><img src="assets/tiles/{t["repo"]}.webp" width="49%" '
                 f'alt="Act {i + k + 1:02d}: {t["repo"]}. {t["desc"].replace(chr(34), "")}"></a>' for k, t in enumerate(pair)]
        rows.append('<p align="center">\n' + "\n".join(cells) + "\n</p>")
    return "\n\n".join(rows) + "\n"


def main():
    tiles = json.loads((HERE / "tiles.json").read_text(encoding="utf-8"))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1360, "height": 900}, device_scale_factor=2)

        def serve(route):
            rel = route.request.url[len(ORIGIN):].split("?")[0].lstrip("/") or "tiles.html"
            f = (HERE / rel).resolve()
            if HERE not in f.parents or not f.is_file():
                return route.fulfill(status=404, body="")
            route.fulfill(status=200, body=f.read_bytes(),
                          headers={"content-type": mimetypes.guess_type(f.name)[0] or "application/octet-stream"})

        pg.route(ORIGIN + "/**", serve)
        pg.goto(ORIGIN + "/tiles.html")
        pg.add_style_tag(content="body{background:transparent!important}")
        pg.evaluate("t => { window.TILES = t; build(); }", tiles)
        pg.wait_for_function("document.fonts.check('800 44px \"Big Shoulders Display\"') && document.fonts.check('500 12px \"DM Mono\"') "
                             "&& document.fonts.check('700 34px \"Cinzel Decorative\"') && [...document.images].every(i => i.complete && i.naturalWidth)", timeout=90000)
        pg.evaluate("fit()")
        OUT.mkdir(parents=True, exist_ok=True)
        for t in tiles:
            png = pg.locator(f'[id="tile-{t["repo"]}"]').screenshot(omit_background=True)
            Image.open(io.BytesIO(png)).save(OUT / f"{t['repo']}.webp", quality=86, method=6)
        print(len(tiles), "tiles", sum(f.stat().st_size for f in OUT.glob("*.webp")) // 1024, "KB")
        png = pg.locator("#foot").screenshot(omit_background=True)
        Image.open(io.BytesIO(png)).save(ROOT / "assets" / "foot.webp", quality=90, method=6)
        # the marquee over the acts: bulbs chasing round the border, three frames on a loop
        mq = b.new_page(viewport={"width": 1240, "height": 300}, device_scale_factor=2)
        mq.route(ORIGIN + "/**", serve)
        mq.goto(ORIGIN + "/marquee.html")
        mq.evaluate(f"setCount({len(tiles)})")
        mq.wait_for_function("document.fonts.check('700 76px \"Cinzel Decorative\"') && document.fonts.check('500 14px \"DM Mono\"')", timeout=60000)
        frames = []
        for i in range(3):
            mq.evaluate(f"frame({i})")
            frames.append(Image.open(io.BytesIO(mq.locator("#sign").screenshot(omit_background=True))).convert("RGBA"))
        frames[0].save(ROOT / "assets" / "marquee.webp", save_all=True, append_images=frames[1:], duration=160, loop=0, quality=88, method=6)
        print("marquee", (ROOT / "assets" / "marquee.webp").stat().st_size // 1024, "KB")
        b.close()
    keep = {f"{t['repo']}.webp" for t in tiles}
    for f in OUT.glob("*.webp"):
        if f.name not in keep:
            f.unlink(); print("removed old tile", f.name)
    readme = ROOT / "README.md"
    src = readme.read_text(encoding="utf-8")
    a, z = "<!-- ACTS:START -->", "<!-- ACTS:END -->"
    if src.count(a) == 1 and src.count(z) == 1:
        head, rest = src.split(a); _, tail = rest.split(z)
        readme.write_text(f"{head}{a}\n{readme_block(tiles)}{z}{tail}", encoding="utf-8", newline="\n")
        print("README acts block written")
    else:
        print("README has no ACTS markers yet; block not written")


if __name__ == "__main__":
    main()

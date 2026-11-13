"""Render the Ringmast4r README hero: the top hat turning under a spotlight.

  py -3.13 render_hero.py --stills 0 0.2 0.5 0.75   # test stills -> frames/still-*.png
  py -3.13 render_hero.py --frames 120              # full loop -> ../assets/hero.webp (4 s)

The scene (hero.html / hero.js) is served to headless Chromium through Playwright's request routing
from this folder (no local server). Each frame is rendered at 2x and downsampled, in two layers: the
hat, and the fx (ring curb, signal rings, dust). They are laid over a black stage with a spotlight
beam, with the hat's reflection on the floor, then the type goes on top (type.html: the name in
Cinzel Decorative, as on ringmast4r.com's circus pages, and the tagline in DM Mono). Encoding 120
frames at WebP method 6 takes a few minutes: run it in the background, at low priority.
"""
import argparse
import base64
import io
import mimetypes
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
OUT_W, OUT_H = 1200, 640
SS = 2
ORIGIN = "https://rm-hero.invalid"
RED = np.array((204, 0, 0), np.float32)
WARM = np.array((255, 236, 210), np.float32)


def serve_from(page):
    def serve(route):
        rel = route.request.url[len(ORIGIN):].split("?")[0].lstrip("/") or "hero.html"
        f = (HERE / rel).resolve()
        if HERE not in f.parents or not f.is_file():
            return route.fulfill(status=404, body="")
        route.fulfill(status=200, body=f.read_bytes(),
                      headers={"content-type": mimetypes.guess_type(f.name)[0] or "application/octet-stream"})
    page.route(ORIGIN + "/**", serve)


def type_layer(browser):
    pg = browser.new_page(viewport={"width": OUT_W, "height": OUT_H}, device_scale_factor=SS)
    serve_from(pg)
    pg.goto(f"{ORIGIN}/type.html")
    pg.wait_for_function("document.fonts.ready.then(() => document.fonts.check('700 40px \"Cinzel Decorative\"') && document.fonts.check('500 13px \"DM Mono\"'))", timeout=60000)
    png = pg.screenshot(omit_background=True)
    pg.close()
    return Image.open(io.BytesIO(png)).convert("RGBA").resize((OUT_W, OUT_H), Image.LANCZOS)


def backdrop(W, H, floor):
    """Black stage: a red glow behind the hat, a soft spotlight beam from above, a pool of light on the floor."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.empty((H, W, 3), np.float32); base[:] = (4, 3, 3)
    d = np.hypot((x - W / 2) / (W * 0.34), (y - H * 0.40) / (H * 0.52))
    base += (np.clip(1 - d, 0, 1) ** 2)[..., None] * RED * 0.32
    # the beam: widens from the top of the frame down to the floor, brightest in the middle
    half = W * 0.11 + (W * 0.20) * np.clip(y / floor, 0, 1.2)
    beam = np.clip(1 - np.abs(x - W / 2) / half, 0, 1) ** 1.6 * np.clip(1.15 - y / (floor * 1.25), 0, 1)
    base += beam[..., None] * WARM * 0.075
    pool = np.exp(-(((x - W / 2) / (W * 0.30)) ** 2 + ((y - floor) / (H * 0.05)) ** 2))
    base += pool[..., None] * WARM * 0.10
    e = np.hypot((x - W / 2) / (W * 0.62), (y - H / 2) / (H * 0.80))
    base *= np.clip(1.25 - e * 0.55, 0.35, 1)[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")


def reflection(hat, floor):
    """The hat mirrored about the floor line, fading out with distance and slightly soft."""
    W, H = hat.size
    f = int(round(floor))
    top = hat.crop((0, max(0, 2 * f - H), W, f)).transpose(Image.FLIP_TOP_BOTTOM)
    a = np.array(top).astype(np.float32)
    k = np.arange(a.shape[0], dtype=np.float32)
    a[:, :, 3] *= (0.30 * np.clip(1 - k / (H * 0.14), 0, 1) ** 1.6)[:, None]
    refl = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.8))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(refl, (0, f))
    return out


def open_scene(p):
    browser = p.chromium.launch(args=["--use-angle=d3d11", "--ignore-gpu-blocklist", "--enable-gpu-rasterization"])
    page = browser.new_page(viewport={"width": OUT_W, "height": OUT_H})
    serve_from(page)
    page.goto(f"{ORIGIN}/hero.html?w={OUT_W * SS}&h={OUT_H * SS}")
    page.wait_for_function("document.body.dataset.ready === '1' || !!document.body.dataset.error", timeout=180000)
    err = page.evaluate("document.body.dataset.error || ''")
    if err:
        raise SystemExit("page error: " + err)
    print("GPU:", page.evaluate("glInfo()"))
    return browser, page


def layer(page, phase, name):
    url = page.evaluate(f"renderFrame({phase}, '{name}')")
    im = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGBA")
    return im.resize((OUT_W, OUT_H), Image.LANCZOS)


class Composer:
    def __init__(self, page, typ):
        self.page, self.typ = page, typ
        self.floor = page.evaluate("floorY()") / SS
        self.back = backdrop(OUT_W, OUT_H, self.floor)

    def frame(self, phase):
        hat = layer(self.page, phase, "hat")
        fx = layer(self.page, phase, "fx")
        out = self.back.copy()
        out.alpha_composite(reflection(hat, self.floor))
        out.alpha_composite(hat)
        out.alpha_composite(fx)
        out.alpha_composite(self.typ)
        return out.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", nargs="*", type=float)
    ap.add_argument("--frames", type=int)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    out_frames = HERE / "frames"; out_frames.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser, page = open_scene(p)
        comp = Composer(page, type_layer(browser))
        if a.stills:
            for ph in a.stills:
                comp.frame(ph).save(out_frames / f"still-{ph:.3f}.png")
                print("still", ph, flush=True)
        if a.frames:
            frames = []
            for i in range(a.frames):
                frames.append(comp.frame(i / a.frames))
                if i % 10 == 0:
                    print("frame", i, flush=True)
            browser.close()
            ASSETS.mkdir(parents=True, exist_ok=True)
            frames[0].save(ASSETS / "hero.webp", save_all=True, append_images=frames[1:],
                           duration=round(1000 / a.fps), loop=0, quality=82, method=6)
            print("wrote", ASSETS / "hero.webp", (ASSETS / "hero.webp").stat().st_size // 1024, "KB")
            return
        browser.close()


if __name__ == "__main__":
    main()

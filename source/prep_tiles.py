"""Gather what every project tile shows into tiles.json and media/ (build inputs for capture_tiles.py).

  py -3.13 prep_tiles.py            # needs `gh` signed in; reads public repos only
  py -3.13 prep_tiles.py --fresh    # also retake every picture (otherwise media/ is reused)

One tile per public repository of Ringmast4r that is not a fork (forks are other people's tools: they
stay in the repo list, not on a tile) and not this profile repo. Order = stars, most first. Each tile's
picture, in this order of preference:
  1. PICTURES below: an image the repo's own README already shows, or its public live page;
  2. TERMINAL: the first shell block in the repo's README, shown as a terminal window;
  3. a headline number taken from the repo's description (336K+, 18,110 ...) or its initials.
Nothing private is read: the repo list is the public one and every picture is already public.
Skipped on purpose: film and TV stills and other people's artwork in READMEs, photos of real people,
and screenshots that show this owner's location.
"""
import base64
import io
import json
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
MEDIA = HERE / "media"
USER = "Ringmast4r"
G = Path(r"D:\01 GITHUB Library")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SKIP = {"Ringmast4r"}

# repo: ("local", path) | ("readme", substring of the image URL in its README) | ("live", url) | ("svg", substring)
PICTURES = {
    "crystal-vault": ("live", "https://ringmast4r.github.io/crystal-vault/"),
    "FLOCK": ("live", "https://ringmast4r.github.io/FLOCK/"),
    "OUI-Master-Database": ("local", G / "OUI-Master-Database" / "OUI Master Database.png"),
    "DEATH_STAR": ("local", G / "DEATH_STAR" / "cmd_b5byTMbUqk.gif"),
    "Global-Data-Center-Map": ("live", "https://data-center-map.com/"),
    "ODINT": ("local", G / "ODINT Github" / "ODINT logo.png"),
    "GNSS": ("live", "https://ringmast4r.github.io/GNSS/"),
    "Epstein": ("svg", "banner.svg"),
    "MAC-SPOOFER": ("local", G / "MAC-SPOOFER" / "docs" / "assets" / "desktop-perspective.png"),
    "PathFinder": ("readme", "dashboard"),
    "surveillance-capabilities-map": ("live", "https://ringmast4r.github.io/surveillance-capabilities-map/"),
    "Surveillance-Industry": ("svg", "banner-readme-header"),
    "DEAD-MANS-TRIGGER": ("local", G / "DEAD-MANS-TRIGGER" / "deadman.png"),
    "NAZIS": ("svg", "title.svg"),
    "Ad-Tech-Surveillance": ("svg", "banner-header"),
    "The-Art-of-War-CLI": ("readme", "artofwar"),
    "PROJECT-159": ("live", "https://ringmast4r.github.io/PROJECT-159/"),
    "Ringmast4r-TV": ("readme", "og-image"),
    "Gods-Eye-Index": ("svg", "logo.svg"),
    "Library-of-Congress-Power-Search": ("local", G / "Library-of-Congress-Power-Search" / "capture.png"),
    "venezuela-vote-tracking-evidence": ("local", G / "venezuela-vote-tracking-evidence" / "assets" / "evidence.png"),
    "Rainmeter": ("local", G / "Rainmeter" / "screenshots" / "nwmodern-processes.png"),
    "Lively-Wallpapers": ("local", G / "Lively-Wallpapers" / "screenshots" / "networks-globe.gif"),
    "OCR-Master-Guide": ("local", G / "OCR-Master-Guide" / "OCR-Master-Guide.png"),
}
# square logos and emblems are shown as a medallion, not inside a browser window
# a headline for a tile with no picture and no command in its README (big word, small line)
BIG = {
    "Huginn-Muninn": ("RAVENS", "crowdsourced device identification"),
    "Iran": ("IRAN", "government infrastructure and media networks"),
    "Cuba": ("CUBA", "an OSINT probe"), "csv-merger": ("N > 1", "CSV files into one mega CSV"),
    "vecert-exposed": ("VECERT", "a Florida LLC, investigated"), "higole": ('5.5"', "industrial tablet mini PC"), "OSINT-VISUALIZER": ("OSINT", "radial charts, client-side search"),
    "Colombia": ("PETRO", "infrastructure mapping, M-19 history"), "fallen-repos": ("DMCA", "repos preserved after takedowns"),
    "website-lists": ("LISTS", "categorized domains for OSINT"),
    "APTs": ("APT", "adversary emulation reference"), "CGPS": ("C++", "sketches for color displays"),
    "Conky": ("CONKY", "Linux desktop widgets"), "agent-city": ("CITY", "Claude Code sessions as an isometric city"),
    "HTML-Viewers": ("6", "offline viewers, one HTML file each"), "viewer-website": ("DnB", "artist site for VIEWER, Guanajuato"),
    "NotClaw": ("LOCAL", "Claude Code on our own rigs"), "Venezuela": ("2026", "US strikes on Venezuela"),
    "FED": ("925+", "intelligence entities, 179 countries"), "CommoditiesTracker": ("65+", "commodities in one HTML file"),
}
EMBLEMS = {"OUI-Master-Database", "ODINT", "Gods-Eye-Index", "OCR-Master-Guide"}
CTX = ssl.create_default_context()
FRESH = "--fresh" in sys.argv   # retake every picture


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def readme(repo):
    d = gh(f"repos/{USER}/{repo}/readme")
    if not d:
        return "", ""
    return base64.b64decode(d["content"]).decode("utf-8", "ignore"), d["download_url"].rsplit("/", 1)[0] + "/"


def readme_image(md, base, needle):
    for m in re.finditer(r'(?:!\[[^\]]*\]\(([^)\s]+)|<img[^>]+src="([^"]+)")', md, re.I):
        src = (m.group(1) or m.group(2)).strip("<>")
        if needle.lower() in src.lower():
            if not src.startswith("http"):
                src = base + src.lstrip("./")
            return src.replace(" ", "%20")
    raise SystemExit(f"no README image matching {needle}")


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-tile-builder"}), context=CTX, timeout=60).read()


def chrome_shot(target, out, w=1440, h=900, wait=15000):
    prof = Path(tempfile.mkdtemp(prefix="rm-tile-"))
    raw = prof / "raw.png"
    try:
        subprocess.run([CHROME, "--headless=new", "--hide-scrollbars", "--mute-audio", "--no-first-run", "--disable-extensions",
                        "--force-device-scale-factor=1", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                        f"--user-data-dir={prof}", f"--window-size={w},{h + 160}", f"--virtual-time-budget={wait}",
                        f"--screenshot={raw}", target], capture_output=True, timeout=150)
        if not raw.exists():
            raise SystemExit(f"no picture from {target}")
        return Image.open(raw).convert("RGB").crop((0, 0, w, h))
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def svg_to_png(svg_bytes):
    tmp = Path(tempfile.mkdtemp(prefix="rm-svg-"))
    try:
        (tmp / "a.svg").write_bytes(svg_bytes)
        page = tmp / "a.html"
        page.write_text('<body style="margin:0;background:#000"><img src="a.svg" style="width:1400px;display:block"></body>', encoding="utf-8")
        im = chrome_shot(page.as_uri(), None, 1400, 900, 3000)
        a = im.convert("L").point(lambda v: 255 if v > 6 else 0)
        box = a.getbbox()
        return im.crop(box) if box else im
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def first_frame(im):
    if getattr(im, "n_frames", 1) > 1:
        im.seek(min(im.n_frames // 3, 40))
    return im.convert("RGB")


def terminal(md):
    """The first shell block in the README, as at most six short lines."""
    for m in re.finditer(r"```(\w*)\r?\n(.*?)```", md.replace("\r\n", "\n"), re.S):
        lang, body = m.group(1).lower(), m.group(2)
        if lang not in ("", "bash", "sh", "shell", "console", "zsh", "powershell", "ps1", "cmd", "bat"):
            continue
        lines = [l.rstrip() for l in body.splitlines() if l.strip() and not l.strip().startswith("#") and not l.rstrip().endswith(("\\", "'"))]
        cmds = [l for l in lines if re.match(r"^\s*(\$ |> )?(git|python3?|py|pip3?|npm|node|npx|sudo|cd|chmod|\./|bash|go|cargo|make|docker|curl|wget|apt|pwsh|powershell|\.\\|start|open)\b", l)]
        if len(cmds) >= 1:
            return [short(re.sub(r"^\s*(\$ |> )", "", l)) for l in cmds[:6]]
    return []


def short(line, n=46):
    """A command cut at a word, so a line never ends mid-word."""
    if len(line) <= n:
        return line
    cut = line[:n].rsplit(" ", 1)[0]
    return (cut if len(cut) > n // 2 else line[:n]) + " \u2026"


def headline(desc):
    m = re.search(r"(\d[\d,.]*\s?[KkMm]?\+?)\s+([A-Za-z][\w-]*(?:\s+[a-z][\w-]*){0,2})", desc or "")
    if m and len(m.group(1).strip()) >= 3:
        return m.group(1).strip(), m.group(2)
    return None


def clean(desc):
    desc = re.sub(r"\s*https?://\S+", "", desc or "").strip()
    return re.sub(r"\s+", " ", desc).replace("\u200b", "")


def main():
    MEDIA.mkdir(exist_ok=True)
    repos = []
    page = 1
    while True:
        batch = gh(f"users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos += batch
        page += 1
    repos = [r for r in repos if not r["fork"] and not r["private"] and r["name"] not in SKIP]
    repos.sort(key=lambda r: (-r["stargazers_count"], r["name"].lower()))
    tiles = []
    for r in repos:
        n = r["name"]
        md, base = readme(n)
        t = {"repo": n, "stars": r["stargazers_count"], "lang": r.get("language") or "", "desc": clean(r.get("description")),
             "demo": (bool(r.get("homepage")) and "github.com/" not in (r.get("homepage") or "")) or n in ("ODINT",), "kind": "", "media": "", "term": [], "big": None}
        spec = PICTURES.get(n)
        cached = MEDIA / f"{n}.jpg"
        if spec and cached.exists() and not FRESH:
            t["kind"], t["media"] = ("emblem" if n in EMBLEMS else "window"), f"media/{n}.jpg"
        elif spec:
            kind, val = spec
            if kind == "local":
                im = first_frame(Image.open(val))
            elif kind == "readme":
                im = first_frame(Image.open(io.BytesIO(fetch(readme_image(md, base, val)))))
            elif kind == "svg":
                im = svg_to_png(fetch(readme_image(md, base, val)))
            else:
                im = chrome_shot(val, None)
            im.thumbnail((1100, 1100), Image.LANCZOS)
            im.save(MEDIA / f"{n}.jpg", quality=88)
            t["kind"], t["media"] = ("emblem" if n in EMBLEMS else "window"), f"media/{n}.jpg"
        else:
            t["term"] = terminal(md)
            if t["term"] and n not in BIG:
                t["kind"] = "terminal"
            else:
                t["kind"], t["big"] = "headline", BIG.get(n) or headline(t["desc"]) or (n[:4].upper(), "")
        print(f"{n:42s} {t['stars']:4d}  {t['kind']:9s} {t['media'] or (t['term'][:1] if t['term'] else t['big'])}", flush=True)
        tiles.append(t)
    (HERE / "tiles.json").write_text(json.dumps(tiles, indent=1, ensure_ascii=False), encoding="utf-8")
    print(len(tiles), "tiles")


if __name__ == "__main__":
    main()

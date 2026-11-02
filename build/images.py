#!/usr/bin/env python3
"""Converts captured original images to optimized WebP for the site (needs Pillow).

    python3 build/images.py

Reads capture/images/* and capture/image-sources.tsv, names files from
content/images.json, and writes assets/img/<name>.webp (max 1200 px, or 1600 px
for hero images), an -800 variant for srcset, and assets/manifest.tsv.
Logos and images flagged keep_png stay PNG to keep transparency.
"""
import hashlib, json, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "capture", "images")
OUT = os.path.join(ROOT, "assets", "img")
names = json.load(open(os.path.join(ROOT, "content", "images.json")))
QUALITY = 81


def stem(fname):
    base = re.sub(r"\.(jpe?g|png|webp|gif)$", "", fname, flags=re.I)
    return re.sub(r"-\d+w$", "", base)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def source_urls():
    p = os.path.join(ROOT, "capture", "image-sources.tsv")
    urls = {}
    if os.path.exists(p):
        rows = open(p, encoding="utf-8-sig").read().splitlines()
        for r in rows[1:]:
            cols = r.split("\t")
            if len(cols) >= 3:
                urls[cols[2]] = cols[1] or cols[0]
    return urls


def save(im, path, png):
    if png:
        im.save(path, "PNG", optimize=True)
    else:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(path, "WEBP", quality=QUALITY, method=6)


def main():
    os.makedirs(OUT, exist_ok=True)
    urls = source_urls()
    seen = {}
    rows = ["source_url\tsource_file\toutput\twidth\theight\tsmall"]
    for f in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, f)
        if not os.path.isfile(p):
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        k = stem(f)
        meta = names.get(k, {})
        if h in seen:
            print(f"duplicate of {seen[h]}: {f}")
            continue
        seen[h] = f
        try:
            im = Image.open(p)
            im.load()
        except Exception as e:
            print(f"skip {f}: {e}")
            continue
        png = bool(meta.get("keep_png"))
        name = meta.get("name") or slug(k)
        maxw = 1600 if meta.get("hero") else 1200
        if png:
            maxw = min(maxw, 600)
        if im.width > maxw:
            im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
        ext = "png" if png else "webp"
        out = f"{name}.{ext}"
        save(im, os.path.join(OUT, out), png)
        small = ""
        if im.width > 800 and not png:
            sm = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
            small = f"{name}-800.{ext}"
            save(sm, os.path.join(OUT, small), png)
        if meta.get("favicon") or name == "truebuilt-construction-group-logo":
            fav = im.copy()
            fav.thumbnail((64, 64))
            fav.save(os.path.join(OUT, "favicon.png"), "PNG", optimize=True)
        rows.append("\t".join([urls.get(f, f), f, out, str(im.width), str(im.height), small]))
        print(f"{f} -> {out} {im.width}x{im.height}")
    open(os.path.join(ROOT, "assets", "manifest.tsv"), "w").write("\n".join(rows) + "\n")


if __name__ == "__main__":
    sys.exit(main())

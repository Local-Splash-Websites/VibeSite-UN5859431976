#!/usr/bin/env python3
"""Static site generator for truebuiltgroupllc.com (stdlib only).

    python3 build/build.py                  # content/ + templates -> public/
    python3 build/build.py --preview FILE   # also write a single-file preview (pages switched by #hash)

Page fragments live in content/pages/<slug>.html. The first line is a
<!--meta {...} --> comment with title and description. Shortcodes:
    {{L:slug}} or {{L:slug#frag}}   internal link
    {{img:<duda file>|alt|classes}} image from assets/manifest.tsv
    {{form:id|eyebrow|heading|text}} lead form band
    {{map}}                          keyless Google map embed
"""
import base64, datetime, html, json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "content")
PUB = os.path.join(ROOT, "public")
ASSETS = os.path.join(ROOT, "assets")
site = json.load(open(os.path.join(C, "site.json")))
images = json.load(open(os.path.join(C, "images.json")))
VERSION = datetime.date.today().strftime("%Y%m%d")
warnings = []


def esc(s):
    return html.escape(s, quote=True)


def stem(fname):
    base = re.sub(r"\.(jpe?g|png|webp|gif)$", "", fname, flags=re.I)
    return re.sub(r"-\d+w$", "", base)


def load_manifest():
    m = {}
    p = os.path.join(ASSETS, "manifest.tsv")
    if os.path.exists(p):
        for line in open(p).read().splitlines()[1:]:
            src_url, src_file, out, w, h, small = line.split("\t")
            m[stem(os.path.basename(src_url))] = dict(out=out, w=int(w), h=int(h), small=small)
    return m


MANIFEST = load_manifest()


def img_tag(key, alt, cls="ph", eager=False, sizes="(max-width: 600px) 100vw, (max-width: 960px) 50vw, 33vw"):
    k = stem(key)
    meta = images.get(k, {})
    alt = alt or meta.get("alt", "")
    m = MANIFEST.get(k)
    if not m:
        warnings.append(f"missing image: {key}")
        return f'<figure class="{cls} missing" data-label="{esc(alt)}"></figure>'
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    srcset = ""
    if m["small"]:
        srcset = f' srcset="/assets/img/{m["small"]} 800w, /assets/img/{m["out"]} {m["w"]}w" sizes="{sizes}"'
    return (f'<figure class="{cls}"><img src="/assets/img/{m["out"]}"{srcset} width="{m["w"]}" height="{m["h"]}" '
            f'{load} decoding="async" alt="{esc(alt)}"></figure>')


def link(target):
    slug, _, frag = target.partition("#")
    path = "/" if slug == "index" else "/" + slug
    return path + ("#" + frag if frag else "")


def form_band(fid, eyebrow, heading, text):
    hours = "".join(f"<dt>{h['days']}</dt><dd>{h['label']}</dd>" for h in site["hours"])
    return f'''<section class="band ink" id="get-in-touch"><div class="wrap split">
<div><p class="eyebrow">{eyebrow}</p><h2>{heading}</h2><p>{text}</p>
<p class="big-phone"><a href="tel:{site["tel"]}">{site["phone"]}</a></p>
<dl class="hours">{hours}</dl></div>
<form class="form" id="{fid}" action="/lead-webhook.php" method="post" novalidate>
<input type="hidden" name="form_id" value="{fid}">
<div class="hp" aria-hidden="true"><label for="{fid}-website">Leave this field empty</label><input id="{fid}-website" name="website" tabindex="-1" autocomplete="off"></div>
<div class="fstep" data-step="1">
<label for="{fid}-name">Full name</label><input id="{fid}-name" name="name" required autocomplete="name">
<label for="{fid}-phone">Phone number</label><input id="{fid}-phone" name="phone" type="tel" required placeholder="+1 555-123-4567" autocomplete="tel">
<label for="{fid}-email">Email</label><input id="{fid}-email" name="email" type="email" required autocomplete="email">
<button type="button" class="btn b next">Next</button></div>
<div class="fstep" data-step="2">
<label for="{fid}-service">Project type</label>
<select id="{fid}-service" name="service"><option>Kitchen remodeling</option><option>Bathroom remodeling</option><option>Basement remodeling</option><option>Room addition</option><option>Whole-home remodeling</option><option>Home restoration</option><option>Garage, deck or fence</option><option>Something else</option></select>
<label for="{fid}-msg">Tell us about your project</label><textarea id="{fid}-msg" name="message" rows="4"></textarea>
<label class="consent" for="{fid}-consent"><input type="checkbox" id="{fid}-consent" name="consent" value="yes" required><span>By checking this box, you agree to our <a href="/privacy-policy">privacy policy</a> and consent to receive SMS messages.</span></label>
<div class="row"><button type="button" class="btn o back">Back</button><button type="submit" class="btn b">Submit Form</button></div></div>
<p class="ferr" role="alert" hidden></p>
<div class="fok" role="status" hidden><h3>We got it.</h3><p>Thank you for contacting us. We'll get back to you as soon as possible.</p></div>
</form></div></section>'''


def map_band():
    q = site["map_query"].replace(" ", "+").replace(",", "%2C")
    return (f'<section class="band alt"><div class="wrap"><p class="eyebrow">Location</p><h2>Based in {site["city"]}, {site["region_name"]}</h2>'
            f'<div class="map"><iframe title="Map of {esc(site["map_query"])}" src="https://maps.google.com/maps?q={q}&amp;z=10&amp;output=embed" '
            f'loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div></div></section>')


def render_body(body):
    first = [True]

    def img_sc(m):
        parts = m.group(1).split("|")
        key, alt, cls = (parts + ["", "ph"])[:3]
        eager = first[0] and "hero" in cls
        first[0] = False
        return img_tag(key, alt, cls, eager)

    body = re.sub(r"\{\{img:([^}]+)\}\}", img_sc, body)
    body = re.sub(r"\{\{form:([^|}]+)\|([^|}]*)\|([^|}]*)\|([^}]*)\}\}", lambda m: form_band(*m.groups()), body)
    body = body.replace("{{map}}", map_band())
    body = re.sub(r"\{\{L:([^}]+)\}\}", lambda m: link(m.group(1)), body)
    return body


def jsonld(slug, title, desc):
    url = site["domain"] + link(slug)
    hrs = [h for h in site["hours"] if "open" in h]
    biz = {
        "@type": "HomeAndConstructionBusiness",
        "@id": site["domain"] + "/#business",
        "name": site["name"],
        "url": site["domain"] + "/",
        "telephone": site["tel"],
        "logo": f'{site["domain"]}/assets/img/{site["logo"]}.png',
        "image": f'{site["domain"]}/assets/img/{site["og_image"]}.png',
        "description": site["mission"],
        "foundingDate": site["founded"],
        "address": {"@type": "PostalAddress", "addressLocality": site["city"], "addressRegion": site["region"], "addressCountry": site["country"]},
        "areaServed": [a["name"] for a in site["areas"]],
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": h["schema_days"], "opens": h["open"], "closes": h["close"]} for h in hrs],
        "paymentAccepted": site["payment"],
        "sameAs": [s["url"] for s in site["social"]],
    }
    page = {"@type": "WebPage", "@id": url, "url": url, "name": title, "description": desc, "isPartOf": {"@id": site["domain"] + "/#business"}}
    return json.dumps({"@context": "https://schema.org", "@graph": [biz, page]}, ensure_ascii=False).replace("</", "<\\/")


def logo_html():
    m = MANIFEST.get(site["logo"]) or MANIFEST.get(next((k for k, v in images.items() if isinstance(v, dict) and v.get("name") == site["logo"]), ""), None)
    if not m:
        return ""
    h = 48
    w = round(m["w"] * h / m["h"])
    return f'<img src="/assets/img/{m["out"]}" width="{w}" height="{h}" alt="" fetchpriority="high">'


def shell_parts():
    hours_short = "".join(f"<dt>{h['short']}</dt><dd>{h['label']}</dd>" for h in site["hours"])
    ql = [("index", "Home"), ("about", "About")] + [(s["slug"], s["name"]) for s in site["services"]] + [("gallery", "Gallery"), ("book-now", "Book Now"), ("contact-us", "Contact Us")]
    return {
        "site_name": esc(site["name"]), "phone": site["phone"], "tel": site["tel"],
        "city_line": f'{site["city"]}, {site["region_name"]}', "mission": esc(site["mission"]),
        "nav_services": "".join(f'<a href="{link(s["slug"])}">{s["name"]}</a>' for s in site["services"]),
        "nav_areas": "".join(f'<a href="{link(a["slug"])}">{a["name"]}</a>' for a in site["areas"]),
        "quick_links": "".join(f'<li><a href="{link(s)}">{n}</a></li>' for s, n in ql),
        "area_links": "".join(f'<li><a href="{link(a["slug"])}">{a["name"]}</a></li>' for a in site["areas"]),
        "hours_short": hours_short,
        "social": " · ".join(f'<a href="{s["url"]}" rel="noopener" target="_blank">{s["name"]}</a>' for s in site["social"]),
        "year": str(datetime.date.today().year), "version": VERSION, "logo": logo_html(),
    }


def read_pages():
    pages = []
    d = os.path.join(C, "pages")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".html"):
            continue
        raw = open(os.path.join(d, f), encoding="utf-8").read()
        m = re.match(r"<!--meta (\{.*?\}) -->\n", raw)
        meta = json.loads(m.group(1))
        pages.append((f[:-5], meta, raw[m.end():]))
    pages.sort(key=lambda p: p[0] != "index")
    return pages


def full_title(slug, t):
    return f'{site["name"]} | {site["city"]}, {site["region"]}' if slug == "index" else f'{t} | {site["name"]}'


def build():
    layout = open(os.path.join(ROOT, "build", "templates", "layout.html"), encoding="utf-8").read()
    shell = shell_parts()
    if os.path.isdir(PUB):
        shutil.rmtree(PUB)
    os.makedirs(PUB)
    # static assets
    for sub in ("css", "js", "fonts", "img"):
        src = os.path.join(ASSETS, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(PUB, "assets", sub))
    static = os.path.join(ROOT, "build", "static")
    for f in os.listdir(static):
        shutil.copy(os.path.join(static, f), os.path.join(PUB, f))

    pages = read_pages()
    out = {}
    for slug, meta, body in pages:
        title = full_title(slug, meta["title"])
        canon = site["domain"] + link(slug)
        vals = dict(shell, title=esc(title), description=esc(meta["description"]), canonical=canon,
                    og_image=f'{site["domain"]}/assets/img/{site["og_image"]}.png', jsonld=jsonld(slug, title, meta["description"]),
                    body=render_body(body), robots="noindex" if meta.get("noindex") else "index, follow")
        doc = re.sub(r"\{\{(\w+)\}\}", lambda m: vals[m.group(1)], layout)
        fname = "index.html" if slug == "index" else slug + ".html"
        open(os.path.join(PUB, fname), "w", encoding="utf-8").write(doc)
        out[slug] = (meta, doc)

    today = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{site['domain']}{link(s)}</loc><lastmod>{today}</lastmod></url>" for s, (m, _) in out.items() if not m.get("noindex"))
    open(os.path.join(PUB, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(PUB, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {site['domain']}/sitemap.xml\n")
    return out


def data_uri(path, mime):
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def preview(path, out):
    """Single-file preview for QA: inlines CSS, JS, fonts and 800px images; pages switch by #slug."""
    css = open(os.path.join(ASSETS, "css", "site.css"), encoding="utf-8").read()
    for f in os.listdir(os.path.join(ASSETS, "fonts")):
        css = css.replace(f"/assets/fonts/{f}", data_uri(os.path.join(ASSETS, "fonts", f), "font/woff2"))
    js = open(os.path.join(ASSETS, "js", "site.js"), encoding="utf-8").read()
    first = out["index"][1]
    header = re.search(r'<a class="skip".*?</header>', first, re.S).group(0)
    footer = re.search(r"<footer.*?</footer>", first, re.S).group(0)
    pages = "".join(f'<div class="page" data-page="{s}">' + re.search(r'<main id="main">(.*)</main>', d, re.S).group(1) + "</div>"
                    for s, (m, d) in out.items() if not m.get("noindex"))
    doc = (f'<title>TrueBuilt Site Preview</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
           f'<style>{css}\n.page{{display:none}}.page.on{{display:block}}</style>\n'
           f'<div class="qa">QA preview of the rebuilt truebuiltgroupllc.com. Forms show their confirmation here but are not sent.</div>\n'
           f'{header}<main id="main">{pages}</main>{footer}\n')

    def inline_img(m):
        f = m.group(1)
        small = re.sub(r"\.(webp|png)$", r"-800.\1", f)
        p = os.path.join(ASSETS, "img", small if os.path.exists(os.path.join(ASSETS, "img", small)) else f)
        mime = "image/png" if p.endswith(".png") else "image/webp"
        return 'src="' + data_uri(p, mime) + '"'

    doc = re.sub(r' srcset="[^"]*" sizes="[^"]*"', "", doc)
    doc = re.sub(r'src="/assets/img/([^"]+)"', inline_img, doc)
    # internal links -> #slug
    slugs = set(out)

    def hl(m):
        p = m.group(1)
        path, _, frag = p.partition("#")
        s = path.strip("/") or "index"
        if s in slugs:
            return f'href="#{frag or s}"'
        return m.group(0)

    doc = re.sub(r'href="(/[^"]*)"', hl, doc)
    doc = doc.replace('href="#index"', 'href="#index"')
    router = '''(function(){var pages=[].slice.call(document.querySelectorAll('.page'));
function show(){var h=decodeURIComponent(location.hash.slice(1))||'index',pg=null;
pages.forEach(function(p){if(p.dataset.page===h)pg=p});
if(pg){pages.forEach(function(p){p.classList.toggle('on',p===pg)});window.scrollTo(0,0);return}
var act=document.querySelector('.page.on')||pages[0];act.classList.add('on');
var t=act.querySelector('#'+CSS.escape(h));if(t)t.scrollIntoView();}
addEventListener('hashchange',show);show();})();'''
    doc += f"<script>window.SITE_PREVIEW=true;{js}\n{router}</script>"
    open(path, "w", encoding="utf-8").write(doc)


if __name__ == "__main__":
    out = build()
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1], out)
    for w in sorted(set(warnings)):
        print("WARNING:", w)
    print(f"built {len(out)} pages -> {PUB}")
    if "--strict" in sys.argv and warnings:
        sys.exit(1)

# truebuiltgroupllc.com

Static rebuild of the TrueBuilt Construction Group, LLC site (previously on Duda), served by Apache with one PHP endpoint for lead forms.

## Layout

| Path | What it is |
|---|---|
| `content/site.json` | Business details: name, phone, hours, service areas, social links, Duda site ID |
| `content/pages/<slug>.html` | Page bodies. First line is `<!--meta {"title","description"} -->`. The slug is the URL path (`rochester--ny.html` → `/rochester--ny`) |
| `content/images.json` | Original Duda image → output file name and alt text |
| `build/build.py` | Stdlib-only generator: `content/` + `build/templates/` → `public/` |
| `build/images.py` | Converts `capture/images/` to WebP in `assets/img/` and writes `assets/manifest.tsv` (needs Pillow) |
| `build/static/` | Copied into `public/` as is: `.htaccess`, `lead-webhook.php` |
| `assets/` | `css/site.css`, `js/site.js`, self-hosted fonts, optimized images |
| `capture/` | Raw HTML and original images captured from the old site, for reference |
| `scripts/` | `setup-server.sh`, `deploy.sh`, `preview.sh` (+ `router.php`) |
| `NOTES.md` | Open questions and anything flagged during the rebuild |

### Page shortcodes

- `{{L:slug}}` / `{{L:slug#anchor}}`: internal link
- `{{img:<original duda file>|alt text|classes}}`: image from the manifest, with width/height, srcset, lazy loading
- `{{form:id|eyebrow|heading|text}}`: lead form band (posts to `/lead-webhook.php`)
- `{{map}}`: keyless Google Maps embed

## Environment variables

See `.env.example`. Put `.env` one level above `public/` on the server (never inside it).

| Variable | Used by | Purpose |
|---|---|---|
| `LEADS_API_URL` | lead-webhook.php | Leads API endpoint (RelevantAds) |
| `LEADS_API_KEY` | lead-webhook.php | Bearer token, if the API needs one |
| `LEADS_SITE_NAME` | lead-webhook.php | `site_name` sent with each lead (Duda site ID `d8e4a61f`) |
| `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`, `DEPLOY_PORT` | deploy.sh | SSH target |
| `DOMAIN`, `CERTBOT_EMAIL` | setup-server.sh | Apache vhost and TLS certificate |
| `PREVIEW_PORT` | preview.sh | Local preview port (default 8080) |

## Build

```sh
python3 build/images.py      # only when images in capture/images change
python3 build/build.py       # writes public/
python3 build/build.py --strict --preview preview.html   # fail on missing images; also write a single-file QA preview
```

## Preview

```sh
scripts/preview.sh           # http://localhost:8080 with the same clean URLs as Apache
```

## Deploy

- **Apache server:** run `scripts/setup-server.sh` once as root, put `.env` at `$DEPLOY_PATH/.env`, then `scripts/deploy.sh` from your machine.
- **Coolify / Docker:** build the `Dockerfile` and set `LEADS_API_URL`, `LEADS_API_KEY`, `LEADS_SITE_NAME` as container environment variables.
- **LS Deploy:** connect the repo in LS Deploy and publish with "+ New site".

## URLs

All original page paths are kept (for example `/rochester--ny`, `/buffalo--ny--usa`). `.htaccess` 301-redirects `*.html`, trailing slashes, and the old Duda service URLs that had no page of their own.

"""AI_101_daily autoposter.

Render stage:   python post.py            (renders next carousel, writes pending.json)
Publish stage:  python post.py --publish  (posts pending.json to Instagram as a carousel)
DRY_RUN=1 skips all network calls.
"""
import json
import os
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
CONTENT = ROOT / "content.json"
HISTORY = ROOT / "history.json"
PENDING = ROOT / "pending.json"
IMAGES = ROOT / "images"

HANDLE = "@ai_101_daily"
W, H = 1080, 1350
MARGIN = 96

PALETTES = [
    {"bg": "#0E1726", "ink": "#EEF2F7", "muted": "#8A9BB3", "accent": "#C6F432", "panel": "#16223A"},
    {"bg": "#141414", "ink": "#F2F0EA", "muted": "#9A958A", "accent": "#4DD8E6", "panel": "#1F1F1F"},
    {"bg": "#1B1330", "ink": "#F1ECFA", "muted": "#A79BC4", "accent": "#FFB547", "panel": "#261B42"},
]

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/dejavu"]


def font(name, size):
    for d in FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def F(size, bold=False, mono=False):
    if mono:
        return font("DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf", size)
    return font("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for w in words:
            test = (line + " " + w).strip()
            if draw.textlength(test, font=fnt) <= width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        lines.append(line)
    return lines


def block(draw, xy, text, fnt, fill, width, spacing=1.35):
    x, y = xy
    lh = int(fnt.size * spacing)
    for ln in wrap(draw, text, fnt, width):
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def frame(pal, day, idx, total):
    img = Image.new("RGB", (W, H), pal["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=pal["accent"])
    d.rectangle([0, H - 14, W, H], fill=pal["accent"])
    d.text((MARGIN, 64), f"AI 101  /  DAY {day:03d}", font=F(26, True, True), fill=pal["accent"])
    d.text((W - MARGIN, 64), f"{idx}/{total}", font=F(26, False, True), fill=pal["muted"], anchor="ra")
    d.text((MARGIN, H - 88), HANDLE, font=F(26, False, True), fill=pal["muted"])
    if idx < total:
        d.text((W - MARGIN, H - 88), "swipe  >", font=F(26, True, True), fill=pal["ink"], anchor="ra")
    return img, d


def section(d, pal, label, y=190):
    d.text((MARGIN, y), label.upper(), font=F(30, True, True), fill=pal["accent"])
    d.rectangle([MARGIN, y + 52, MARGIN + 90, y + 58], fill=pal["accent"])
    return y + 110


def render(post, day, pal):
    tw = W - 2 * MARGIN
    total = 5
    slides = []

    # 1. hook
    img, d = frame(pal, day, 1, total)
    d.text((MARGIN, 300), "What is", font=F(56), fill=pal["muted"])
    size = 150
    while d.textlength(post["term"], font=F(size, True)) > tw and size > 70:
        size -= 6
    y = block(d, (MARGIN, 380), post["term"], F(size, True), pal["ink"], tw, 1.1)
    d.rectangle([MARGIN, y + 30, MARGIN + 160, y + 40], fill=pal["accent"])
    block(d, (MARGIN, y + 90), post["hook"], F(46), pal["ink"], tw)
    slides.append(img)

    # 2. definition
    img, d = frame(pal, day, 2, total)
    y = section(d, pal, "In one line")
    block(d, (MARGIN, y), post["what"], F(52, True), pal["ink"], tw)
    slides.append(img)

    # 3. analogy
    img, d = frame(pal, day, 3, total)
    y = section(d, pal, "Think of it like")
    d.rounded_rectangle([MARGIN - 20, y - 20, W - MARGIN + 20, H - 200], 28, fill=pal["panel"])
    block(d, (MARGIN + 20, y + 30), post["analogy"], F(46), pal["ink"], tw - 40)
    slides.append(img)

    # 4. how it works
    img, d = frame(pal, day, 4, total)
    y = section(d, pal, "How it works")
    for i, step in enumerate(post["how"], 1):
        d.ellipse([MARGIN, y, MARGIN + 72, y + 72], fill=pal["accent"])
        d.text((MARGIN + 36, y + 36), str(i), font=F(38, True, True), fill=pal["bg"], anchor="mm")
        y = block(d, (MARGIN + 110, y + 8), step, F(42), pal["ink"], tw - 110) + 60
    slides.append(img)

    # 5. takeaway
    img, d = frame(pal, day, 5, total)
    y = section(d, pal, "Remember this")
    y = block(d, (MARGIN, y), post["takeaway"], F(60, True), pal["accent"], tw, 1.25)
    d.rectangle([MARGIN, H - 330, W - MARGIN, H - 328], fill=pal["muted"])
    d.text((MARGIN, H - 290), f"Tomorrow: {post.get('next', 'another AI term')}", font=F(36, True), fill=pal["ink"])
    d.text((MARGIN, H - 235), "Follow for one AI idea a day.", font=F(34), fill=pal["muted"])
    slides.append(img)
    return slides


def next_post():
    content = load(CONTENT, [])
    done = {h["id"] for h in load(HISTORY, [])}
    for i, p in enumerate(content):
        if p["id"] not in done:
            return i, p, content
    return None, None, content


def stage_render():
    i, post, content = next_post()
    if post is None:
        sys.exit("Content bank exhausted. Add posts to content.json.")
    if i + 1 < len(content):
        post.setdefault("next", content[i + 1]["term"])
    day = len(load(HISTORY, [])) + 1
    pal = PALETTES[(day - 1) % len(PALETTES)]
    IMAGES.mkdir(exist_ok=True)
    files = []
    for n, img in enumerate(render(post, day, pal), 1):
        name = f"images/{post['id']}_{n}.jpg"
        img.save(ROOT / name, "JPEG", quality=92)
        files.append(name)
    caption = post["caption"] + "\n\n" + " ".join(post["hashtags"])
    PENDING.write_text(json.dumps({"id": post["id"], "term": post["term"], "files": files, "caption": caption}, indent=2))
    print(f"Rendered day {day}: {post['term']} -> {files}")


def api(method, path, **params):
    import requests
    host = os.environ.get("IG_API_HOST", "graph.facebook.com")
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.request(method, f"https://{host}/v21.0/{path}", data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=60)
    if r.status_code >= 400:
        raise SystemExit(f"Graph API error {r.status_code} on {path}: {r.text}")
    return r.json()


def wait_ready(cid):
    for _ in range(30):
        s = api("GET", cid, fields="status_code").get("status_code")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise SystemExit(f"Container {cid} failed")
        time.sleep(5)
    raise SystemExit(f"Container {cid} not ready in time")


def stage_publish():
    pending = load(PENDING, None)
    if not pending:
        sys.exit("No pending.json. Run the render stage first.")
    base = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    urls = [f"{base}/{f}" for f in pending["files"]]
    if os.environ.get("DRY_RUN") == "1":
        print("DRY RUN, would publish:", urls)
        media_id = "dry-run"
    else:
        uid = os.environ["IG_USER_ID"]
        children = []
        for u in urls:
            c = api("POST", f"{uid}/media", image_url=u, is_carousel_item="true")["id"]
            wait_ready(c)
            children.append(c)
        parent = api("POST", f"{uid}/media", media_type="CAROUSEL", children=",".join(children),
                     caption=pending["caption"])["id"]
        wait_ready(parent)
        media_id = api("POST", f"{uid}/media_publish", creation_id=parent)["id"]
    hist = load(HISTORY, [])
    hist.append({"id": pending["id"], "term": pending["term"], "media_id": media_id,
                 "posted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    HISTORY.write_text(json.dumps(hist, indent=2))
    PENDING.unlink()
    print(f"Published {pending['term']} as {media_id}")


if __name__ == "__main__":
    stage_publish() if "--publish" in sys.argv else stage_render()

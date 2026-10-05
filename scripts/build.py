#!/usr/bin/env python3
"""Build các phần động của site Cameramienbac từ data/*.json (CMS ghi) — Python stdlib, không
cần cài gì. Quyết định nghiệp vụ chốt ở ../GAS.md mục VIII; đọc trước khi sửa.

Ghi đè ĐÚNG các vùng nằm giữa 2 mốc `<!-- cms:<tên>:start -->` / `<!-- cms:<tên>:end -->`,
phần còn lại của file giữ nguyên (trang viết tay):
  html/partials/catalog.html          cms:catalog          lưới sản phẩm (/san-pham/ + 8 trang nhóm)
  html/hang-<hãng>/index.html         cms:brand-products   "Sản phẩm tiêu biểu" của hãng
  html/tin-tuc/index.html             cms:news-filter      nút lọc theo danh mục tin
                                      cms:news-list        danh sách tin (CMS + bài viết tay cũ)
  html/index.html                     cms:home-news        3 tin mới nhất ở trang chủ
  html/trung-tam-ai/index.html        cms:ai-news          3 tin chủ đề AI ở trang Trung tâm AI
Sinh mới từ template:
  html/tin-tuc/<slug>/index.html      templates/news-detail.html (mang dấu GENERATED_MARKER)
Sinh toàn bộ (không sửa tay):
  html/sitemap.xml                    mọi trang */index.html, trừ trang noindex + thư mục kỹ thuật
  html/robots.txt                     cho phép tất cả + trỏ tới sitemap

Không tìm thấy mốc = DỪNG build với lỗi rõ ràng (không im lặng bỏ qua — ai đó sửa tay trang mà
lỡ xoá mốc thì CMS sẽ "lưu mà không thấy gì đổi").

Chạy: python3 scripts/build.py   (CI chạy khi data/catalog.json, data/news.json,
data/news-categories.json, data/legacy-news.json, templates/** hoặc file này đổi.)
"""

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "html"
TEMPLATES = ROOT / "templates"

GENERATED_MARKER = "<!-- build.py:generated -->"

# Domain chính thức (Cloudflare). Đổi domain thì sửa đúng 1 dòng này.
SITE_URL = "https://cameramienbac.com.vn"
# Thư mục không phải trang nội dung — không bao giờ vào sitemap.
SITEMAP_SKIP_DIRS = {"admin", "partials", "docs", "vendor", "assets"}

# ---- Danh sách CỐ ĐỊNH — PHẢI KHỚP y hệt hằng số cùng tên trong gas/Code.js ----------------
# (gas/ không nằm trong git nên 2 chỗ không tự đồng bộ: sửa 1 bên thì sửa luôn bên kia.)
PRODUCT_CATEGORIES = [
    ("camera-ai", "Camera AI"),
    ("luu-tru", "NVR & lưu trữ"),
    ("ai-server", "AI Server / AI Box"),
    ("ra-vao", "Kiểm soát ra vào"),
    ("anpr", "Barrier & ANPR"),
    ("iot", "IoT & cảm biến"),
    ("mang", "Thiết bị mạng"),
    ("phan-mem", "Phần mềm"),
]
PRODUCT_APPS = [
    ("an-ninh", "An ninh"),
    ("toa-nha", "Tòa nhà"),
    ("truong-hoc", "Trường học"),
    ("van-phong", "Văn phòng"),
    ("nha-may", "Nhà máy, KCN"),
    ("bai-xe", "Bãi xe"),
    ("do-thi", "Đô thị"),
]
# Thông tin hãng là HARD-CODE (GAS.md mục 0). page = thư mục trang hãng, None = chưa có trang.
BRANDS = [
    ("hikvision", "Hikvision", "hang-hikvision"),
    ("dahua", "Dahua", "hang-dahua"),
    ("axis", "Axis", "hang-axis"),
    ("hanwha", "Hanwha Vision", "hang-hanwha"),
    ("tvt", "TVT", None),
    ("nvidia", "NVIDIA", None),
    ("intel", "Intel", None),
]

CAT_LABEL = dict(PRODUCT_CATEGORIES)
CAT_ORDER = {slug: i for i, (slug, _) in enumerate(PRODUCT_CATEGORIES)}
APP_LABEL = dict(PRODUCT_APPS)
BRAND_LABEL = {slug: label for slug, label, _ in BRANDS}

ARROW_SVG = ('<svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M4 12h15m-6-6 6 6-6 6"/></svg>')
CAL_SVG = ('<svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" '
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<rect x="3.4" y="5" width="17.2" height="15" rx="1.6"/>'
           '<path d="M3.4 9.4h17.2M8 3v3.6M16 3v3.6"/></svg>')
CLOCK_SVG = ('<svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M12 6.8V12l3.4 2"/></svg>')


# ---------------------------------------------------------------------------- helpers

def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def load_json(name, default):
    path = DATA / name
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read(path):
    return path.read_text(encoding="utf-8")


def write_if_changed(path, content):
    """Chỉ ghi khi nội dung đổi — build 2 lần liên tiếp không được sinh diff (idempotent)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and read(path) == content:
        return False
    path.write_text(content, encoding="utf-8")
    print("  ghi", path.relative_to(ROOT))
    return True


def replace_region(content, name, inner, path):
    start = f"<!-- cms:{name}:start -->"
    end = f"<!-- cms:{name}:end -->"
    pattern = re.compile(r"(" + re.escape(start) + r"\n)(.*?)(\n[ \t]*" + re.escape(end) + r")", re.S)
    if not pattern.search(content):
        sys.exit(f"LỖI: không tìm thấy mốc {start} ... {end} trong {path.relative_to(ROOT)} — "
                 "đã có ai sửa tay trang này và xoá mất mốc? Thêm lại mốc rồi build lại.")
    return pattern.sub(lambda m: m.group(1) + inner + m.group(3), content, count=1)


def patch_file(path, regions):
    content = read(path)
    for name, inner in regions:
        content = replace_region(content, name, inner, path)
    write_if_changed(path, content)


def date_display(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else str(iso or "")


def price_display(value):
    try:
        n = int(value or 0)
    except (TypeError, ValueError):
        n = 0
    return f"{n:,}".replace(",", ".") + " ₫" if n > 0 else ""


def contact_query(text):
    """Giá trị ?sp= cho link "Yêu cầu cấu hình" — giữ đúng kiểu cũ (dấu cách -> '+', chữ có dấu
    để nguyên), chỉ mã hoá các ký tự làm vỡ query string."""
    out = str(text)
    for ch, code in (("%", "%25"), ("+", "%2B"), ("&", "%26"), ("#", "%23"), ("?", "%3F"), ("=", "%3D")):
        out = out.replace(ch, code)
    return out.replace(" ", "+")


# ---------------------------------------------------------------------------- sản phẩm

def sort_products(products):
    return sorted(products, key=lambda p: (CAT_ORDER.get(p.get("category"), 99),
                                           int(p.get("order") or 0)))


def product_inner(p, indent, with_filters):
    """1 thẻ .pitem. with_filters=True: bản ở catalog (có data-* cho bộ lọc + 2 hàng chip);
    False: bản ở trang hãng (giống hệt nhưng không có bộ lọc/chip — đúng như 4 trang hãng gốc)."""
    pad = " " * indent
    inner = " " * (indent + 2)
    title = p.get("title", "")
    lines = []
    if with_filters:
        lines.append(f'{pad}<article class="pitem" data-cat="{esc(p.get("category"))}" '
                     f'data-app="{esc(" ".join(p.get("apps") or []))}" '
                     f'data-brand="{esc(" ".join(p.get("brands") or []))}">')
    else:
        lines.append(f'{pad}<article class="pitem">')
    if p.get("image"):
        lines.append(f'{inner}<div class="pitem__media"><img src="/{esc(p["image"])}" '
                     f'alt="{esc(p.get("image_alt") or title)}" loading="lazy" width="320" '
                     f'height="320" decoding="async"></div>')
    lines.append(f'{inner}<p class="pitem__cat">{esc(CAT_LABEL.get(p.get("category"), ""))}</p>')
    lines.append(f'{inner}<h3 class="pitem__title">{esc(title)}</h3>')
    if p.get("description"):
        lines.append(f'{inner}<p class="pitem__text">{esc(p["description"])}</p>')
    price = price_display(p.get("price"))
    if p.get("model"):
        note = f' ({esc(p["model_note"])})' if p.get("model_note") else ""
        lines.append(f'{inner}<p class="pitem__model">Model tiêu biểu: <strong>{esc(p["model"])}'
                     f'</strong>{note}</p>')
    if p.get("model") or price:
        if price:
            lines.append(f'{inner}<p class="pitem__price">{price}</p>')
        else:
            lines.append(f'{inner}<p class="pitem__price pitem__price--contact">Liên hệ báo giá</p>')
    if with_filters:
        apps = "".join(f'<span class="chip chip--app">{esc(APP_LABEL.get(a, a))}</span>'
                       for a in (p.get("apps") or []))
        if apps:
            lines.append(f'{inner}<div class="pitem__row">{apps}</div>')
        brands = "".join(f'<span class="chip">{esc(BRAND_LABEL.get(b, b))}</span>'
                         for b in (p.get("brands") or [])) or '<span class="chip">Theo dự án</span>'
        lines.append(f'{inner}<div class="pitem__row">{brands}</div>')
    cta_url = p.get("cta_url") or f'/lien-he/?sp={contact_query(title)}#tu-van'
    cta_label = p.get("cta_label") or "Yêu cầu cấu hình"
    lines.append(f'{inner}<div class="pitem__foot"><a class="btn btn--solid btn--xs" '
                 f'href="{esc(cta_url)}">{esc(cta_label)} {ARROW_SVG}</a></div>')
    lines.append(f"{pad}</article>")
    return "\n".join(lines)


def build_products(products):
    products = sort_products(products)
    catalog = "\n".join(product_inner(p, 10, True) for p in products)
    patch_file(SITE / "partials" / "catalog.html", [("catalog", catalog)])

    for slug, label, page in BRANDS:
        if not page:
            continue
        path = SITE / page / "index.html"
        if not path.exists():
            print(f"  CẢNH BÁO: thiếu trang hãng {path.relative_to(ROOT)} — bỏ qua")
            continue
        mine = [p for p in products if p.get("model_brand") == slug]
        inner = "\n".join(product_inner(p, 8, False) for p in mine) or (
            '        <p class="psec__lead">Đang cập nhật sản phẩm tiêu biểu của hãng ' + esc(label) +
            ' — <a href="/lien-he/#tu-van">liên hệ</a> để được tư vấn model phù hợp.</p>')
        patch_file(path, [("brand-products", inner)])


# ---------------------------------------------------------------------------- tin tức

def news_items(news, legacy):
    """Gộp bài CMS + bài viết tay cũ thành 1 danh sách thống nhất, mới nhất trước."""
    items = []
    for n in news:
        items.append({
            "title": n.get("title", ""), "url": f'/tin-tuc/{n["slug"]}/',
            "image": n.get("cover", ""), "category": n.get("category", ""),
            "date": n.get("date", ""), "read_min": n.get("read_min") or 1,
            "description": n.get("description", ""), "slug": n["slug"],
        })
    cms_urls = {i["url"] for i in items}
    for n in legacy:
        if n.get("url") in cms_urls:
            continue
        items.append(dict(n, slug=None))
    items.sort(key=lambda i: str(i.get("date") or ""), reverse=True)
    return items


def news_card(item, cat_name, featured):
    url = esc(item["url"])
    cls = "news news--feat" if featured else "news"
    return "\n".join([
        f'        <article class="{cls}">',
        f'          <a class="news__media" href="{url}" tabindex="-1" aria-hidden="true">'
        f'<img src="/{esc(item["image"])}" alt="" loading="lazy" width="1280" height="720" '
        f'decoding="async"><span class="news__tag">{esc(cat_name)}</span></a>',
        '          <div class="news__body">',
        f'            <p class="news__meta"><span>{CAL_SVG}{esc(date_display(item["date"]))}</span>'
        f'<span>{CLOCK_SVG}{esc(item["read_min"])} phút đọc</span></p>',
        f'            <h3 class="news__title"><a href="{url}">{esc(item["title"])}</a></h3>',
        f'            <p class="news__text">{esc(item["description"])}</p>',
        f'            <span class="news__more">Đọc tiếp {ARROW_SVG}</span>',
        '          </div>',
        '        </article>',
    ])


# Chủ đề tin hiện ở khối "Tin tức & sự kiện" trang /trung-tam-ai/ (theo slug danh mục tin).
AI_NEWS_CATEGORIES = {"cong-nghe", "giao-duc", "an-ninh", "giai-phap"}


def news_card_compact(item, cat_name):
    """Thẻ tin dạng gọn của trang /trung-tam-ai/ (chỉ có thời gian đọc, thụt lề sâu hơn 1 cấp)."""
    url = esc(item["url"])
    return "\n".join([
        '          <article class="news">',
        f'            <a class="news__media" href="{url}" tabindex="-1" aria-hidden="true">'
        f'<img src="/{esc(item["image"])}" alt="" loading="lazy" width="1280" height="720" '
        f'decoding="async"><span class="news__tag">{esc(cat_name)}</span></a>',
        '            <div class="news__body">',
        f'              <p class="news__meta"><span>{CLOCK_SVG}{esc(item["read_min"])} phút đọc</span></p>',
        f'              <h3 class="news__title"><a href="{url}">{esc(item["title"])}</a></h3>',
        f'              <p class="news__text">{esc(item["description"])}</p>',
        f'              <span class="news__more">Đọc tiếp {ARROW_SVG}</span>',
        '            </div>',
        '          </article>',
    ])


def build_news(news, legacy, categories):
    cat_name = {c["slug"]: c["name"] for c in categories}
    cats = sorted(categories, key=lambda c: int(c.get("order") or 0))
    items = news_items(news, legacy)

    buttons = "".join(f'<button type="button" data-news-filter="{esc(c["name"])}">{esc(c["name"])}</button>'
                      for c in cats)
    cards = "\n".join(news_card(it, cat_name.get(it["category"], ""), i == 0)
                      for i, it in enumerate(items))
    patch_file(SITE / "tin-tuc" / "index.html",
               [("news-filter", "        " + buttons), ("news-list", cards)])
    # Trang chủ: 3 bài mới nhất, thẻ thường (không có thẻ nổi bật như trang /tin-tuc/).
    home_cards = "\n".join(news_card(it, cat_name.get(it["category"], ""), False) for it in items[:3])
    patch_file(SITE / "index.html", [("home-news", home_cards)])
    # Trang Trung tâm AI: 3 bài mới nhất thuộc các chủ đề gần AI (không đủ thì lấy bài mới nhất).
    ai_items = [it for it in items if it["category"] in AI_NEWS_CATEGORIES]
    ai_items += [it for it in items if it not in ai_items]
    ai_cards = "\n".join(news_card_compact(it, cat_name.get(it["category"], "")) for it in ai_items[:3])
    patch_file(SITE / "trung-tam-ai" / "index.html", [("ai-news", ai_cards)])

    tpl = read(TEMPLATES / "news-detail.html")
    generated = set()
    for meta in news:
        slug = meta["slug"]
        detail_path = DATA / "news" / f"{slug}.json"
        if not detail_path.exists():
            print(f"  CẢNH BÁO: thiếu {detail_path.relative_to(ROOT)} — bỏ qua bài {slug}")
            continue
        post = json.loads(read(detail_path))
        related = [it for it in items if it.get("slug") != slug]
        related.sort(key=lambda it: it.get("category") != post.get("category"))  # cùng danh mục trước
        related_html = "\n".join(
            f'            <li><a href="{esc(it["url"])}"><img src="/{esc(it["image"])}" alt="" loading="lazy" '
            f'width="96" height="64" decoding="async"><span>{esc(it["title"])}</span></a></li>' for it in related[:3])
        mapping = {
            "{{TITLE}}": esc(post.get("title")),
            "{{DESCRIPTION}}": esc(post.get("description")),
            "{{CATEGORY}}": esc(cat_name.get(post.get("category"), "")),
            "{{DATE}}": esc(date_display(post.get("date"))),
            "{{READ_MIN}}": esc(post.get("read_min") or 1),
            "{{COVER}}": esc(post.get("cover")),
            "{{COVER_ALT}}": esc(post.get("cover_alt") or post.get("title")),
            "{{RELATED}}": related_html,
            # Nội dung là HTML do CMS soạn — chèn nguyên văn, đã thêm lazy cho ảnh.
            "{{CONTENT}}": lazy_images(post.get("content_html") or ""),
        }
        out = tpl
        for key, value in mapping.items():
            out = out.replace(key, value)
        out = inject_smart_assets(out)
        # Gắn khối SEO ngay lúc render (không đợi bước sitemap) để file chỉ ghi khi thật sự đổi.
        out = with_seo(out, f"{SITE_URL}/tin-tuc/{slug}/", meta)
        write_if_changed(SITE / "tin-tuc" / slug / "index.html", out)
        generated.add(slug)
    clean_orphan_news(generated)


def inject_smart_assets(page):
    """Bài Smart content (thân bài có khối class="tv-...") -> nạp CSS/JS khối. Bài thường không
    nạp gì thêm, output giữ nguyên như trước khi có tính năng này."""
    if 'class="tv-' not in page:
        return page
    page = page.replace("</head>", '<link rel="stylesheet" href="/assets/css/smart.css">\n</head>', 1)
    return page.replace("</body>", '<script src="/assets/js/smart.js" defer></script>\n</body>', 1)


def lazy_images(content):
    return re.sub(r"<img(?![^>]*\bloading=)", '<img loading="lazy" decoding="async"', content)


def clean_orphan_news(keep):
    """Xoá trang tin đã bị xoá khỏi CMS. CHỈ đụng thư mục con của html/tin-tuc/ có index.html
    mang GENERATED_MARKER — trang viết tay (không có dấu) không bao giờ bị xoá."""
    for page in (SITE / "tin-tuc").glob("*/index.html"):
        slug = page.parent.name
        if slug in keep:
            continue
        if GENERATED_MARKER not in read(page):
            continue
        shutil.rmtree(page.parent)
        print("  xoá trang mồ côi", page.parent.relative_to(ROOT))


# ---------------------------------------------------------------------------- sitemap + robots

def page_url(index_path):
    rel = index_path.parent.relative_to(SITE).as_posix()
    return SITE_URL + "/" if rel == "." else f"{SITE_URL}/{rel}/"


def is_noindex(content):
    m = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', content, re.I)
    return bool(m and "noindex" in m.group(1).lower())


# ---- Thông tin doanh nghiệp cho JSON-LD — lấy đúng như footer/trang Liên hệ. ----
ORG = {
    "name": "Cameramienbac",
    "legal_name": "Công ty Cổ phần Thương mại và Truyền thông Doanh Nhân Việt",
    "description": "Camera AI & giải pháp an ninh thông minh cho doanh nghiệp, trường học và tòa nhà.",
    "telephone": "+84979406868",
    "email": "cameramienbac@cmvn.vn",
    "street": "15 ngõ 36 Hoàng Quốc Việt",
    "district": "Cầu Giấy",
    "city": "Hà Nội",
    "logo": "/assets/images/logo-full.png",
    "default_image": "/assets/images/hero-bg.webp",
}
# Loại WebPage theo trang (mặc định "WebPage").
PAGE_TYPES = {"tin-tuc": "CollectionPage", "san-pham": "CollectionPage", "du-an": "CollectionPage",
              "lien-he": "ContactPage", "ve-chung-toi": "AboutPage", "cau-hoi-thuong-gap": "FAQPage"}

SEO_BLOCK_RE = re.compile(r"[ \t]*<!-- seo:start -->.*?<!-- seo:end -->\n?", re.S)
CANONICAL_RE = re.compile(r'[ \t]*<link\s+rel="canonical"\s+href="[^"]*"\s*/?>\n?', re.I)


def abs_url(path):
    return path if path.startswith("http") else SITE_URL + "/" + path.lstrip("/")


def strip_tags(text):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))).strip()


def head_text(content, pattern):
    m = re.search(pattern, content, re.S | re.I)
    return html.unescape(m.group(1)).strip() if m else ""


def page_image(content):
    """Ảnh đại diện khi chia sẻ: ảnh hero desktop đang preload của trang, không có thì ảnh mặc định."""
    m = re.search(r'<link rel="preload" as="image" href="([^"]+)" media="\(min-width', content)
    return abs_url(m.group(1) if m else ORG["default_image"])


def breadcrumb_items(content, url, title):
    """Lấy từ breadcrumb hiển thị (.phero__crumbs) nếu có; không có thì Trang chủ > tên trang."""
    items = []
    m = re.search(r'<nav class="phero__crumbs"[^>]*>(.*?)</nav>', content, re.S)
    if m:
        for href, label in re.findall(r'<a href="([^"]+)">(.*?)</a>', m.group(1)):
            items.append((strip_tags(label), abs_url(href)))
        last = re.findall(r"<span>(.*?)</span>", m.group(1))
        if last:
            items.append((strip_tags(last[-1]), url))
    else:
        items = [("Trang chủ", SITE_URL + "/"), (title, url)]
    # Tên cuối "Bài viết" chung chung -> dùng tiêu đề thật cho Google hiển thị đẹp.
    if items and items[-1][0] in ("Bài viết", ""):
        items[-1] = (title, url)
    return [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]


def faq_entities(content):
    out = []
    for q, a in re.findall(r"<details><summary>(.*?)</summary><div class=\"faq__a\">(.*?)</div></details>", content, re.S):
        out.append({"@type": "Question", "name": strip_tags(q),
                    "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}})
    return out


def org_node():
    return {
        "@type": "LocalBusiness", "@id": SITE_URL + "/#organization",
        "name": ORG["name"], "legalName": ORG["legal_name"], "description": ORG["description"],
        "url": SITE_URL + "/", "logo": abs_url(ORG["logo"]), "image": abs_url(ORG["default_image"]),
        "telephone": ORG["telephone"], "email": ORG["email"],
        "address": {"@type": "PostalAddress", "streetAddress": ORG["street"],
                    "addressLocality": ORG["district"], "addressRegion": ORG["city"], "addressCountry": "VN"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                                       "opens": "08:00", "closes": "17:30"}],
        "contactPoint": [{"@type": "ContactPoint", "telephone": ORG["telephone"], "email": ORG["email"],
                          "contactType": "customer service", "areaServed": "VN", "availableLanguage": ["vi"]}],
    }


def seo_block(content, url, article=None):
    """Khối SEO trong <head>: canonical + robots + Open Graph + Twitter + JSON-LD (@graph).
    article = bản ghi tin tức (data/news.json) nếu là trang bài viết."""
    title = head_text(content, r"<title>(.*?)</title>")
    desc = head_text(content, r'<meta name="description" content="([^"]*)"')
    h1 = strip_tags(head_text(content, r'<h1[^>]*>(.*?)(?:<span|</h1>)')) or title.split(" — ")[0]
    image = abs_url(article["cover"]) if article else page_image(content)
    is_home = url == SITE_URL + "/"

    tags = [
        f'<link rel="canonical" href="{esc(url)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        f'<meta property="og:type" content="{"article" if article else "website"}">',
        f'<meta property="og:site_name" content="{esc(ORG["name"])}">',
        '<meta property="og:locale" content="vi_VN">',
        f'<meta property="og:url" content="{esc(url)}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:image" content="{esc(image)}">',
        f'<meta property="og:image:alt" content="{esc(h1)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
        f'<meta name="twitter:image" content="{esc(image)}">',
        '<meta name="theme-color" content="#0057c2">',
    ]
    if article:
        tags += [f'<meta property="article:published_time" content="{esc(article.get("date", ""))}">',
                 f'<meta property="article:modified_time" content="{esc(str(article.get("updated_at") or article.get("date", ""))[:10])}">']

    org_ref = {"@id": SITE_URL + "/#organization"}
    graph = [org_node(), {
        "@type": "WebSite", "@id": SITE_URL + "/#website", "url": SITE_URL + "/",
        "name": ORG["name"], "inLanguage": "vi", "publisher": org_ref,
    }]
    slug = url[len(SITE_URL) + 1:].strip("/").split("/")[0] if not is_home else ""
    page = {
        "@type": PAGE_TYPES.get(slug, "WebPage") if url.count("/") <= 4 or slug != "tin-tuc" else "WebPage",
        "@id": url + "#webpage", "url": url, "name": title, "description": desc, "inLanguage": "vi",
        "isPartOf": {"@id": SITE_URL + "/#website"}, "about": org_ref,
        "primaryImageOfPage": {"@type": "ImageObject", "url": image},
    }
    if not is_home:
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
                      "itemListElement": breadcrumb_items(content, url, h1)})
        page["breadcrumb"] = {"@id": url + "#breadcrumb"}
    if page["@type"] == "FAQPage":
        faqs = faq_entities(content)
        if faqs:
            page["mainEntity"] = faqs
        else:
            page["@type"] = "WebPage"
    graph.append(page)
    if article:
        graph.append({
            "@type": "BlogPosting", "@id": url + "#article", "mainEntityOfPage": {"@id": url + "#webpage"},
            "headline": article.get("title", ""), "description": article.get("description", ""),
            "image": [image], "datePublished": article.get("date", ""),
            "dateModified": str(article.get("updated_at") or article.get("date", ""))[:10],
            "author": org_ref, "publisher": org_ref, "inLanguage": "vi",
        })
    data = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    data = data.replace("</", "<\\/")  # không để chuỗi nội dung đóng nhầm thẻ <script>
    return ("<!-- seo:start -->\n" + "\n".join(tags) +
            '\n<script type="application/ld+json">\n' + data + "\n</script>\n<!-- seo:end -->\n")


def with_seo(content, url, article=None):
    """Thay (hoặc chèn) khối SEO; gỡ canonical đứng lẻ cũ để không bị trùng. Idempotent."""
    content = SEO_BLOCK_RE.sub("", content)
    content = CANONICAL_RE.sub("", content)
    block = seo_block(content, url, article)
    m = re.search(r'<meta\s+name="description"[^>]*>\n?', content, re.I)
    if m:
        cut = m.end() if m.group(0).endswith("\n") else m.end()
        sep = "" if m.group(0).endswith("\n") else "\n"
        return content[:cut] + sep + block + content[cut:]
    return content.replace("</head>", block + "</head>", 1)


def build_sitemap(news, legacy):
    """Gắn khối SEO (canonical, OG, JSON-LD) cho từng trang + sinh sitemap. Quét mọi html/**/index.html (kể cả trang viết tay thêm sau này) — không cần khai báo
    tay. Bỏ qua thư mục kỹ thuật và trang tự khai noindex (vd /admin/, /nguon-anh/).
    lastmod chỉ ghi cho tin tức (có ngày thật trong data/); trang viết tay không có nguồn ngày
    tin cậy trong CI (checkout nông) nên bỏ trống thay vì ghi ngày build sai mỗi lần."""
    lastmod = {}
    articles = {f'{SITE_URL}/tin-tuc/{n["slug"]}/': n for n in news}
    for n in legacy:
        if n.get("url", "").startswith("/") and not n["url"].startswith("/lien-he/"):
            lastmod[SITE_URL + n["url"]] = str(n.get("date") or "")[:10]
    for n in news:
        lastmod[f'{SITE_URL}/tin-tuc/{n["slug"]}/'] = str(n.get("updated_at") or n.get("date") or "")[:10]

    urls = []
    for page in SITE.rglob("index.html"):
        parts = page.relative_to(SITE).parts
        if parts[0] in SITEMAP_SKIP_DIRS:
            continue
        content = read(page)
        if is_noindex(content):
            continue
        url = page_url(page)
        write_if_changed(page, with_seo(content, url, articles.get(url)))
        urls.append(url)
    # Trang chủ trước, còn lại theo thứ tự chữ cái -> output ổn định, build lại không sinh diff.
    urls.sort(key=lambda u: (u != SITE_URL + "/", u))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lm = lastmod.get(u)
        lines.append(f"  <url><loc>{esc(u)}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>")
    lines.append("</urlset>")
    write_if_changed(SITE / "sitemap.xml", "\n".join(lines) + "\n")

    # KHÔNG khai Disallow cho /admin/: robots.txt công khai, khai ra là tự quảng cáo đường dẫn
    # quản trị; trang đó đã tự chặn bằng meta noindex (static-site-build.md mục 6b).
    write_if_changed(SITE / "robots.txt",
                     "User-agent: *\nAllow: /\n\nSitemap: " + SITE_URL + "/sitemap.xml\n")
    return len(urls)


# ---------------------------------------------------------------------------- main

def main():
    products = load_json("catalog.json", [])
    news = load_json("news.json", [])
    legacy = load_json("legacy-news.json", [])
    categories = load_json("news-categories.json", [])
    print(f"build: {len(products)} sản phẩm, {len(news)} tin CMS + {len(legacy)} tin cũ, "
          f"{len(categories)} danh mục tin")
    build_products(products)
    build_news(news, legacy, categories)
    count = build_sitemap(news, legacy)
    print(f"xong. sitemap: {count} URL")


if __name__ == "__main__":
    main()

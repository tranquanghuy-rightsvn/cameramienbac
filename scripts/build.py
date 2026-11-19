#!/usr/bin/env python3
"""Build các phần động của site Cameramienbac từ data/*.json (CMS ghi) — Python stdlib, không
cần cài gì. Quyết định nghiệp vụ chốt ở ../GAS.md mục IX; đọc trước khi sửa.

Ghi đè ĐÚNG các vùng nằm giữa 2 mốc `<!-- cms:<tên>:start -->` / `<!-- cms:<tên>:end -->`,
phần còn lại của file giữ nguyên (trang viết tay):
  html/partials/catalog.html          cms:catalog          lưới sản phẩm (/san-pham/ + 8 trang nhóm)
  html/hang-<hãng>/index.html         cms:brand-products   "Sản phẩm tiêu biểu" của hãng
  html/tin-tuc/index.html             cms:news-filter      nút lọc theo danh mục tin
                                      cms:news-list        danh sách tin (CMS + bài viết tay cũ)
  html/index.html                     cms:home-news        3 tin mới nhất ở trang chủ
  html/trung-tam-ai/index.html        cms:ai-news          3 tin chủ đề AI ở trang Trung tâm AI
  html/du-an/index.html               cms:project-cities   ô lọc Tỉnh/Thành phố (lấy từ dữ liệu)
                                      cms:project-years    ô lọc Năm triển khai (lấy từ dữ liệu)
                                      cms:project-count    dòng đếm số dự án
                                      cms:project-list     lưới dự án
  html/index.html                     cms:home-projects    3 dự án tiêu biểu ở trang chủ
Sinh mới từ template:
  html/tin-tuc/<slug>/index.html      templates/news-detail.html (mang dấu GENERATED_MARKER)
  html/du-an/<slug>/index.html        templates/project-detail.html — CHỈ dự án có nội dung
  html/san-pham/<slug>/index.html     templates/product-detail.html — từ data/products.json (dữ liệu
                                      cào bằng scripts/crawl_products.py, KHÔNG thuộc CMS)
Lưới model sản phẩm (data/products.json):
  html/san-pham/index.html            cms:product-models   toàn bộ model, nhóm theo hãng
  html/hang-<hãng>/index.html         cms:brand-models     model chi tiết của hãng
Sinh toàn bộ (không sửa tay):
  html/sitemap.xml                    mọi trang */index.html, trừ trang noindex + thư mục kỹ thuật
  html/robots.txt                     cho phép tất cả + trỏ tới sitemap

Không tìm thấy mốc = DỪNG build với lỗi rõ ràng (không im lặng bỏ qua — ai đó sửa tay trang mà
lỡ xoá mốc thì CMS sẽ "lưu mà không thấy gì đổi").

Chạy: python3 scripts/build.py   (CI chạy khi data/catalog.json, data/news.json,
data/news-categories.json, data/legacy-news.json, data/projects.json, templates/** hoặc file
này đổi.)
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
# Model (đã chuẩn hoá bằng model_key) -> URL trang chi tiết sản phẩm (điền trong main() từ data/products.json).
PD_LINKS = {}
# id dòng sản phẩm catalog CMS -> URL trang chi tiết riêng (sinh từ catalog hoặc trang viết tay sẵn có).
CAT_LINKS = {}


def model_key(text):
    """Chuẩn hoá mã model để so khớp: bỏ dấu cách, gạch, ngoặc, '/' ("DS-2TD8167-150ZC4F/W" = "...ZC4FW")."""
    return re.sub(r"[^A-Z0-9]", "", str(text or "").upper())


def model_link(model):
    mk = model_key(model)
    if not mk:
        return None
    return next((u for m, u in sorted(PD_LINKS.items(), key=lambda kv: -len(kv[0])) if m and m in mk), None)

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

# Loại công trình của dự án: (slug, tên ở bộ lọc, nhãn trên ảnh, nét vẽ icon nhãn). Slug khớp các
# ô lọc "Danh mục dự án" viết tay ở html/du-an/index.html.
PROJECT_CATEGORIES = [
    ("chung-cu", "Tòa nhà - Chung cư", "Chung cư",
     '<rect x="4.4" y="3.4" width="15.2" height="17.2" rx="1.4"/><path d="M8 7.4h2.6M13.4 7.4H16M8 11.4h2.6M13.4 11.4H16M8 15.4h2.6M13.4 15.4H16"/>'),
    ("do-thi", "Khu đô thị", "Khu đô thị",
     '<path d="M2.8 20.6h18.4"/><rect x="3.8" y="9.4" width="5" height="11.2"/><rect x="9.8" y="4.4" width="5" height="16.2"/><rect x="15.8" y="12.4" width="4.4" height="8.2"/>'),
    ("van-phong", "Văn phòng", "Văn phòng",
     '<rect x="4.4" y="3.4" width="15.2" height="17.2" rx="1.4"/><path d="M8 7.4h2.4M13.6 7.4H16M8 11.4h2.4M13.6 11.4H16M8 15.4h2.4M13.6 15.4H16"/>'),
    ("nha-may", "Nhà máy - KCN", "Nhà máy - KCN",
     '<path d="M2.8 20.6V10l6 3.6V10l6 3.6V6.4h6.4v14.2H2.8Z"/>'),
    ("truong-hoc", "Trường học", "Trường học",
     '<path d="M12 3.4 1.8 8.2 12 13l10.2-4.8L12 3.4Z"/><path d="M5.6 10.6v4.8c0 1.9 2.9 3.4 6.4 3.4s6.4-1.5 6.4-3.4v-4.8"/>'),
    ("ngan-hang", "Ngân hàng", "Ngân hàng",
     '<path d="M3.2 9.4 12 4.2l8.8 5.2"/><path d="M5.4 9.4v9.2M9.8 9.4v9.2M14.2 9.4v9.2M18.6 9.4v9.2M2.8 20.6h18.4"/>'),
    ("benh-vien", "Bệnh viện", "Bệnh viện",
     '<rect x="4" y="4.4" width="16" height="16.2" rx="2"/><path d="M12 8.6v7.4M8.3 12.3h7.4"/>'),
    ("khac", "Khác", "Công trình khác",
     '<path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/>'),
]
PROJECT_CAT = {slug: (name, tag, icon) for slug, name, tag, icon in PROJECT_CATEGORIES}

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
    # Trang chi tiết của model tiêu biểu (data/products.json) -> ảnh + tên + nút "Xem chi tiết" dẫn tới đó.
    # Trang riêng của dòng sản phẩm (có Nội dung chi tiết viết trong CMS / chưa có model chi tiết) ưu tiên
    # hơn trang của model tiêu biểu.
    link = CAT_LINKS.get(p.get("id")) or model_link(p.get("model"))
    lines = []
    if with_filters:
        lines.append(f'{pad}<article class="pitem" data-cat="{esc(p.get("category"))}" '
                     f'data-app="{esc(" ".join(p.get("apps") or []))}" '
                     f'data-brand="{esc(" ".join(p.get("brands") or []))}">')
    else:
        lines.append(f'{pad}<article class="pitem">')
    if p.get("image"):
        img = (f'<img src="/{esc(p["image"])}" alt="{esc(p.get("image_alt") or title)}" loading="lazy" '
               f'width="320" height="320" decoding="async">')
        if link:
            img = f'<a href="{link}" tabindex="-1" aria-hidden="true">{img}</a>'
        lines.append(f'{inner}<div class="pitem__media">{img}</div>')
    lines.append(f'{inner}<p class="pitem__cat">{esc(CAT_LABEL.get(p.get("category"), ""))}</p>')
    title_html = f'<a href="{link}">{esc(title)}</a>' if link else esc(title)
    lines.append(f'{inner}<h3 class="pitem__title">{title_html}</h3>')
    if p.get("description"):
        lines.append(f'{inner}<p class="pitem__text">{esc(p["description"])}</p>')
    price = price_display(p.get("price"))
    if p.get("model"):
        note = f' ({esc(p["model_note"])})' if p.get("model_note") else ""
        model_html = esc(p["model"])
        if link:
            model_html = f'<a href="{link}">{model_html}</a>'
        lines.append(f'{inner}<p class="pitem__model">Model tiêu biểu: <strong>{model_html}'
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
    detail = f'<a class="pitem__more" href="{link}">Xem chi tiết</a>' if link else ""
    lines.append(f'{inner}<div class="pitem__foot">{detail}<a class="btn btn--solid btn--xs" '
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
            # smart_html = bản Smart content làm bằng công cụ AI trong CMS (GAS.md III.9); content_html là bản gốc.
            "{{CONTENT}}": lazy_images(post.get("smart_html") or post.get("content_html") or ""),
        }
        out = tpl
        for key, value in mapping.items():
            out = out.replace(key, value)
        out = inject_smart_assets(out)
        # Gắn khối SEO ngay lúc render (không đợi bước sitemap) để file chỉ ghi khi thật sự đổi.
        out = with_seo(out, f"{SITE_URL}/tin-tuc/{slug}/", meta)
        write_if_changed(SITE / "tin-tuc" / slug / "index.html", out)
        generated.add(slug)
    clean_orphan_pages(SITE / "tin-tuc", generated)


# ---------------------------------------------------------------------------- dự án

def svg(paths, width="1.6"):
    return (f'<svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg>')


PIN_SVG = svg('<path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/>')
CAM_SVG = svg('<rect x="2.6" y="7" width="13" height="10" rx="2.2"/><path d="m16 11.2 5-2.6v7l-5-2.6z"/>')
AI_SVG = svg('<path d="M3.4 8.4V5.4a2 2 0 0 1 2-2h3M15.6 3.4h3a2 2 0 0 1 2 2v3M20.6 15.6v3a2 2 0 0 1-2 2h-3'
             'M8.4 20.6h-3a2 2 0 0 1-2-2v-3"/><circle cx="12" cy="10.4" r="2.4"/><path d="M8 16.6a4.6 4.6 0 0 1 8 0"/>')
CAM_BADGE_SVG = svg('<rect x="2.6" y="7" width="13" height="10" rx="2.4"/><path d="m16 11.2 5-2.6v7l-5-2.6z"/>'
                    '<circle cx="8.4" cy="12" r="2.2"/>')
CAL_BADGE_SVG = svg('<rect x="3.4" y="4.8" width="17.2" height="15.8" rx="1.8"/><path d="M3.4 9.6h17.2M8 2.8v4M16 2.8v4"/>')


def sort_projects(projects):
    return sorted(projects, key=lambda p: (int(p.get("order") or 0), p.get("slug", "")))


def project_url(p):
    """Dự án có nội dung -> có trang chi tiết riêng; không có thì thẻ dẫn về form tư vấn."""
    return f'/du-an/{p["slug"]}/' if (p.get("smart_html") or p.get("content_html") or "").strip() else None


def project_card(p):
    url = project_url(p)
    _, tag, icon = PROJECT_CAT.get(p.get("category"), PROJECT_CAT["khac"])
    title = esc(p.get("title"))
    stats = []
    if int(p.get("cameras") or 0) > 0:
        stats.append(f'<li><i>{CAM_SVG}</i><span><b>{esc(p["cameras"])}</b>camera</span></li>')
    stats.append(f'<li><i>{AI_SVG}</i><span><b>AI</b>nhận diện</span></li>')
    if p.get("year"):
        stats.append(f'<li><i>{CLOCK_SVG}</i><span><b>{esc(p["year"])}</b>hoàn thành</span></li>')
    lines = [
        f'          <article class="prj" data-category="{esc(p.get("category"))}" data-city="{esc(p.get("city"))}" '
        f'data-year="{esc(p.get("year") or "")}">',
        '            <div class="prj__media">',
        f'              <img src="/{esc(p.get("cover"))}" alt="{esc(p.get("cover_alt") or p.get("title"))}" '
        'loading="lazy" width="1280" height="720" decoding="async">',
        f'              <span class="prj__tag">{svg(icon)}{esc(tag)}</span>',
        '            </div>',
        '            <div class="prj__body">',
        f'              <h3 class="prj__title">' + (f'<a href="{url}">{title}</a>' if url else title) + '</h3>',
    ]
    if p.get("location"):
        lines.append(f'              <p class="prj__loc">{PIN_SVG}{esc(p["location"])}</p>')
    if p.get("description"):
        lines.append(f'              <p class="prj__text">{esc(p["description"])}</p>')
    lines.append('              <ul class="prj__stats">')
    lines += ["                " + s for s in stats]
    lines.append('              </ul>')
    if url:
        lines.append(f'              <a class="btn" href="{url}">Xem chi tiết {ARROW_SVG}</a>')
    else:
        lines.append(f'              <a class="btn" href="/lien-he/">Nhận tư vấn {ARROW_SVG}</a>')
    lines += ['            </div>', '          </article>']
    return "\n".join(lines)


def home_project_card(p):
    url = project_url(p)
    href = url or "/du-an/"
    loc = " · ".join(x for x in [p.get("location") or "",
                                 f'{p["cameras"]} camera' if int(p.get("cameras") or 0) > 0 else ""] if x)
    more = "Xem chi tiết" if url else "Xem dự án"
    return "\n".join([
        '        <article class="hprj">',
        f'          <a class="hprj__media" href="{href}" tabindex="-1" aria-hidden="true"><img src="/{esc(p.get("cover"))}" '
        'alt="" loading="lazy" width="1280" height="720" decoding="async"></a>',
        '          <div class="hprj__body">',
        f'            <h3 class="hprj__title"><a href="{href}">{esc(p.get("title"))}</a></h3>',
        f'            <p class="hprj__loc">{esc(loc)}</p>',
        f'            <p class="hprj__text">{esc(p.get("description"))}</p>',
        f'            <div class="hprj__foot"><a class="link-more" href="{href}"><i>{ARROW_SVG}</i>{more}</a></div>',
        '          </div>',
        '        </article>',
    ])


def project_facts(p):
    name = PROJECT_CAT.get(p.get("category"), PROJECT_CAT["khac"])[0]
    rows = [("Loại công trình", esc(name))]
    if p.get("location"):
        rows.append(("Địa điểm", esc(p["location"])))
    if int(p.get("cameras") or 0) > 0:
        rows.append(("Quy mô", f'{esc(p["cameras"])} camera'))
    if p.get("solution"):
        rows.append(("Giải pháp", esc(p["solution"])))
    if p.get("year"):
        rows.append(("Hoàn thành", esc(p["year"])))
    out = [f"            <div><dt>{dt}</dt><dd>{dd}</dd></div>" for dt, dd in rows]
    owner = (f'<dd>{esc(p["owner"])}</dd>' if p.get("owner")
             else '<dd class="pending">Cập nhật khi được phép công bố</dd>')
    out.append(f"            <div><dt>Chủ đầu tư</dt>{owner}</div>")
    return "\n".join(out)


def project_badges(p):
    items = []
    if p.get("location"):
        items.append((PIN_SVG, esc(p["location"])))
    if int(p.get("cameras") or 0) > 0:
        items.append((CAM_BADGE_SVG, f'{esc(p["cameras"])} camera'))
    if p.get("year"):
        items.append((CAL_BADGE_SVG, f'Hoàn thành {esc(p["year"])}'))
    return "".join(f'<li class="phero__badge"><i>{ico}</i><span>{text}</span></li>' for ico, text in items)


def build_projects(projects):
    projects = sort_projects(projects)
    page = SITE / "du-an" / "index.html"
    cities = sorted({p.get("city") for p in projects if p.get("city")})
    years = sorted({int(p["year"]) for p in projects if p.get("year")}, reverse=True)
    options = lambda values: "<option>Tất cả</option>" + "".join(f"<option>{esc(v)}</option>" for v in values)
    count = (f"{len(projects)} dự án tiêu biểu trong hơn 500 dự án Cameramienbac đã triển khai trên toàn miền Bắc."
             if projects else "Danh sách dự án đang được cập nhật.")
    cards = "\n".join(project_card(p) for p in projects)
    patch_file(page, [
        ("project-cities", f'              <select id="f-city">{options(cities)}</select>'),
        ("project-years", f'              <select id="f-year">{options(years)}</select>'),
        ("project-count", f'          <p class="psec__lead" id="prj-count">{esc(count)}</p>'),
        ("project-list", cards),
    ])
    # Trang chủ: dự án đánh dấu "hiện ở trang chủ" trước, thiếu thì lấy tiếp theo thứ tự -> luôn đủ 3.
    home = [p for p in projects if p.get("featured")] + [p for p in projects if not p.get("featured")]
    patch_file(SITE / "index.html", [("home-projects", "\n".join(home_project_card(p) for p in home[:3]))])

    tpl = read(TEMPLATES / "project-detail.html")
    generated = set()
    for p in projects:
        if not project_url(p):
            continue
        slug = p["slug"]
        mapping = {
            "{{TITLE}}": esc(p.get("title")),
            "{{SUBTITLE}}": f'<span>{esc(p["subtitle"])}</span>' if p.get("subtitle") else "",
            "{{DESCRIPTION}}": esc(p.get("description")),
            "{{COVER}}": esc(p.get("cover")),
            "{{COVER_ALT}}": esc(p.get("cover_alt") or p.get("title")),
            "{{BADGES}}": project_badges(p),
            "{{FACTS}}": project_facts(p),
            "{{CONTENT}}": lazy_images(p.get("smart_html") or p.get("content_html") or ""),
        }
        out = tpl
        for key, value in mapping.items():
            out = out.replace(key, value)
        out = inject_smart_assets(out)
        out = with_seo(out, f"{SITE_URL}/du-an/{slug}/")
        write_if_changed(SITE / "du-an" / slug / "index.html", out)
        generated.add(slug)
    clean_orphan_pages(SITE / "du-an", generated)


# ---------------------------------------------------------------------------- trang chi tiết sản phẩm

# Hãng của sản phẩm cào (data/products.json): slug -> (tên hiển thị, trang hãng hoặc None).
PD_BRANDS = {
    "hikvision": ("Hikvision", "/hang-hikvision/"), "dahua": ("Dahua", "/hang-dahua/"),
    "axis": ("Axis", "/hang-axis/"), "hanwha": ("Hanwha Vision", "/hang-hanwha/"),
    "cisco": ("Cisco", None), "poly": ("Poly", None), "allied-telesis": ("Allied Telesis", None),
}
PD_BRAND_ORDER = list(PD_BRANDS)
# Nhóm thông số tiếng Anh -> tiếng Việt (giá trị giữ nguyên như datasheet của hãng).
SPEC_GROUP_VI = {
    "camera": "Camera", "lens": "Ống kính", "video": "Video", "audio": "Âm thanh", "network": "Mạng",
    "interface": "Cổng giao tiếp", "electrical": "Nguồn điện", "environmental": "Môi trường hoạt động",
    "construction": "Cấu tạo", "general": "Thông số chung", "power": "Nguồn điện", "security": "Bảo mật",
    "compression": "Chuẩn nén", "intelligence": "Phân tích thông minh", "certifications": "Chứng nhận",
    "operational": "Vận hành", "analytics": "Phân tích AI", "mechanical": "Cơ khí",
    "ptz": "PTZ", "environmental & electrical": "Môi trường & nguồn điện",
    "certifications & standards": "Chứng nhận & tiêu chuẩn", "": "Thông số chung",
}
PD_SKIP_DIRS = {slug for slug, _ in PRODUCT_CATEGORIES} | {"aiot-platform"}


def pd_type(p):
    """Loại thiết bị hiển thị (eyebrow, JSON-LD category). Ghi `type` trong data để ép tay."""
    if p.get("type"):
        return p["type"]
    t = (p.get("title", "") + " " + p.get("source_category", "") + " " + p.get("subtitle", "")).lower()
    rules = [
        (("webex", "polycom", "poly studio", "room kit", "realpresence", "sx10", "sx20", "hội nghị", "họp trực tuyến", "dx80"),
         "Thiết bị hội nghị truyền hình"),
        (("media converter", "converter"), "Thiết bị mạng"),
        (("ảnh nhiệt", "thermal", "cháy rừng"), "Camera ảnh nhiệt"),
        (("biển số", "anpr", "lpr"), "Camera nhận diện biển số"),
        (("ptz", "speed dome", "speeddome", "tandemvu"), "Camera PTZ"),
        (("hd-tvi", "hdtvi", "turbo hd", "tubo hd", "ds-2ce", "4 in 1"), "Camera HD-TVI"),
        (("fisheye", "mắt cá"), "Camera mắt cá (Fisheye)"),
        (("box camera",), "Camera thân hộp (Box)"),
    ]
    for keys, label in rules:
        if any(k in t for k in keys):
            return label
    return "Camera IP"


def pd_brand(p):
    if "brand_label" in p:  # trang của dòng sản phẩm catalog
        return p["brand_label"], p.get("brand_page")
    return PD_BRANDS.get(p.get("brand"), (p.get("brand", "").title(), None))


def pd_ph(p, cls):
    """Khung biểu tượng nhóm thay cho ảnh (dòng sản phẩm catalog chưa có ảnh)."""
    return (f'<div class="{cls}" role="img" aria-label="{esc(p["title"])}">{svg(p.get("icon") or "", "1.3")}'
            f'<span>{esc(pd_type(p))}</span></div>')


def pd_url(p):
    return f'/san-pham/{p["slug"]}/'


def pd_model_label(p):
    return p.get("model") or p.get("title", "")


def clip(text, limit):
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:–-")
    return cut + "…"


def pd_description(p):
    """Meta description ≤ 160 ký tự: đoạn giới thiệu tiếng Việt, rơi về câu tự soạn từ loại + ý chính."""
    brand = pd_brand(p)[0]
    if p.get("intro"):
        return clip(strip_tags(p["intro"]), 160)
    first = ""
    m = re.search(r"<p>(.*?)</p>", p.get("content_html") or "", re.S)
    if m and len(strip_tags(m.group(1))) > 80 and not re.search(r"[a-z]{4,} [a-z]{4,} [a-z]{4,} the ", strip_tags(m.group(1))):
        first = strip_tags(m.group(1))
    if first:
        return clip(first, 160)
    hl = ", ".join(h.rstrip(".") for h in p.get("highlights", [])[:3])
    base = f"{pd_type(p)} {brand} {pd_model_label(p)} chính hãng"
    return clip(f"{base}: {hl}. Tư vấn, báo giá, lắp đặt tại Hà Nội." if hl else
                f"{base} — thông số kỹ thuật, hình ảnh, tư vấn và báo giá lắp đặt tại Hà Nội.", 160)


def pd_meta_title(p):
    brand = pd_brand(p)[0]
    full = f'{p["title"]} | Cameramienbac'
    if len(full) <= 68:
        return full
    model = pd_model_label(p)
    short = f"{pd_type(p)} {brand} {model} | Cameramienbac"
    return short if len(short) <= 75 else f"{brand} {model} | Cameramienbac"


def pd_card(p, heading="h3"):
    brand = pd_brand(p)[0]
    if p.get("images"):
        media = (f'<div class="pd-card__media"><img src="{esc(p["images"][0])}" alt="{esc(p["title"])}" '
                 f'loading="lazy" decoding="async" width="320" height="320"></div>')
    else:
        media = pd_ph(p, "pd-card__media pd-ph")
    model = (f'<p class="pd-card__model">Model: <strong>{esc(p["model"])}</strong></p>' if p.get("model")
             else '<p class="pd-card__model">Xem chi tiết &rarr;</p>')
    return (f'<a class="pd-card" href="{pd_url(p)}">{media}'
            f'<div class="pd-card__body"><p class="pd-card__brand">{esc(brand)} · {esc(pd_type(p))}</p>'
            f'<{heading} class="pd-card__title">{esc(p["title"])}</{heading}>{model}</div></a>')


def pd_specs_html(p):
    groups = []
    for g in p.get("specs") or []:
        name = SPEC_GROUP_VI.get(g["group"].strip().lower(), g["group"])
        rows = "".join(f"<tr><th scope=\"row\">{esc(k)}</th><td>{esc(v)}</td></tr>" for k, v in g["items"])
        groups.append(f'<div class="pd-specs__group"><h3>{esc(name)}</h3><table>{rows}</table></div>')
    return '<div class="pd-specs">' + "".join(groups) + "</div>" if groups else ""


def pd_related(p, products):
    same_brand = [x for x in products if x is not p and x["brand"] == p["brand"]]
    same_type = [x for x in same_brand if pd_type(x) == pd_type(p)]
    others = [x for x in products if x is not p and x not in same_brand and pd_type(x) == pd_type(p)]
    out = []
    for x in same_type + same_brand + others:
        if x not in out:
            out.append(x)
    return out[:4]


def pd_crumbs(p):
    name, page = pd_brand(p)
    parts = ['<a href="/">Trang chủ</a>', '<a href="/san-pham/">Sản phẩm</a>']
    if p.get("crumb"):
        name, page = p["crumb"]
    if page:
        parts.append(f'<a href="{page}">{esc(name)}</a>')
    parts.append(f"<span>{esc(pd_model_label(p))}</span>")
    return '<span aria-hidden="true">/</span>'.join(parts)


def pd_page(p, products, tpl):
    brand, brand_page = pd_brand(p)
    model = pd_model_label(p)
    images = p.get("images") or [ORG["default_image"]]
    w, h = ((p.get("image_size") or []) + [0, 0])[:2]
    w, h = (w or 800), (h or 800)
    thumbs = ""
    if len(images) > 1:
        thumbs = ('          <ul class="pd-thumbs">' + "".join(
            f'<li><button type="button" data-src="{esc(src)}" aria-current="{"true" if i == 0 else "false"}" '
            f'aria-label="Xem ảnh {i + 1}"><img src="{esc(src)}" alt="{esc(p["title"])} — ảnh {i + 1}" '
            f'width="74" height="74" loading="lazy" decoding="async"></button></li>'
            for i, src in enumerate(images)) + "</ul>")
    meta_rows = [("Hãng", f'<a href="{brand_page}">{esc(brand)}</a>' if brand_page else esc(brand))]
    if p.get("model"):
        meta_rows.append(("Model", f'<a href="{p["model_url"]}">{esc(model)}</a>' if p.get("model_url") else esc(model)))
    meta_rows.append(("Nhóm" if p.get("catalog") else "Loại thiết bị", esc(pd_type(p))))
    if p.get("catalog"):
        meta_rows.append(("Giá tham khảo", esc(price_display(p.get("price")) or "Liên hệ báo giá")))
    meta_html = "\n".join(f"            <div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in meta_rows)
    hl = p.get("highlights") or []
    hl_html = ('          <ul class="pd-hl">' + "".join(f"<li>{esc(x)}</li>" for x in hl[:8]) + "</ul>") if hl else ""

    sections, tabs = [], []
    intro = p.get("intro") or ""
    content = p.get("content_html") or ""
    if intro or content:
        body = ""
        if intro:
            body += "".join(f"<p>{esc(par)}</p>" for par in intro.split("\n\n") if par.strip())
        if content:
            if intro and p.get("source") in ("axis.com", "hanwhavision.com"):
                body += '<h3>Thông tin từ hãng sản xuất (tiếng Anh)</h3>'
            body += lazy_images(content)
        sections.append(("gioi-thieu", f"Giới thiệu {model}", f'<div class="prose">{body}</div>'))
    specs = pd_specs_html(p)
    if specs and p.get("catalog"):
        specs += ('<p class="pd-note">Model, cấu hình và số lượng cụ thể được Cameramienbac đề xuất sau khi khảo sát '
                  'công trình; giá tham khảo có thể thay đổi theo thời điểm và cấu hình.</p>')
        sections.append(("thong-so", "Thông tin sản phẩm", specs))
    elif specs:
        specs += ('<p class="pd-note">Thông số theo tài liệu công bố của hãng ' + esc(brand) +
                  ', có thể thay đổi theo phiên bản phần cứng/firmware. Liên hệ Cameramienbac để được xác nhận '
                  'cấu hình và phụ kiện đi kèm trước khi đặt hàng.</p>')
        sections.append(("thong-so", f"Thông số kỹ thuật {model}", specs))
    if hl and not specs:
        sections.append(("tinh-nang", "Tính năng nổi bật",
                         '<div class="prose"><ul>' + "".join(f"<li>{esc(x)}</li>" for x in hl) + "</ul></div>"))
    sections.append(("tu-van", "Tư vấn & lắp đặt", '<div class="prose">' +
                     f"<p>Cameramienbac tư vấn, cung cấp và lắp đặt <strong>{esc(p['title'])}</strong> cùng các "
                     f"thiết bị đồng bộ (đầu ghi, ổ cứng, switch PoE, phần mềm quản lý) cho doanh nghiệp, "
                     f"trường học, tòa nhà tại Hà Nội và các tỉnh miền Bắc.</p><ul>"
                     "<li>Khảo sát hiện trạng, đề xuất số lượng và vị trí lắp đặt phù hợp.</li>"
                     "<li>Báo giá trọn gói thiết bị + thi công, xuất hóa đơn VAT.</li>"
                     "<li>Cấu hình xem từ xa trên điện thoại, bàn giao và hướng dẫn sử dụng.</li>"
                     "<li>Bảo hành chính hãng, hỗ trợ kỹ thuật trong giờ làm việc (T2–T7, 8:00–17:30).</li>"
                     '</ul><p>Gọi <a href="tel:0978406868">0978 406 868</a> hoặc '
                     f'<a href="/lien-he/?sp={esc(contact_query(model))}#tu-van">gửi yêu cầu báo giá</a> để được tư vấn.</p></div>'))
    sec_html = "\n".join(f'          <section class="pd-sec" id="{sid}"><h2 class="pd-sec__title">{esc(title)}</h2>{body}</section>'
                         for sid, title, body in sections)
    tabs = "".join(f'<a href="#{sid}">{esc(title.replace(" " + model, ""))}</a>' for sid, title, _ in sections)

    rel = p["related"] if "related" in p else pd_related(p, products)
    related = ""
    if rel:
        related = ('  <section class="psec psec--tint psec--last">\n    <div class="container">\n'
                   '      <div class="psec__head"><h2 class="psec__title">Sản phẩm liên quan</h2></div>\n'
                   '      <div class="pd-cards">' + "".join(pd_card(x) for x in rel) + "</div>\n"
                   "    </div>\n  </section>")
    mapping = {
        "{{META_TITLE}}": esc(pd_meta_title(p)),
        "{{DESCRIPTION}}": esc(pd_description(p)),
        "{{IMAGE}}": esc(images[0]), "{{IMAGE_ALT}}": esc(p["title"]),
        "{{IMAGE_W}}": str(w), "{{IMAGE_H}}": str(h),
        "{{THUMBS}}": thumbs, "{{CRUMBS}}": pd_crumbs(p),
        "{{TYPE}}": esc(pd_type(p)), "{{BRAND}}": esc(brand), "{{TITLE}}": esc(p["title"]),
        "{{META_ROWS}}": meta_html, "{{HIGHLIGHTS}}": hl_html,
        "{{CTA_URL}}": esc(f"/lien-he/?sp={contact_query(model)}#tu-van"),
        "{{MODEL_SHORT}}": esc(model), "{{TABS}}": tabs, "{{SECTIONS}}": sec_html, "{{RELATED}}": related,
    }
    out = tpl
    for key, value in mapping.items():
        out = out.replace(key, value)
    if not p.get("images"):  # chưa có ảnh: khung biểu tượng nhóm, bỏ preload ảnh
        out = re.sub(r'<figure class="pd-gallery__main">.*?</figure>', pd_ph(p, "pd-gallery__main pd-ph"), out, count=1, flags=re.S)
        out = re.sub(r'<link rel="preload" as="image"[^>]*>\n', "", out, count=1)
    return out


def product_ld(p, url):
    brand = pd_brand(p)[0]
    props = []
    for g in p.get("specs") or []:
        for k, v in g["items"]:
            if len(props) >= 30:
                break
            props.append({"@type": "PropertyValue", "name": k, "value": v})
    node = {
        "@type": "Product", "@id": url + "#product", "url": url, "name": p["title"],
        "description": pd_description(p), "sku": p.get("model") or p["slug"],
        "brand": {"@type": "Brand", "name": brand}, "category": pd_type(p),
        "image": [abs_url(i) for i in (p.get("images") or [ORG["default_image"]])],
        "mainEntityOfPage": {"@id": url + "#webpage"},
    }
    if p.get("model"):
        node["mpn"] = p["model"]
    if p.get("catalog"):
        if not p.get("brand_specific"):
            node.pop("brand")
        try:
            price = int(p.get("price") or 0)
        except (TypeError, ValueError):
            price = 0
        if price > 0:  # giá đang hiện công khai trên catalog
            node["offers"] = {"@type": "Offer", "url": url, "price": price, "priceCurrency": "VND",
                              "seller": {"@id": SITE_URL + "/#organization"}}
    if props:
        node["additionalProperty"] = props
    return node


def build_product_pages(products, catalog_recs=()):
    """Sinh /san-pham/<slug>/ từ data/products.json (dữ liệu cào, không thuộc CMS) + lưới model ở
    /san-pham/ và trang hãng. Trả {url: bản ghi} để khối SEO gắn JSON-LD Product."""
    # title_vi (tên tiếng Việt viết tay) thay cho tên gốc của nguồn khi hiển thị.
    products = [dict(p, title=p.get("title_vi") or p["title"]) for p in products if p.get("slug") and p.get("title")]
    bad = [p["slug"] for p in products if p["slug"] in PD_SKIP_DIRS]
    if bad:
        sys.exit(f"LỖI: slug sản phẩm trùng thư mục nhóm có sẵn: {bad}")
    products.sort(key=lambda p: (PD_BRAND_ORDER.index(p["brand"]) if p["brand"] in PD_BRAND_ORDER else 99,
                                 pd_type(p), pd_model_label(p)))
    tpl = read(TEMPLATES / "product-detail.html")
    by_url, keep = {}, set()
    for p in products:
        url = SITE_URL + pd_url(p)
        write_if_changed(SITE / "san-pham" / p["slug"] / "index.html",
                         with_seo(pd_page(p, products, tpl), url, product=p))
        by_url[url] = p
        keep.add(p["slug"])
    for p in catalog_recs:
        url = SITE_URL + pd_url(p)
        write_if_changed(SITE / "san-pham" / p["slug"] / "index.html",
                         with_seo(inject_smart_assets(pd_page(p, products, tpl)), url, product=p))
        by_url[url] = p
        keep.add(p["slug"])
    clean_orphan_pages(SITE / "san-pham", keep | PD_SKIP_DIRS)

    # Lưới model ở /san-pham/ (nhóm theo hãng, có nút nhảy tới từng hãng).
    groups = []
    for b in PD_BRAND_ORDER:
        mine = [p for p in products if p["brand"] == b]
        if mine:
            groups.append((b, mine))
    chips = "".join(f'<a href="#model-{b}">{esc(PD_BRANDS[b][0])} ({len(m)})</a>' for b, m in groups)
    blocks = "\n".join(
        f'        <div class="pd-group"><h3 class="pd-group__title" id="model-{b}">{esc(PD_BRANDS[b][0])} '
        f'<small>{len(m)} model</small></h3><div class="pd-cards">' + "".join(pd_card(p, "h4") for p in m) + "</div></div>"
        for b, m in groups)
    patch_file(SITE / "san-pham" / "index.html",
               [("product-models", f'        <div class="pd-brands">{chips}</div>\n{blocks}')])
    for b, (name, page) in PD_BRANDS.items():
        if not page:
            continue
        mine = [p for p in products if p["brand"] == b]
        inner = ('        <div class="pd-cards">' + "".join(pd_card(p) for p in mine) + "</div>") if mine else (
            '        <p class="psec__lead">Đang cập nhật model chi tiết.</p>')
        patch_file(SITE / page.strip("/") / "index.html", [("brand-models", inner)])
    return by_url


CAT_ICONS = {
    "camera-ai": '<rect x="2.6" y="7" width="13" height="10" rx="2.2"/><path d="m16 11.2 5-2.6v7l-5-2.6z"/><circle cx="9" cy="12" r="2.2"/>',
    "luu-tru": '<rect x="3.4" y="3.6" width="17.2" height="5.4" rx="1.2"/><rect x="3.4" y="10.6" width="17.2" height="5.4" rx="1.2"/><path d="M7 6.3h.01M7 13.3h.01M6 20.4h12"/>',
    "ai-server": '<rect x="6" y="6" width="12" height="12" rx="1.6"/><path d="M9.4 9.4h5.2v5.2H9.4zM9 2.8V6M15 2.8V6M9 18v3.2M15 18v3.2M2.8 9H6M2.8 15H6M18 9h3.2M18 15h3.2"/>',
    "ra-vao": '<path d="M5 21V4.6A1.6 1.6 0 0 1 6.6 3h8.8A1.6 1.6 0 0 1 17 4.6V21M3 21h18"/><circle cx="13.4" cy="12.4" r=".9"/>',
    "anpr": '<path d="M4 16.4V12l1.8-4.6A2 2 0 0 1 7.7 6h8.6a2 2 0 0 1 1.9 1.4L20 12v4.4"/><rect x="2.8" y="12" width="18.4" height="5" rx="1.4"/><path d="M6.4 19.6v-2.6M17.6 19.6v-2.6M9 14.5h6"/>',
    "iot": '<circle cx="12" cy="12" r="2.6"/><path d="M7.6 7.6a6.2 6.2 0 0 0 0 8.8M16.4 16.4a6.2 6.2 0 0 0 0-8.8M4.6 4.6a10.4 10.4 0 0 0 0 14.8M19.4 19.4a10.4 10.4 0 0 0 0-14.8"/>',
    "mang": '<rect x="9" y="2.8" width="6" height="5" rx="1"/><rect x="2.8" y="16.2" width="6" height="5" rx="1"/><rect x="15.2" y="16.2" width="6" height="5" rx="1"/><path d="M12 7.8v4.2M5.8 16.2V12h12.4v4.2"/>',
    "phan-mem": '<rect x="2.8" y="4" width="18.4" height="13.4" rx="1.6"/><path d="M2.8 8h18.4M8.4 21h7.2M12 17.4V21"/>',
}


def catalog_records(catalog, crawled):
    """Dòng sản phẩm catalog CMS CHƯA có trang chi tiết model (data/products.json) -> bản ghi trang
    /san-pham/<id>/ (GAS.md II.6). Trùng trang viết tay sẵn có (vd aiot-platform) thì dẫn tới trang đó.
    Nội dung bổ sung (giới thiệu, tính năng) ở data/catalog-extra.json (không thuộc CMS)."""
    extra = load_json("catalog-extra.json", {})
    slugs = {p.get("slug") for p in crawled}
    recs = []
    for c in sort_products(catalog):
        cid = c.get("id") or ""
        cms_content = (c.get("smart_html") or c.get("content_html") or "").strip()
        mlink = model_link(c.get("model"))
        # Có model chi tiết và KHÔNG có nội dung viết trong CMS -> thẻ dẫn thẳng trang model.
        if not cid or (mlink and not cms_content):
            continue
        page = SITE / "san-pham" / cid / "index.html"
        if page.exists() and GENERATED_MARKER not in read(page):
            CAT_LINKS[cid] = f"/san-pham/{cid}/"
            if cms_content:
                print(f"  CẢNH BÁO: '{cid}' trùng trang viết tay — Nội dung chi tiết trong CMS không được hiển thị")
            continue
        if cid in slugs or cid in PD_SKIP_DIRS:
            print(f"  CẢNH BÁO: id catalog '{cid}' trùng trang khác — không sinh trang riêng")
            continue
        CAT_LINKS[cid] = f"/san-pham/{cid}/"
        x = extra.get(cid, {})
        cat = c.get("category", "")
        brands = [BRAND_LABEL.get(b, b) for b in c.get("brands") or []]
        mb = c.get("model_brand") or ""
        brand_page = next((f"/{pg}/" for slug, _, pg in BRANDS if slug == mb and pg), None)
        if mb:
            brand_label = BRAND_LABEL.get(mb, mb)
        elif len(brands) == 1:
            brand_label = brands[0]
        else:
            brand_label = "Nhiều hãng" if brands else "Theo dự án"
        items = [["Nhóm sản phẩm", CAT_LABEL.get(cat, cat)]]
        if c.get("apps"):
            items.append(["Ứng dụng", ", ".join(APP_LABEL.get(a, a) for a in c["apps"])])
        items.append(["Hãng cung cấp", ", ".join(brands) if brands else "Theo dự án (đề xuất sau khảo sát)"])
        if c.get("model"):
            items.append(["Model tiêu biểu", c["model"] + (f' ({c["model_note"]})' if c.get("model_note") else "")])
        items.append(["Giá tham khảo", price_display(c.get("price")) or "Liên hệ báo giá"])
        desc = (c.get("description") or "").strip()
        recs.append({
            "catalog": True, "slug": cid, "title": c.get("title", ""), "type": CAT_LABEL.get(cat, cat),
            "category": cat, "model": c.get("model") or "", "brand": "_cat", "brand_label": brand_label,
            "brand_page": brand_page, "brand_specific": bool(mb or len(brands) == 1),
            "crumb": (CAT_LABEL.get(cat, cat), f"/san-pham/{cat}/") if (SITE / "san-pham" / cat / "index.html").exists() else None,
            "images": ["/" + c["image"].lstrip("/")] if c.get("image") else [], "image_size": [1000, 1000],
            "icon": CAT_ICONS.get(cat, CAT_ICONS["camera-ai"]),
            # Nội dung viết trong CMS (TinyMCE / Smart content) thay cho phần giới thiệu mặc định.
            "content_html": cms_content,
            "intro": "" if cms_content else (x.get("intro") or desc),
            "model_url": mlink,
            "highlights": x.get("features") or ([desc] if desc and x.get("intro") else []),
            "specs": [{"group": "Thông tin sản phẩm", "items": items}],
            "price": c.get("price"), "brands": c.get("brands") or [],
            "crawled_at": str(c.get("updated_at") or "")[:10],
        })
    # Liên quan: dòng cùng nhóm trước, rồi model chi tiết của các hãng mà dòng này cung cấp.
    for r in recs:
        same = [o for o in recs if o is not r and o["category"] == r["category"]]
        models = [m for m in crawled if m.get("slug") and m.get("brand") in r["brands"]]
        first = [m for m in models if r["model_url"] and pd_url(m) == r["model_url"]]
        models = first + [m for m in models if m not in first]
        r["related"] = (first[:1] and [dict(first[0], title=first[0].get("title_vi") or first[0]["title"])] or [])
        r["related"] += same + [dict(m, title=m.get("title_vi") or m["title"]) for m in models if m not in first]
        r["related"] = r["related"][:4]
    return recs


def product_link_index(products):
    """Model (chữ hoa) -> URL trang chi tiết, để thẻ catalog CMS tự gắn link "Model tiêu biểu"."""
    return {model_key(p["model"]): pd_url(p) for p in products if p.get("model") and p.get("slug")}


def inject_smart_assets(page):
    """Bài Smart content (thân bài có khối class="tv-...") -> nạp CSS/JS khối. Bài thường không
    nạp gì thêm, output giữ nguyên như trước khi có tính năng này."""
    if 'class="tv-' not in page:
        return page
    page = page.replace("</head>", '<link rel="stylesheet" href="/assets/css/smart.css">\n</head>', 1)
    return page.replace("</body>", '<script src="/assets/js/smart.js" defer></script>\n</body>', 1)


def lazy_images(content):
    return re.sub(r"<img(?![^>]*\bloading=)", '<img loading="lazy" decoding="async"', content)


def clean_orphan_pages(parent, keep):
    """Xoá trang con đã bị xoá khỏi CMS (tin tức, dự án). CHỈ đụng thư mục con của `parent` có
    index.html mang GENERATED_MARKER — trang viết tay (không có dấu) không bao giờ bị xoá."""
    for page in parent.glob("*/index.html"):
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
    "telephone": "+84978406868",
    "email": "daotienhic@gmail.com",
    "street": "Số 15 ngõ 26 đường Hoàng Quốc Việt, Nghĩa Đô",
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
    m = re.search(r'<nav class="(?:phero__crumbs|pd-crumbs)"[^>]*>(.*?)</nav>', content, re.S)
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


def seo_block(content, url, article=None, product=None):
    """Khối SEO trong <head>: canonical + robots + Open Graph + Twitter + JSON-LD (@graph).
    article = bản ghi tin tức (data/news.json) nếu là trang bài viết."""
    title = head_text(content, r"<title>(.*?)</title>")
    desc = head_text(content, r'<meta name="description" content="([^"]*)"')
    h1 = strip_tags(head_text(content, r'<h1[^>]*>(.*?)(?:<span|</h1>)')) or title.split(" — ")[0]
    image = abs_url(article["cover"]) if article else page_image(content)
    if product and product.get("images"):
        image = abs_url(product["images"][0])
    is_home = url == SITE_URL + "/"

    tags = [
        f'<link rel="canonical" href="{esc(url)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        f'<meta property="og:type" content="{"article" if article else "product" if product else "website"}">',
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
        # Trang con của tin tức/dự án (1 bài, 1 dự án) là WebPage, không phải trang danh sách.
        "@type": PAGE_TYPES.get(slug, "WebPage") if url.count("/") <= 4 or slug not in ("tin-tuc", "du-an") else "WebPage",
        "@id": url + "#webpage", "url": url, "name": title, "description": desc, "inLanguage": "vi",
        "isPartOf": {"@id": SITE_URL + "/#website"}, "about": org_ref,
        "primaryImageOfPage": {"@type": "ImageObject", "url": image},
    }
    if not is_home:
        graph.append({"@type": "BreadcrumbList", "@id": url + "#breadcrumb",
                      "itemListElement": breadcrumb_items(content, url, h1)})
        page["breadcrumb"] = {"@id": url + "#breadcrumb"}
    if product:
        page["@type"] = "ItemPage"
        page["mainEntity"] = {"@id": url + "#product"}
    if page["@type"] == "FAQPage":
        faqs = faq_entities(content)
        if faqs:
            page["mainEntity"] = faqs
        else:
            page["@type"] = "WebPage"
    graph.append(page)
    if product:
        graph.append(product_ld(product, url))
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


def with_seo(content, url, article=None, product=None):
    """Thay (hoặc chèn) khối SEO; gỡ canonical đứng lẻ cũ để không bị trùng. Idempotent."""
    content = SEO_BLOCK_RE.sub("", content)
    content = CANONICAL_RE.sub("", content)
    block = seo_block(content, url, article, product)
    m = re.search(r'<meta\s+name="description"[^>]*>\n?', content, re.I)
    if m:
        cut = m.end() if m.group(0).endswith("\n") else m.end()
        sep = "" if m.group(0).endswith("\n") else "\n"
        return content[:cut] + sep + block + content[cut:]
    return content.replace("</head>", block + "</head>", 1)


def build_sitemap(news, legacy, products=None):
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
    products = products or {}
    for u, p in products.items():
        lastmod[u] = str(p.get("crawled_at") or "")[:10]

    urls, pages = [], []
    for page in SITE.rglob("index.html"):
        parts = page.relative_to(SITE).parts
        if parts[0] in SITEMAP_SKIP_DIRS:
            continue
        content = read(page)
        if is_noindex(content):
            continue
        url = page_url(page)
        write_if_changed(page, with_seo(content, url, articles.get(url), products.get(url)))
        urls.append(url)
        title = re.split(r"\s+[|—]\s+", head_text(content, r"<title>(.*?)</title>"))[0].strip()
        pages.append({"url": url[len(SITE_URL):] or "/", "title": title})
    # Trang chủ trước, còn lại theo thứ tự chữ cái -> output ổn định, build lại không sinh diff.
    urls.sort(key=lambda u: (u != SITE_URL + "/", u))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
             'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for u in urls:
        lm = lastmod.get(u)
        # Trang sản phẩm: khai thêm ảnh (Google Images) — tối đa 5 ảnh/trang cho gọn.
        imgs = "".join(f"<image:image><image:loc>{esc(abs_url(i))}</image:loc></image:image>"
                       for i in (products.get(u, {}).get("images") or [])[:5])
        lines.append(f"  <url><loc>{esc(u)}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + imgs + "</url>")
    lines.append("</urlset>")
    write_if_changed(SITE / "sitemap.xml", "\n".join(lines) + "\n")
    # Danh sách trang + tiêu đề cho công cụ AI trong CMS chèn link nội bộ (không bịa URL - GAS.md III.9).
    pages.sort(key=lambda x: x["url"])
    write_if_changed(SITE / "assets" / "pages.json", json.dumps(pages, ensure_ascii=False, indent=0) + "\n")

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
    projects = load_json("projects.json", [])
    crawled = load_json("products.json", [])
    PD_LINKS.update(product_link_index(crawled))
    cat_recs = catalog_records(products, crawled)  # điền CAT_LINKS trước khi vẽ thẻ catalog
    print(f"build: {len(products)} sản phẩm, {len(news)} tin CMS + {len(legacy)} tin cũ, "
          f"{len(categories)} danh mục tin, {len(projects)} dự án")
    build_products(products)
    build_news(news, legacy, categories)
    build_projects(projects)
    pd_pages = build_product_pages(crawled, cat_recs)
    print(f"  {len(pd_pages)} trang chi tiết sản phẩm ({len(cat_recs)} trang dòng sản phẩm catalog)")
    count = build_sitemap(news, legacy, pd_pages)
    print(f"xong. sitemap: {count} URL")


if __name__ == "__main__":
    main()

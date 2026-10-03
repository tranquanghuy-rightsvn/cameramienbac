# Remake nội dung & UI/UX toàn site — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nâng cấp 11 trang HTML tĩnh của Cameramienbac (nội dung, UI/UX, behavior header, responsive) lên chuẩn có thể release cho khách hàng, giữ nguyên design system hiện tại.

**Architecture:** Site tĩnh HTML/CSS/JS không có framework, không có test runner. Mỗi trang include `partials/header.html` / `partials/footer.html` qua `fetch()` (`assets/js/main.js`), dùng chung `assets/css/style.css`. Không có bước build. "Kiểm thử" = kiểm tra cấu trúc bằng `grep`/`git diff` + xác nhận trực quan qua trình duyệt tại `python3 -m http.server` (README đã ghi hướng dẫn chạy).

**Tech Stack:** HTML5, CSS3 (không tiền xử lý), Vanilla JS (ES5-style, không module bundler).

**Spec:** `docs/superpowers/specs/2026-09-22-toan-site-remake-design.md`

## Global Constraints

- Giữ nguyên design token (màu, font, layout tổng thể) — chỉ thêm class/rule mới, không sửa token hiện có.
- Không tạo backend thật, không tạo trang chi tiết tin tức, không thêm ảnh thật mới, không thêm số ĐKKD hoặc link MXH giả — đúng phần "Ngoài phạm vi" của spec.
- Tên khách hàng/dự án thật (Vinhomes, FPT, BIDV, Bệnh viện Bạch Mai, ĐHQGHN, Samsung Bắc Ninh, các trường nêu tên) **giữ nguyên** — đã xác nhận là khách hàng thật.
- Đối tác: 2 nhãn cố định xuyên toàn site — **"Đối tác thiết bị"** = Hikvision, Dahua, TVT, Axis, Hanwha; **"Đối tác công nghệ AI"** = FPT, Intel, NVIDIA, Microsoft, AWS, Viettel.
- Mỗi task commit riêng, message tiếng Việt ngắn gọn theo văn phong `feat:`/`fix:`/`content:` đã dùng trong repo.
- Chạy `python3 -m http.server 8000` (README) để xác nhận trực quan trước khi commit các task có thay đổi UI/behavior/responsive.

---

### Task 1: Header sticky + smooth scroll

**Files:**
- Modify: `assets/css/style.css:53` (base), `assets/css/style.css:151-155` (`.site-header`)

**Interfaces:**
- Không có JS/HTML phụ thuộc. Task độc lập hoàn toàn.

- [ ] **Step 1: Thêm `scroll-behavior: smooth` vào `html`**

Sửa dòng 53 từ:
```css
html { -webkit-text-size-adjust: 100%; }
```
thành:
```css
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
```

- [ ] **Step 2: Đổi `.site-header` sang sticky**

Sửa khối dòng 151-155 từ:
```css
.site-header {
  position: relative;
  z-index: 60;
  background: #001338 url("../images/header-bg.jpg") center / cover no-repeat;
}
```
thành:
```css
.site-header {
  position: sticky;
  top: 0;
  z-index: 60;
  background: #001338 url("../images/header-bg.jpg") center / cover no-repeat;
}
```

- [ ] **Step 3: Xác nhận trực quan**

Chạy `python3 -m http.server 8000`, mở `http://localhost:8000/du-an.html` (trang dài), cuộn xuống — header phải dính ở top, không bị đè bởi nội dung, không có khoảng trắng lạ phía trên.

- [ ] **Step 4: Commit**

```bash
git add assets/css/style.css
git commit -m "feat(header): header dính khi cuộn, thêm scroll mượt cho anchor"
```

---

### Task 2: Mobile nav behavior — khoá scroll, Escape, click-outside, aria-expanded

**Files:**
- Modify: `assets/js/main.js` (toàn bộ `initNav`)
- Modify: `assets/css/style.css` (thêm class `body.nav-locked` gần block `.nav-toggle` responsive, dòng ~783)

**Interfaces:**
- Consumes: DOM có sẵn sau khi `partials/header.html` được include (không đổi cấu trúc HTML của header).
- Produces: hàm `initNav(root)` trong `main.js` (tên giữ nguyên, chữ ký giữ nguyên `function initNav(root)`), được gọi từ `DOMContentLoaded` handler đã có sẵn — không có task nào khác phụ thuộc vào nội bộ hàm này.

- [ ] **Step 1: Thêm CSS khoá scroll cho `<body>`**

Thêm ngay trước `.nav-toggle { display: none; }` ở dòng 270 của `assets/css/style.css`:
```css
body.nav-locked { overflow: hidden; }
```

- [ ] **Step 2: Viết lại `initNav` trong `assets/js/main.js`**

Thay toàn bộ hàm `initNav` (dòng 10-32) bằng:
```javascript
  function initNav(root) {
    var toggle = root.querySelector(".nav-toggle");
    var nav = root.querySelector(".main-nav");
    var header = root.querySelector(".site-header");

    function closeMenu() {
      if (!nav || !nav.classList.contains("is-open")) return;
      nav.classList.remove("is-open");
      document.body.classList.remove("nav-locked");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }

    function openMenu() {
      if (!nav) return;
      nav.classList.add("is-open");
      document.body.classList.add("nav-locked");
      if (toggle) toggle.setAttribute("aria-expanded", "true");
    }

    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        if (nav.classList.contains("is-open")) {
          closeMenu();
        } else {
          openMenu();
        }
      });
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" || event.key === "Esc") {
        closeMenu();
        root.querySelectorAll(".nav-group.is-open").forEach(function (group) {
          group.classList.remove("is-open");
        });
      }
    });

    document.addEventListener("click", function (event) {
      if (!nav || !nav.classList.contains("is-open")) return;
      if (header && header.contains(event.target)) return;
      closeMenu();
    });

    // On touch/narrow layouts the first tap opens the submenu instead of navigating.
    root.querySelectorAll(".nav-group").forEach(function (group) {
      var link = group.querySelector(".nav-link");
      if (!link) return;
      link.addEventListener("click", function (event) {
        if (window.matchMedia("(max-width: 1023px)").matches && !group.classList.contains("is-open")) {
          event.preventDefault();
          group.classList.add("is-open");
          group.setAttribute("aria-expanded", "true");
        }
      });
    });
  }
```

- [ ] **Step 3: Xác nhận không có lỗi cú pháp**

Chạy: `node --check assets/js/main.js`
Expected: không in gì ra (exit code 0).

- [ ] **Step 4: Xác nhận trực quan (thu nhỏ trình duyệt < 1024px)**

- Bấm hamburger → menu mở, nền trang không cuộn được (thử cuộn chuột trên phần overlay).
- Bấm phím Escape → menu đóng.
- Mở lại menu, click ra ngoài `<header>` (vd vào `<main>`) → menu đóng.
- Bấm vào "Giải pháp" (có submenu) lần đầu → submenu mở, không điều hướng; bấm lần hai → điều hướng sang `giai-phap.html`.

- [ ] **Step 5: Commit**

```bash
git add assets/js/main.js assets/css/style.css
git commit -m "fix(header): khoá scroll nền, đóng menu mobile bằng Escape/click-outside, thêm aria-expanded cho submenu"
```

---

### Task 3: Footer — cột Liên kết nhanh, dòng bản quyền, ẩn icon MXH chưa có link thật

**Files:**
- Modify: `partials/footer.html`
- Modify: `assets/css/style.css` (thêm block CSS mới gần "11. Footer", sau dòng 778; sửa `.footer__inner` grid tại dòng 679-701, 839-843, 892-897)
- Modify: `assets/js/main.js` (thêm gán năm hiện tại)

**Interfaces:**
- Sản phẩm: cột mới `<div class="footer__col footer__col--links">` với id `footer-year` cho span năm — task 12 (lien-he.html social icons) tham chiếu cùng quyết định "ẩn icon MXH chưa có link thật" nhưng là file khác, không phụ thuộc kỹ thuật lẫn nhau.

- [ ] **Step 1: Sửa `partials/footer.html`** — xoá `.footer__social` (5 icon `href="#"`), thêm cột Liên kết nhanh, thêm dòng bản quyền dưới `.footer__inner`

Thay toàn bộ nội dung file bằng:
```html
<footer class="site-footer">
  <div class="container footer__inner">

    <div class="footer__col footer__col--brand">
      <a class="brand" href="index.html" aria-label="Cameramienbac — AI &amp; Smart">
        <svg class="brand__mark" viewBox="0 0 48 58" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="bf-shell" x1="1.6" y1="29" x2="46.4" y2="29" gradientUnits="userSpaceOnUse">
              <stop stop-color="#18cbfd"/>
              <stop offset=".5" stop-color="#0ab5fb"/>
              <stop offset="1" stop-color="#0293f7"/>
            </linearGradient>
            <linearGradient id="bf-lens" x1="14" y1="14" x2="34" y2="49" gradientUnits="userSpaceOnUse">
              <stop stop-color="#07a4e8"/>
              <stop offset="1" stop-color="#20c9fe"/>
            </linearGradient>
          </defs>
          <path d="M24 .6 46.4 9v19.6c0 13-9.4 22-22.4 28.8C11 50.6 1.6 41.6 1.6 28.6V9L24 .6Z" fill="url(#bf-shell)"/>
          <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8-9-4.8-15.6-11.4-15.6-20.8V13.9L24 7.6Z" fill="#00235f"/>
          <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8V7.6Z" fill="#3c74ce" opacity=".62"/>
          <rect x="13.8" y="15" width="8.4" height="33.6" rx="4.2" fill="url(#bf-lens)"/>
          <circle cx="26" cy="26.8" r="12.1" fill="url(#bf-lens)"/>
          <circle cx="26" cy="26.8" r="5" fill="#0a2a66" opacity=".16"/>
          <circle cx="34.6" cy="12.8" r="1.7" fill="#bfe9ff" opacity=".85"/>
        </svg>
        <span class="brand__text">
          <span class="brand__name">CAMERAMIENBAC</span>
          <span class="brand__sub">AI &amp; SMART</span>
        </span>
      </a>
      <p class="footer__tagline">Camera AI &amp; giải pháp an ninh thông minh cho doanh nghiệp, trường học và tòa nhà.</p>
    </div>

    <div class="footer__col footer__col--links">
      <span class="footer__label footer__label--head">Liên kết nhanh</span>
      <nav class="footer__links" aria-label="Liên kết nhanh">
        <a href="giai-phap.html">Giải pháp</a>
        <a href="san-pham.html">Sản phẩm</a>
        <a href="du-an.html">Dự án</a>
        <a href="ve-chung-toi.html">Về chúng tôi</a>
        <a href="tin-tuc.html">Tin tức</a>
        <a href="lien-he.html">Liên hệ</a>
      </nav>
    </div>

    <div class="footer__col footer__col--contact">
      <div class="footer__row">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M6.3 10.6a15.1 15.1 0 0 0 6.5 6.5l2.1-2.1a1 1 0 0 1 1-.25c1.1.37 2.3.57 3.5.57a1 1 0 0 1 1 1v3.3a1 1 0 0 1-1 1A16.6 16.6 0 0 1 3 4.1a1 1 0 0 1 1-1h3.3a1 1 0 0 1 1 1c0 1.2.2 2.4.57 3.5a1 1 0 0 1-.25 1l-2.1 2Z"/>
          <path d="M15.4 3.9a6.4 6.4 0 0 1 4.7 4.7"/>
        </svg>
        <div>
          <span class="footer__label">Tư vấn &amp; Hỗ trợ (Quốc Việt, Cầu Giấy, Hà Nội)</span>
          <a class="footer__phone" href="tel:0979406868">0979 406 868</a>
        </div>
      </div>

      <div class="footer__row">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linejoin="round" aria-hidden="true">
          <rect x="2.6" y="5" width="18.8" height="14" rx="1.4"/>
          <path d="m3.4 6.2 8.6 6.6 8.6-6.6"/>
        </svg>
        <a class="footer__mail" href="mailto:cameramienbac@cmvn.vn">cameramienbac@cmvn.vn</a>
      </div>
    </div>

    <div class="footer__col footer__col--cta">
      <p class="footer__cta-text">Bất cứ thắc mắc nào, chúng tôi luôn sẵn sàng hỗ trợ bạn!</p>
      <a class="btn btn--solid" href="lien-he.html">
        Nhận tư vấn ngay
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>
      </a>
    </div>

  </div>
  <div class="footer__bottom">
    <div class="container footer__bottom-inner">
      <span>© <span id="footer-year">2026</span> Cameramienbac. All rights reserved.</span>
    </div>
  </div>
</footer>
```

- [ ] **Step 2: Cập nhật CSS grid footer từ 3 cột lên 4 cột + style cột mới + thanh bản quyền**

Sửa dòng 679-701 từ:
```css
.footer__inner {
  display: grid;
  grid-template-columns: 1fr 1.2fr 0.8fr;
  gap: 32px;
  min-height: 172px;
  padding: 32px 0 36px;
  align-items: start;
}

.footer__col { position: relative; padding-top: 0; }

.footer__col + .footer__col::before {
  content: "";
  position: absolute;
  left: 0;
  top: 4px;
  height: 80px;
  border-left: 1px solid rgba(120, 175, 225, .35);
}

.footer__col--brand { padding-left: 0; }
.footer__col--contact { padding-left: 32px; }
.footer__col--cta { padding-left: 32px; text-align: right; }
```
thành:
```css
.footer__inner {
  display: grid;
  grid-template-columns: 1.1fr 0.8fr 1.1fr 0.8fr;
  gap: 32px;
  min-height: 172px;
  padding: 32px 0 36px;
  align-items: start;
}

.footer__col { position: relative; padding-top: 0; }

.footer__col + .footer__col::before {
  content: "";
  position: absolute;
  left: 0;
  top: 4px;
  height: 80px;
  border-left: 1px solid rgba(120, 175, 225, .35);
}

.footer__col--brand { padding-left: 0; }
.footer__col--links { padding-left: 32px; }
.footer__col--contact { padding-left: 32px; }
.footer__col--cta { padding-left: 32px; text-align: right; }

.footer__tagline { margin-top: 14px; max-width: 240px; font-size: 14px; line-height: 20px; color: #a9c6e8; }

.footer__label--head { display: block; margin-bottom: 14px; font-size: 14px; font-weight: 600; color: #fff; }

.footer__links { display: flex; flex-direction: column; gap: 10px; }
.footer__links a { font-size: 14px; color: #c0d8f0; }
.footer__links a:hover { color: var(--cyan-300); }

.footer__bottom { border-top: 1px solid rgba(120, 175, 225, .25); }
.footer__bottom-inner { padding: 16px 0; font-size: 13px; color: #90aed4; text-align: center; }
```

- [ ] **Step 3: Cập nhật 2 breakpoint responsive của footer**

Sửa dòng 839-843 (trong `@media (max-width: 1023px)`) từ:
```css
  .footer__inner { grid-template-columns: 1fr 1fr; gap: 28px 0; padding: 28px 0 32px; }
  .footer__col--cta { grid-column: 1 / -1; padding-left: 0; text-align: left; }
  .footer__col--cta::before { display: none; }
  .footer__cta-text { margin-left: 0; }
  .footer__col--cta .btn { margin-left: 0; }
```
thành:
```css
  .footer__inner { grid-template-columns: 1fr 1fr; gap: 28px 0; padding: 28px 0 32px; }
  .footer__col--links, .footer__col--contact { padding-left: 0; }
  .footer__col--cta { grid-column: 1 / -1; padding-left: 0; text-align: left; }
  .footer__col--cta::before { display: none; }
  .footer__cta-text { margin-left: 0; }
  .footer__col--cta .btn { margin-left: 0; }
```

Sửa dòng 892-897 (trong `@media (max-width: 719px)`) từ:
```css
  .footer__inner { grid-template-columns: 1fr; gap: 24px; padding: 24px 0 28px; }
  .footer__col + .footer__col::before { display: none; }
  .footer__col--contact { padding-left: 0; }
  .footer__col--cta { text-align: left; }
  .footer__cta-text { margin-left: 0; }
  .footer__col--cta .btn { margin-left: 0; }
```
thành:
```css
  .footer__inner { grid-template-columns: 1fr; gap: 24px; padding: 24px 0 28px; }
  .footer__col + .footer__col::before { display: none; }
  .footer__col--links, .footer__col--contact { padding-left: 0; }
  .footer__col--cta { text-align: left; }
  .footer__cta-text { margin-left: 0; }
  .footer__col--cta .btn { margin-left: 0; }
```

- [ ] **Step 4: Gán năm hiện tại vào `#footer-year` trong `assets/js/main.js`**

Trong `document.addEventListener("DOMContentLoaded", ...)`, sau dòng `Promise.all(slots.map(include)).then(function () {`, thêm dòng gán năm ngay sau `markCurrent(document);`:
```javascript
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
```

- [ ] **Step 5: Xác nhận trực quan + grep**

`grep -n 'footer__social\|href="#"' partials/footer.html` → không còn kết quả nào.
Mở bất kỳ trang nào trong trình duyệt, cuộn xuống footer: 4 cột hiển thị đúng ở desktop, năm hiện tại hiển thị đúng, không còn icon MXH.

- [ ] **Step 6: Commit**

```bash
git add partials/footer.html assets/css/style.css assets/js/main.js
git commit -m "feat(footer): thêm liên kết nhanh, dòng bản quyền, bỏ icon MXH chưa có link thật"
```

---

### Task 4: Fix bug responsive grid-template-columns inline (aiot-platform.html + trung-tam-ai.html)

**Files:**
- Modify: `aiot-platform.html:33,71,115,134`
- Modify: `trung-tam-ai.html:33`
- Modify: `assets/css/style.css` (thêm 2 class mới trước block "responsive" ở dòng 2286, thêm fallback mobile trong `@media (max-width: 719px)` dòng 2294-2298)

**Interfaces:**
- Sản phẩm: 2 class CSS mới `.grid--ai-intro`, `.grid--iot-features`. Không class nào khác trong plan dùng lại 2 tên này.

- [ ] **Step 1: Thêm 2 class mới vào `assets/css/style.css`**

Thêm ngay trước dòng `/* --- responsive ---------------------------------------------------------- */` (dòng 2286):
```css
.grid--ai-intro { grid-template-columns: 1fr 1fr; gap: 20px; align-items: center; }
.grid--iot-features { grid-template-columns: 1.35fr 1fr; gap: 18px; align-items: start; }
```

Sửa khối `@media (max-width: 719px)` (dòng 2294-2298) từ:
```css
@media (max-width: 719px) {
  .value-band__list { grid-template-columns: 1fr; }
  .svc { flex-direction: column; }
  .boxed { padding: 18px 16px 20px; }
}
```
thành:
```css
@media (max-width: 719px) {
  .value-band__list { grid-template-columns: 1fr; }
  .svc { flex-direction: column; }
  .boxed { padding: 18px 16px 20px; }
  .grid--ai-intro, .grid--iot-features { grid-template-columns: 1fr; }
}
```

- [ ] **Step 2: Sửa `trung-tam-ai.html:33`**

Từ:
```html
      <div class="grid" style="grid-template-columns:1fr 1fr;gap:20px;align-items:center">
```
thành:
```html
      <div class="grid grid--ai-intro">
```

- [ ] **Step 3: Sửa `aiot-platform.html:33`**

Từ:
```html
      <div class="grid" style="grid-template-columns:1.35fr 1fr;gap:18px;align-items:start">
```
thành:
```html
      <div class="grid grid--iot-features">
```

- [ ] **Step 4: Dọn 3 inline style thừa còn lại trong `aiot-platform.html`**

Dòng 71, từ:
```html
          <div class="grid grid--3" style="gap:12px">
```
thành:
```html
          <div class="grid grid--3 grid--tight">
```
Thêm class `.grid--tight { gap: 12px; }` vào ngay dưới 2 class vừa thêm ở Step 1 (cùng vị trí, trước comment responsive):
```css
.grid--tight { gap: 12px; }
```

Dòng 115 và 134, xoá `style="margin-top:12px"` (đã có sẵn trong `.arch__link` ở CSS dòng 2164) — từ:
```html
          <p class="arch__link" style="margin-top:12px"><b>Kết nối</b>IoT / Internet →</p>
```
thành:
```html
          <p class="arch__link"><b>Kết nối</b>IoT / Internet →</p>
```
và từ:
```html
          <p class="arch__link" style="margin-top:12px"><b>API / SDK</b>← Kết nối hai chiều</p>
```
thành:
```html
          <p class="arch__link"><b>API / SDK</b>← Kết nối hai chiều</p>
```

- [ ] **Step 5: Xác nhận**

`grep -n 'style="' aiot-platform.html trung-tam-ai.html` → chỉ còn các dòng thuộc Task 5 (chưa chạy) ở `trung-tam-ai.html`, không còn dòng nào ở `aiot-platform.html`.

Thu nhỏ trình duyệt xuống ≤719px, mở `aiot-platform.html` và `trung-tam-ai.html`: 2 khối grid 2 cột phải chuyển thành 1 cột, không tràn ngang.

- [ ] **Step 6: Commit**

```bash
git add aiot-platform.html trung-tam-ai.html assets/css/style.css
git commit -m "fix(responsive): sửa bug inline grid-template-columns khiến layout không đổ 1 cột trên mobile"
```

---

### Task 5: trung-tam-ai.html — dọn inline style còn lại, sửa số liệu, tách nhãn đối tác

**Files:**
- Modify: `trung-tam-ai.html:36,38,43,145-160,164-200`
- Modify: `assets/css/style.css` (thêm CSS mới gần `.boxed__head` ở dòng 2049, gần `.news--wide` ở dòng ~1995)

**Interfaces:**
- Produces: CSS class `.boxed__head--row`, `.boxed__head--sub`, `.news--compact`, và rule `.boxed__head + .psec__lead { margin-top: 0; }`. Task 7 (ve-chung-toi.html) **tiêu thụ** rule `.boxed__head + .psec__lead` — phải chạy Task 5 trước Task 7.

- [ ] **Step 1: Thêm CSS mới vào `assets/css/style.css`**

Thêm ngay sau dòng `.boxed__head p { flex: 1 0 100%; margin: -4px 0 0 45px; font-size: 15px; color: #4b6a97; font-weight: 400; }` (dòng 2049):
```css
.boxed__head + .psec__lead { margin-top: 0; }
.boxed__head--row { justify-content: space-between; }
.boxed__head--row > span { display: flex; align-items: center; gap: 11px; }
.boxed__head--row .link-more { margin-top: 0; }
.boxed__head--sub { margin-top: 24px; }
```

Thêm ngay sau dòng `.news--wide .news__title { font-size: 21px; }` (gần dòng 1995):
```css
.news--compact .news__title { font-size: 13px; }
```

- [ ] **Step 2: Sửa dòng 36 — bỏ inline `margin-top:0`**

Từ:
```html
          <p class="psec__lead" style="margin-top:0">Trung tâm AI của Cameramienbac tập trung nghiên cứu, phát triển và triển khai các giải pháp trí tuệ nhân tạo tiên tiến, ứng dụng vào các lĩnh vực an ninh, giám sát, quản lý đô thị, giao thông, giáo dục, y tế và doanh nghiệp.</p>
```
thành:
```html
          <p class="psec__lead">Trung tâm AI của Cameramienbac tập trung nghiên cứu, phát triển và triển khai các giải pháp trí tuệ nhân tạo tiên tiến, ứng dụng vào các lĩnh vực an ninh, giám sát, quản lý đô thị, giao thông, giáo dục, y tế và doanh nghiệp.</p>
```

- [ ] **Step 3: Sửa dòng 38 — hạ số chuyên gia AI xuống mức nhất quán với tổng "60+ kỹ sư" của công ty**

Từ:
```html
            <li><b>100+</b><span>Chuyên gia AI và công nghệ</span></li>
```
thành:
```html
            <li><b>30+</b><span>Chuyên gia AI và công nghệ</span></li>
```

- [ ] **Step 4: Sửa dòng 43 — thay inline style bằng `.btn--sm`**

Từ:
```html
          <a class="btn btn--solid" href="lien-he.html" style="width:auto;height:38px;padding:0 20px;font-size:13px;margin-top:18px;gap:10px">Tìm hiểu thêm <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
```
thành:
```html
          <a class="btn btn--solid btn--sm" href="lien-he.html">Tìm hiểu thêm <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
```

- [ ] **Step 5: Tách khối "ĐỐI TÁC CÔNG NGHỆ" thành 2 nhóm nhãn**

Thay toàn bộ section (dòng 145-160):
```html
  <section class="psec psec--tint">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg></i><h2>ĐỐI TÁC CÔNG NGHỆ</h2>
          <p>Chúng tôi hợp tác với các đối tác hàng đầu để mang đến giải pháp AI tốt nhất cho khách hàng.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/brand-fpt.jpg" alt="FPT" loading="lazy"></li>
          <li><img src="assets/images/brand-intel.jpg" alt="Intel" loading="lazy"></li>
          <li><img src="assets/images/brand-nvidia.jpg" alt="NVIDIA" loading="lazy"></li>
          <li><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></li>
          <li><img src="assets/images/partner-dahua.png" alt="Dahua" loading="lazy"></li>
          <li><img src="assets/images/brand-microsoft.jpg" alt="Microsoft" loading="lazy"></li>
        </ul>
      </div>
    </div>
  </section>
```
bằng:
```html
  <section class="psec psec--tint">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg></i><h2>ĐỐI TÁC CÔNG NGHỆ AI</h2>
          <p>Nền tảng và hạ tầng AI chúng tôi hợp tác để phát triển giải pháp.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/brand-fpt.jpg" alt="FPT" loading="lazy"></li>
          <li><img src="assets/images/brand-intel.jpg" alt="Intel" loading="lazy"></li>
          <li><img src="assets/images/brand-nvidia.jpg" alt="NVIDIA" loading="lazy"></li>
          <li><img src="assets/images/brand-microsoft.jpg" alt="Microsoft" loading="lazy"></li>
          <li><img src="assets/images/brand-aws.jpg" alt="AWS" loading="lazy"></li>
          <li><img src="assets/images/brand-viettel.jpg" alt="Viettel" loading="lazy"></li>
        </ul>
        <div class="boxed__head boxed__head--sub"><h2>ĐỐI TÁC THIẾT BỊ</h2>
          <p>Thương hiệu camera và thiết bị an ninh chúng tôi triển khai.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></li>
          <li><img src="assets/images/partner-dahua.png" alt="Dahua" loading="lazy"></li>
          <li><img src="assets/images/partner-tvt.png" alt="TVT" loading="lazy"></li>
          <li><img src="assets/images/partner-axis.png" alt="Axis" loading="lazy"></li>
          <li><img src="assets/images/partner-hanwha.png" alt="Hanwha Vision" loading="lazy"></li>
        </ul>
      </div>
    </div>
  </section>
```

- [ ] **Step 6: Dọn khối "TIN TỨC & SỰ KIỆN" (dòng 164-200) — bỏ inline style, dùng `.boxed__head--row` và `.news--compact`**

Từ:
```html
        <div class="boxed__head" style="justify-content:space-between">
          <span style="display:flex;align-items:center;gap:11px"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.4 3.4H6.6a2 2 0 0 0-2 2v13.2a2 2 0 0 0 2 2h10.8a2 2 0 0 0 2-2V9.4l-6-6Z"/><path d="M13.4 3.4v6h6"/></svg></i><h2>TIN TỨC &amp; SỰ KIỆN</h2></span>
          <a class="link-more" href="tin-tuc.html" style="margin:0">Xem tất cả <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i></a>
        </div>
```
thành:
```html
        <div class="boxed__head boxed__head--row">
          <span><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.4 3.4H6.6a2 2 0 0 0-2 2v13.2a2 2 0 0 0 2 2h10.8a2 2 0 0 0 2-2V9.4l-6-6Z"/><path d="M13.4 3.4v6h6"/></svg></i><h2>TIN TỨC &amp; SỰ KIỆN</h2></span>
          <a class="link-more" href="tin-tuc.html">Xem tất cả <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i></a>
        </div>
```

Trong 4 thẻ `<article class="news">` ngay dưới (bọc 4 tin), đổi `class="news"` thành `class="news news--compact"` (4 chỗ), và bỏ `style="font-size:13px"` trên mỗi `<h3 class="news__title" style="font-size:13px">` (4 chỗ) — chỉ còn `<h3 class="news__title">`.

- [ ] **Step 7: Xác nhận**

`grep -n 'style="' trung-tam-ai.html` → không còn kết quả.

- [ ] **Step 8: Commit**

```bash
git add trung-tam-ai.html assets/css/style.css
git commit -m "content(trung-tam-ai): dọn inline style, sửa số chuyên gia AI, tách nhãn đối tác thiết bị/AI"
```

---

### Task 6: aiot-platform.html — tách nhãn đối tác

**Files:**
- Modify: `aiot-platform.html:154-168`

**Interfaces:**
- Consumes: class `.boxed__head--sub` từ Task 5 (đã tồn tại trong `assets/css/style.css` sau Task 5) — chạy sau Task 5.

- [ ] **Step 1: Tách khối "THƯƠNG HIỆU ĐỒNG HÀNH" thành 2 nhóm nhãn**

Thay (dòng 154-168):
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg></i><h2>THƯƠNG HIỆU ĐỒNG HÀNH</h2>
          <p>Chúng tôi hợp tác với các đối tác công nghệ hàng đầu để mang đến giải pháp AIoT tối ưu nhất.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></li>
          <li><img src="assets/images/partner-dahua.png" alt="Dahua" loading="lazy"></li>
          <li><img src="assets/images/brand-viettel.jpg" alt="Viettel" loading="lazy"></li>
          <li><img src="assets/images/brand-fpt.jpg" alt="FPT" loading="lazy"></li>
          <li><img src="assets/images/brand-microsoft.jpg" alt="Microsoft" loading="lazy"></li>
          <li><img src="assets/images/brand-intel.jpg" alt="Intel" loading="lazy"></li>
          <li><img src="assets/images/brand-aws.jpg" alt="AWS" loading="lazy"></li>
        </ul>
      </div>
    </div>
  </section>
```
bằng:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg></i><h2>ĐỐI TÁC CÔNG NGHỆ AI</h2>
          <p>Chúng tôi hợp tác với các đối tác công nghệ hàng đầu để mang đến giải pháp AIoT tối ưu nhất.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/brand-fpt.jpg" alt="FPT" loading="lazy"></li>
          <li><img src="assets/images/brand-intel.jpg" alt="Intel" loading="lazy"></li>
          <li><img src="assets/images/brand-microsoft.jpg" alt="Microsoft" loading="lazy"></li>
          <li><img src="assets/images/brand-aws.jpg" alt="AWS" loading="lazy"></li>
          <li><img src="assets/images/brand-viettel.jpg" alt="Viettel" loading="lazy"></li>
        </ul>
        <div class="boxed__head boxed__head--sub"><h2>ĐỐI TÁC THIẾT BỊ</h2>
          <p>Thương hiệu camera và thiết bị IoT chúng tôi tích hợp vào nền tảng.</p></div>
        <ul class="logo-strip">
          <li><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></li>
          <li><img src="assets/images/partner-dahua.png" alt="Dahua" loading="lazy"></li>
          <li><img src="assets/images/partner-tvt.png" alt="TVT" loading="lazy"></li>
          <li><img src="assets/images/partner-axis.png" alt="Axis" loading="lazy"></li>
          <li><img src="assets/images/partner-hanwha.png" alt="Hanwha Vision" loading="lazy"></li>
        </ul>
      </div>
    </div>
  </section>
```

- [ ] **Step 2: Xác nhận**

`grep -c 'logo-strip' aiot-platform.html` → `2`.

- [ ] **Step 3: Commit**

```bash
git add aiot-platform.html
git commit -m "content(aiot-platform): tách nhãn đối tác thiết bị/công nghệ AI"
```

---

### Task 7: ve-chung-toi.html — dọn inline style, sửa số liệu, tách nhãn đối tác, polish đội ngũ

**Files:**
- Modify: `ve-chung-toi.html:48,50,98-99,121-146`
- Modify: `assets/css/style.css` (thêm 2 modifier class gần `.split__panel`/`.split__text` dòng 1300, gần `.person` nếu cần)

**Interfaces:**
- Consumes: rule `.boxed__head + .psec__lead { margin-top: 0; }` và class `.boxed__head--sub` từ Task 5 — chạy sau Task 5.

- [ ] **Step 1: Thêm 2 modifier class vào `assets/css/style.css`**

Thêm ngay sau dòng `.split__text { max-width: 360px; margin-top: 10px; font-size: 15px; line-height: 23px; color: #cfe2f7; }` (dòng 1300):
```css
.split__text--wide { max-width: none; }
.split__panel--about { background-image: url("../images/prj-2.jpg"); }
```

- [ ] **Step 2: Sửa dòng 48, 50 — bỏ 2 inline style**

Từ:
```html
        <div class="split__panel" style="background-image:url('assets/images/prj-2.jpg')">
          <h2 class="split__title">Câu chuyện của chúng tôi</h2>
          <p class="split__text" style="max-width:none">Khởi đầu từ một nhóm kỹ sư đam mê công nghệ giám sát, Cameramienbac đã phát triển thành đối tác triển khai camera AI cho hàng trăm doanh nghiệp. Chúng tôi tin rằng an ninh tốt không nằm ở số lượng camera, mà ở khả năng hiểu và phản ứng kịp thời với những gì camera nhìn thấy.</p>
```
thành:
```html
        <div class="split__panel split__panel--about">
          <h2 class="split__title">Câu chuyện của chúng tôi</h2>
          <p class="split__text split__text--wide">Khởi đầu từ một nhóm kỹ sư đam mê công nghệ giám sát, Cameramienbac đã phát triển thành đối tác triển khai camera AI cho hàng trăm doanh nghiệp. Chúng tôi tin rằng an ninh tốt không nằm ở số lượng camera, mà ở khả năng hiểu và phản ứng kịp thời với những gì camera nhìn thấy.</p>
```

- [ ] **Step 3: Sửa dòng 98-99 — chỉnh lead "Đội ngũ" cho khớp số liệu chuẩn**

Giữ nguyên nội dung (đã đúng "Hơn 60 kỹ sư"), không cần sửa số ở bước này — chỉ xác nhận không đổi.

- [ ] **Step 4: Sửa khối "TRUNG TÂM AI" (dòng 121-131) — hạ số chuyên gia AI, bỏ inline style**

Từ:
```html
  <section class="psec psec--tint">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.4" y="6.4" width="11.2" height="11.2" rx="1.6"/><rect x="9.8" y="9.8" width="4.4" height="4.4" rx=".8"/><path d="M9.4 2.6v3.8M14.6 2.6v3.8M9.4 17.6v3.8M14.6 17.6v3.8M2.6 9.4h3.8M2.6 14.6h3.8M17.6 9.4h3.8M17.6 14.6h3.8"/></svg></i>
          <h2>TRUNG TÂM AI</h2>
          <p>Bộ phận nghiên cứu và phát triển các giải pháp trí tuệ nhân tạo của Cameramienbac.</p></div>
        <p class="psec__lead" style="margin-top:0">Hơn 100 chuyên gia AI và công nghệ, 50+ dự án AI đã triển khai trong các lĩnh vực an ninh, giao thông, đô thị, giáo dục và y tế.</p>
        <a class="link-more" href="trung-tam-ai.html"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Tìm hiểu Trung tâm AI</a>
      </div>
    </div>
  </section>
```
thành:
```html
  <section class="psec psec--tint">
    <div class="container">
      <div class="boxed">
        <div class="boxed__head"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.4" y="6.4" width="11.2" height="11.2" rx="1.6"/><rect x="9.8" y="9.8" width="4.4" height="4.4" rx=".8"/><path d="M9.4 2.6v3.8M14.6 2.6v3.8M9.4 17.6v3.8M14.6 17.6v3.8M2.6 9.4h3.8M2.6 14.6h3.8M17.6 9.4h3.8M17.6 14.6h3.8"/></svg></i>
          <h2>TRUNG TÂM AI</h2>
          <p>Bộ phận nghiên cứu và phát triển các giải pháp trí tuệ nhân tạo của Cameramienbac.</p></div>
        <p class="psec__lead">Hơn 30 chuyên gia AI và công nghệ, 50+ dự án AI đã triển khai trong các lĩnh vực an ninh, giao thông, đô thị, giáo dục và y tế.</p>
        <a class="link-more" href="trung-tam-ai.html"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Tìm hiểu Trung tâm AI</a>
      </div>
    </div>
  </section>
```

- [ ] **Step 5: Sửa khối "Đối tác công nghệ" (dòng 132-146) — đổi nhãn thành "Đối tác thiết bị" + thêm nhóm "Đối tác công nghệ AI"**

Từ:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="psec__head">
        <h2 class="psec__title">Đối tác công nghệ</h2>
        <p class="psec__lead">Chúng tôi là đối tác uỷ quyền của các thương hiệu camera hàng đầu thế giới.</p>
      </div>
      <div class="partners__list" style="margin-top:0">
        <div class="partners__item"><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-dahua.png" alt="Dahua Technology" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-tvt.png" alt="TVT" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-axis.png" alt="Axis Communications" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-hanwha.png" alt="Hanwha Vision" loading="lazy"></div>
      </div>
    </div>
  </section>
```
thành:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="psec__head">
        <h2 class="psec__title">Đối tác thiết bị</h2>
        <p class="psec__lead">Chúng tôi là đối tác uỷ quyền của các thương hiệu camera hàng đầu thế giới.</p>
      </div>
      <div class="partners__list">
        <div class="partners__item"><img src="assets/images/partner-hikvision.png" alt="Hikvision" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-dahua.png" alt="Dahua Technology" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-tvt.png" alt="TVT" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-axis.png" alt="Axis Communications" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/partner-hanwha.png" alt="Hanwha Vision" loading="lazy"></div>
      </div>
      <div class="psec__head" style="margin-top:28px">
        <h2 class="psec__title">Đối tác công nghệ AI</h2>
        <p class="psec__lead">Nền tảng và hạ tầng AI chúng tôi hợp tác để phát triển Trung tâm AI.</p>
      </div>
      <div class="partners__list">
        <div class="partners__item"><img src="assets/images/brand-fpt.jpg" alt="FPT" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/brand-intel.jpg" alt="Intel" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/brand-nvidia.jpg" alt="NVIDIA" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/brand-microsoft.jpg" alt="Microsoft" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/brand-aws.jpg" alt="AWS" loading="lazy"></div>
        <div class="partners__item"><img src="assets/images/brand-viettel.jpg" alt="Viettel" loading="lazy"></div>
      </div>
    </div>
  </section>
```

Ghi chú: `style="margin-top:28px"` trên `.psec__head` thứ hai là inline mới duy nhất được thêm ở bước này để tách khoảng cách giữa 2 nhóm — chấp nhận được vì đây là spacing one-off giữa 2 khối lặp lại cấu trúc trong cùng 1 section, không phải giá trị thiết kế lặp lại nhiều nơi như các trường hợp đã dọn ở Task 5-7. Nếu muốn dọn triệt để, có thể thay bằng class `.psec__head--spaced { margin-top: 28px; }` — thêm class này vào `assets/css/style.css` ngay cạnh `.psec__head { margin-bottom: 20px; }` (dòng 1007) và dùng `class="psec__head psec__head--spaced"` thay vì inline.

- [ ] **Step 6: Áp dụng `.psec__head--spaced` thay vì inline (hoàn thiện Step 5)**

Thêm vào `assets/css/style.css` ngay sau dòng `.psec__head { margin-bottom: 20px; }` (dòng 1007):
```css
.psec__head--spaced { margin-top: 28px; }
```
Sửa lại dòng vừa thêm ở Step 5 từ `<div class="psec__head" style="margin-top:28px">` thành `<div class="psec__head psec__head--spaced">`.

- [ ] **Step 7: Xác nhận**

`grep -n 'style="' ve-chung-toi.html` → không còn kết quả.
`grep -c 'partners__list' ve-chung-toi.html` → `2`.

- [ ] **Step 8: Commit**

```bash
git add ve-chung-toi.html assets/css/style.css
git commit -m "content(ve-chung-toi): dọn inline style, sửa số chuyên gia AI, tách nhãn đối tác thiết bị/AI"
```

---

### Task 8: giai-phap.html — thêm card Trung tâm AI, rút gọn section trùng lặp thành teaser

**Files:**
- Modify: `giai-phap.html:33-79` (Nhóm giải pháp chính)
- Modify: `giai-phap.html:110-154` (Giải pháp theo từng lĩnh vực)

**Interfaces:** Không phụ thuộc task khác.

- [ ] **Step 1: Thêm card "Trung tâm AI" vào "Nhóm giải pháp chính", đổi `grid--3` → `grid--4`, sửa "Ba hướng" → "Bốn hướng"**

Từ (dòng 33-77, mở đầu section):
```html
      <div class="psec__head">
        <h2 class="psec__title">Nhóm giải pháp chính</h2>
        <p class="psec__lead">Ba hướng giải pháp cốt lõi, có thể triển khai độc lập hoặc kết hợp thành một hệ thống duy nhất.</p>
      </div>
      <div class="grid grid--3">
```
thành:
```html
      <div class="psec__head">
        <h2 class="psec__title">Nhóm giải pháp chính</h2>
        <p class="psec__lead">Bốn hướng giải pháp cốt lõi, có thể triển khai độc lập hoặc kết hợp thành một hệ thống duy nhất.</p>
      </div>
      <div class="grid grid--4">
```

Ngay trước thẻ đóng `</div>` cuối cùng của khối `.grid.grid--3` cũ (ngay sau `</article>` của card "Giải pháp toàn diện", trước dòng `</div>` đóng grid ở dòng 77), thêm article thứ 4:
```html
        <article class="mcard">
          <div class="mcard__media"><img src="assets/images/ai-intro.jpg" alt="Trung tâm AI" loading="lazy"></div>
          <div class="mcard__body">
            <span class="mcard__badge"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.4" y="6.4" width="11.2" height="11.2" rx="1.6"/><rect x="9.8" y="9.8" width="4.4" height="4.4" rx=".8"/><path d="M9.4 2.6v3.8M14.6 2.6v3.8M9.4 17.6v3.8M14.6 17.6v3.8M2.6 9.4h3.8M2.6 14.6h3.8M17.6 9.4h3.8M17.6 14.6h3.8"/></svg></span>
            <h3 class="mcard__title">Trung tâm AI</h3>
            <ul class="mcard__list">
            <li>Nhận diện khuôn mặt &amp; biển số xe</li>
            <li>Phân tích hành vi, cảnh báo bất thường</li>
            <li>Tự động hóa quy trình bằng AI</li>
            </ul>
            <a class="link-more" href="trung-tam-ai.html"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Tìm hiểu thêm</a>
          </div>
        </article>
```

- [ ] **Step 2: Rút gọn "Giải pháp theo từng lĩnh vực" thành teaser 3 mục + CTA "Xem tất cả"**

Thay toàn bộ section (dòng 110-154):
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="psec__head">
        <h2 class="psec__title">Giải pháp theo từng lĩnh vực</h2>
        <p class="psec__lead">Mỗi lĩnh vực có đặc thù riêng — cấu hình thiết bị và kịch bản cảnh báo được thiết kế riêng.</p>
      </div>
      <div class="grid grid--5">
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-1.jpg" alt="Hộ gia đình" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Hộ gia đình</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>An toàn cho gia đình bạn</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-2.jpg" alt="Trường học" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Trường học</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Giám sát an ninh, quản lý học sinh</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-3.jpg" alt="Văn phòng &amp; Doanh nghiệp" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Văn phòng &amp; Doanh nghiệp</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Bảo mật tài sản, kiểm soát ra vào</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-4.jpg" alt="Nhà xưởng &amp; Khu công nghiệp" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Nhà xưởng &amp; Khu công nghiệp</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Giám sát sản xuất, phòng chống rủi ro</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-5.jpg" alt="Khu đô thị &amp; Công cộng" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Khu đô thị &amp; Công cộng</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Đảm bảo an ninh, trật tự cộng đồng</p>
          </div>
        </article>
      </div>
    </div>
  </section>
```
bằng:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="psec__head psec__head--row">
        <h2 class="psec__title">Giải pháp theo từng lĩnh vực</h2>
        <a class="link-more" href="giai-phap-toan-dien.html">Xem tất cả lĩnh vực <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i></a>
      </div>
      <div class="grid grid--3">
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-1.jpg" alt="Hộ gia đình" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Hộ gia đình</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>An toàn cho gia đình bạn</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-2.jpg" alt="Trường học" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Trường học</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Giám sát an ninh, quản lý học sinh</p>
          </div>
        </article>
        <article class="pj">
          <div class="pj__media"><img src="assets/images/all-field-3.jpg" alt="Văn phòng &amp; Doanh nghiệp" loading="lazy"></div>
          <div class="pj__body">
            <h3 class="pj__title">Văn phòng &amp; Doanh nghiệp</h3>
            <p class="pj__meta"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21.4s7-6 7-11a7 7 0 1 0-14 0c0 5 7 11 7 11Z"/><circle cx="12" cy="10.2" r="2.6"/></svg>Bảo mật tài sản, kiểm soát ra vào</p>
          </div>
        </article>
      </div>
    </div>
  </section>
```

- [ ] **Step 3: Xác nhận**

`grep -c 'class="mcard"' giai-phap.html` → `4`.
`grep -c 'class="pj"' giai-phap.html` → `3`.
Mở `giai-phap.html` trong trình duyệt: 4 card giải pháp chính hiển thị 1 hàng ở ≥1024px, section lĩnh vực chỉ còn 3 card + link "Xem tất cả lĩnh vực" dẫn sang `giai-phap-toan-dien.html`.

- [ ] **Step 4: Commit**

```bash
git add giai-phap.html
git commit -m "content(giai-phap): thêm card Trung tâm AI, rút gọn section lĩnh vực trùng lặp thành teaser"
```

---

### Task 9: truong-hoc-ai.html — thay "Khóa học tiêu biểu" bằng ứng dụng camera AI, sửa testimonial lệch chủ đề

**Files:**
- Modify: `truong-hoc-ai.html:115-153`
- Modify: `truong-hoc-ai.html:212-215`

**Interfaces:** Không phụ thuộc task khác.

- [ ] **Step 1: Thay khối "Các khóa học tiêu biểu" bằng "Ứng dụng camera AI trong quản lý trường học"**

Thay (dòng 115-153):
```html
        <div class="psec__head">
            <h2 class="psec__title split__title--sm">Các khóa học tiêu biểu</h2>
            <p class="psec__lead">Đa dạng khóa học từ cơ bản đến nâng cao, phù hợp với mọi lứa tuổi.</p>
          </div>
          <div class="grid grid--2">
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9.2" cy="8.2" r="3.4"/><path d="M2.8 20.2a6.4 6.4 0 0 1 12.8 0"/><path d="M16.4 5.2a3.4 3.4 0 0 1 0 6.6M17.8 14.6a6.4 6.4 0 0 1 3.4 5.6"/></svg></span>
            <div>
              <h3 class="course__title">Kỹ năng AI cho học sinh</h3>
              <p class="tagrow"><span class="tag">Cơ bản</span><span class="tag">6 - 12 tuổi</span></p>
              <p class="course__text">Làm quen với AI, tư duy công nghệ và sáng tạo nội dung.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.4" y="7.6" width="15.2" height="11" rx="2.4"/><path d="M12 3.4v4.2"/><circle cx="8.8" cy="12.6" r="1.3"/><circle cx="15.2" cy="12.6" r="1.3"/><path d="M9.6 16h4.8"/></svg></span>
            <div>
              <h3 class="course__title">Lập trình &amp; Robotics</h3>
              <p class="tagrow"><span class="tag tag--warn">Nâng cao</span><span class="tag">10 - 18 tuổi</span></p>
              <p class="course__text">Tư duy lập trình, phát triển ứng dụng và robot.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3.6 4.6h6a3 3 0 0 1 3 3v12a2.4 2.4 0 0 0-2.4-2.4H3.6V4.6Z"/><path d="M20.4 4.6h-6a3 3 0 0 0-3 3v12a2.4 2.4 0 0 1 2.4-2.4h6.6V4.6Z"/></svg></span>
            <div>
              <h3 class="course__title">Ứng dụng AI trong học tập</h3>
              <p class="tagrow"><span class="tag">Cơ bản</span><span class="tag">12 - 18 tuổi</span></p>
              <p class="course__text">Sử dụng AI để học hiệu quả, tối ưu thời gian và phương pháp.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.6" y="10.4" width="14.8" height="10.2" rx="2"/><path d="M8.2 10.4V7.6a3.8 3.8 0 0 1 7.6 0v2.8"/><circle cx="12" cy="15.4" r="1.4"/></svg></span>
            <div>
              <h3 class="course__title">Kỹ năng số &amp; An toàn Internet</h3>
              <p class="tagrow"><span class="tag">Cơ bản</span><span class="tag">6 - 18 tuổi</span></p>
              <p class="course__text">Bảo vệ bản thân, sử dụng Internet an toàn và văn minh.</p>
            </div>
          </article>
          </div>
```
bằng:
```html
        <div class="psec__head">
            <h2 class="psec__title split__title--sm">Ứng dụng camera AI trong quản lý trường học</h2>
            <p class="psec__lead">Camera AI hỗ trợ nhà trường ở từng khâu vận hành, từ cổng trường đến lớp học.</p>
          </div>
          <div class="grid grid--2">
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.6" y="7" width="13" height="10" rx="2.4"/><path d="m16 11.2 5-2.6v7l-5-2.6z"/><circle cx="8.4" cy="12" r="2.2"/></svg></span>
            <div>
              <h3 class="course__title">Điểm danh bằng khuôn mặt</h3>
              <p class="tagrow"><span class="tag">Tự động</span><span class="tag">Tiết kiệm thời gian</span></p>
              <p class="course__text">Ghi nhận điểm danh học sinh qua camera AI, đồng bộ với phần mềm quản lý, giảm sai sót thủ công.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4 5.8v6.1c0 5 3.4 9.2 8 10.4 4.6-1.2 8-5.4 8-10.4V5.8l-8-3.2Z"/></svg></span>
            <div>
              <h3 class="course__title">Giám sát an ninh khuôn viên</h3>
              <p class="tagrow"><span class="tag">24/7</span></p>
              <p class="course__text">Theo dõi cổng trường, hành lang, sân chơi; phát hiện người lạ ra vào ngoài giờ.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="15" cy="4.6" r="1.8"/><path d="M12.6 21.4 14 16l-3-2.6.9-5.2 3.7 3 3.1.8"/><path d="M11.9 8.2 8.2 9.8l-1 3.4M11 13.4l-4.6 2.4-2.8 4"/></svg></span>
            <div>
              <h3 class="course__title">Cảnh báo hành vi bất thường</h3>
              <p class="tagrow"><span class="tag tag--warn">Cảnh báo tức thì</span></p>
              <p class="course__text">Phát hiện xô xát, tụ tập đông người bất thường, gửi cảnh báo ngay tới ban giám hiệu.</p>
            </div>
          </article>
          <article class="course">
            <span class="course__icon"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.6" y="2.6" width="10.8" height="18.8" rx="2.4"/><path d="M10.6 5.6h2.8"/><path d="M11 18.4h2"/></svg></span>
            <div>
              <h3 class="course__title">Kết nối phụ huynh – nhà trường</h3>
              <p class="tagrow"><span class="tag">Realtime</span></p>
              <p class="course__text">Gửi thông báo điểm danh và hình ảnh qua ứng dụng di động tới phụ huynh theo thời gian thực.</p>
            </div>
          </article>
          </div>
```

- [ ] **Step 2: Sửa testimonial của Trường THCS Trần Phú — bỏ nhắc "Khóa học AI", đổi sang nội dung camera/an ninh**

Từ (dòng 212-215):
```html
          <article class="quote">
            <p class="quote__mark">&ldquo;</p>
            <p class="quote__text">Khóa học AI giúp học sinh tiếp cận công nghệ sớm, tự tin hơn khi bước vào tương lai.</p>
            <p class="quote__by"><img src="assets/images/edu-school-3.jpg" alt="Trường THCS Trần Phú" loading="lazy"><span><b>Trường THCS Trần Phú</b><span>Đà Nẵng</span></span></p>
          </article>
```
thành:
```html
          <article class="quote">
            <p class="quote__mark">&ldquo;</p>
            <p class="quote__text">Camera AI giúp nhà trường kiểm soát an ninh cổng trường chặt chẽ hơn, phụ huynh cũng yên tâm hơn khi con đến trường.</p>
            <p class="quote__by"><img src="assets/images/edu-school-3.jpg" alt="Trường THCS Trần Phú" loading="lazy"><span><b>Trường THCS Trần Phú</b><span>Đà Nẵng</span></span></p>
          </article>
```

- [ ] **Step 3: Xác nhận**

`grep -n 'Khóa học\|khóa học' truong-hoc-ai.html` → không còn kết quả.
Mở `truong-hoc-ai.html` trong trình duyệt, kiểm tra section vừa đổi hiển thị đúng 4 card, không vỡ layout.

- [ ] **Step 4: Commit**

```bash
git add truong-hoc-ai.html
git commit -m "content(truong-hoc-ai): thay khóa học AI bằng ứng dụng camera AI trong quản lý trường học"
```

---

### Task 10: du-an.html — dải thống kê, bộ lọc thật bằng JS, CTA cuối trang

**Files:**
- Modify: `du-an.html:17-29` (thêm section thống kê ngay sau hero)
- Modify: `du-an.html:34-62` (bộ lọc: thêm `id`, `value`, checkbox "Ngân hàng", trim city select)
- Modify: `du-an.html:59-218` (grid id, data-attribute từng `.prj`, phần tử "không có kết quả", CTA cuối trang)
- Modify: `assets/js/main.js` (thêm `initProjectFilter`, gọi trong `DOMContentLoaded`)
- Modify: `assets/css/style.css` (thêm `.prj-empty`)

**Interfaces:**
- Produces: hàm `initProjectFilter(root)` trong `main.js`, chỉ chạy khi tồn tại `#prj-filters` — không ảnh hưởng trang khác.
- Consumes: không phụ thuộc task khác.

- [ ] **Step 1: Thêm section thống kê ngay sau hero (sau dòng 29 `</section>`, trước dòng 30 `<section class="psec psec--tint psec--last">`)**

Chèn:
```html
  <section class="psec">
    <div class="container">
      <div class="stat-grid">
        <div class="stat"><b>500+</b><span>Dự án đã bàn giao</span></div>
        <div class="stat"><b>20.000+</b><span>Camera đã lắp đặt</span></div>
        <div class="stat"><b>98%</b><span>Khách hàng quay lại</span></div>
        <div class="stat"><b>24/7</b><span>Hỗ trợ kỹ thuật</span></div>
      </div>
    </div>
  </section>
```

- [ ] **Step 2: Sửa khối bộ lọc — thêm `id`, `value` cho từng checkbox, thêm "Ngân hàng", trim city select**

Từ (dòng 34-51):
```html
          <div class="aside-card">
            <h3 class="aside-card__head"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.6"/><path d="m16 16 4.4 4.4"/></svg>Lọc dự án</h3>
            <h4>Danh mục dự án</h4>
          <label class="check"><input type="checkbox" name="cat" checked><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Tất cả dự án</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Tòa nhà - Chung cư</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Khu đô thị</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Văn phòng</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Nhà máy - KCN</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Trường học</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Bệnh viện</label>
          <label class="check"><input type="checkbox" name="cat"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Khác</label>
            <h4>Tỉnh/Thành phố</h4>
            <p class="field field--select"><label class="sr-only" for="f-city">Tỉnh/Thành phố</label>
              <select id="f-city"><option>Tất cả</option><option>Hà Nội</option><option>TP. Hồ Chí Minh</option><option>Hưng Yên</option><option>Bắc Ninh</option></select></p>
            <h4>Năm triển khai</h4>
            <p class="field field--select"><label class="sr-only" for="f-year">Năm triển khai</label>
              <select id="f-year"><option>Tất cả</option><option>2023</option><option>2022</option><option>2021</option><option>2020</option><option>2019</option></select></p>
            <button class="btn btn--solid" type="button"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.6"/><path d="m16 16 4.4 4.4"/></svg>Tìm kiếm</button>
          </div>
```
thành:
```html
          <div class="aside-card" id="prj-filters">
            <h3 class="aside-card__head"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.6"/><path d="m16 16 4.4 4.4"/></svg>Lọc dự án</h3>
            <h4>Danh mục dự án</h4>
          <label class="check"><input type="checkbox" name="cat" value="all" checked><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Tất cả dự án</label>
          <label class="check"><input type="checkbox" name="cat" value="chung-cu"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Tòa nhà - Chung cư</label>
          <label class="check"><input type="checkbox" name="cat" value="do-thi"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Khu đô thị</label>
          <label class="check"><input type="checkbox" name="cat" value="van-phong"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Văn phòng</label>
          <label class="check"><input type="checkbox" name="cat" value="nha-may"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Nhà máy - KCN</label>
          <label class="check"><input type="checkbox" name="cat" value="truong-hoc"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Trường học</label>
          <label class="check"><input type="checkbox" name="cat" value="ngan-hang"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Ngân hàng</label>
          <label class="check"><input type="checkbox" name="cat" value="benh-vien"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Bệnh viện</label>
          <label class="check"><input type="checkbox" name="cat" value="khac"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m4.6 12.6 4.8 4.8 10-10.8"/></svg></i>Khác</label>
            <h4>Tỉnh/Thành phố</h4>
            <p class="field field--select"><label class="sr-only" for="f-city">Tỉnh/Thành phố</label>
              <select id="f-city"><option>Tất cả</option><option>Hà Nội</option><option>Hưng Yên</option><option>Bắc Ninh</option></select></p>
            <h4>Năm triển khai</h4>
            <p class="field field--select"><label class="sr-only" for="f-year">Năm triển khai</label>
              <select id="f-year"><option>Tất cả</option><option>2023</option><option>2022</option><option>2021</option><option>2020</option><option>2019</option></select></p>
            <button class="btn btn--solid" type="button"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.6"/><path d="m16 16 4.4 4.4"/></svg>Tìm kiếm</button>
          </div>
```

- [ ] **Step 3: Gắn `id` cho lưới dự án, đổi nhãn link-more, thêm `data-category`/`data-city`/`data-year` cho từng `.prj`, thêm phần tử "không có kết quả"**

Sửa dòng mở đầu khối (dòng 60-64) từ:
```html
          <div class="psec__head psec__head--row">
            <h2 class="psec__title"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3Z"/></svg>Dự án nổi bật</h2>
            <a class="link-more" href="lien-he.html">Xem tất cả dự án <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i></a>
          </div>
          <div class="grid grid--3">
```
thành:
```html
          <div class="psec__head psec__head--row">
            <h2 class="psec__title"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3Z"/></svg>Dự án nổi bật</h2>
            <a class="link-more" href="lien-he.html">Tư vấn dự án tương tự <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i></a>
          </div>
          <p class="psec__lead">9 dự án tiêu biểu trong hơn 500 dự án Cameramienbac đã triển khai trên toàn miền Bắc.</p>
          <div class="grid grid--3" id="prj-grid">
```

Trên 9 thẻ mở `<article class="prj">`, đổi thành (giữ đúng thứ tự xuất hiện trong file):
1. `<article class="prj" data-category="chung-cu" data-city="Hà Nội" data-year="2023">` (Vinhomes Ocean Park)
2. `<article class="prj" data-category="van-phong" data-city="Hà Nội" data-year="2023">` (Trụ sở Tập đoàn FPT)
3. `<article class="prj" data-category="nha-may" data-city="Hà Nội" data-year="2022">` (KCN Bắc Thăng Long)
4. `<article class="prj" data-category="truong-hoc" data-city="Hà Nội" data-year="2022">` (Trường THPT Chuyên Hà Nội – Amsterdam)
5. `<article class="prj" data-category="do-thi" data-city="Hưng Yên" data-year="2021">` (Khu đô thị Ecopark)
6. `<article class="prj" data-category="ngan-hang" data-city="Hà Nội" data-year="2019">` (Ngân hàng BIDV)
7. `<article class="prj" data-category="benh-vien" data-city="Hà Nội" data-year="2020">` (Bệnh viện Bạch Mai)
8. `<article class="prj" data-category="truong-hoc" data-city="Hà Nội" data-year="2020">` (Đại học Quốc gia Hà Nội)
9. `<article class="prj" data-category="nha-may" data-city="Bắc Ninh" data-year="2019">` (Nhà máy Samsung Bắc Ninh)

Ngay sau thẻ đóng `</div>` của `.grid.grid--3#prj-grid` (dòng 218 gốc, trước `</div></div></section>`), thêm:
```html
          <p class="prj-empty" id="prj-empty" hidden>Không tìm thấy dự án phù hợp với bộ lọc đã chọn. Vui lòng thử tiêu chí khác hoặc <a href="lien-he.html">liên hệ trực tiếp</a> để được tư vấn.</p>
```

- [ ] **Step 4: Thêm CTA `.slogan` cuối trang trước `</main>`**

Ngay trước dòng `</main>` (dòng 224 gốc), thêm section mới:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="slogan">
        <div class="slogan__inner">
          <span class="brand"><svg class="brand__mark" viewBox="0 0 48 58" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="dp-shell" x1="1.6" y1="29" x2="46.4" y2="29" gradientUnits="userSpaceOnUse">
            <stop stop-color="#18cbfd"/><stop offset=".5" stop-color="#0ab5fb"/><stop offset="1" stop-color="#0293f7"/>
          </linearGradient>
          <linearGradient id="dp-lens" x1="14" y1="14" x2="34" y2="49" gradientUnits="userSpaceOnUse">
            <stop stop-color="#07a4e8"/><stop offset="1" stop-color="#20c9fe"/>
          </linearGradient>
        </defs>
        <path d="M24 .6 46.4 9v19.6c0 13-9.4 22-22.4 28.8C11 50.6 1.6 41.6 1.6 28.6V9L24 .6Z" fill="url(#dp-shell)"/>
        <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8-9-4.8-15.6-11.4-15.6-20.8V13.9L24 7.6Z" fill="#00235f"/>
        <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8V7.6Z" fill="#3c74ce" opacity=".62"/>
        <rect x="13.8" y="15" width="8.4" height="33.6" rx="4.2" fill="url(#dp-lens)"/>
        <circle cx="26" cy="26.8" r="12.1" fill="url(#dp-lens)"/>
        <circle cx="26" cy="26.8" r="5" fill="#0a2a66" opacity=".16"/>
        <circle cx="34.6" cy="12.8" r="1.7" fill="#bfe9ff" opacity=".85"/>
      </svg>
            <span class="brand__text"><span class="brand__name">CAMERAMIENBAC</span><span class="brand__sub">AI &amp; SMART</span></span>
          </span>
          <div class="slogan__body">
            <p class="slogan__title">Dự án tiếp theo có thể là của bạn</p>
            <ul class="slogan__points">
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4 5.8v6.1c0 5 3.4 9.2 8 10.4 4.6-1.2 8-5.4 8-10.4V5.8l-8-3.2Z"/><path d="m8.8 12 2.2 2.2 4.2-4.4"/></svg>Chuyên nghiệp</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg>Uy tín</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><path d="M19.6 14.6a1.4 1.4 0 0 0 .3 1.5l.1.1a1.7 1.7 0 1 1-2.4 2.4l-.1-.1a1.4 1.4 0 0 0-1.5-.3 1.4 1.4 0 0 0-.9 1.3v.2a1.7 1.7 0 1 1-3.4 0v-.1a1.4 1.4 0 0 0-.9-1.3 1.4 1.4 0 0 0-1.5.3l-.1.1a1.7 1.7 0 1 1-2.4-2.4l.1-.1a1.4 1.4 0 0 0 .3-1.5 1.4 1.4 0 0 0-1.3-.9h-.2a1.7 1.7 0 1 1 0-3.4h.1a1.4 1.4 0 0 0 1.3-.9 1.4 1.4 0 0 0-.3-1.5l-.1-.1a1.7 1.7 0 1 1 2.4-2.4l.1.1a1.4 1.4 0 0 0 1.5.3h.1a1.4 1.4 0 0 0 .9-1.3v-.2a1.7 1.7 0 1 1 3.4 0v.1a1.4 1.4 0 0 0 .9 1.3 1.4 1.4 0 0 0 1.5-.3l.1-.1a1.7 1.7 0 1 1 2.4 2.4l-.1.1a1.4 1.4 0 0 0-.3 1.5v.1a1.4 1.4 0 0 0 1.3.9h.2a1.7 1.7 0 1 1 0 3.4h-.1a1.4 1.4 0 0 0-1.3.9Z"/></svg>Hiệu quả</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.4 14v-2a7.6 7.6 0 0 1 15.2 0v2"/><rect x="2.8" y="13.4" width="4" height="6" rx="1.6"/><rect x="17.2" y="13.4" width="4" height="6" rx="1.6"/><path d="M19.6 19.4a3 3 0 0 1-3 2.2h-2"/></svg>Hỗ trợ 24/7</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
```

- [ ] **Step 5: Thêm CSS `.prj-empty` vào `assets/css/style.css`**

Thêm vào cuối file (trước dòng cuối cùng, hoặc ngay sau block `.aside-card`/`.check` nếu tìm thấy — chấp nhận thêm cuối file vì đây là component mới độc lập):
```css
.prj-empty { padding: 32px 0; text-align: center; font-size: 15px; color: #4b6a97; }
.prj-empty a { color: var(--blue-600); font-weight: 600; }
```

- [ ] **Step 6: Thêm `initProjectFilter` vào `assets/js/main.js` và gọi trong `DOMContentLoaded`**

Thêm hàm mới ngay trước `function markCurrent(root) {`:
```javascript
  function initProjectFilter(root) {
    var filterPanel = root.getElementById("prj-filters");
    var grid = root.getElementById("prj-grid");
    var empty = root.getElementById("prj-empty");
    if (!filterPanel || !grid) return;

    var catBoxes = Array.prototype.slice.call(filterPanel.querySelectorAll('input[name="cat"]'));
    var allBox = filterPanel.querySelector('input[name="cat"][value="all"]');
    var citySelect = root.getElementById("f-city");
    var yearSelect = root.getElementById("f-year");
    var submitBtn = filterPanel.querySelector("button");
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".prj"));

    function apply() {
      var checked = catBoxes.filter(function (box) {
        return box.checked && box.value !== "all";
      }).map(function (box) { return box.value; });

      var city = citySelect && citySelect.value !== "Tất cả" ? citySelect.value : "";
      var year = yearSelect && yearSelect.value !== "Tất cả" ? yearSelect.value : "";

      var visibleCount = 0;
      cards.forEach(function (card) {
        var matchCat = checked.length === 0 || checked.indexOf(card.getAttribute("data-category")) !== -1;
        var matchCity = !city || card.getAttribute("data-city") === city;
        var matchYear = !year || card.getAttribute("data-year") === year;
        var show = matchCat && matchCity && matchYear;
        card.hidden = !show;
        if (show) visibleCount++;
      });

      if (empty) empty.hidden = visibleCount !== 0;
    }

    catBoxes.forEach(function (box) {
      box.addEventListener("change", function () {
        if (box.value === "all") {
          if (box.checked) {
            catBoxes.forEach(function (other) {
              if (other !== box) other.checked = false;
            });
          }
        } else if (box.checked && allBox) {
          allBox.checked = false;
        }
        var anyChecked = catBoxes.some(function (b) { return b.checked; });
        if (!anyChecked && allBox) allBox.checked = true;
        apply();
      });
    });

    if (citySelect) citySelect.addEventListener("change", apply);
    if (yearSelect) yearSelect.addEventListener("change", apply);
    if (submitBtn) {
      submitBtn.addEventListener("click", function (event) {
        event.preventDefault();
        apply();
      });
    }
  }

```

Sửa khối `DOMContentLoaded` (cuối file) từ:
```javascript
  document.addEventListener("DOMContentLoaded", function () {
    var slots = Array.prototype.slice.call(document.querySelectorAll("[data-include]"));
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
  });
```
thành:
```javascript
  document.addEventListener("DOMContentLoaded", function () {
    var slots = Array.prototype.slice.call(document.querySelectorAll("[data-include]"));
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      initProjectFilter(document);
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
  });
```

- [ ] **Step 7: Xác nhận**

`node --check assets/js/main.js` → không lỗi.
`grep -c 'data-category=' du-an.html` → `9`.
Mở `du-an.html` qua `python3 -m http.server 8000`: tick "Trường học" → chỉ còn 2 card (Ams, ĐHQGHN); chọn tỉnh "Bắc Ninh" → chỉ còn Samsung; tick "Ngân hàng" + chọn năm "2020" (không khớp BIDV là 2019) → hiển thị thông báo "Không tìm thấy dự án phù hợp".

- [ ] **Step 8: Commit**

```bash
git add du-an.html assets/js/main.js assets/css/style.css
git commit -m "feat(du-an): thêm dải thống kê, bộ lọc dự án thật bằng JS, CTA cuối trang"
```

---

### Task 11: san-pham.html — bỏ inline style thừa, thêm CTA cuối trang

**Files:**
- Modify: `san-pham.html:231` (bỏ inline style trùng với rule `.pband__inner .btn` đã có sẵn)
- Modify: `san-pham.html:238` (thêm CTA trước `</main>`)

**Interfaces:** Không phụ thuộc task khác.

- [ ] **Step 1: Bỏ inline style trên nút AIoT Platform (đã trùng với `.pband__inner .btn` có sẵn trong CSS — dòng 1421)**

Từ:
```html
            <a class="btn btn--solid" href="aiot-platform.html" style="height:36px;padding:0 20px;font-size:13px;width:auto;gap:10px">Khám phá AIoT Platform <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
```
thành:
```html
            <a class="btn btn--solid" href="aiot-platform.html">Khám phá AIoT Platform <svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>
```

- [ ] **Step 2: Thêm CTA `.slogan` trước `</main>` (dòng 238)**

Chèn ngay trước `</main>`:
```html
  <section class="psec psec--last">
    <div class="container">
      <div class="slogan">
        <div class="slogan__inner">
          <span class="brand"><svg class="brand__mark" viewBox="0 0 48 58" fill="none" aria-hidden="true">
        <defs>
          <linearGradient id="sp-shell" x1="1.6" y1="29" x2="46.4" y2="29" gradientUnits="userSpaceOnUse">
            <stop stop-color="#18cbfd"/><stop offset=".5" stop-color="#0ab5fb"/><stop offset="1" stop-color="#0293f7"/>
          </linearGradient>
          <linearGradient id="sp-lens" x1="14" y1="14" x2="34" y2="49" gradientUnits="userSpaceOnUse">
            <stop stop-color="#07a4e8"/><stop offset="1" stop-color="#20c9fe"/>
          </linearGradient>
        </defs>
        <path d="M24 .6 46.4 9v19.6c0 13-9.4 22-22.4 28.8C11 50.6 1.6 41.6 1.6 28.6V9L24 .6Z" fill="url(#sp-shell)"/>
        <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8-9-4.8-15.6-11.4-15.6-20.8V13.9L24 7.6Z" fill="#00235f"/>
        <path d="M24 7.6 39.6 13.9v14.7c0 9.4-6.6 16-15.6 20.8V7.6Z" fill="#3c74ce" opacity=".62"/>
        <rect x="13.8" y="15" width="8.4" height="33.6" rx="4.2" fill="url(#sp-lens)"/>
        <circle cx="26" cy="26.8" r="12.1" fill="url(#sp-lens)"/>
        <circle cx="26" cy="26.8" r="5" fill="#0a2a66" opacity=".16"/>
        <circle cx="34.6" cy="12.8" r="1.7" fill="#bfe9ff" opacity=".85"/>
      </svg>
            <span class="brand__text"><span class="brand__name">CAMERAMIENBAC</span><span class="brand__sub">AI &amp; SMART</span></span>
          </span>
          <div class="slogan__body">
            <p class="slogan__title">Chọn đúng thiết bị, an tâm vận hành</p>
            <ul class="slogan__points">
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4 5.8v6.1c0 5 3.4 9.2 8 10.4 4.6-1.2 8-5.4 8-10.4V5.8l-8-3.2Z"/><path d="m8.8 12 2.2 2.2 4.2-4.4"/></svg>Chính hãng</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.6 12.4 6.2 8.8h3.6l2.2 2.2 2.2-2.2h3.6l3.6 3.6-3.4 3.4-2-2-1.6 1.6-1.4-1.4-1.4 1.4-1.6-1.6-2 2-3.4-3.4Z"/><path d="M6.2 8.8 9 6h6l2.8 2.8"/></svg>Bảo hành rõ ràng</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3.2"/><path d="M19.6 14.6a1.4 1.4 0 0 0 .3 1.5l.1.1a1.7 1.7 0 1 1-2.4 2.4l-.1-.1a1.4 1.4 0 0 0-1.5-.3 1.4 1.4 0 0 0-.9 1.3v.2a1.7 1.7 0 1 1-3.4 0v-.1a1.4 1.4 0 0 0-.9-1.3 1.4 1.4 0 0 0-1.5.3l-.1.1a1.7 1.7 0 1 1-2.4-2.4l.1-.1a1.4 1.4 0 0 0 .3-1.5 1.4 1.4 0 0 0-1.3-.9h-.2a1.7 1.7 0 1 1 0-3.4h.1a1.4 1.4 0 0 0 1.3-.9 1.4 1.4 0 0 0-.3-1.5l-.1-.1a1.7 1.7 0 1 1 2.4-2.4l.1.1a1.4 1.4 0 0 0 1.5.3h.1a1.4 1.4 0 0 0 .9-1.3v-.2a1.7 1.7 0 1 1 3.4 0v.1a1.4 1.4 0 0 0 .9 1.3 1.4 1.4 0 0 0 1.5-.3l.1-.1a1.7 1.7 0 1 1 2.4 2.4l-.1.1a1.4 1.4 0 0 0-.3 1.5v.1a1.4 1.4 0 0 0 1.3.9h.2a1.7 1.7 0 1 1 0 3.4h-.1a1.4 1.4 0 0 0-1.3.9Z"/></svg>Hiệu quả</li>
              <li><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.4 14v-2a7.6 7.6 0 0 1 15.2 0v2"/><rect x="2.8" y="13.4" width="4" height="6" rx="1.6"/><rect x="17.2" y="13.4" width="4" height="6" rx="1.6"/><path d="M19.6 19.4a3 3 0 0 1-3 2.2h-2"/></svg>Hỗ trợ 24/7</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
```

- [ ] **Step 3: Xác nhận**

`grep -n 'style="' san-pham.html` → không còn kết quả.
Mở `san-pham.html`, cuộn xuống cuối trang: có dải CTA trước footer, không kết thúc đột ngột.

- [ ] **Step 4: Commit**

```bash
git add san-pham.html
git commit -m "content(san-pham): bỏ inline style thừa, thêm CTA cuối trang"
```

---

### Task 12: lien-he.html — điền lead trống, ẩn icon MXH chưa có link thật, nâng UX form liên hệ

**Files:**
- Modify: `lien-he.html:22` (điền `phero__lead`)
- Modify: `lien-he.html:44-54` (bỏ khối MXH toàn `href="#"`)
- Modify: `lien-he.html:65,95-97` (thêm `#form-status`, sửa nút submit)
- Modify: `assets/js/main.js` (thêm `initContactForm`, gọi trong `DOMContentLoaded`)
- Modify: `assets/css/style.css` (thêm `.btn.is-loading`, `.form-status`)

**Interfaces:**
- Produces: hàm `initContactForm(root)` trong `main.js`.
- Consumes: khối `DOMContentLoaded` đã có dòng gọi `initProjectFilter(document);` từ Task 10 — chạy sau Task 10.

- [ ] **Step 1: Điền `phero__lead` đang rỗng (dòng 22)**

Từ:
```html
      <p class="phero__lead"></p>
```
thành:
```html
      <p class="phero__lead">Đội ngũ tư vấn Cameramienbac sẵn sàng khảo sát, báo giá và triển khai giải pháp camera AI phù hợp với nhu cầu của bạn.</p>
```

- [ ] **Step 2: Bỏ khối "Kết nối với chúng tôi" — toàn bộ 5 icon MXH hiện là `href="#"`**

Từ (dòng 44-54):
```html
          <hr class="hr">
          <div class="panel__head" style="margin-bottom:12px">
            <i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9.2" cy="8.2" r="3.4"/><path d="M2.8 20.2a6.4 6.4 0 0 1 12.8 0"/><path d="M16.4 5.2a3.4 3.4 0 0 1 0 6.6M17.8 14.6a6.4 6.4 0 0 1 3.4 5.6"/></svg></i>
            <div><h2 class="panel__subtitle">Kết nối với chúng tôi</h2></div>
          </div>
          <ul class="social-row">
          <li><a href="#" aria-label="Facebook"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true"><path d="M13.5 21v-8h2.7l.4-3.1h-3.1V7.9c0-.9.25-1.5 1.55-1.5h1.65V3.6c-.29-.04-1.27-.12-2.41-.12-2.39 0-4.03 1.46-4.03 4.14V9.9H7.5V13h2.76v8h3.24Z"/></svg></a>Facebook</li>
          <li><a href="#" aria-label="YouTube"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true"><path d="M21.6 7.2a2.5 2.5 0 0 0-1.75-1.77C18.3 5 12 5 12 5s-6.3 0-7.85.43A2.5 2.5 0 0 0 2.4 7.2 26 26 0 0 0 2 12a26 26 0 0 0 .4 4.8 2.5 2.5 0 0 0 1.75 1.77C5.7 19 12 19 12 19s6.3 0 7.85-.43a2.5 2.5 0 0 0 1.75-1.77A26 26 0 0 0 22 12a26 26 0 0 0-.4-4.8ZM10 15.1V8.9l5.2 3.1-5.2 3.1Z"/></svg></a>YouTube</li>
          <li><a href="#" aria-label="Zalo"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true"><path d="M6.4 6.2h5.3v1.35L8.1 13.1h3.7v1.5H5.9v-1.4l3.6-5.5H6.4V6.2Zm7.3 1.4h1.45v7h-1.45v-7Zm4.3 2.1c1.45 0 2.55 1.1 2.55 2.55S19.45 14.8 18 14.8s-2.55-1.1-2.55-2.55 1.1-2.55 2.55-2.55Zm0 1.35a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4ZM4.2 16.6c3.3 1.7 12.3 1.7 15.6 0 .5-.25.9.3.5.7-2.2 2.2-14.4 2.2-16.6 0-.4-.4 0-.95.5-.7Z"/></svg></a>Zalo</li>
          <li><a href="#" aria-label="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" stroke="none" aria-hidden="true"><path d="M6.94 8.5H4.06V20h2.88V8.5ZM5.5 7.2a1.7 1.7 0 1 0 0-3.4 1.7 1.7 0 0 0 0 3.4ZM20 13.9c0-3.1-1.66-4.55-3.87-4.55-1.78 0-2.58.98-3.02 1.67V8.5H10.2c.04.82 0 11.5 0 11.5h2.9v-6.42c0-.26.02-.52.1-.7.2-.52.68-1.06 1.48-1.06 1.05 0 1.47.8 1.47 1.96V20H20v-6.1Z"/></svg></a>LinkedIn</li>
          </ul>
          <div class="map">
```
thành:
```html
          <div class="map">
```

- [ ] **Step 3: Thêm `#form-status`, bỏ `hr`/social đã xử lý ở Step 2 không ảnh hưởng form — thêm status message dưới nút submit**

Từ (dòng 95-97):
```html
            <button class="btn btn--solid" type="submit"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 3 10.6 13.4M21 3l-6.6 18-3.8-7.6L3 9.8 21 3Z"/></svg>Gửi yêu cầu</button>
            <p class="form-note"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4 5.8v6.1c0 5 3.4 9.2 8 10.4 4.6-1.2 8-5.4 8-10.4V5.8l-8-3.2Z"/><path d="m8.8 12 2.2 2.2 4.2-4.4"/></svg>Thông tin của bạn được bảo mật tuyệt đối</p>
          </form>
```
thành:
```html
            <button class="btn btn--solid" type="submit"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 3 10.6 13.4M21 3l-6.6 18-3.8-7.6L3 9.8 21 3Z"/></svg>Gửi yêu cầu</button>
            <p class="form-status" id="form-status" hidden></p>
            <p class="form-note"><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2.6 4 5.8v6.1c0 5 3.4 9.2 8 10.4 4.6-1.2 8-5.4 8-10.4V5.8l-8-3.2Z"/><path d="m8.8 12 2.2 2.2 4.2-4.4"/></svg>Thông tin của bạn được bảo mật tuyệt đối</p>
          </form>
```

- [ ] **Step 4: Thêm CSS trạng thái loading + thông báo thành công**

Thêm vào cuối `assets/css/style.css`:
```css
.btn.is-loading { opacity: .7; pointer-events: none; }
.form-status { margin-top: 12px; padding: 12px 14px; border-radius: 8px; background: #e7f6ec; color: #1d7a3d; font-size: 14px; font-weight: 600; }
```

- [ ] **Step 5: Thêm `initContactForm` vào `assets/js/main.js`, gọi trong `DOMContentLoaded`**

Thêm hàm mới ngay trước `function markCurrent(root) {`:
```javascript
  function initContactForm(root) {
    var form = root.querySelector(".form-grid");
    if (!form) return;
    var button = form.querySelector('button[type="submit"]');
    var status = root.getElementById("form-status");

    // Form chưa nối backend/email thật (action="#") — đây chỉ là UX mô phỏng
    // phía client. Cần nối API/email thật (vd Formspree hoặc backend riêng)
    // trước khi release chính thức.
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (typeof form.checkValidity === "function" && !form.checkValidity()) {
        if (typeof form.reportValidity === "function") form.reportValidity();
        return;
      }
      if (button) {
        button.disabled = true;
        button.classList.add("is-loading");
      }
      window.setTimeout(function () {
        if (button) {
          button.disabled = false;
          button.classList.remove("is-loading");
        }
        if (status) {
          status.hidden = false;
          status.textContent = "Cảm ơn bạn đã gửi yêu cầu! Đội ngũ Cameramienbac sẽ liên hệ lại trong thời gian sớm nhất.";
        }
        form.reset();
      }, 900);
    });
  }

```

Sửa khối `DOMContentLoaded` từ:
```javascript
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      initProjectFilter(document);
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
```
thành:
```javascript
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      initProjectFilter(document);
      initContactForm(document);
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
```

- [ ] **Step 6: Xác nhận**

`node --check assets/js/main.js` → không lỗi.
`grep -n 'href="#"' lien-he.html` → không còn kết quả.
Mở `lien-he.html`, điền form với "Nội dung yêu cầu" để trống → bấm Gửi yêu cầu → trình duyệt chặn submit (validate required). Điền đủ → bấm Gửi → nút chuyển trạng thái loading ~0.9s rồi hiện thông báo xanh "Cảm ơn bạn đã gửi yêu cầu!", form reset.

- [ ] **Step 7: Commit**

```bash
git add lien-he.html assets/js/main.js assets/css/style.css
git commit -m "content(lien-he): điền lead trống, ẩn icon MXH chưa có link thật, nâng UX form liên hệ"
```

---

### Task 13: tin-tuc.html — biến thể hero riêng, bỏ link "Đọc tiếp" chết, đổi ảnh khớp chủ đề

**Files:**
- Modify: `assets/css/style.css` (thêm `.phero--news` gần `.phero--bld` dòng 920, gần `.phero::before` dòng 930)
- Modify: `tin-tuc.html:18` (đổi class hero)
- Modify: `tin-tuc.html:37-98` (bỏ 6 link "Đọc tiếp", đổi ảnh)

**Interfaces:** Không phụ thuộc task khác.

- [ ] **Step 1: Thêm biến thể hero `.phero--news` vào `assets/css/style.css`**

Sửa dòng 920 từ:
```css
.phero--bld { background-image: url("../images/sol-bld-hero.jpg"); }
```
thành:
```css
.phero--bld { background-image: url("../images/sol-bld-hero.jpg"); }
.phero--news { background-image: url("../images/sol-bld-hero.jpg"); }
```

Thêm ngay sau khối `.phero::before { ... }` (dòng 930):
```css
.phero--news::before { background: linear-gradient(90deg, rgba(3,20,56,.95) 0%, rgba(5,60,92,.84) 38%, rgba(5,82,112,.4) 64%, rgba(0,20,60,0) 86%); }
```

- [ ] **Step 2: Đổi class hero trong `tin-tuc.html:18`**

Từ:
```html
  <section class="phero phero--bld">
```
thành:
```html
  <section class="phero phero--news">
```

- [ ] **Step 3: Bỏ "Đọc tiếp" ở bài viết nổi bật (dòng 36-44), đổi ảnh sang `prd-hero.jpg`**

Từ:
```html
      <article class="news news--wide">
        <div class="news__media"><img src="assets/images/prj-5.jpg" alt="5 dấu hiệu cho thấy hệ thống camera của bạn đã lỗi thời" loading="lazy"></div>
        <div class="news__body">
          <p class="news__meta"><span class="tag">Giải pháp</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>12/09/2025</p>
          <h3 class="news__title">5 dấu hiệu cho thấy hệ thống camera của bạn đã lỗi thời</h3>
          <p class="news__text">Hình ảnh mờ ban đêm, không tìm được cảnh quay cũ, không có cảnh báo chủ động… Đây là lúc nên cân nhắc nâng cấp lên camera AI.</p>
          <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
        </div>
      </article>
```
thành:
```html
      <article class="news news--wide">
        <div class="news__media"><img src="assets/images/prd-hero.jpg" alt="5 dấu hiệu cho thấy hệ thống camera của bạn đã lỗi thời" loading="lazy"></div>
        <div class="news__body">
          <p class="news__meta"><span class="tag">Giải pháp</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>12/09/2025</p>
          <h3 class="news__title">5 dấu hiệu cho thấy hệ thống camera của bạn đã lỗi thời</h3>
          <p class="news__text">Hình ảnh mờ ban đêm, không tìm được cảnh quay cũ, không có cảnh báo chủ động… Đây là lúc nên cân nhắc nâng cấp lên camera AI.</p>
        </div>
      </article>
```

- [ ] **Step 4: Sửa 5 card còn lại (dòng 54-98) — đổi ảnh 3 card lệch chủ đề, bỏ "Đọc tiếp" cả 5 card**

Từ:
```html
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-2.jpg" alt="Nhận diện khuôn mặt hoạt động thế nào trong thực tế?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Công nghệ</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>02/09/2025</p>
            <h3 class="news__title">Nhận diện khuôn mặt hoạt động thế nào trong thực tế?</h3>
            <p class="news__text">Từ khâu thu hình, trích đặc trưng đến so khớp — và vì sao ánh sáng, góc đặt camera quyết định 80% độ chính xác.</p>
            <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-9.jpg" alt="Bàn giao hệ thống 300 camera cho nhà máy tại Bắc Ninh" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Dự án</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>25/08/2025</p>
            <h3 class="news__title">Bàn giao hệ thống 300 camera cho nhà máy tại Bắc Ninh</h3>
            <p class="news__text">Toàn bộ nhà xưởng, cổng ra vào và kho vận được giám sát tập trung, tích hợp kiểm soát nhân sự theo ca.</p>
            <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-4.jpg" alt="Điểm danh bằng AI: trường học tiết kiệm được bao nhiêu thời gian?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Giáo dục</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>14/08/2025</p>
            <h3 class="news__title">Điểm danh bằng AI: trường học tiết kiệm được bao nhiêu thời gian?</h3>
            <p class="news__text">Một khảo sát nhỏ tại 12 trường cho thấy giáo viên tiết kiệm trung bình 25 phút mỗi ngày nhờ điểm danh tự động.</p>
            <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-7.jpg" alt="Chọn ổ cứng cho đầu ghi: bao nhiêu TB là đủ?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Hướng dẫn</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>05/08/2025</p>
            <h3 class="news__title">Chọn ổ cứng cho đầu ghi: bao nhiêu TB là đủ?</h3>
            <p class="news__text">Công thức tính dung lượng theo số camera, độ phân giải, số ngày lưu trữ — kèm bảng tra nhanh cho các cấu hình phổ biến.</p>
            <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-3.jpg" alt="Phòng chống trộm cắp tại kho hàng bằng cảnh báo chủ động" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">An ninh</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>28/07/2025</p>
            <h3 class="news__title">Phòng chống trộm cắp tại kho hàng bằng cảnh báo chủ động</h3>
            <p class="news__text">Kết hợp camera AI với cảm biến và đèn còi để xử lý sự cố ngay khi phát hiện, thay vì chỉ xem lại sau khi mất.</p>
            <a class="link-more" href="#"><i><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></i>Đọc tiếp</a>
          </div>
        </article>
```
thành:
```html
        <article class="news">
          <div class="news__media"><img src="assets/images/ai-news-2.jpg" alt="Nhận diện khuôn mặt hoạt động thế nào trong thực tế?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Công nghệ</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>02/09/2025</p>
            <h3 class="news__title">Nhận diện khuôn mặt hoạt động thế nào trong thực tế?</h3>
            <p class="news__text">Từ khâu thu hình, trích đặc trưng đến so khớp — và vì sao ánh sáng, góc đặt camera quyết định 80% độ chính xác.</p>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-9.jpg" alt="Bàn giao hệ thống 300 camera cho nhà máy tại Bắc Ninh" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Dự án</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>25/08/2025</p>
            <h3 class="news__title">Bàn giao hệ thống 300 camera cho nhà máy tại Bắc Ninh</h3>
            <p class="news__text">Toàn bộ nhà xưởng, cổng ra vào và kho vận được giám sát tập trung, tích hợp kiểm soát nhân sự theo ca.</p>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prj-4.jpg" alt="Điểm danh bằng AI: trường học tiết kiệm được bao nhiêu thời gian?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Giáo dục</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>14/08/2025</p>
            <h3 class="news__title">Điểm danh bằng AI: trường học tiết kiệm được bao nhiêu thời gian?</h3>
            <p class="news__text">Một khảo sát nhỏ tại 12 trường cho thấy giáo viên tiết kiệm trung bình 25 phút mỗi ngày nhờ điểm danh tự động.</p>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/prd-dev-4.jpg" alt="Chọn ổ cứng cho đầu ghi: bao nhiêu TB là đủ?" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">Hướng dẫn</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>05/08/2025</p>
            <h3 class="news__title">Chọn ổ cứng cho đầu ghi: bao nhiêu TB là đủ?</h3>
            <p class="news__text">Công thức tính dung lượng theo số camera, độ phân giải, số ngày lưu trữ — kèm bảng tra nhanh cho các cấu hình phổ biến.</p>
          </div>
        </article>
        <article class="news">
          <div class="news__media"><img src="assets/images/ai-use-1.jpg" alt="Phòng chống trộm cắp tại kho hàng bằng cảnh báo chủ động" loading="lazy"></div>
          <div class="news__body">
            <p class="news__meta"><span class="tag">An ninh</span><svg viewBox="0 0 24 24" stroke="currentColor" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.4" y="5" width="17.2" height="15.6" rx="2"/><path d="M3.4 9.6h17.2M8 3v4M16 3v4"/></svg>28/07/2025</p>
            <h3 class="news__title">Phòng chống trộm cắp tại kho hàng bằng cảnh báo chủ động</h3>
            <p class="news__text">Kết hợp camera AI với cảm biến và đèn còi để xử lý sự cố ngay khi phát hiện, thay vì chỉ xem lại sau khi mất.</p>
          </div>
        </article>
```

- [ ] **Step 5: Xác nhận**

`grep -n 'href="#"' tin-tuc.html` → không còn kết quả.
Mở `tin-tuc.html`, so sánh với `toa-nha-thong-minh.html` — dải hero có tông màu khác nhau dù cùng ảnh nền.

- [ ] **Step 6: Commit**

```bash
git add tin-tuc.html assets/css/style.css
git commit -m "content(tin-tuc): thêm biến thể hero riêng, bỏ link Đọc tiếp chết, đổi ảnh khớp chủ đề"
```

---

### Task 14: QA cuối — grep sanity check + xác nhận responsive/behavior toàn site

**Files:** Không tạo/sửa file mới theo kế hoạch; chỉ sửa nếu Step 1-2 phát hiện sai sót từ Task 1-13.

**Interfaces:** Chạy sau tất cả Task 1-13.

- [ ] **Step 1: Grep sanity check — không còn dấu vết lỗi cũ**

Chạy lần lượt, tất cả đều phải trả về rỗng (trừ dòng đã ghi chú lý do giữ lại ở Task 7 Step 5-6, nếu Step 6 đã áp dụng thì cũng phải rỗng):

```bash
grep -rn 'style="' aiot-platform.html trung-tam-ai.html ve-chung-toi.html san-pham.html lien-he.html
grep -rn 'href="#"' partials/footer.html lien-he.html tin-tuc.html
grep -n 'class="container crumb"' *.html
grep -n 'Khóa học\|khóa học' truong-hoc-ai.html
node --check assets/js/main.js
```

Nếu bất kỳ lệnh nào trả về dòng không mong đợi, sửa trực tiếp file tương ứng trước khi qua Step 2.

- [ ] **Step 2: Xác nhận responsive + behavior tại 4 mốc, cho toàn bộ 11 trang**

Chạy `python3 -m http.server 8000`. Dùng DevTools responsive mode, kiểm tra ở 1440px, 1024px, 768px, 375px cho từng trang (`index.html`, `giai-phap.html`, `toa-nha-thong-minh.html`, `truong-hoc-ai.html`, `giai-phap-toan-dien.html`, `trung-tam-ai.html`, `san-pham.html`, `aiot-platform.html`, `du-an.html`, `ve-chung-toi.html`, `tin-tuc.html`, `lien-he.html`):

- Không có thanh cuộn ngang ở bất kỳ mốc nào.
- Header dính khi cuộn (Task 1); ở ≤1023px, hamburger hoạt động, khoá scroll nền, đóng bằng Escape/click-outside (Task 2).
- `aiot-platform.html` và `trung-tam-ai.html`: 2 khối grid đổi đúng 1 cột ở ≤719px (Task 4).
- `du-an.html`: bộ lọc hoạt động đúng ở cả desktop và mobile (Task 10).
- `lien-he.html`: form submit đúng luồng loading → thông báo thành công (Task 12).
- Footer 4 cột ở desktop, xếp dọc đúng thứ tự ở mobile, năm hiện tại hiển thị đúng (Task 3).

- [ ] **Step 3: Nếu phát hiện lỗi, sửa và commit riêng cho từng lỗi**

Với mỗi lỗi phát hiện ở Step 1/2, sửa trực tiếp trong file liên quan rồi commit:
```bash
git add <file-đã-sửa>
git commit -m "fix: <mô tả lỗi phát hiện ở QA cuối>"
```

- [ ] **Step 4: Commit QA log rỗng (nếu không có lỗi phát sinh ở Step 3)**

Nếu Step 1-2 không phát hiện lỗi nào, không cần commit gì thêm — Task 14 coi như hoàn tất, toàn bộ 13 task trước đó là bàn giao cuối cùng.

---

## Tổng kết phạm vi

14 task bao phủ đầy đủ 4 lớp trong spec: Task 1-4 (hạ tầng dùng chung), Task 5-9 (nội dung + dọn inline style theo từng trang liên quan), Task 10-13 (nội dung + UI polish cho các trang còn lại), Task 14 (QA responsive/behavior cuối cùng cho toàn bộ 11 trang). Không có task nào tạo backend thật, trang chi tiết tin tức, ảnh thật mới, hoặc thay đổi design token — đúng "Ngoài phạm vi" của spec.

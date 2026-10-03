# Remake nội dung & UI/UX toàn site Cameramienbac

Ngày: 2026-09-22

## Bối cảnh

Site tĩnh HTML/CSS/JS (11 trang + `partials/header.html`, `partials/footer.html`,
`assets/css/style.css`, `assets/js/main.js`) là bản clone từ 1 file thiết kế
(`trang-chu.png` cho trang chủ; các trang khác chỉ bám bố cục/nội dung/icon).
Mục tiêu: nâng cấp để có thể release cho khách hàng thật — nội dung đúng/đủ,
UI/UX chuyên nghiệp, behavior đầy đủ hợp lý (đặc biệt header), responsive
đúng trên mọi trang (đặc biệt header/menu mobile) — **giữ nguyên style hệ
thống hiện tại** (màu, font, token, layout tổng thể), chỉ bổ sung
component/pattern mới khi trang quá sơ sài.

Audit toàn site (11 trang + partials + CSS 2301 dòng + JS) đã xác định các
vấn đề cụ thể theo 4 tiêu chí: nội dung, bố cục/UI-UX, behavior, responsive.
Chi tiết từng vấn đề và quyết định xử lý nằm trong các lớp bên dưới.

## Cách tiếp cận

Triển khai theo 4 lớp tuần tự, tận dụng kiến trúc partial + 1 file CSS/JS
dùng chung để tránh sửa lặp lại nhiều lần trên từng trang:

1. Hạ tầng dùng chung (header/footer/CSS/JS)
2. Nội dung từng trang
3. UI/UX polish
4. QA responsive toàn site

## Lớp 1 — Hạ tầng dùng chung

**Header (`partials/header.html`, `assets/css/style.css`):**
- `.site-header`: đổi `position: relative` → `position: sticky; top: 0;`
  (giữ `z-index: 60` hiện có).
- Thêm `scroll-behavior: smooth` toàn site (áp ở `html`).
- Giữ nguyên cơ chế dropdown desktop hiện tại (`:hover` + `:focus-within`
  trên `.nav-group`) — không có lỗi, không sửa.

**Mobile nav (`assets/js/main.js`):**
- Khoá scroll `<body>` khi `.main-nav.is-open` (thêm/gỡ class, vd
  `body.nav-locked { overflow: hidden; }`).
- Đóng menu mobile khi nhấn phím **Escape**.
- Đóng menu mobile khi **click ra ngoài** `<nav>`/`<header>`.
- Cập nhật `aria-expanded` trên phần tử `.nav-group` khi tap mở/đóng submenu
  con trên mobile (hiện chỉ `.nav-toggle` có `aria-expanded`, `.nav-group`
  thì không).

**Footer (`partials/footer.html`):**
- Thêm cột "Liên kết nhanh" (sitemap các trang chính: Giải pháp, Sản phẩm,
  Dự án, Về chúng tôi, Tin tức, Liên hệ).
- Thêm dòng cuối: `© {năm hiện tại — lấy động bằng JS} Cameramienbac. All
  rights reserved.` Không thêm số ĐKKD (không có thông tin thật, không bịa).
- Ẩn (không render) icon mạng xã hội chưa có link thật (Facebook, Zalo,
  YouTube, TikTok, LinkedIn hiện đều `href="#"`) — theo quyết định của
  người dùng, để trống thay vì dẫn tới trang chết.

**Bug/nợ kỹ thuật sửa ngay (không đổi giao diện hiện có):**
- `aiot-platform.html:33` và `trung-tam-ai.html:33`: inline
  `style="grid-template-columns:..."` khiến layout 2 cột không bao giờ
  chuyển 1 cột ở mobile (inline style thắng mọi rule trong `@media`).
  Chuyển sang class CSS có breakpoint đúng (tái dùng pattern `.grid--2`
  hiện có hoặc modifier tương đương).
- Dọn toàn bộ inline `style="..."` còn lại ở `trung-tam-ai.html`,
  `aiot-platform.html`, `ve-chung-toi.html`, `du-an.html` thành class dùng
  lại được — không đổi giao diện, chỉ đổi cách khai báo.

## Lớp 2 — Nội dung từng trang

**Quyết định nền tảng (đã chốt với người dùng):**
- Tên khách hàng/dự án thật (Vinhomes, FPT, BIDV, Bệnh viện Bạch Mai,
  Samsung Bắc Ninh, các trường THPT/THCS nêu tên) — **giữ nguyên**, đây là
  khách hàng thật. Rà soát lại số liệu đi kèm (số camera, quy mô) cho hợp lý
  và nhất quán.
- Đối tác công nghệ: tách 2 nhãn rõ ràng —
  - "Đối tác thiết bị": Hikvision, Dahua, TVT, Axis, Hanwha
  - "Đối tác công nghệ AI": FPT, Intel, NVIDIA, Microsoft, AWS, Viettel
  Áp dụng nhất quán ở `ve-chung-toi.html`, `trung-tam-ai.html`,
  `aiot-platform.html` (hiện đang hiển thị lệch nhãn giữa các trang).
- Số liệu mâu thuẫn: `ve-chung-toi.html` "60+ kỹ sư" (toàn công ty) vs
  `trung-tam-ai.html` "100+ chuyên gia AI" (riêng 1 đơn vị) — không hợp lý
  về số học. Hạ số chuyên gia AI xuống mức nằm trong tổng (vd "30+ chuyên
  gia AI") để nhất quán.
- `san-pham.html`: viết theo nhóm sản phẩm/tính năng chung chung (không có
  model/thông số/giá cụ thể) để tránh sai lệch thông tin thương mại — mọi
  CTA vẫn dẫn về `lien-he.html`.

**Theo trang:**
- `du-an.html`: thêm dải thống kê đầu trang "500+ dự án đã triển khai,
  20.000+ camera lắp đặt..." (đồng bộ với số liệu ở `ve-chung-toi.html`),
  ghi rõ 9 dự án hiển thị là "dự án tiêu biểu" — khớp với con số 500+ mà
  không cần thêm dự án giả. Bộ lọc (danh mục/tỉnh/năm) chuyển từ UI chết
  sang lọc thật bằng JS phía client trên dữ liệu tĩnh sẵn có (không cần
  backend); có trạng thái "không có kết quả".
- `giai-phap.html`: thêm card "Trung tâm AI" còn thiếu trong section "Nhóm
  giải pháp chính" (hiện chỉ 3/4, trong khi menu header đã có mục này).
  Rút gọn section "Giải pháp theo từng lĩnh vực" (đang trùng lặp gần như
  y hệt với `giai-phap-toan-dien.html`) thành bản teaser 3 mục + nút "Xem
  tất cả lĩnh vực" trỏ sang `giai-phap-toan-dien.html`.
- `truong-hoc-ai.html`: thay section "Khóa học tiêu biểu" (dạy AI/lập
  trình/robotics — không phải dịch vụ thật) bằng section đúng chuyên môn:
  ứng dụng camera AI trong quản lý trường học (điểm danh khuôn mặt, giám
  sát an ninh, cảnh báo bất thường).
- `tin-tuc.html`: gỡ toàn bộ link "Đọc tiếp" trỏ `href="#"` (không tạo
  trang chi tiết bài viết ở giai đoạn này — theo quyết định người dùng);
  đổi ảnh minh hoạ mỗi bài cho khớp chủ đề hơn (dùng ảnh có sẵn phù hợp
  thay vì ảnh dự án không liên quan).
- `lien-he.html`: điền nội dung cho `phero__lead` đang rỗng (dòng 22).
  Form liên hệ: nâng UX phía client (validate, trạng thái loading/thành
  công giả lập) nhưng giữ comment rõ trong code rằng cần nối backend/email
  thật trước khi release chính thức (action hiện tại `action="#"`, không có
  endpoint thật).

## Lớp 3 — UI/UX polish

- **Hero trùng lặp thị giác**: `tin-tuc.html` và `toa-nha-thong-minh.html`
  dùng chung đúng 1 ảnh nền (`sol-bld-hero.jpg`), không có ảnh thay thế phù
  hợp trong thư viện hiện có (ảnh tin tức hiện có chỉ 711×198px, quá nhỏ
  cho banner 2048px). Thêm biến thể overlay/gradient riêng cho
  `tin-tuc.html` để không nhìn giống hệt, không cần ảnh mới.
- **Đội ngũ** (`ve-chung-toi.html`): giữ icon-avatar (không có ảnh nhân sự
  thật), nâng cấp trình bày theo phòng ban/vai trò thay vì ngụ ý chân dung
  cá nhân thật.
- **CTA cuối trang thiếu nhất quán**: `san-pham.html` và `du-an.html` hiện
  kết thúc đột ngột trước footer. Tái dùng component `.slogan` đã có sẵn ở
  `lien-he.html` (không tạo component mới) với nội dung phù hợp từng trang.
- Kết quả của việc dọn inline-style ở Lớp 1 cũng giúp spacing nhất quán hơn
  giữa các trang — không có việc riêng thêm ở lớp này ngoài các mục trên.

## Lớp 4 — QA Responsive (cuối cùng)

- Xác nhận bản vá bug `grid-template-columns` (Lớp 1) hoạt động đúng — 1
  cột trên mobile.
- Kiểm tra thủ công toàn bộ 11 trang ở các mốc: 1440px, 1024px (mốc chuẩn
  theo README), 768px, 375px. Soi riêng: header/menu mobile (mở/đóng, khoá
  scroll, Escape, click-outside), form liên hệ, bộ lọc dự án mới, các
  section vừa thêm/sửa ở Lớp 2 và Lớp 3.
- Không refactor lại vị trí các khối `@media` rải rác trong CSS (hiện ở 4
  vị trí: dòng 783, 1474, 1999, 2287) vì không ảnh hưởng chức năng — rule
  mới thêm cạnh component liên quan, không dọn toàn bộ file để tránh
  rework/rủi ro ngoài phạm vi.

## Ngoài phạm vi (out of scope)

- Không chụp/thêm ảnh thật mới (không có nguồn ảnh thật để dùng).
- Không nối backend/email thật cho form liên hệ (chỉ nâng UX phía client).
- Không tạo trang chi tiết bài viết tin tức (`tin-tuc-chi-tiet.html`).
- Không đổi màu sắc/font/design token hoặc cấu trúc layout tổng thể.
- Không refactor lại vị trí các khối CSS responsive hiện có.
- Không thêm số ĐKKD hoặc link mạng xã hội giả vào footer.

## Kiểm thử

- Kiểm tra thủ công qua trình duyệt (site chạy qua `python3 -m http.server`
  theo README) ở các breakpoint nêu ở Lớp 4, cho từng trang trong 11 trang.
- Kiểm tra console không có lỗi JS mới sau khi thêm body-scroll-lock,
  Escape/click-outside handler, và bộ lọc dự án.
- Kiểm tra thủ công bằng bàn phím (Tab/Shift+Tab/Escape) cho header và menu
  mobile.

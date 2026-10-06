# Cameramienbac — website tĩnh (HTML / CSS / JS)

Clone tĩnh của thiết kế `assets/design/trang-chu.png`. Trang chủ `index.html` được dựng
làm mẫu; header và footer tách thành partial để các trang sau dùng lại.

## Chạy dự án

Trang dùng `fetch()` để nạp partial nên cần chạy qua HTTP (mở trực tiếp bằng `file://`
trình duyệt sẽ chặn vì CORS):

```bash
cd cameramienbac
python3 -m http.server 8000
# mở http://localhost:8000/
```

## Cấu trúc

Mỗi trang là một thư mục `/<slug>/index.html` và được gọi bằng URL `/<slug>/`.
Mọi link nội bộ, asset và partial đều dùng đường dẫn tuyệt đối từ gốc site
(`/lien-he/`, `/assets/...`, `/partials/...`) nên site phải được phục vụ tại gốc domain.

```
index.html                         Trang chủ (/)
giai-phap/index.html               Giải pháp (trang tổng)
toa-nha-thong-minh/index.html      Giải pháp › Tòa nhà thông minh
truong-hoc-ai/index.html           Giải pháp › Trường học AI
giai-phap-toan-dien/index.html     Giải pháp › Giải pháp toàn diện
san-pham/index.html                Sản phẩm
san-pham/camera-ai/index.html      Sản phẩm › Camera AI
san-pham/luu-tru/index.html        Sản phẩm › NVR & lưu trữ
san-pham/ai-server/index.html      Sản phẩm › AI Server / AI Box
san-pham/ra-vao/index.html         Sản phẩm › Kiểm soát ra vào
san-pham/anpr/index.html           Sản phẩm › Barrier & ANPR
san-pham/iot/index.html            Sản phẩm › IoT & cảm biến
san-pham/mang/index.html           Sản phẩm › Thiết bị mạng
san-pham/aiot-platform/index.html  Sản phẩm › AIoT Platform
trung-tam-ai/index.html            Giải pháp › Trung tâm AI
du-an/index.html                   Dự án (có bộ lọc + 9 dự án mẫu)
ve-chung-toi/index.html            Về chúng tôi
tin-tuc/index.html                 Tin tức
lien-he/index.html                 Liên hệ (thông tin + bản đồ + form)
partials/header.html               Header dùng chung (logo, menu, hotline)
partials/footer.html               Footer dùng chung (logo, liên hệ, MXH, CTA)
assets/css/style.css               Toàn bộ style
assets/js/main.js                  Nạp partial + menu mobile + active menu
assets/images/                     Ảnh đã tách từ file thiết kế
assets/design/                     File thiết kế gốc (tham chiếu)
```

### Vùng do trang quản trị (CMS) quản lý — KHÔNG sửa tay

Sản phẩm, tin tức, danh mục tin được quản lý ở `/admin/` (xem `../GAS.md`). `../scripts/build.py`
ghi đè các vùng nằm giữa mốc `<!-- cms:<tên>:start -->` / `<!-- cms:<tên>:end -->` trong
`partials/catalog.html`, `hang-*/index.html`, `tin-tuc/index.html`, và sinh `tin-tuc/<slug>/`.
Sửa tay trong các vùng đó sẽ bị mất ở lần build sau; xoá mốc thì build dừng với lỗi.
Muốn sửa giao diện thẻ/bài viết: sửa `../scripts/build.py` hoặc `../templates/news-detail.html`.

### Thêm trang mới

```html
<!-- file: /<slug>/index.html -->
<div data-include="/partials/header.html"></div>
<main> ... </main>
<div data-include="/partials/footer.html"></div>
<script src="/assets/js/main.js"></script>
```

`main.js` tự thay placeholder bằng nội dung partial và tự gắn class `is-active` cho
menu trùng slug của URL đang mở (`/<slug>/`).

## Quy ước dựng layout

- **Khung tham chiếu: viewport 1024px** — ở độ rộng này trang khớp gần như tuyệt đối với
  `trang-chu.png` (sai lệch pixel trung bình ~4%, phần còn lại chủ yếu do file thiết kế
  là ảnh raster bị nhoè).
- `.container`: `max-width: 1200px; padding: 0 28px` → tại 1024px nội dung rộng đúng 968px
  như thiết kế.
- Font: **Barlow** (Google Fonts) — đã đo và đối chiếu tỉ lệ bề rộng / chiều cao chữ hoa
  trên 7 chuỗi khác nhau của thiết kế; Barlow là font khớp nhất trong các font có hỗ trợ
  tiếng Việt.
- Ảnh trong `assets/images/` được cắt trực tiếp từ file thiết kế. Các nền có chữ in sẵn
  (hero, dải "Vì sao chọn", header, footer, panel "Giải pháp toàn diện") đã được xoá chữ
  bằng thuật toán inpaint để dùng lại làm background sạch.

## Mức độ bám thiết kế theo trang

| Trang | Mức độ |
|-------|--------|
| `index.html` | Khớp pixel với `trang-chu.png` (xem phần dưới) |
| 8 trang có file thiết kế | Bám **bố cục, nội dung và icon** theo ảnh thiết kế; kích thước/khoảng cách dùng lại design system của trang chủ thay vì đo từng pixel |
| `/ve-chung-toi/`, `/tin-tuc/` | Không có file thiết kế — tự dựng bằng đúng design system (token màu, font, component) |

**Vị trí 2 trang mới trong menu**

| Trang | Đặt ở | Lý do |
|-------|-------|-------|
| `/san-pham/aiot-platform/` | **Sản phẩm › AIoT Platform** | Là nền tảng phần mềm; trong ảnh thiết kế menu đang active ở "Sản phẩm" |
| `/trung-tam-ai/` | **Giải pháp › Trung tâm AI** | Bản chất là nhóm giải pháp AI; thêm vào dropdown sẵn có nên không phải thêm mục cấp 1 |

Cả hai đều được thêm **link chéo**: `/san-pham/` có khối giới thiệu AIoT Platform,
`/ve-chung-toi/` có khối giới thiệu Trung tâm AI.

**Đã gỡ khỏi bản clone:**
- Section *"Giải pháp toàn diện từ Cameramienbac"* trên trang chủ (nội dung nay ở `/giai-phap-toan-dien/`).
- Dải CTA cuối trang (logo lớn + nút liên hệ) ở các trang trong — trùng chức năng với footer
  dùng chung nên bỏ để tránh lặp.

Header/footer của mọi trang dùng chung một partial, nên thương hiệu thống nhất là
**AI & SMART / 0978 406 868**, không theo biến thể *AI & FPT / 0973 406 668* xuất hiện trong
vài file thiết kế.

## Khác biệt có chủ đích so với ảnh thiết kế

Trong `trang-chu.png`, dải màu xanh đậm chứa logo / hotline / email / mạng xã hội nằm ở
**giữa trang** (phía dưới nó vẫn còn 2 section). Đây là footer bị đặt sai vị trí trong
ảnh mock, nên bản clone đưa footer xuống cuối trang:

```
Header → Hero → Anh đang giải quyết bài toán nào? → Vì sao chọn Cameramienbac?
       → Giải pháp toàn diện → Đối tác tin cậy → Footer
```

## Responsive

| Độ rộng   | Bố cục                                                        |
|-----------|---------------------------------------------------------------|
| ≥ 1024px  | Đúng như thiết kế (5 card / hàng, 4 cột "Vì sao chọn", footer 3 cột) |
| 720–1023  | Menu thu gọn (hamburger), 3 card / hàng, 2 cột "Vì sao chọn"   |
| < 720px   | 1 card / hàng, hotline chỉ còn icon, footer xếp dọc            |

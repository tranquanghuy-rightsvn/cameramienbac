# GAS.md — Guideline CMS Cameramienbac (Google Apps Script)

> Nguồn quyết định CHỐT cho mọi file trong `gas/` (Code.js, index.html, app.html, css.html,
> js.html) và cho `scripts/build.py`. Đọc TOÀN BỘ file này trước khi sửa bất cứ thứ gì.
> Theo playbook skill `free-cms-static-site-pipeline` (dự án mẫu: xevip; phần "Nội dung AI"
> tham khảo khtcard).
>
> ⚠️ Các mục đánh dấu **[ĐỀ XUẤT]** là do bên kỹ thuật suy ra từ cấu trúc site hiện có, CHƯA
> được khách xác nhận. Khách đổi ý thì sửa code + sửa file này trong CÙNG 1 lượt.

## 0. Phạm vi — ĐÚNG 5 mục, không làm rộng hơn

1. **Sản phẩm** — danh mục thiết bị ở `/san-pham/` (+ 8 trang nhóm `/san-pham/<nhóm>/`, cùng
   dùng partial `partials/catalog.html`) và khối "Sản phẩm tiêu biểu" ở 4 trang hãng
   `/hang-<hãng>/`. **Thông tin hãng là HARD-CODE** (danh sách hãng, nhãn hiển thị, nội dung
   giới thiệu ở trang `/hang-*/`) — không quản lý qua CMS.
2. **Tin tức** — bài viết `/tin-tuc/<slug>/` + danh sách `/tin-tuc/`.
3. **Danh mục tin tức** — các nút lọc chủ đề ở `/tin-tuc/`.
4. **Người dùng** — tài khoản được phép đăng nhập CMS.
5. **Nội dung AI** — kiến thức nạp cho trợ lý chat ở góc phải website (ghi chú chung + cặp
   hỏi đáp), tham khảo tab "Hỏi đáp AI" của khtcard.

KHÔNG thuộc phạm vi: form liên hệ/khảo sát (`form[data-lead]` hiện chưa gửi đi đâu), dự án,
trang giải pháp, trang chủ. Không tự thêm.

## I. Đăng nhập & phân quyền

1. Luồng: nhập email → nhận OTP qua email → nhập mã → vào Admin. Không mật khẩu.
2. Chỉ email có trong Sheet `Users` mới xin được OTP — NGOẠI TRỪ chủ script.
3. Chủ script (người deploy) LUÔN là `root` ngầm định, không cần/không hiện trong danh sách
   người dùng (`ownerEmail_()` dùng chung cho `requestOtp` và `whoAmI_`).
4. Phân quyền **[ĐỀ XUẤT]** 3 cấp `root > admin > editor`:
   | Quyền | Sản phẩm | Tin tức | Danh mục tin | Nội dung AI | Người dùng |
   |---|---|---|---|---|---|
   | editor | ✔ | ✔ | ✔ | ✔ | ✘ |
   | admin | ✔ | ✔ | ✔ | ✔ | ✔ (chỉ thêm/sửa/xoá admin + editor) |
   | root | ✔ | ✔ | ✔ | ✔ | ✔ |
   Dòng `root` chỉ sửa tay trong Sheet. Không ai tự sửa/xoá chính mình qua CMS.
5. OTP sống 10 phút, cooldown 60 giây, tối đa 5 lần nhập sai. Token phiên 30 ngày (localStorage).
   `verifyOtp` gọi `purgeExpiredTokens_()`; nút Đăng xuất gọi `logout(token)` phía server.
6. Server tự `requireRole_` ở MỌI hàm — ẩn nút trên UI không phải bảo mật.

## II. Sản phẩm

Mỗi sản phẩm = 1 thẻ `.pitem` ("dòng sản phẩm" kèm model tiêu biểu). Lưu GỌN trong 1 file
`data/catalog.json` (mảng, kèm toàn bộ field — ít bản ghi, không tách index/detail).

1. Field CÓ ô nhập (khớp đúng các phần tử của thẻ `.pitem` hiện có):
   - **Tên dòng sản phẩm** (`title`) — `pitem__title`.
   - **Nhóm** (`category`) — chọn 1 trong danh sách CỐ ĐỊNH `PRODUCT_CATEGORIES`
     (camera-ai, luu-tru, ai-server, ra-vao, anpr, iot, mang, phan-mem) — khớp các nút lọc
     của catalog và 8 trang `/san-pham/<nhóm>/`.
   - **Ứng dụng** (`apps`) — chọn nhiều trong danh sách CỐ ĐỊNH `PRODUCT_APPS` (an-ninh,
     toa-nha, truong-hoc, van-phong, nha-may, bai-xe, do-thi) — khớp ô lọc "Ứng dụng".
   - **Hãng cung cấp** (`brands`) — chọn nhiều trong danh sách HARD-CODE `BRANDS` (hikvision,
     dahua, axis, hanwha, tvt, nvidia, intel). Để trống = hiện chip "Theo dự án".
   - **Mô tả ngắn** (`description`) — `pitem__text`.
   - **Hãng của model tiêu biểu** (`model_brand`) — 1 hãng trong `BRANDS` hoặc trống.
     Quyết định sản phẩm có hiện ở khối "Sản phẩm tiêu biểu" của trang `/hang-<hãng>/` không
     (đúng quy luật của 4 trang hãng hiện có).
   - **Model tiêu biểu** (`model`, vd "Hikvision DS-2CD2683G2-LIZS2UHUN") + **Ghi chú model**
     (`model_note`, vd "8MP") — `pitem__model`. Trống thì không hiện dòng model.
   - **Giá** (`price`, số nguyên VNĐ) — trống/0 = "Liên hệ báo giá".
   - **Ảnh** (`image`) — tuỳ chọn (vài dòng IoT/mạng hiện không có ảnh).
   - **Nút**: `cta_label` + `cta_url` tuỳ chọn — trống thì mặc định "Yêu cầu cấu hình" →
     `/lien-he/?sp=<tên>#tu-van` (đúng như mọi thẻ hiện có).
   - **Thứ tự** (`order`) — trong cùng nhóm, nhỏ hiện trước.
2. Field KHÔNG có ô nhập (server tự suy): `id` (slug từ tên lúc tạo, BẤT BIẾN — dùng đặt tên
   ảnh), `image_alt` (= tên + model; bản ghi migrate giữ alt gốc cho tới khi đổi ảnh),
   `updated_at`.
3. Danh sách trong Admin: tải qua `boot()` (đọc thẳng GitHub — luôn mới nhất).
4. Ảnh: nén phía client (cạnh dài ≤ 1000px, JPEG 0.85), upload thẳng GitHub ngay khi chọn, tên
   tất định `html/assets/images/products/<id>.jpg` (ghi đè khi đổi ảnh). Ảnh RIÊNG 1-1.
   Ảnh migrate (tên theo model, vd `ds-2ce72df0t-f.jpg`) giữ nguyên, CMS không đụng.
5. Thứ tự hiển thị trên site: theo thứ tự nhóm trong `PRODUCT_CATEGORIES`, rồi `order`.

## III. Tin tức

1. Field CÓ ô nhập: **Tiêu đề**, **URL** (slug tự sinh, bất biến sau lần Lưu đầu), **Danh mục**
   (chọn từ danh mục tin — mục IV), **Mô tả** (lead dưới tiêu đề + meta description + đoạn
   tóm tắt ở thẻ danh sách), **Ảnh bìa** (bắt buộc), **Nội dung** (TinyMCE: đoạn/H2/H3,
   đậm/nghiêng, danh sách, link, bảng, **CÓ nút chèn ảnh nhanh** — mở thẳng hộp chọn file,
   ảnh bọc `<figure>` + `<figcaption>`, alt = caption, rơi về tiêu đề nếu caption rỗng).
2. Field KHÔNG có ô nhập: `date` (ngày Lưu lần đầu, giữ nguyên khi sửa), `read_min` (tự tính
   theo số chữ, ~200 chữ/phút, tối thiểu 1), `cover_alt` (= tiêu đề), `updated_at`.
3. Lưu trữ: `data/news.json` (index nhẹ, commit CHỐT) + `data/news/<slug>.json` (đầy đủ).
4. Ảnh: `html/assets/images/news/<slug>-cover.jpg` (ghi đè), ảnh nội dung
   `html/assets/images/news/<slug>-content-<N>.jpg` (đánh số bất biến). Trong `content_html`
   lưu đường dẫn TUYỆT ĐỐI theo domain `/assets/images/news/...` (site dùng đường dẫn tuyệt
   đối từ gốc ở mọi nơi). Trong editor hiển thị qua raw.githubusercontent.com.
5. Bài viết tay có sẵn (`/tin-tuc-5-dau-hieu-camera-loi-thoi/` + 5 thẻ mẫu) nằm ở
   `data/legacy-news.json` — CMS KHÔNG sửa/xoá; build chỉ liệt kê chúng trong danh sách, không
   build lại trang chi tiết. Muốn bỏ 5 thẻ mẫu (đang trỏ `/lien-he/`) thì xoá tay trong file đó.
6. Sửa: slug khoá cả server (throw) lẫn client (disabled; nhớ bật lại khi tạo mới).
7. Xoá: xoá `data/news/<slug>.json` + ảnh bìa + ảnh nội dung của bài (an toàn vì ảnh 1-1) +
   gỡ khỏi index (ghi SAU CÙNG). Có popup xác nhận.

## IV. Danh mục tin tức

1. Field: **Tên** (hiện ở nút lọc + nhãn trên ảnh), **slug** (tự sinh, bất biến, là khoá tham
   chiếu từ bài viết), **Thứ tự**.
2. Lưu `data/news-categories.json` (1 file, tự nó là commit chốt). Đổi tên → mọi bài (kể cả
   legacy) tự hiện tên mới sau lần build kế (bài lưu slug, không lưu tên).
3. Không cho xoá danh mục đang có bài dùng (CMS hoặc legacy) — báo rõ số bài.

## V. Nội dung AI (trợ lý chat trên website)

1. Hai loại nội dung, cùng 1 tab "Nội dung AI":
   - **Kiến thức chung** (`data/ai-settings.json` → `extra_notes`): văn bản tự do — chính sách
     bảo hành, khu vực phục vụ, quy trình khảo sát... mọi thứ chưa có trên site. Kèm
     `out_of_scope_message` (câu trả lời khi bị hỏi ngoài phạm vi).
   - **Cặp hỏi đáp** (`data/chat-qa.json`): câu hỏi + câu trả lời + trạng thái
     (`published` / `draft` = tạm tắt). Ưu tiên CAO NHẤT khi trợ lý trả lời.
2. Trợ lý còn TỰ biết (không cần nạp): danh mục sản phẩm (`data/catalog.json`), danh sách
   tin tức, thông tin liên hệ hard-code (hotline 0979 406 868, cameramienbac@cmvn.vn,
   15 ngõ 36 Hoàng Quốc Việt, Cầu Giấy, Hà Nội, T2–T7 8:00–17:30).
3. Khác khtcard: site này KHÔNG có Cloudflare Worker. Khung chat (`html/assets/js/main.js`)
   gọi THẲNG `doPost` của GAS (`{action:"chat"}`, Content-Type `text/plain`), GAS ghép system
   prompt từ các file trên (cache 10 phút, tự xoá cache mỗi khi Lưu bất kỳ nội dung nào trong
   CMS) rồi gọi Gemini bằng `GEMINI_API_KEY`. → Lưu Nội dung AI có hiệu lực NGAY, không cần
   chờ build.
4. Chưa cấu hình `GEMINI_API_KEY` hoặc lỗi bất kỳ → khung chat tự rơi về câu trả lời mẫu cũ
   (khớp từ khoá) + mời để lại SĐT. Không bao giờ để khách nhìn khung chat chết.
5. Chống lạm dụng endpoint công khai: trần 30 lượt/phút toàn endpoint + 10 lượt/phút mỗi cuộc
   trò chuyện, tối đa 10 tin gần nhất, mỗi tin ≤ 1000 ký tự.
6. Tab có ô **"Thử trợ lý"** để admin hỏi thử ngay trong CMS (cùng prompt với website).
7. Không ghi nhật ký hội thoại (chưa yêu cầu).

## VI. Người dùng

Xem mục I.4. Tab "Người dùng" chỉ hiện với admin/root; server chặn lại bằng `requireRole_`.

## VII. UX chung

- Modal Xác nhận (Huỷ/Xoá) trước mọi thao tác xoá; modal Thông báo (1 nút Đóng) sau khi xong —
  không `alert()`/`confirm()` native, không toast.
- Mọi nút async: `withLoading` (disable + spinner, tự phục hồi kể cả khi lỗi).
- Sau Lưu/Xoá: quay về danh sách của chính mục đó, danh sách tự cập nhật, boot cache đồng bộ
  ngay (`syncBootCache_`).
- Chuyển tab chỉ ẩn/hiện. Mở app: 1 lượt `boot()`; lần sau hiện ngay từ cache rồi revalidate.
- Phiên bản client (`CLIENT_BUILD`) do server BĂM từ nội dung app.html + js.html — không gõ
  tay. Mọi key localStorage (trừ token) mang phiên bản này, bản cũ tự dọn.
- TinyMCE tự host tại `<SITE_URL>/vendor/tinymce/` (copy từ xevip, 6.8.5); init chỉ khi tab
  soạn đã hiện.
- Không lộ tên hạ tầng (Sheet/Drive/GitHub/Apps Script) trong chữ hiển thị, thông báo lỗi
  và comment của các file gửi xuống trình duyệt.

## VIII. Kiến trúc lưu trữ

- Google Sheet "Cameramienbac CMS Data" (tự tạo lần đầu): sheet `Users` (cột `email`, `role`).
- GitHub (Contents API) — đường dẫn cố định, đổi phải sửa cả `scripts/build.py` + CI:
  | Đường dẫn | Vai trò | Trigger CI |
  |---|---|---|
  | `data/catalog.json` | toàn bộ sản phẩm | ✔ |
  | `data/news.json` | index tin tức (ghi SAU CÙNG) | ✔ |
  | `data/news/<slug>.json` | chi tiết 1 bài | — |
  | `data/news-categories.json` | danh mục tin | ✔ |
  | `data/legacy-news.json` | bài viết tay cũ (CMS không ghi) | ✔ |
  | `data/chat-qa.json`, `data/ai-settings.json` | Nội dung AI (GAS đọc lúc chat) | — |
  | `html/assets/images/products/<id>.jpg` | ảnh sản phẩm CMS | — |
  | `html/assets/images/news/*` | ảnh tin tức | — |
- `data/products.json` (84 bản ghi crawl thô) KHÔNG thuộc CMS, CMS không đọc/ghi.
- `scripts/build.py` ghi đè vùng giữa các mốc `<!-- cms:... -->`:
  `html/partials/catalog.html` (lưới sản phẩm), `html/hang-{hikvision,dahua,axis,hanwha}/index.html`
  (lưới "Sản phẩm tiêu biểu"), `html/tin-tuc/index.html` (nút lọc + danh sách); và sinh
  `html/tin-tuc/<slug>/index.html` từ `templates/news-detail.html` (có dấu
  `<!-- build.py:generated -->`, trang mồ côi tự bị xoá). Xoá mốc = build báo lỗi, không im lặng.
- Độ trễ Lưu → lên site: ~1–2 phút (CI build + hosting deploy). Nội dung AI: tức thì.

## IX. Bug đã gặp ở dự án này

- (chưa có — ghi vào đây khi gặp)

## X. Script Properties (tên CỐ ĐỊNH)

- `GITHUB_TOKEN`, `GITHUB_OWNER` (`tranquanghuy-rightsvn`), `GITHUB_REPO` (`cameramienbac`),
  `GITHUB_BRANCH` (`master`) — bắt buộc.
- `SITE_URL` — domain thật của site, không có `/` cuối (vd `https://cameramienbac.vn`). Dùng để
  tải TinyMCE tự host. Chưa có domain thì để trống: CMS tạm tải TinyMCE từ CDN.
- `GEMINI_API_KEY` — key Gemini cho trợ lý chat. Trống = chat dùng câu trả lời mẫu.
- `GEMINI_MODEL` — tuỳ chọn, mặc định `gemini-3.5-flash-lite`.
- `SPREADSHEET_ID` — KHÔNG cần điền, code tự tạo lần đầu.

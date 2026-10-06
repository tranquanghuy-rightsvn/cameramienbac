# GAS.md — Guideline CMS Cameramienbac (Google Apps Script)

> Nguồn quyết định CHỐT cho mọi file trong `gas/` (Code.js, index.html, app.html, css.html,
> js.html) và cho `scripts/build.py`. Đọc TOÀN BỘ file này trước khi sửa bất cứ thứ gì.
> Theo playbook skill `free-cms-static-site-pipeline` (dự án mẫu: xevip; phần "Nội dung AI"
> tham khảo khtcard).
>
> ⚠️ Các mục đánh dấu **[ĐỀ XUẤT]** là do bên kỹ thuật suy ra từ cấu trúc site hiện có, CHƯA
> được khách xác nhận. Khách đổi ý thì sửa code + sửa file này trong CÙNG 1 lượt.

## 0. Phạm vi — ĐÚNG 6 mục, không làm rộng hơn

1. **Sản phẩm** — danh mục thiết bị ở `/san-pham/` (+ 8 trang nhóm `/san-pham/<nhóm>/`, cùng
   dùng partial `partials/catalog.html`) và khối "Sản phẩm tiêu biểu" ở 4 trang hãng
   `/hang-<hãng>/`. **Thông tin hãng là HARD-CODE** (danh sách hãng, nhãn hiển thị, nội dung
   giới thiệu ở trang `/hang-*/`) — không quản lý qua CMS.
2. **Tin tức** — bài viết `/tin-tuc/<slug>/` + danh sách `/tin-tuc/`.
3. **Danh mục tin tức** — các nút lọc chủ đề ở `/tin-tuc/`.
4. **Dự án** — lưới dự án ở `/du-an/` (+ bộ lọc Tỉnh/Năm), 3 dự án ở trang chủ, trang chi tiết
   `/du-an/<slug>/` (thêm 06/10/2026 theo yêu cầu khách).
5. **Người dùng** — tài khoản được phép đăng nhập CMS.
6. **Nội dung AI** — kiến thức nạp cho trợ lý chat ở góc phải website (ghi chú chung + cặp
   hỏi đáp), tham khảo tab "Hỏi đáp AI" của khtcard.

Ngoài 6 mục trên, GAS còn nhận **form tư vấn** trên website (mục VI-b) — không có ô quản lý
trong CMS, dữ liệu xem trong sheet `Leads` + email báo.

KHÔNG thuộc phạm vi: trang giải pháp, phần còn lại của trang chủ, khối "dự án" minh hoạ ở trang `/toa-nha-thong-minh/` và các
lời chứng thực (vẫn viết tay). Không tự thêm.

## I. Đăng nhập & phân quyền

1. Luồng: nhập email → nhận OTP qua email → nhập mã → vào Admin. Không mật khẩu.
2. Chỉ email có trong Sheet `Users` mới xin được OTP — NGOẠI TRỪ chủ script.
3. Chủ script (người deploy) LUÔN là `root` ngầm định, không cần/không hiện trong danh sách
   người dùng (`ownerEmail_()` dùng chung cho `requestOtp` và `whoAmI_`).
4. Phân quyền **[ĐỀ XUẤT]** 3 cấp `root > admin > editor`:
   | Quyền | Sản phẩm | Tin tức | Danh mục tin | Dự án | Nội dung AI | Người dùng |
   |---|---|---|---|---|---|---|
   | editor | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ |
   | admin | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ (chỉ thêm/sửa/xoá admin + editor) |
   | root | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
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
5. 6 bài có sẵn từ trước (bài thật `5-dau-hieu-camera-loi-thoi` + 5 bài mẫu) ĐÃ chuyển vào CMS
   ngày 06/10/2026 — admin thấy và sửa/xoá được như bài thường. URL cũ
   `/tin-tuc-5-dau-hieu-camera-loi-thoi/` chuyển hướng 301 qua `html/_redirects`. 5 bài mẫu mới
   chỉ có 1 đoạn mô tả làm nội dung — cần viết thêm hoặc xoá. Bài chuyển vào giữ ảnh bìa có sẵn
   (`assets/images/news-N.webp`) cho tới khi tải ảnh bìa mới. `data/legacy-news.json` giờ rỗng
   (build vẫn hỗ trợ nếu sau này cần).
6. Sửa: slug khoá cả server (throw) lẫn client (disabled; nhớ bật lại khi tạo mới).
7. Xoá: xoá `data/news/<slug>.json` + ảnh bìa + ảnh nội dung của bài (an toàn vì ảnh 1-1) +
   gỡ khỏi index (ghi SAU CÙNG). Có popup xác nhận.

8. **Smart content** (áp dụng 06/10/2026 cho 5 bài mẫu đã viết dày): bài có cờ `smart: true` trong
   `data/news.json` + `data/news/<slug>.json`, thân bài là HTML thiết kế sẵn bằng các khối `tv-`
   (quy trình, slider, dải ảnh phóng to, thẻ cảnh báo, bảng, hỏi đáp, thẻ liên hệ).
   - CMS: sửa được Tiêu đề, Mô tả, Danh mục, Ảnh bìa; KHÔNG sửa được thân bài (server giữ nguyên
     `content_html` cũ dù client gửi gì), KHÔNG xoá được; danh sách hiện nhãn 🔒 Smart content.
   - Site: `build.py` tự nạp `html/assets/css/smart.css` + `html/assets/js/smart.js` cho bài có
     `class="tv-`; bài thường không nạp gì thêm.
   - Sửa nội dung bài smart = sửa trực tiếp `content_html` trong `data/news/<slug>.json` (bên kỹ
     thuật), pull repo trước vì CMS có thể vừa đổi tiêu đề/mô tả/ảnh bìa.

## IV. Danh mục tin tức

1. Field: **Tên** (hiện ở nút lọc + nhãn trên ảnh), **slug** (tự sinh, bất biến, là khoá tham
   chiếu từ bài viết), **Thứ tự**.
2. Lưu `data/news-categories.json` (1 file, tự nó là commit chốt). Đổi tên → mọi bài (kể cả
   legacy) tự hiện tên mới sau lần build kế (bài lưu slug, không lưu tên).
3. Không cho xoá danh mục đang có bài dùng (CMS hoặc legacy) — báo rõ số bài.

## V. Dự án

Mỗi dự án = 1 thẻ `.prj` ở `/du-an/`. Lưu GỌN trong 1 file `data/projects.json` (mảng, kèm cả
`content_html` — ít bản ghi; tự nó là commit chốt). `boot()` chỉ trả bản nhẹ (bỏ `content_html`,
thêm `has_content`), nội dung lấy riêng bằng `getProject` lúc mở form sửa.

1. Field CÓ ô nhập:
   - **Tên dự án** (`title`) — tiêu đề thẻ + H1 trang chi tiết. **URL** (`slug`) tự sinh, bất biến
     sau lần Lưu đầu (khoá cả server lẫn client như tin tức).
   - **Loại công trình** (`category`) — 1 trong danh sách CỐ ĐỊNH `PROJECT_CATEGORIES` (chung-cu,
     do-thi, van-phong, nha-may, truong-hoc, ngan-hang, benh-vien, khac) — khớp các ô lọc "Danh
     mục dự án" viết tay ở `/du-an/`. Nhãn trên ảnh + icon nằm ở `PROJECT_CATEGORIES` của build.py.
   - **Địa điểm** (`location`, vd "Gia Lâm, Hà Nội") — dòng có icon ghim.
   - **Tỉnh/Thành phố** (`city`, bắt buộc) — dùng cho ô lọc; danh sách ô lọc TỰ SINH từ dữ liệu.
   - **Năm hoàn thành** (`year`) — chỉ số + ô lọc "Năm triển khai" (tự sinh, mới nhất trước).
   - **Số camera** (`cameras`) — trống/0 thì không hiện chỉ số camera.
   - **Mô tả ngắn** (`description`) — đoạn trên thẻ, thẻ trang chủ, lead + meta description trang
     chi tiết.
   - **Ảnh bìa** (bắt buộc) — `html/assets/images/projects/<slug>-cover.jpg` (ghi đè), cạnh dài
     ≤ 1600px. Dùng cho thẻ, nền hero và ảnh đầu bài trang chi tiết.
   - **Dòng phụ dưới tên** (`subtitle`), **Giải pháp** (`solution`), **Chủ đầu tư** (`owner`, trống
     = "Cập nhật khi được phép công bố") — chỉ hiện ở trang chi tiết.
   - **Nội dung chi tiết** (`content_html`, TinyMCE giống tin tức, ảnh
     `<slug>-content-<N>.jpg`). **Trống = KHÔNG có trang chi tiết**: thẻ hiện nút "Nhận tư vấn" →
     `/lien-he/`. Có nội dung → sinh `/du-an/<slug>/`, thẻ có link tên + nút "Xem chi tiết".
   - **Hiện ở trang chủ** (`featured`) — trang chủ lấy dự án có dấu này trước theo thứ tự, thiếu
     thì lấy tiếp các dự án khác cho đủ 3.
   - **Thứ tự** (`order`) — nhỏ hiện trước (trang `/du-an/` và trang chủ).
2. Field KHÔNG có ô nhập: `cover` (ảnh CMS theo slug, chưa tải thì giữ ảnh cũ), `cover_alt`
   (= tên; bản migrate giữ alt gốc tới khi đổi ảnh), `updated_at`.
3. 9 dự án có sẵn ĐÃ chuyển vào CMS ngày 06/10/2026 (giữ ảnh `assets/images/prj-N.webp`). Trang
   viết tay `/du-an-kcn-bac-thang-long/` thành `/du-an/kcn-bac-thang-long/` (301 qua
   `html/_redirects`). Các con số "500+ dự án / 20.000+ camera" và dòng "trong hơn 500 dự án" vẫn
   viết tay (`project-count` chỉ thay số dự án hiện có).
4. Xoá: gỡ khỏi `data/projects.json` + xoá ảnh CMS của dự án (`<slug>-cover.jpg`,
   `<slug>-content-*.jpg`); ảnh có sẵn của site không bao giờ bị xoá. Có popup xác nhận.
5. Trợ lý AI tự biết danh sách dự án (tên, loại, địa điểm, năm, số camera, mô tả, giải pháp).

## VI. Nội dung AI (trợ lý chat trên website)

1. Hai loại nội dung, cùng 1 tab "Nội dung AI":
   - **Kiến thức chung** (`data/ai-settings.json` → `extra_notes`): văn bản tự do — chính sách
     bảo hành, khu vực phục vụ, quy trình khảo sát... mọi thứ chưa có trên site. Kèm
     `out_of_scope_message` (câu trả lời khi bị hỏi ngoài phạm vi).
   - **Cặp hỏi đáp** (`data/chat-qa.json`): câu hỏi + câu trả lời + trạng thái
     (`published` / `draft` = tạm tắt). Ưu tiên CAO NHẤT khi trợ lý trả lời.
2. Trợ lý còn TỰ biết (không cần nạp): danh mục sản phẩm (`data/catalog.json`), danh sách
   tin tức, danh sách dự án (`data/projects.json`), thông tin liên hệ hard-code (hotline 0978 406 868, daotienhic@gmail.com,
   Số 15 ngõ 26 đường Hoàng Quốc Việt, Nghĩa Đô, Cầu Giấy, Hà Nội, T2–T7 8:00–17:30).
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
7. **Nhật ký hội thoại** (thêm 06/10/2026, cơ chế lấy từ khtcard): mỗi lượt khách chat trên
   website ghi 2 dòng (`user` + `model`) vào sheet `ChatLogs` (cột `conversation_id`,
   `submitted_at`, `role`, `message`, `page`; tự tạo ở lượt đầu, có `LockService` chống ghi đè).
   - Ghi trong `handleChat_` SAU khi có câu trả lời (site không có Worker như khtcard) — thêm vài
     trăm ms mỗi lượt; lỗi ghi chỉ vào log máy chủ, KHÔNG làm hỏng câu trả lời cho khách.
   - AI lỗi vẫn ghi câu hỏi kèm ghi chú lỗi (khách nhận câu trả lời mẫu ở site). Lượt bị chặn vì
     quá nhiều tin và ô "Thử trợ lý" trong CMS KHÔNG ghi.
   - Tab **"Hội thoại AI"** (editor trở lên, chỉ đọc): gom theo cuộc, cuộc có tin mới nhất lên
     đầu, có ô tìm trong nội dung; trả tối đa 300 cuộc gần nhất. Không tải lúc boot, chỉ tải khi
     mở tab. Muốn xoá nhật ký cũ: xoá dòng trực tiếp trong sheet `ChatLogs`.

## VI-b. Form tư vấn trên website (`form[data-lead]`, 22 trang)

Thêm 06/10/2026 — trước đó form CHỈ GIẢ LẬP gửi (đợi 0,7 giây rồi báo thành công), mọi yêu cầu
của khách đều bị mất.
1. `main.js` gửi `fetch` tới cùng URL `/exec` của khung chat, `{action:"lead", fields, source}`,
   `Content-Type: text/plain;charset=utf-8` (né CORS preflight). Chỉ hiện "Đã ghi nhận" khi máy
   chủ trả `ok`; lỗi thì hiện `message` (câu tiếng Việt máy chủ soạn) hoặc câu chung kèm hotline,
   GIỮ nguyên nội dung khách đã điền. Mã yêu cầu `CMB-yyMMdd-XXXX` do MÁY CHỦ sinh (trùng mã
   trong email).
2. Chống spam: honeypot `_hp` (main.js tự chèn, ẩn bằng style INLINE — không phụ thuộc rule CSS,
   tránh gotcha #27; có giá trị = âm thầm bỏ qua nhưng vẫn trả `ok`), trần 20 lượt/phút toàn
   endpoint, mỗi số điện thoại 1 lượt/60 giây. Kiểm tra server: họ tên, SĐT 9–15 số, ô đồng ý.
3. Lưu TRƯỚC vào sheet `Leads` (tự tạo; cột `code, submitted_at, status` + các ô form + `page,
   landing, referrer, utm, email_sent`), có `LockService`. Dữ liệu khách CHỈ nằm trong Sheet,
   không bao giờ ghi vào repo công khai.
4. Gửi SAU email HTML (mẫu `gas/email-lead.html`: logo + tên Cameramienbac, mã yêu cầu, nút Gọi /
   Zalo, bảng thông tin, nguồn truy cập, chân thư thông tin công ty) tới Script Property
   `NOTIFY_EMAIL` (nhiều địa chỉ cách nhau dấu phẩy). Chưa khai/gửi lỗi → vẫn lưu Sheet, cột
   `email_sent` = "CHƯA gửi", khách vẫn nhận thành công. Hàm `debugLeadEmail` (chạy tay) gửi 1
   email mẫu để xem giao diện.
5. ⚠️ Lệch khỏi playbook theo yêu cầu khách: playbook khuyên báo qua Telegram để giữ quota Gmail
   (~100 mail/ngày, DÙNG CHUNG với OTP đăng nhập). Khách chọn email. Nếu có ngày lượng yêu cầu
   lớn làm OTP không gửi được → chuyển kênh báo sang Telegram.

## VII. Người dùng

Xem mục I.4. Tab "Người dùng" chỉ hiện với admin/root; server chặn lại bằng `requireRole_`.

## VIII. UX chung

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

## IX. Kiến trúc lưu trữ

- Google Sheet "Cameramienbac CMS Data" (tự tạo lần đầu): sheet `Users` (cột `email`, `role`) +
  sheet `ChatLogs` (nhật ký chat — mục VI.7, tự tạo ở lượt chat đầu tiên).
- GitHub (Contents API) — đường dẫn cố định, đổi phải sửa cả `scripts/build.py` + CI:
  | Đường dẫn | Vai trò | Trigger CI |
  |---|---|---|
  | `data/catalog.json` | toàn bộ sản phẩm | ✔ |
  | `data/news.json` | index tin tức (ghi SAU CÙNG) | ✔ |
  | `data/news/<slug>.json` | chi tiết 1 bài | — |
  | `data/news-categories.json` | danh mục tin | ✔ |
  | `data/legacy-news.json` | bài viết tay cũ (CMS không ghi) | ✔ |
  | `data/projects.json` | toàn bộ dự án (kể cả nội dung) | ✔ |
  | `data/chat-qa.json`, `data/ai-settings.json` | Nội dung AI (GAS đọc lúc chat) | — |
  | `html/assets/images/products/<id>.jpg` | ảnh sản phẩm CMS | — |
  | `html/assets/images/news/*` | ảnh tin tức | — |
  | `html/assets/images/projects/*` | ảnh dự án CMS | — |
- `data/products.json` (84 bản ghi crawl thô) KHÔNG thuộc CMS, CMS không đọc/ghi.
- `scripts/build.py` ghi đè vùng giữa các mốc `<!-- cms:... -->`:
  `html/partials/catalog.html` (lưới sản phẩm), `html/hang-{hikvision,dahua,axis,hanwha}/index.html`
  (lưới "Sản phẩm tiêu biểu"), `html/tin-tuc/index.html` (nút lọc + danh sách), `html/index.html` (3 tin mới nhất + 3 dự án),
  `html/du-an/index.html` (ô lọc Tỉnh/Năm, dòng đếm, lưới dự án); và sinh
  `html/tin-tuc/<slug>/index.html` từ `templates/news-detail.html`, `html/du-an/<slug>/index.html`
  từ `templates/project-detail.html` (có dấu `<!-- build.py:generated -->`, trang mồ côi tự bị xoá). Xoá mốc = build báo lỗi, không im lặng.
- `scripts/build.py` cũng sinh lại toàn bộ `html/sitemap.xml` (quét mọi `*/index.html`, bỏ
  `admin/ partials/ docs/ vendor/ assets/` và trang có meta `noindex`; `lastmod` chỉ cho tin tức)
  và `html/robots.txt` (Allow all + Sitemap; CỐ Ý không `Disallow: /admin/`). Domain ở hằng
  `SITE_URL` đầu file build.py (`https://cameramienbac.com.vn`).
- `scripts/build.py` gắn vào `<head>` MỌI trang công khai 1 khối `<!-- seo:start -->…<!-- seo:end -->`
  (tự sinh, không sửa tay): canonical, robots, Open Graph, Twitter Card, theme-color và JSON-LD
  `@graph` (LocalBusiness + WebSite + WebPage/CollectionPage/ContactPage/AboutPage/FAQPage +
  BreadcrumbList lấy từ breadcrumb hiển thị; trang tin thêm BlogPosting). Thông tin doanh nghiệp
  ở hằng `ORG` đầu build.py. Muốn đổi title/description 1 trang: sửa `<title>`/meta description
  của trang đó, khối SEO tự theo.
- Độ trễ Lưu → lên site: ~1–2 phút (CI build + hosting deploy). Nội dung AI: tức thì.

## X. Bug đã gặp ở dự án này

- 06/10/2026 — Admin báo `Cannot access 'MANAGEABLE_ROLES' before initialization` khi mở lại
  trang lúc đã đăng nhập. Nguyên nhân: `js.html` gọi `bootApp()` giữa file; boot từ cache render
  ĐỒNG BỘ nên chạy tới `renderUsersTable` trước khi `const MANAGEABLE_ROLES` (khai báo phía dưới)
  được khởi tạo. Sửa: lời gọi khởi động nằm ở CUỐI `js.html` — giữ nguyên như vậy.

## XI. Script Properties (tên CỐ ĐỊNH)

- `GITHUB_TOKEN`, `GITHUB_OWNER` (`tranquanghuy-rightsvn`), `GITHUB_REPO` (`cameramienbac`),
  `GITHUB_BRANCH` (`master`) — bắt buộc.
- `SITE_URL` — domain thật của site, không có `/` cuối (`https://cameramienbac.com.vn`). Dùng để
  tải TinyMCE tự host. Chưa có domain thì để trống: CMS tạm tải TinyMCE từ CDN.
- `GEMINI_API_KEY` — key Gemini cho trợ lý chat. Trống = chat dùng câu trả lời mẫu.
- `GEMINI_MODEL` — tuỳ chọn, mặc định `gemini-3.5-flash-lite`.
- `NOTIFY_EMAIL` — email nhận báo "Yêu cầu tư vấn mới" từ form trên website (mục VI-b), nhiều
  địa chỉ cách nhau dấu phẩy. Không có giá trị mặc định trong code; trống = không gửi mail
  (yêu cầu vẫn lưu sheet `Leads`).
- `SPREADSHEET_ID` — KHÔNG cần điền, code tự tạo lần đầu.

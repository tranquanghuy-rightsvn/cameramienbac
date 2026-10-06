/* Cameramienbac — shared behaviour
   - loads the header/footer partials into their placeholders
   - wires up the mobile navigation
   Run the site through a local web server (e.g. `python3 -m http.server`)
   so that fetch() can read the partials. */

(function () {
  "use strict";

  // URL /exec của trang quản trị (Google Apps Script) — nơi trợ lý chat AI trả lời, dùng nội
  // dung nạp ở tab "Nội dung AI". Để trống thì khung chat dùng câu trả lời mẫu bên dưới.
  // Deploy lại bằng "New version" thì URL không đổi, không phải sửa ở đây.
  var CHAT_ENDPOINT = "https://script.google.com/macros/s/AKfycbwPx44O9dZEjJwYZY5FNk3pqjTIC9jfFkJADA2VzCzKtXCQ_g2kG3aV_Px6IPBq23pI/exec";

  function initNav(root) {
    var toggle = root.querySelector(".nav-toggle");
    var nav = root.querySelector(".main-nav");
    var header = root.querySelector(".site-header");
    var mobileMq = window.matchMedia("(max-width: 1023px)");
    var groups = Array.prototype.slice.call(root.querySelectorAll(".nav-group"));

    function setGroup(group, open) {
      var link = group.querySelector(".nav-link");
      group.classList.toggle("is-open", open);
      if (link) link.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function closeGroups(except) {
      groups.forEach(function (g) { if (g !== except) setGroup(g, false); });
    }

    function closeMenu() {
      closeGroups();
      if (!nav || !nav.classList.contains("is-open")) return;
      nav.classList.remove("is-open");
      document.body.classList.remove("nav-locked");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }

    function openMenu() {
      if (!nav) return;
      nav.classList.add("is-open");
      nav.scrollTop = 0;
      document.body.classList.add("nav-locked");
      if (toggle) toggle.setAttribute("aria-expanded", "true");
    }

    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        if (nav.classList.contains("is-open")) closeMenu();
        else openMenu();
      });
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" || event.key === "Esc") {
        var wasOpen = nav && nav.classList.contains("is-open");
        closeMenu();
        if (wasOpen && toggle) toggle.focus();
      }
    });

    document.addEventListener("click", function (event) {
      if (!nav || !nav.classList.contains("is-open")) return;
      if (header && header.contains(event.target)) return;
      closeMenu();
    });

    // Leaving the mobile layout (rotate / resize) must not leave the page
    // scroll-locked behind a hidden menu.
    var onBreakpoint = function (e) { if (!e.matches) closeMenu(); };
    if (mobileMq.addEventListener) mobileMq.addEventListener("change", onBreakpoint);
    else if (mobileMq.addListener) mobileMq.addListener(onBreakpoint);

    // Mobile: a parent item is a disclosure toggle (tap again to close); its
    // overview page is reachable through the first link inside the submenu.
    // Desktop keeps the hover dropdown and the parent link navigates.
    groups.forEach(function (group) {
      var link = group.querySelector(".nav-link");
      if (!link) return;
      link.addEventListener("click", function (event) {
        if (!mobileMq.matches) return;
        event.preventDefault();
        var open = !group.classList.contains("is-open");
        closeGroups(group);
        setGroup(group, open);
      });
    });
  }

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
    var countEl = root.getElementById("prj-count");
    var defaultCount = countEl ? countEl.textContent : "";

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

      if (countEl) {
        var filtered = checked.length > 0 || city || year;
        if (filtered) {
          countEl.innerHTML = "Tìm thấy <b>" + visibleCount + " / " + cards.length +
            "</b> dự án phù hợp với bộ lọc. <button type=\"button\" class=\"prj-reset\" data-prj-reset>Xóa bộ lọc</button>";
        } else {
          countEl.textContent = defaultCount;
        }
      }
    }

    // Criteria only take effect when the user presses "Tìm kiếm"; until then
    // the button is flagged so it's clear there are unapplied changes.
    function markDirty() {
      if (submitBtn) submitBtn.classList.add("is-dirty");
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
        markDirty();
      });
    });

    if (citySelect) citySelect.addEventListener("change", markDirty);
    if (yearSelect) yearSelect.addEventListener("change", markDirty);

    function reset() {
      catBoxes.forEach(function (b) { b.checked = b === allBox; });
      if (citySelect) citySelect.selectedIndex = 0;
      if (yearSelect) yearSelect.selectedIndex = 0;
      apply();
      if (submitBtn) submitBtn.classList.remove("is-dirty");
    }

    if (submitBtn) {
      submitBtn.addEventListener("click", function (event) {
        event.preventDefault();
        apply();
        submitBtn.classList.remove("is-dirty");
        // On stacked (mobile) layouts the results sit below the filter panel.
        if (window.matchMedia("(max-width: 1023px)").matches) {
          (countEl || grid).scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }

    root.addEventListener("click", function (event) {
      if (event.target.closest("[data-prj-reset]")) {
        event.preventDefault();
        reset();
      }
    });
  }

  function initNewsFilter(root) {
    var bar = root.querySelector(".news-filter");
    if (!bar) return;
    var cards = Array.prototype.slice.call(root.querySelectorAll(".news-list .news"));
    bar.addEventListener("click", function (event) {
      var btn = event.target.closest("[data-news-filter]");
      if (!btn) return;
      var topic = btn.getAttribute("data-news-filter");
      bar.querySelectorAll("button").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      });
      cards.forEach(function (card) {
        var tag = card.querySelector(".news__tag");
        card.hidden = topic !== "all" && (!tag || tag.textContent.trim() !== topic);
        // the featured layout only makes sense when it's not the only card
        card.classList.toggle("news--flat", topic !== "all");
      });
    });
  }


  // ---- lead source (landing page, referrer, UTM) --------------------------
  // Ghi lại nguồn truy cập đầu tiên trong phiên để gắn vào mọi form lead (gửi kèm lên GAS).
  function leadSource() {
    var KEY = "cmb_src";
    var data = null;
    try { data = JSON.parse(sessionStorage.getItem(KEY) || "null"); } catch (e) {}
    if (!data) {
      var q = new URLSearchParams(location.search);
      data = {
        landing: location.pathname,
        referrer: document.referrer || "direct",
        utm_source: q.get("utm_source") || "",
        utm_medium: q.get("utm_medium") || "",
        utm_campaign: q.get("utm_campaign") || ""
      };
      try { sessionStorage.setItem(KEY, JSON.stringify(data)); } catch (e) {}
    }
    return data;
  }

  // Gửi form tư vấn lên GAS (doPost action "lead"): GAS lưu Sheet "Leads", gửi email báo tới
  // NOTIFY_EMAIL và trả mã yêu cầu. text/plain để né CORS preflight (GAS không xử lý OPTIONS).
  function submitLead(form, src) {
    var fields = {};
    Array.prototype.forEach.call(form.elements, function (el) {
      if (!el.name || el.name === "nguon") return;
      fields[el.name] = el.type === "checkbox" ? el.checked : el.value;
    });
    return fetch(CHAT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ action: "lead", fields: fields, source: Object.assign({ page: location.pathname }, src) })
    }).then(function (res) { return res.json(); });
  }

  // Ô bẫy bot (honeypot) — người thật không thấy, bot tự điền -> GAS âm thầm bỏ qua. Ẩn bằng
  // style INLINE ngay tại đây (không phụ thuộc rule CSS ở file khác có thể bị mất khi sửa CSS).
  function addHoneypot(form) {
    if (form.querySelector('[name="_hp"]')) return;
    var wrap = document.createElement("div");
    wrap.setAttribute("aria-hidden", "true");
    wrap.style.cssText = "position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden";
    wrap.innerHTML = '<label>Website<input type="text" name="_hp" tabindex="-1" autocomplete="off"></label>';
    form.appendChild(wrap);
  }

  function showLeadError(form, message) {
    var box = form.querySelector(".lead-form__error");
    if (!box) {
      box = document.createElement("p");
      box.className = "lead-form__error";
      box.setAttribute("role", "alert");
      var actions = form.querySelector(".lead-form__actions");
      form.insertBefore(box, actions || null);
    }
    box.textContent = message || "";
    box.hidden = !message;
  }

  function initLeadForms(root) {
    var src = leadSource();
    var q = new URLSearchParams(location.search);
    root.querySelectorAll("form[data-lead]").forEach(function (form) {
      var srcField = form.querySelector('[name="nguon"]');
      if (srcField) srcField.value = JSON.stringify(Object.assign({ page: location.pathname }, src));

      // prefill from query (?nhu-cau=..., ?sp=...)
      var need = q.get("nhu-cau");
      var sel = form.querySelector('select[name="nhucau"]');
      if (need && sel) {
        Array.prototype.forEach.call(sel.options, function (o) { if (o.value === need || o.text === need) sel.value = o.value; });
      }
      var sp = q.get("sp");
      var note = form.querySelector('textarea[name="noidung"]');
      if (sp && note && !note.value) note.value = "Yêu cầu cấu hình/báo giá: " + sp + "\n";
      if (sp && sel && !sel.value) {
        Array.prototype.forEach.call(sel.options, function (o) { if (/cấu hình/i.test(o.text)) sel.value = o.value || o.text; });
      }

      addHoneypot(form);
      var done = form.parentNode.querySelector(".lead-done");
      var button = form.querySelector('button[type="submit"]');
      form.addEventListener("submit", function (event) {
        event.preventDefault();
        if (!form.checkValidity()) { form.reportValidity(); return; }
        if (button && button.disabled) return;
        showLeadError(form, "");
        if (button) { button.disabled = true; button.classList.add("is-loading"); }
        var failMsg = "Chưa gửi được yêu cầu (lỗi kết nối). Vui lòng thử lại hoặc gọi hotline 0978 406 868.";
        var send = CHAT_ENDPOINT && window.fetch ? submitLead(form, src) : Promise.reject(new Error("no_fetch"));
        send.then(function (res) {
          if (button) { button.disabled = false; button.classList.remove("is-loading"); }
          // Chỉ hiện "message" (câu tiếng Việt máy chủ soạn sẵn), không bao giờ in mã lỗi kỹ thuật.
          if (!res || !res.ok) { showLeadError(form, (res && res.message) || failMsg); return; }
          var code = res.code;
          if (done) {
            var nameField = form.querySelector('[name="ten"]');
            done.querySelectorAll("[data-code]").forEach(function (el) { el.textContent = code; });
            done.querySelectorAll("[data-name]").forEach(function (el) { el.textContent = nameField && nameField.value ? nameField.value.trim() : "bạn"; });
            form.hidden = true;
            done.hidden = false;
            done.setAttribute("tabindex", "-1");
            done.focus({ preventScroll: true });
            var top = done.getBoundingClientRect().top + window.pageYOffset - 120;
            if (done.getBoundingClientRect().top < 80) window.scrollTo({ top: top, behavior: "smooth" });
          }
          form.reset();
          if (srcField) srcField.value = JSON.stringify(Object.assign({ page: location.pathname }, src));
        }).catch(function () {
          // Không bao giờ báo "đã gửi" khi chưa gửi được — giữ nguyên nội dung khách đã điền.
          if (button) { button.disabled = false; button.classList.remove("is-loading"); }
          showLeadError(form, failMsg);
        });
      });
      if (done) {
        var again = done.querySelector(".lead-done__again");
        if (again) again.addEventListener("click", function () { done.hidden = true; form.hidden = false; });
      }
    });
  }

  // "Đăng ký" on a course card preselects that course in the form below
  function initCoursePick(root) {
    root.querySelectorAll("[data-course]").forEach(function (a) {
      a.addEventListener("click", function () {
        var sel = root.querySelector('form[data-lead] select[name="nhucau"]');
        if (sel) sel.value = a.getAttribute("data-course");
      });
    });
  }

  // ---- in-page section nav (solution pages) --------------------------------
  function initSolnav(root) {
    var nav = root.querySelector(".solnav");
    if (!nav || !("IntersectionObserver" in window)) return;
    var links = Array.prototype.slice.call(nav.querySelectorAll('a[href^="#"]'));
    var map = {};
    links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var current = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var a = map[e.target.id];
        if (!a || a === current) return;
        if (current) current.classList.remove("is-current");
        a.classList.add("is-current");
        current = a;
        var list = a.parentNode;
        if (list.scrollWidth > list.clientWidth) {
          list.scrollTo({ left: a.offsetLeft - 16, behavior: "smooth" });
        }
      });
    }, { rootMargin: "-35% 0px -60% 0px" });
    Object.keys(map).forEach(function (id) {
      var sec = root.getElementById(id);
      if (sec) io.observe(sec);
    });
  }

  // ---- product catalog filter ---------------------------------------------
  function initCatalog(root) {
    var box = root.querySelector("[data-catalog]");
    if (!box) return;
    var items = Array.prototype.slice.call(box.querySelectorAll(".pitem"));
    var cats = box.querySelectorAll(".cats button");
    var app = box.querySelector('[data-f="app"]');
    var brand = box.querySelector('[data-f="brand"]');
    var count = box.querySelector(".catbar__count");
    var empty = box.querySelector(".cat-empty");
    var reset = box.querySelector(".catbar__reset");
    var cat = "";
    function apply() {
      var n = 0;
      items.forEach(function (it) {
        var ok = (!cat || it.dataset.cat === cat) &&
          (!app.value || (" " + it.dataset.app + " ").indexOf(" " + app.value + " ") > -1) &&
          (!brand.value || (" " + it.dataset.brand + " ").indexOf(" " + brand.value + " ") > -1);
        it.hidden = !ok;
        if (ok) n++;
      });
      if (count) count.textContent = "Hiển thị " + n + " / " + items.length + " dòng sản phẩm";
      if (empty) empty.hidden = n > 0;
    }
    cats.forEach(function (b) {
      b.addEventListener("click", function () {
        cats.forEach(function (x) { x.classList.toggle("is-active", x === b); x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        cat = b.dataset.cat || "";
        apply();
      });
    });
    [app, brand].forEach(function (s) { s.addEventListener("change", apply); });
    if (reset) reset.addEventListener("click", function () {
      app.value = ""; brand.value = ""; cat = "";
      cats.forEach(function (x, i) { x.classList.toggle("is-active", i === 0); x.setAttribute("aria-pressed", i === 0 ? "true" : "false"); });
      apply();
    });
    // deep link: san-pham/camera-ai/ (via <body data-nhom>) or legacy ?nhom=camera-ai#danh-muc
    var pre = root.body.getAttribute("data-nhom") || new URLSearchParams(location.search).get("nhom");
    if (pre) {
      cats.forEach(function (b) { if (b.dataset.cat === pre) b.click(); });
    } else {
      apply();
    }
  }

  // ---- downloads not yet supplied ------------------------------------------
  function initPendingFiles(root) {
    root.querySelectorAll("[data-file-pending]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var note = a.closest(".dl-wrap") && a.closest(".dl-wrap").querySelector(".dl-note");
        if (note) note.hidden = false;
      });
    });
  }

  function initChatWidget(root) {
    var chatbox = root.getElementById("chatbox");
    var toggle = root.getElementById("chatbtn-toggle");
    var closeBtn = root.getElementById("chatbox-close");
    var messages = root.getElementById("chatbox-messages");
    var form = root.getElementById("chatbox-form");
    var input = root.getElementById("chatbox-input");
    var heroForm = root.getElementById("hero-agent-form");
    var heroField = root.getElementById("hero-agent-field");
    if (!chatbox || !toggle || !messages || !form || !input) return;

    var REPLIES = [
      { match: "tòa nhà", text: "Với tòa nhà văn phòng/chung cư, chúng tôi thường triển khai camera AI nhận diện khuôn mặt kiểm soát ra vào, phát hiện đám đông và cảnh báo hành vi bất thường. Bạn cho mình xin quy mô toà nhà (số tầng/căn hộ) để tư vấn cấu hình phù hợp nhé?" },
      { match: "trường học", text: "Giải pháp trường học AI của chúng tôi hỗ trợ điểm danh tự động bằng khuôn mặt, chống gian lận thi cử và giám sát an ninh khuôn viên. Bạn đang quan tâm ở cấp học nào và quy mô bao nhiêu học sinh?" },
      { match: "nâng cấp", text: "Camera hiện hữu của anh/chị có thể nâng cấp lên AI mà không cần thay mới toàn bộ — chỉ cần đầu ghi hỗ trợ AI hoặc box AI gắn thêm. Bạn cho mình biết đang dùng loại camera/đầu ghi gì để kiểm tra khả năng nâng cấp nhé?" },
      { match: "aiot", text: "AIoT Platform của chúng tôi tích hợp camera, cảm biến IoT và dashboard vận hành tập trung cho Smart City/Smart Building. Bạn muốn triển khai ở quy mô nào (toà nhà đơn lẻ, khu đô thị hay thành phố)?" }
    ];
    var DEFAULT_REPLY = "Cảm ơn câu hỏi của bạn! Đội ngũ kỹ thuật Cameramienbac sẽ liên hệ tư vấn chi tiết sớm nhất. Trong lúc chờ, bạn có thể để lại số điện thoại hoặc xem thêm tại trang Liên hệ.";

    function pickReply(text) {
      var lower = text.toLowerCase();
      for (var i = 0; i < REPLIES.length; i++) {
        if (lower.indexOf(REPLIES[i].match) !== -1) return REPLIES[i].text;
      }
      return DEFAULT_REPLY;
    }

    function scrollToBottom() {
      messages.scrollTop = messages.scrollHeight;
    }

    function appendMessage(text, from) {
      var bubble = document.createElement("div");
      bubble.className = "chatbox__msg chatbox__msg--" + from;
      bubble.textContent = text;
      messages.appendChild(bubble);
      scrollToBottom();
    }

    // Lịch sử hội thoại gửi kèm mỗi lượt (máy chủ chỉ giữ ~10 tin gần nhất).
    var history = [];
    var pending = false;

    function conversationId() {
      var KEY = "cmb_chat_id";
      var id = "";
      try { id = sessionStorage.getItem(KEY) || ""; } catch (e) {}
      if (!id) {
        id = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
        try { sessionStorage.setItem(KEY, id); } catch (e) {}
      }
      return id;
    }

    // Hỏi trợ lý AI; mọi lỗi (chưa cấu hình, mạng, quá tải) đều rơi về câu trả lời mẫu —
    // không bao giờ để khách nhìn khung chat chết.
    function askAssistant(text) {
      if (!CHAT_ENDPOINT || !window.fetch) {
        return new Promise(function (resolve) {
          window.setTimeout(function () { resolve(pickReply(text)); }, 800);
        });
      }
      var ctrl = window.AbortController ? new AbortController() : null;
      var timer = ctrl ? window.setTimeout(function () { ctrl.abort(); }, 30000) : 0;
      return fetch(CHAT_ENDPOINT, {
        method: "POST",
        // text/plain: giữ request "đơn giản" để trình duyệt không gửi preflight (máy chủ không xử lý OPTIONS).
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify({ action: "chat", conversationId: conversationId(), page: location.pathname, messages: history }),
        signal: ctrl ? ctrl.signal : undefined
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data && data.ok && data.reply) return data.reply;
          throw new Error((data && data.error) || "no_reply");
        })
        .catch(function (err) {
          console.warn("[chat] dùng câu trả lời mẫu:", err && err.message);
          return pickReply(text);
        })
        .then(function (reply) {
          if (timer) window.clearTimeout(timer);
          return reply;
        });
    }

    function sendMessage(text) {
      text = (text || "").trim();
      if (!text || pending) return;
      pending = true;
      var chips = root.getElementById("chatbox-chips");
      if (chips) chips.remove();
      appendMessage(text, "user");
      history.push({ role: "user", text: text });

      var typing = document.createElement("div");
      typing.className = "chatbox__msg chatbox__msg--bot chatbox__msg--typing";
      typing.innerHTML = "<i></i><i></i><i></i>";
      messages.appendChild(typing);
      scrollToBottom();

      askAssistant(text).then(function (reply) {
        typing.remove();
        appendMessage(reply, "bot");
        history.push({ role: "model", text: reply });
        if (history.length > 20) history = history.slice(-20);
        pending = false;
      });
    }

    function openChat(prefillText) {
      chatbox.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      if (prefillText) {
        sendMessage(prefillText);
      } else if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
        // On touch devices focusing would pop the keyboard over the suggestions.
        input.focus();
      }
    }

    function closeChat() {
      chatbox.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", function (event) {
      event.preventDefault();
      if (chatbox.hidden) {
        openChat();
      } else {
        closeChat();
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        closeChat();
      });
    }

    document.addEventListener("keydown", function (event) {
      if ((event.key === "Escape" || event.key === "Esc") && !chatbox.hidden) {
        closeChat();
      }
    });

    document.addEventListener("click", function (event) {
      if (chatbox.hidden) return;
      if (event.target.closest("#chatbox, #chatbtn-toggle, [data-chat-open], [data-chat-ask], #hero-agent-form")) return;
      closeChat();
    });

    root.querySelectorAll("[data-chat-open]").forEach(function (el) {
      el.addEventListener("click", function (event) {
        event.preventDefault();
        openChat();
      });
    });

    root.querySelectorAll("[data-chat-ask]").forEach(function (el) {
      el.addEventListener("click", function (event) {
        event.preventDefault();
        openChat(el.getAttribute("data-chat-ask"));
      });
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var text = input.value;
      input.value = "";
      if (chatbox.hidden) chatbox.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      sendMessage(text);
    });

    if (heroForm && heroField) {
      heroForm.addEventListener("submit", function (event) {
        event.preventDefault();
        var text = heroField.value;
        heroField.value = "";
        openChat(text);
      });
    }
  }

  function markCurrent(root) {
    // URL dạng /slug/ (file slug/index.html); trang chủ là "/"
    function slugOf(path) {
      var clean = path.split("?")[0].split("#")[0].replace(/(index)?\.html$/, "").replace(/\/+$/, "");
      return clean.split("/").pop() || "index";
    }
    var here = document.body.getAttribute("data-nav") || slugOf(location.pathname);
    root.querySelectorAll(".main-nav a").forEach(function (link) {
      var target = link.getAttribute("href");
      if (!target || target.charAt(0) === "#") return;
      // deep links (?nhom=, #anchor) point into a page — never mark them current
      if (!link.classList.contains("nav-link") && /[?#]/.test(target)) return;
      var norm = slugOf(target);
      var match = norm === here;
      if (link.classList.contains("nav-link")) {
        link.classList.toggle("is-active", match);
      } else if (match) {
        link.classList.add("is-current");
        var group = link.closest(".nav-group");
        var parent = group && group.querySelector(".nav-link");
        if (parent) parent.classList.add("is-active");
      }
    });
  }

  function include(el) {
    var url = el.getAttribute("data-include");
    return fetch(url)
      .then(function (res) {
        if (!res.ok) throw new Error(url + " → " + res.status);
        return res.text();
      })
      .then(function (html) {
        el.outerHTML = html;
      })
      .catch(function (err) {
        console.error("[partials] " + err.message +
          " — serve the site over http:// so the partials can be fetched.");
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var slots = Array.prototype.slice.call(document.querySelectorAll("[data-include]"));
    Promise.all(slots.map(include)).then(function () {
      initNav(document);
      markCurrent(document);
      initProjectFilter(document);
      initNewsFilter(document);
      initLeadForms(document);
      initCoursePick(document);
      initSolnav(document);
      initCatalog(document);
      initPendingFiles(document);
      initChatWidget(document);
      // header/footer are injected after first paint, so re-apply the #anchor offset
      if (location.hash.length > 1) {
        var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
        if (target) target.scrollIntoView();
      }
      var yearEl = document.getElementById("footer-year");
      if (yearEl) yearEl.textContent = String(new Date().getFullYear());
    });
  });
})();

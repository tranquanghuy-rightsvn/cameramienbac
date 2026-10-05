/* Smart content cho cameramienbac.com.vn: hiệu ứng quy trình, slider ảnh, dải ảnh + phóng to, video. */
// Hiệu ứng "hiện dần khi cuộn tới lần đầu" cho các khối Smart content (hiện có: thanh tóm tắt
// quy trình .tv-process-map). Chỉ chạy 1 lần. Không có JS / trình duyệt cũ / người dùng tắt hiệu
// ứng -> khối vẫn hiện bình thường (trạng thái ẩn chỉ áp khi <html> có class tv-js).
(() => {
  const els = document.querySelectorAll('.tv-process-map');
  if (!els.length || !('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('tv-js');
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.35 });
  els.forEach((el) => io.observe(el));
})();

// Slider ảnh trong thân bài: figure[data-slider]. Trượt bằng scroll-snap (vuốt tự nhiên trên
// điện thoại); nút ‹ ›, tab tên hạng mục và phím ← → chỉ gọi scrollTo. Không tự chạy để khách
// đọc kịp chữ trên ảnh.
document.querySelectorAll('[data-slider]').forEach((slider) => {
  const frame = slider.querySelector('.tv-slider-frame');
  const track = slider.querySelector('.tv-slider-track');
  const slides = [...track.children];
  const tabs = [...slider.querySelectorAll('.tv-slider-tab')];
  const count = slider.querySelector('.tv-slider-count');
  let current = -1;

  const go = (i) => {
    const n = (i + slides.length) % slides.length;
    track.scrollTo({ left: n * track.clientWidth });
  };
  const sync = () => {
    const i = Math.round(track.scrollLeft / track.clientWidth);
    if (i === current) return;
    current = i;
    slides.forEach((s, k) => {
      s.classList.toggle('is-active', k === i);
      s.setAttribute('aria-hidden', k === i ? 'false' : 'true');
    });
    tabs.forEach((t, k) => {
      t.classList.toggle('is-active', k === i);
      t.setAttribute('aria-selected', k === i ? 'true' : 'false');
    });
    if (count) count.textContent = `${i + 1} / ${slides.length}`;
    // Chỉ cuộn ngang hàng tab (scrollIntoView sẽ kéo cả trang xuống slider)
    const tab = tabs[i], bar = tab && tab.parentElement;
    if (bar) bar.scrollTo({ left: tab.offsetLeft - bar.offsetLeft - (bar.clientWidth - tab.offsetWidth) / 2, behavior: 'smooth' });
  };

  let raf;
  track.addEventListener('scroll', () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(sync); }, { passive: true });
  addEventListener('resize', () => { track.scrollTo({ left: current * track.clientWidth, behavior: 'instant' }); });
  slider.querySelector('.tv-slider-btn--prev').addEventListener('click', () => go(current - 1));
  slider.querySelector('.tv-slider-btn--next').addEventListener('click', () => go(current + 1));
  tabs.forEach((t, k) => t.addEventListener('click', () => go(k)));
  frame.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(current - 1); }
    if (e.key === 'ArrowRight') { e.preventDefault(); go(current + 1); }
  });
  sync();
});

// Khối ảnh + video của Smart content:
//  - .tv-gallery[data-gallery]: dải ảnh trượt ngang, nút ‹ ›, bấm ảnh để phóng to (xem ảnh lớn ở data-full)
//  - .tv-video[data-video]: ảnh chờ phủ đầy khung + nút Play; video để preload="none" nên KHÔNG tải
//    gì cho tới khi người xem bấm Play, và không tự chạy.
// Không có JS: dải ảnh vẫn vuốt ngang được, video vẫn có sẵn trong trang.
(() => {
  // ---------- Slider ảnh ----------
  document.querySelectorAll('.tv-gallery[data-gallery]').forEach((g) => {
    const track = g.querySelector('.tv-gallery-track');
    const prev = g.querySelector('.tv-gallery-btn--prev');
    const next = g.querySelector('.tv-gallery-btn--next');
    if (!track) return;
    const step = () => {
      const item = track.querySelector('.tv-gallery-item');
      return item ? item.getBoundingClientRect().width + 12 : track.clientWidth;
    };
    const update = () => {
      const max = track.scrollWidth - track.clientWidth - 2;
      if (prev) prev.disabled = track.scrollLeft <= 2;
      if (next) next.disabled = track.scrollLeft >= max;
    };
    if (prev) prev.addEventListener('click', () => track.scrollBy({ left: -step(), behavior: 'smooth' }));
    if (next) next.addEventListener('click', () => track.scrollBy({ left: step(), behavior: 'smooth' }));
    track.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  });

  // ---------- Phóng to ảnh ----------
  let box = null, list = [], idx = 0, startX = null;
  const icon = (d) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';
  function show() {
    const it = list[idx];
    const img = box.querySelector('img');
    img.src = it.full;
    img.alt = it.alt;
    box.querySelector('.tv-lightbox-cap').textContent = (idx + 1) + ' / ' + list.length + (it.cap ? '  ·  ' + it.cap : '');
  }
  function close() {
    if (!box) return;
    box.remove();
    box = null;
    document.removeEventListener('keydown', onKey);
    document.documentElement.style.overflow = '';
  }
  function move(d) { idx = (idx + d + list.length) % list.length; show(); }
  function onKey(e) {
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') move(-1);
    else if (e.key === 'ArrowRight') move(1);
  }
  function open(items, i) {
    list = items; idx = i;
    box = document.createElement('div');
    box.className = 'tv-lightbox';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<img alt=""><p class="tv-lightbox-cap"></p>' +
      '<button type="button" class="tv-lightbox-close" aria-label="Đóng">' + icon('<path d="M18 6 6 18M6 6l12 12"/>') + '</button>' +
      (items.length > 1
        ? '<button type="button" class="tv-lightbox-prev" aria-label="Ảnh trước">' + icon('<path d="m15 18-6-6 6-6"/>') + '</button>' +
          '<button type="button" class="tv-lightbox-next" aria-label="Ảnh tiếp theo">' + icon('<path d="m9 18 6-6-6-6"/>') + '</button>'
        : '');
    box.addEventListener('click', (e) => {
      if (e.target === box) close();
      else if (e.target.closest('.tv-lightbox-close')) close();
      else if (e.target.closest('.tv-lightbox-prev')) move(-1);
      else if (e.target.closest('.tv-lightbox-next')) move(1);
    });
    box.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
    box.addEventListener('touchend', (e) => {
      if (startX === null) return;
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) move(dx < 0 ? 1 : -1);
      startX = null;
    });
    document.body.appendChild(box);
    document.documentElement.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey);
    show();
    requestAnimationFrame(() => box && box.classList.add('is-open'));
    const btn = box.querySelector('.tv-lightbox-close');
    if (btn) btn.focus();
  }
  // Nhóm ảnh bấm phóng to: dải ảnh tv-gallery và thẻ công trình tv-proof (chú thích = tên công trình)
  document.querySelectorAll('.tv-gallery[data-gallery], .tv-proof[data-gallery]').forEach((g) => {
    const medias = Array.prototype.slice.call(g.querySelectorAll('.tv-gallery-media, .tv-proof-media'));
    const items = medias.map((m) => {
      const img = m.querySelector('img');
      const card = m.closest('.tv-proof-card');
      const cap = card ? card.querySelector('h3') : m.parentNode.querySelector('.tv-gallery-cap');
      return { full: m.getAttribute('data-full') || (img && img.currentSrc) || (img && img.src), alt: img ? img.alt : '', cap: cap ? cap.textContent.trim() : '' };
    });
    medias.forEach((m, i) => {
      m.setAttribute('role', 'button');
      m.setAttribute('tabindex', '0');
      m.setAttribute('aria-label', 'Phóng to ảnh ' + (i + 1));
      m.addEventListener('click', () => open(items, i));
      m.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(items, i); } });
    });
  });

  // ---------- Video: bấm mới tải + phát ----------
  document.querySelectorAll('.tv-video[data-video]').forEach((w) => {
    const video = w.querySelector('video');
    const cover = w.querySelector('.tv-video-cover');
    if (!video || !cover) return;
    cover.addEventListener('click', () => {
      document.querySelectorAll('.tv-video video').forEach((v) => { if (v !== video) v.pause(); });
      video.controls = true;
      w.classList.add('is-playing');
      const p = video.play();
      if (p && p.catch) p.catch(() => { /* trình duyệt chặn phát: vẫn còn nút phát của video */ });
    });
  });
})();


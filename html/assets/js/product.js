/* Trang chi tiết sản phẩm: bấm ảnh nhỏ -> đổi ảnh lớn. Không có JS vẫn xem đủ ảnh đầu tiên. */
(function () {
  var g = document.querySelector('[data-pd-gallery]');
  if (!g) return;
  var main = g.querySelector('[data-pd-main]');
  g.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-src]');
    if (!b) return;
    main.src = b.getAttribute('data-src');
    main.alt = b.querySelector('img').alt;
    g.querySelectorAll('button[data-src]').forEach(function (x) { x.setAttribute('aria-current', x === b ? 'true' : 'false'); });
  });
})();

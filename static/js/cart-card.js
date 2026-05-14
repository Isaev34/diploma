/**
 * Корзина на главной: добавление через AJAX, счётчик − N +, обновление счётчика в навбаре.
 * Использует fetch() к существующим endpoints корзины.
 */
(function () {
    function getCsrfToken() {
        var name = 'csrftoken';
        var match = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[1]) : null;
    }

    function updateNavbarCount(count) {
        var el = document.getElementById('cart-count');
        if (el && count !== undefined) el.textContent = String(count);
    }

    function getUpdateCartItemUrl(itemId) {
        if (typeof window.CART_UPDATE_URL === 'string') {
            return window.CART_UPDATE_URL.replace(/\/$/, '') + '/' + itemId + '/';
        }
        return '/cart/update/' + itemId + '/';
    }

    function showCounter(wrap, cartItemId, quantity) {
        var counter = wrap && wrap.querySelector('.product-card-counter');
        var numEl = counter && counter.querySelector('.product-card-counter-num');
        if (!counter || !numEl) return;
        counter.dataset.cartItemId = String(cartItemId);
        numEl.textContent = String(quantity);
        counter.classList.remove('product-card-counter--hidden');
        wrap.classList.add('product-card-cart-wrap--counter-visible');
    }

    function showForm(wrap) {
        var counter = wrap && wrap.querySelector('.product-card-counter');
        if (counter) {
            counter.dataset.cartItemId = '';
            counter.classList.add('product-card-counter--hidden');
            var numEl = counter.querySelector('.product-card-counter-num');
            if (numEl) numEl.textContent = '0';
        }
        if (wrap) wrap.classList.remove('product-card-cart-wrap--counter-visible');
    }

    document.addEventListener('DOMContentLoaded', function () {
        var updateUrl = document.querySelector('[data-cart-update-url]');
        if (updateUrl) {
            window.CART_UPDATE_URL = (updateUrl.getAttribute('data-cart-update-url') || '').replace(/\/\d+\/$/, '/');
        }

        document.addEventListener('submit', function (e) {
            var form = e.target;
            if (!form || !form.classList.contains('js-product-card-add-form')) return;
            e.preventDefault();

            var wrap = form.closest('.product-card-cart-wrap');
            var body = new FormData(form);
            var headers = { 'X-Requested-With': 'XMLHttpRequest' };
            var token = getCsrfToken();
            if (token) headers['X-CSRFToken'] = token;

            fetch(form.action, { method: 'POST', body: body, headers: headers })
                .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
                .then(function (result) {
                    if (!result.ok && result.data && !result.data.success) {
                        if (result.data.message) alert(result.data.message);
                        return;
                    }
                    var data = result.data;
                    if (!data.success) return;
                    updateNavbarCount(data.cart_count);
                    if (wrap && data.cart_item_id != null && data.item_quantity != null) {
                        showCounter(wrap, data.cart_item_id, data.item_quantity);
                    }
                })
                .catch(function () { });
        });

        document.addEventListener('click', function (e) {
            var btn = e.target.closest('.product-card-counter-btn--minus, .product-card-counter-btn--plus');
            if (!btn) return;
            e.preventDefault();
            var counter = btn.closest('.product-card-counter');
            var wrap = counter && counter.closest('.product-card-cart-wrap');
            var cartItemId = counter && counter.dataset.cartItemId;
            var numEl = counter && counter.querySelector('.product-card-counter-num');
            if (!counter || !cartItemId || !numEl) return;

            var current = parseInt(numEl.textContent, 10) || 0;
            var delta = btn.classList.contains('product-card-counter-btn--minus') ? -1 : 1;
            var newQty = Math.max(0, current + delta);

            var formData = new FormData();
            formData.append('quantity', String(newQty));
            formData.append('csrfmiddlewaretoken', getCsrfToken() || '');

            var url = getUpdateCartItemUrl(cartItemId);
            var headers = { 'X-Requested-With': 'XMLHttpRequest' };
            var token = getCsrfToken();
            if (token) headers['X-CSRFToken'] = token;

            btn.disabled = true;
            fetch(url, { method: 'POST', body: formData, headers: headers })
                .then(function (res) { return res.json().then(function (data) { return { ok: res.ok, data: data }; }); })
                .then(function (result) {
                    if (!result.ok) return;
                    var data = result.data;
                    if (!data.success) return;
                    updateNavbarCount(data.cart_count);
                    if (data.item_quantity === 0) {
                        showForm(wrap);
                    } else {
                        numEl.textContent = String(data.item_quantity);
                    }
                })
                .catch(function () { })
                .then(function () { btn.disabled = false; });
        });
    });
})();

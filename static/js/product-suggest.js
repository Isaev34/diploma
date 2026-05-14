(function() {
    var SUGGEST_URL = '/api/product-suggest/';
    var DEBOUNCE_MS = 280;
    var MIN_LENGTH = 1;

    function init() {
        var inputs = document.querySelectorAll('input[data-product-suggest]');
        inputs.forEach(function(input) {
            setupSuggest(input);
        });
    }

    function setupSuggest(input) {
        var container = input.closest('.product-suggest-wrap') || input.parentElement;
        if (!container) return;
        if (!container.classList.contains('product-suggest-wrap')) {
            var wrap = document.createElement('div');
            wrap.className = 'product-suggest-wrap';
            wrap.style.position = 'relative';
            input.parentNode.insertBefore(wrap, input);
            wrap.appendChild(input);
            container = wrap;
        }
        var dropdown = document.createElement('div');
        dropdown.className = 'product-suggest-dropdown';
        dropdown.setAttribute('hidden', '');
        container.appendChild(dropdown);

        var debounceTimer = null;
        var lastQuery = '';

        function hideDropdown() {
            dropdown.setAttribute('hidden', '');
            dropdown.innerHTML = '';
        }

        function showDropdown(items) {
            dropdown.innerHTML = '';
            if (!items || items.length === 0) {
                hideDropdown();
                return;
            }
            items.forEach(function(item) {
                var a = document.createElement('a');
                a.href = item.url;
                a.className = 'product-suggest-item';
                a.textContent = item.name;
                a.addEventListener('click', function(e) {
                    e.preventDefault();
                    window.location.href = item.url;
                });
                dropdown.appendChild(a);
            });
            dropdown.removeAttribute('hidden');
        }

        function fetchSuggestions(query) {
            if (query.length < MIN_LENGTH) {
                hideDropdown();
                return;
            }
            var categorySlug = (input.getAttribute('data-suggest-category') || '').trim();
            var qs = 'q=' + encodeURIComponent(query);
            if (categorySlug) {
                qs += '&category=' + encodeURIComponent(categorySlug);
            }
            var xhr = new XMLHttpRequest();
            xhr.open('GET', SUGGEST_URL + '?' + qs, true);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onreadystatechange = function() {
                if (xhr.readyState !== 4) return;
                if (xhr.status === 200) {
                    try {
                        var data = JSON.parse(xhr.responseText);
                        showDropdown(data.suggestions || []);
                    } catch (e) {
                        hideDropdown();
                    }
                } else {
                    hideDropdown();
                }
            };
            xhr.send();
        }

        input.addEventListener('input', function() {
            var query = (input.value || '').trim();
            clearTimeout(debounceTimer);
            if (query.length < MIN_LENGTH) {
                hideDropdown();
                return;
            }
            debounceTimer = setTimeout(function() {
                lastQuery = query;
                fetchSuggestions(query);
            }, DEBOUNCE_MS);
        });

        input.addEventListener('blur', function() {
            setTimeout(hideDropdown, 180);
        });

        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideDropdown();
                input.blur();
            }
        });

        dropdown.addEventListener('mousedown', function(e) {
            e.preventDefault();
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

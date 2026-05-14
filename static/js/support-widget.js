(function () {
    var cfg = window.SUPPORT_CONFIG;
    if (!cfg) return;

    var root = document.getElementById('support-widget-root');
    var btn = document.getElementById('support-widget-toggle');
    var panel = document.getElementById('support-widget-panel');
    var closeBtn = document.getElementById('support-widget-close');
    var guest = document.getElementById('support-widget-guest');
    var chat = document.getElementById('support-widget-chat');
    var messagesEl = document.getElementById('support-widget-messages');
    var orderSel = document.getElementById('support-widget-order');
    var input = document.getElementById('support-widget-input');
    var sendBtn = document.getElementById('support-widget-send');

    if (!root || !btn || !panel) return;

    var isAuth = root.getAttribute('data-auth') === '1';
    var pollTimer = null;

    function getCsrf() {
        var el = document.getElementById('support-csrf-token');
        if (el && el.value) return el.value;
        var name = 'csrftoken';
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var c = cookies[i].trim();
            if (c.indexOf(name + '=') === 0) return decodeURIComponent(c.slice(name.length + 1));
        }
        return '';
    }

    function apiHeaders() {
        return {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrf(),
            'X-Next-Path': window.location.pathname + window.location.search
        };
    }

    function formatTime(iso) {
        try {
            var d = new Date(iso);
            return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return '';
        }
    }

    function sortByTime(a, b) {
        return new Date(a.created_at) - new Date(b.created_at);
    }

    /** Группировка: вопрос клиента + ответы поддержки с reply_to = этому сообщению (как «переписка в рамке»). */
    function buildTurns(sorted) {
        var turns = [];
        sorted.forEach(function (m) {
            if (!m.is_staff_reply) {
                turns.push({ client: m, replies: [] });
                return;
            }
            if (m.reply_to_id) {
                var placed = false;
                for (var j = turns.length - 1; j >= 0; j--) {
                    if (turns[j].client && turns[j].client.id === m.reply_to_id) {
                        turns[j].replies.push(m);
                        placed = true;
                        break;
                    }
                }
                if (!placed) {
                    turns.push({ client: null, orphanStaff: m });
                }
            } else {
                if (turns.length && turns[turns.length - 1].client) {
                    turns[turns.length - 1].replies.push(m);
                } else {
                    turns.push({ client: null, orphanStaff: m });
                }
            }
        });
        return turns;
    }

    function appendBubble(container, m) {
        var wrap = document.createElement('div');
        wrap.className =
            'support-widget__msg ' + (m.is_staff_reply ? 'support-widget__msg--staff' : 'support-widget__msg--user');

        var bubble = document.createElement('div');
        bubble.className = 'support-widget__msg-bubble';
        bubble.textContent = m.body;
        wrap.appendChild(bubble);

        var meta = document.createElement('div');
        meta.className = 'support-widget__msg-meta';
        meta.textContent = (m.is_staff_reply ? 'Поддержка · ' : 'Вы · ') + formatTime(m.created_at);
        wrap.appendChild(meta);

        container.appendChild(wrap);
    }

    function renderMessages(list) {
        messagesEl.innerHTML = '';
        if (!list || !list.length) {
            var empty = document.createElement('div');
            empty.className = 'support-widget__loading';
            empty.textContent = '';
            messagesEl.appendChild(empty);
            return;
        }

        var sorted = list.slice().sort(sortByTime);
        var turns = buildTurns(sorted);

        turns.forEach(function (turn) {
            var shell = document.createElement('section');
            shell.className = 'support-widget__turn';

            if (turn.client) {
                if (turn.client.order_label) {
                    var ctxLine = document.createElement('div');
                    ctxLine.className = 'support-widget__ctx-line';
                    ctxLine.textContent = turn.client.order_label;
                    shell.appendChild(ctxLine);
                }
                appendBubble(shell, turn.client);
                turn.replies.forEach(function (r) {
                    appendBubble(shell, r);
                });
            } else if (turn.orphanStaff) {
                appendBubble(shell, turn.orphanStaff);
            }

            messagesEl.appendChild(shell);
        });

        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function loadOrders() {
        return fetch(cfg.ordersUrl, { headers: apiHeaders(), credentials: 'same-origin' })
            .then(function (r) {
                if (r.status === 401) return null;
                return r.json();
            })
            .then(function (data) {
                if (!data || !data.orders) return;
                orderSel.innerHTML = '';
                var def = document.createElement('option');
                def.value = '';
                def.textContent = 'Общий вопрос';
                orderSel.appendChild(def);
                data.orders.forEach(function (o) {
                    var opt = document.createElement('option');
                    opt.value = String(o.id);
                    opt.textContent = o.label;
                    orderSel.appendChild(opt);
                });
            });
    }

    function loadMessages() {
        messagesEl.innerHTML = '<div class="support-widget__loading">Загрузка…</div>';
        return fetch(cfg.messagesUrl, { headers: apiHeaders(), credentials: 'same-origin' })
            .then(function (r) {
                if (r.status === 401) return Promise.reject({ unauthorized: true });
                return r.json();
            })
            .then(function (data) {
                if (data && data.messages) renderMessages(data.messages);
            })
            .catch(function (err) {
                if (err && err.unauthorized) throw err;
                messagesEl.innerHTML = '<div class="support-widget__error">Не удалось загрузить сообщения.</div>';
            });
    }

    function openPanel() {
        panel.hidden = false;
        btn.setAttribute('aria-expanded', 'true');
        if (!isAuth) {
            guest.hidden = false;
            chat.hidden = true;
            return;
        }
        guest.hidden = true;
        chat.hidden = false;
        loadOrders()
            .then(function () {
                return loadMessages();
            })
            .catch(function () {
                guest.hidden = false;
                chat.hidden = true;
                isAuth = false;
            });
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(function () {
            if (!panel.hidden && isAuth && !chat.hidden) {
                fetch(cfg.messagesUrl, { headers: apiHeaders(), credentials: 'same-origin' })
                    .then(function (r) {
                        return r.ok ? r.json() : null;
                    })
                    .then(function (data) {
                        if (data && data.messages) renderMessages(data.messages);
                    });
            }
        }, 15000);
    }

    function closePanel() {
        panel.hidden = true;
        btn.setAttribute('aria-expanded', 'false');
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function sendMessage() {
        var body = (input.value || '').trim();
        if (!body) return;
        sendBtn.disabled = true;
        var oid = orderSel.value || '';
        fetch(cfg.sendUrl, {
            method: 'POST',
            headers: Object.assign({}, apiHeaders(), { 'Content-Type': 'application/json' }),
            credentials: 'same-origin',
            body: JSON.stringify({ body: body, order_id: oid || null })
        })
            .then(function (r) {
                if (r.status === 401) {
                    window.location.href =
                        cfg.loginUrl + '?next=' + encodeURIComponent(window.location.pathname + window.location.search);
                    return null;
                }
                return r.json();
            })
            .then(function (data) {
                if (!data) return;
                if (!data.ok) {
                    alert(data.error || 'Ошибка отправки');
                    return;
                }
                input.value = '';
                return loadMessages();
            })
            .finally(function () {
                sendBtn.disabled = false;
            });
    }

    btn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (panel.hidden) openPanel();
        else closePanel();
    });
    closeBtn.addEventListener('click', closePanel);
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !panel.hidden) closePanel();
    });

    document.addEventListener('click', function (e) {
        if (panel.hidden) return;
        if (root.contains(e.target)) return;
        closePanel();
    });
})();

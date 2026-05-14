/**
 * Система горячих клавиш для интернет-магазина ВкусВилл
 * Поддерживает не менее 8 горячих клавиш для частых операций
 */

(function() {
    'use strict';

    // Состояние системы горячих клавиш
    const Hotkeys = {
        enabled: true,
        helpVisible: false,
        init: function() {
            this.bindEvents();
            this.createHelpOverlay();
            this.showWelcomeMessage();
        },

        // Привязка событий
        bindEvents: function() {
            document.addEventListener('keydown', this.handleKeyDown.bind(this));
            
            // Показ справки по Ctrl+?
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey && e.key === '?') {
                    e.preventDefault();
                    Hotkeys.toggleHelp();
                }
            });
        },

        // Обработка нажатий клавиш
        handleKeyDown: function(e) {
            // Игнорируем, если пользователь вводит текст в input/textarea
            if (this.isInputFocused(e.target)) {
                // Но разрешаем некоторые клавиши даже в input
                if (e.key === 'Escape') {
                    e.target.blur();
                }
                return;
            }

            // Комбинации с Ctrl
            if (e.ctrlKey || e.metaKey) {
                this.handleCtrlCombinations(e);
                return;
            }

            // Одиночные клавиши
            this.handleSingleKeys(e);
        },

        // Проверка, находится ли фокус в поле ввода
        isInputFocused: function(target) {
            const tagName = target.tagName.toLowerCase();
            const isEditable = target.isContentEditable;
            return (tagName === 'input' || tagName === 'textarea' || isEditable) 
                && target.type !== 'checkbox' 
                && target.type !== 'radio';
        },

        // Обработка комбинаций с Ctrl
        handleCtrlCombinations: function(e) {
            switch(e.key.toLowerCase()) {
                case 'k':
                    // Поиск (Ctrl+K)
                    e.preventDefault();
                    this.focusSearch();
                    break;
                case 'enter':
                    // Оформить заказ (Ctrl+Enter на странице checkout)
                    if (window.location.pathname.includes('/cart/checkout/')) {
                        e.preventDefault();
                        this.submitOrder();
                    }
                    break;
                case '/':
                    // Показать справку (Ctrl+/)
                    e.preventDefault();
                    this.toggleHelp();
                    break;
            }
        },

        // Обработка одиночных клавиш
        handleSingleKeys: function(e) {
            // Игнорируем, если нажата модификаторная клавиша
            if (e.ctrlKey || e.altKey || e.metaKey || e.shiftKey) {
                return;
            }

            switch(e.key.toLowerCase()) {
                case 'h':
                case 'home':
                    // Главная страница (H или Home)
                    e.preventDefault();
                    this.goToHome();
                    break;
                case 'c':
                    // Корзина (C)
                    e.preventDefault();
                    this.goToCart();
                    break;
                case 'l':
                    // Вход/Выход (L)
                    e.preventDefault();
                    this.toggleLogin();
                    break;
                case 'p':
                    // Профиль (P)
                    e.preventDefault();
                    this.goToProfile();
                    break;
                case 'o':
                    // Заказы (O)
                    e.preventDefault();
                    this.goToOrders();
                    break;
                case 'a':
                    // Аналитика (A) - только для менеджеров
                    e.preventDefault();
                    this.goToAnalytics();
                    break;
                case 'escape':
                case 'esc':
                    // Закрыть модальные окна, убрать фокус (Esc)
                    e.preventDefault();
                    this.handleEscape();
                    break;
                case 'enter':
                case ' ':
                    // Добавить в корзину (Enter или Space на странице товара)
                    if (window.location.pathname.includes('/products/')) {
                        e.preventDefault();
                        this.addToCart();
                    }
                    break;
                case '/':
                    // Поиск (/)
                    e.preventDefault();
                    this.focusSearch();
                    break;
            }
        },

        // Действия
        goToHome: function() {
            window.location.href = '/';
        },

        goToCart: function() {
            window.location.href = '/cart/';
        },

        toggleLogin: function() {
            const userAuthenticated = document.body.getAttribute('data-user-authenticated') === 'true';
            if (userAuthenticated) {
                // Выход
                if (confirm('Вы уверены, что хотите выйти?')) {
                    window.location.href = '/users/logout/';
                }
            } else {
                // Вход
                window.location.href = '/users/login/';
            }
        },

        goToProfile: function() {
            const userAuthenticated = document.body.getAttribute('data-user-authenticated') === 'true';
            if (userAuthenticated) {
                window.location.href = '/users/profile/';
            } else {
                this.showNotification('Сначала войдите в систему', 'warning');
            }
        },

        goToOrders: function() {
            const userAuthenticated = document.body.getAttribute('data-user-authenticated') === 'true';
            if (userAuthenticated) {
                window.location.href = '/cart/orders/';
            } else {
                this.showNotification('Сначала войдите в систему', 'warning');
            }
        },

        goToAnalytics: function() {
            const isManager = document.body.getAttribute('data-user-is-manager') === 'true';
            if (isManager) {
                window.location.href = '/analytics/dashboard/';
            } else {
                this.showNotification('Доступ только для менеджеров и администраторов', 'warning');
            }
        },

        focusSearch: function() {
            // Ищем поле поиска на странице
            const searchInput = document.querySelector('input[type="search"], input[name="search"], #search, .search-input');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            } else {
                // Если поля поиска нет, переходим на страницу товаров
                window.location.href = '/products/';
            }
        },

        addToCart: function() {
            // Ищем кнопку "Добавить в корзину"
            const addButton = document.querySelector('button[type="submit"], .add-to-cart, form[action*="add"] button');
            if (addButton) {
                addButton.click();
            } else {
                this.showNotification('Товар недоступен для добавления в корзину', 'info');
            }
        },

        submitOrder: function() {
            // Ищем форму оформления заказа
            const orderForm = document.querySelector('form[action*="checkout"]');
            if (orderForm) {
                const submitButton = orderForm.querySelector('button[type="submit"]');
                if (submitButton && !submitButton.disabled) {
                    submitButton.click();
                } else {
                    this.showNotification('Заполните все обязательные поля', 'warning');
                }
            }
        },

        handleEscape: function() {
            // Закрываем модальные окна Bootstrap
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });

            // Убираем фокус с полей ввода
            if (document.activeElement && document.activeElement.blur) {
                document.activeElement.blur();
            }

            // Закрываем dropdown меню
            const dropdowns = document.querySelectorAll('.dropdown-menu.show');
            dropdowns.forEach(dropdown => {
                const bsDropdown = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
                if (bsDropdown) {
                    bsDropdown.hide();
                }
            });
        },

        // Создание overlay со справкой
        createHelpOverlay: function() {
            const overlay = document.createElement('div');
            overlay.id = 'hotkeys-help-overlay';
            overlay.className = 'hotkeys-help-overlay';
            overlay.innerHTML = `
                <div class="hotkeys-help-content">
                    <div class="hotkeys-help-header">
                        <h3><i class="fas fa-keyboard me-2"></i>Горячие клавиши</h3>
                        <button class="btn-close" onclick="Hotkeys.toggleHelp()"></button>
                    </div>
                    <div class="hotkeys-help-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h5>Навигация</h5>
                                <div class="hotkey-item">
                                    <kbd>H</kbd> или <kbd>Home</kbd>
                                    <span>Главная страница</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>C</kbd>
                                    <span>Корзина</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>P</kbd>
                                    <span>Профиль</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>O</kbd>
                                    <span>Мои заказы</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>A</kbd>
                                    <span>Аналитика (Manager/Admin)</span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h5>Действия</h5>
                                <div class="hotkey-item">
                                    <kbd>Ctrl</kbd> + <kbd>K</kbd> или <kbd>/</kbd>
                                    <span>Поиск</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>L</kbd>
                                    <span>Вход/Выход</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>Enter</kbd> или <kbd>Space</kbd>
                                    <span>Добавить в корзину (на странице товара)</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
                                    <span>Оформить заказ (на странице оформления)</span>
                                </div>
                                <div class="hotkey-item">
                                    <kbd>Esc</kbd>
                                    <span>Закрыть модальные окна</span>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3 text-center">
                            <small class="text-muted">Нажмите <kbd>Ctrl</kbd> + <kbd>?</kbd> или <kbd>Esc</kbd> для закрытия</small>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        },

        // Показать/скрыть справку
        toggleHelp: function() {
            const overlay = document.getElementById('hotkeys-help-overlay');
            if (overlay) {
                this.helpVisible = !this.helpVisible;
                if (this.helpVisible) {
                    overlay.classList.add('show');
                    document.body.style.overflow = 'hidden';
                } else {
                    overlay.classList.remove('show');
                    document.body.style.overflow = '';
                }
            }
        },

        // Показать приветственное сообщение
        showWelcomeMessage: function() {
            // Показываем только один раз (используем localStorage)
            if (!localStorage.getItem('hotkeys-welcome-shown')) {
                setTimeout(() => {
                    this.showNotification('💡 Подсказка: Нажмите Ctrl+? для просмотра горячих клавиш', 'info', 5000);
                    localStorage.setItem('hotkeys-welcome-shown', 'true');
                }, 2000);
            }
        },

        // Показать уведомление
        showNotification: function(message, type = 'info', duration = 3000) {
            // Создаем элемент уведомления
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show hotkey-notification`;
            notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Автоматически скрываем через duration
            if (duration > 0) {
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.classList.remove('show');
                        setTimeout(() => notification.remove(), 150);
                    }
                }, duration);
            }
        }
    };

    // Инициализация при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            Hotkeys.init();
        });
    } else {
        Hotkeys.init();
    }

    // Экспорт в глобальную область для доступа из HTML
    window.Hotkeys = Hotkeys;
})();










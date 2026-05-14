# Логика приложения «Сборщик заказов»

Подробное описание всех экранов и действий, которые может выполнить сборщик.

---

## 1. Вход (LoginFragment)

### Экраны и элементы
- Поля: логин, пароль.
- Кнопка «Войти».
- Индикатор загрузки.

### Функции

| Функция | Действие сборщика | Что делает приложение |
|--------|--------------------|-------------------------|
| **doLogin()** | Нажимает «Войти» | Проверяет, что логин и пароль не пустые. Показывает загрузку. Отправляет `POST auth/token/` с `LoginRequest(username, password)`. При успехе сохраняет `access` токен в TokenStorage и переходит на список заказов (`action_login_to_ordersList`). При ошибке или пустом ответе показывает Toast «Ошибка входа». При сетевой ошибке — «Ошибка сети». |

---

## 2. Список заказов (OrdersListFragment)

### Экраны и элементы
- Туллибар: кнопка «Назад», меню (Выйти).
- Список карточек заказов (номер, ID, метки «Ваш активный заказ» / «Готов к отправке»).
- Пустое состояние «Нет заказов к сборке».
- Индикатор загрузки.

### Функции

| Функция | Действие сборщика | Что делает приложение |
|--------|--------------------|-------------------------|
| **Авто-возврат (onViewCreated)** | Открывает список заказов впервые | Читает из SharedPreferences «PickerPrefs» ключ `active_order_id`. Если значение не -1 и это первый показ (`isFirstLoad == true`), сразу выполняет навигацию в PickingProcessFragment с этим `orderId` и не вызывает loadOrders(). Иначе ставит `isFirstLoad = false` и вызывает loadOrders(). |
| **Выход (toolbar menu)** | Нажимает «Выйти» в меню | Очищает токен в TokenStorage, выполняет навигацию на экран логина с очисткой стека до ordersListFragment. |
| **Назад (toolbar)** | Нажимает стрелку «Назад» | Вызывает системный onBackPressed (возврат назад). |
| **loadOrders()** | Фрагмент показывается / возобновляется | Показывает загрузку. Отправляет три запроса: `getOrders("PENDING")`, `getOrders("ASSEMBLING")`, `getOrders("ASSEMBLED")`. Объединяет результаты в один список: assembled + assembling + pending, без дубликатов по id. Передаёт список в адаптер. Скрывает загрузку. При ошибке любого запроса показывает Toast «Ошибка сети». При пустом списке показывает «Нет заказов к сборке». |
| **Клик по заказу (OrdersAdapter callback)** | Нажимает на карточку заказа | **Если статус ASSEMBLING или ASSEMBLED:** сразу навигация в PickingProcessFragment с `orderId`. **Если статус PENDING:** в корутине вызывается `ApiClient.startAssembling(order.id)`; при успешном ответе — навигация в PickingProcessFragment с этим `orderId`; при ошибке — Toast «Ошибка сети». **Иначе (любой другой статус):** навигация в PickingProcessFragment с `orderId`. |

### Отображение карточек (OrdersAdapter)
- Номер заказа, ID.
- При статусе ASSEMBLING: надпись «Ваш активный заказ», цветная обводка карточки.
- При статусе ASSEMBLED или (ASSEMBLING и все позиции собраны): зелёная надпись «Готов к отправке».

---

## 3. Сборка заказа (PickingProcessFragment)

Фрагмент получает `orderId` через аргумент навигации.

### Состояния экрана (showState)
- **START** — оверлей «Начать сборку» поверх списка, кнопка «Начать сборку», без FAB сканера.
- **PICKING** — виден заголовок, список товаров, прогресс, FAB сканера, кнопка «Завершить сборку».
- **RESULT** — скрыты работа и FAB, показан экран результата: текст, QR-код, кнопка «К списку заказов».

### Функции

| Функция | Действие сборщика | Что делает приложение |
|--------|--------------------|-------------------------|
| **loadOrder()** | Открытие экрана / обновление после скана | Запрашивает `GET picker/orders/{id}/` с текущим orderId. При успехе: сохраняет заказ в `currentOrder`, передаёт `order.items` в адаптер, при статусе ASSEMBLING выставляет `assemblyStarted = true` и showState("PICKING"). Обновляет заголовок (updateHeader) и UI (updateUiForOrder). При 404 и уже сохранённом verification_code ничего не делает (не показывает ошибку). При другой ошибке вызывает showErrorFromResponse. |
| **updateHeader(order)** | — (вызывается после загрузки/обновления заказа) | Подставляет номер заказа, текст статуса (В ожидании / В сборке / Собран), прогресс-бар и текст «N из M позиций» по данным заказа. |
| **updateUiForOrder(order)** | — (после загрузки заказа) | Если заказ завершён (assemblyFinished) — ничего. Если статус PENDING и сборка ещё не начата: showState("START"), показ кнопки «Начать сборку», кнопка «Завершить сборку» выключена. Если статус ASSEMBLING или assemblyStarted: showState("PICKING"), кнопка «Завершить сборку» включена только если все товары отсканированы и есть savedVerificationCode. |
| **Назад (toolbar)** | Нажимает стрелку «Назад» | showExitOrderConfirm(): диалог «Вы уверены, что хотите выйти из заказа?» с кнопками «Да, выйти» и «Отмена». При «Да, выйти» — только navigateUp(), **active_order_id не очищается** (сборщик может вернуться в заказ через список). |
| **startAssembly()** | Нажимает «Начать сборку» | Показывает загрузку, отключает кнопку. Отправляет `POST picker/orders/{id}/start_assembly/`. При успехе: сохраняет orderId в SharedPreferences (saveActiveOrderId), выставляет assemblyStarted, showState("PICKING"), запрашивает заказ getOrder(orderId) и обновляет список и заголовок, затем loadOrder(). При ошибке: скрывает загрузку, включает кнопку, showErrorFromResponse (при 403/409 — сообщение «Заказ уже собирается другим сотрудником» и navigateUp с очисткой active_order_id). |
| **openScanner()** | Нажимает FAB (камера) | Проверяет assemblyStarted и не assemblyFinished. Показывает ScanBarcodeDialogFragment; в колбек передаётся onBarcodeScanned. |
| **onBarcodeScanned(barcode)** | В диалоге сканера отсканирован штрихкод | Проверяет, что сборка начата и не завершена. Игнорирует повторный тот же штрихкод. Ищет в currentOrder.items позицию с expectedBarcode == barcode. Если не найдена — Toast «Штрихкод не совпадает», return. Иначе: triggerScanFeedback() (вибрация + звук), adapter.setLastScannedItemId(item.id), отмена предыдущего verifyJob. Запускает корутину: POST picker/verify-barcode/ с orderId и barcode. При успехе и body.success: Toast «Товар отмечен»; при наличии verificationCode сохраняет код и сообщение, включает кнопку «Завершить сборку»; если verificationCode нет — loadOrder(), иначе updateLastItemScanned(barcode). При неуспехе — сброс lastScannedBarcode, показ body.message в Toast. Через 2 секунды lastScannedBarcode сбрасывается. |
| **triggerScanFeedback()** | — (после успешного распознавания своего штрихкода) | Короткая вибрация (50 ms) и короткий системный звук (ToneGenerator TONE_PROP_BEEP). |
| **updateLastItemScanned(barcode)** | — (после verify, когда пришёл verificationCode) | В currentOrder помечает позицию с данным barcode как isScanned, обновляет currentOrder и adapter, обновляет заголовок (без запроса к API). |
| **finishOrderAndShowResult()** | Нажимает «Завершить сборку» | Проверяет наличие savedVerificationCode. Отправляет `POST picker/orders/{id}/finish_assembly/`. **Только при успешном ответе:** clearActiveOrderId(), затем showResult(code, message). При ошибке — showErrorFromResponse, active_order_id не очищается. |
| **showResult(verificationCode, paymentMessage)** | — (после успешного finishOrder) | assemblyFinished = true, showState("RESULT"), подставляет paymentMessage или «Заказ собран», генерирует и показывает QR из verificationCode (generateAndShowQr). |
| **К списку заказов (btnBackToOrders)** | На экране результата нажимает «К списку заказов» | clearActiveOrderId(), навигация на ordersListFragment с очисткой стека (popUpTo ordersListFragment inclusive). |
| **showErrorFromResponse(code, errorBody)** | — (при ошибках API) | При 403/409: сообщение «Заказ уже собирается другим сотрудником», clearActiveOrderId(), navigateUp(). Иначе: сообщение из errorBody или «Ошибка при сборке заказа», Toast. |

### Сохранение активного заказа (SharedPreferences «PickerPrefs», ключ active_order_id)
- **Сохраняется:** при успешном ответе start_assembly в PickingProcessFragment (saveActiveOrderId(orderId)).
- **Очищается:** при успешном ответе finish_assembly (finishOrderAndShowResult); при нажатии «К списку заказов» на экране результата; при ответах 403/409 (чужой заказ).

---

## 4. Диалог сканера (ScanBarcodeDialogFragment)

### Элементы
- Полноэкранная камера, тёмный оверлей, квадратный видоискатель, анимированная «лазерная» линия.
- Подпись «Наведите камеру на штрихкод».
- Кнопка «Отмена».

### Функции

| Функция | Действие сборщика | Что делает приложение |
|--------|--------------------|-------------------------|
| **Открытие** | FAB на экране сборки | Запрашивает разрешение CAMERA при необходимости. Запускает камеру (Preview + ImageAnalysis с BarcodeAnalyzer), запускает анимацию линии в видоискателе. |
| **BarcodeAnalyzer** | Камера видит штрихкод | ML Kit распознаёт штрихкод, вызывается колбек onBarcodeScanned(rawValue). На UI-потоке вызываются переданный колбек с barcode и dismiss() — диалог закрывается без задержки. |
| **Отмена** | Нажимает «Отмена» | dismiss(). |

---

## 5. API (кратко)

| Метод | Назначение |
|-------|------------|
| POST auth/token/ | Вход, получение JWT. |
| GET picker/orders/?status= | Список заказов (PENDING / ASSEMBLING / ASSEMBLED). |
| GET picker/orders/{id}/ | Детали заказа по id. |
| POST picker/orders/{id}/start_assembly/ | Начать сборку заказа. |
| POST picker/verify-barcode/ | Подтвердить отсканированный штрихкод (order_id, barcode). |
| POST picker/orders/{id}/finish_assembly/ | Завершить сборку заказа (очистка active_order_id только при успехе). |

Все запросы (кроме логина) идут с заголовком Authorization: Bearer &lt;token&gt; (AuthInterceptor).

---

## 6. Последовательность типичных сценариев

1. **Вход** → логин/пароль → doLogin() → токен сохранён → переход в список заказов.
2. **Список** → loadOrders() (PENDING + ASSEMBLING + ASSEMBLED) → сборщик видит все свои и доступные заказы.
3. **Первый вход после прерванной сборки** → в списке при isFirstLoad и active_order_id != -1 сразу переход в экран сборки этого заказа.
4. **Клик по PENDING** → startAssembling(order.id) → при успехе переход в сборку (заказ уже ASSEMBLING).
5. **Клик по ASSEMBLING/ASSEMBLED** → сразу переход в сборку без вызова startAssembling.
6. **Экран сборки (PENDING, не начата)** → showState("START"), кнопка «Начать сборку» → startAssembly() → после успеха showState("PICKING"), сохранение active_order_id.
7. **Экран сборки (уже ASSEMBLING)** → loadOrder() → showState("PICKING"), список товаров, FAB, «Завершить сборку».
8. **Сканирование** → FAB → диалог сканера → штрихкод распознан → колбек → verifyBarcode → при успехе обновление списка/заголовка, при последнем товаре — сохранение verificationCode и включение «Завершить сборку».
9. **Завершение** → «Завершить сборку» → finishOrder(orderId) → при успехе clearActiveOrderId(), showResult (QR и сообщение).
10. **Выход из заказа без завершения** → «Назад» → подтверждение → navigateUp(), active_order_id не очищается.
11. **С экрана результата** → «К списку заказов» → clearActiveOrderId(), переход в список заказов.

Это полная логика приложения с точки зрения действий сборщика и вызываемых функций.

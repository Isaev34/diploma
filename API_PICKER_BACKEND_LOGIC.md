# Логика API сборщика (Backend) — для Android

Документ описывает работу backend с точки зрения Android‑приложения: endpoints, форматы запросов/ответов и сценарии использования.

---

## 1. Базовые настройки

| Параметр | Значение |
|----------|----------|
| Base URL | `https://your-server.com/api/` (замените на ваш домен) |
| Аутентификация | JWT (Bearer token) |
| Заголовок | `Authorization: Bearer <access_token>` |
| Content-Type | `application/json` |

**Важно:** Все endpoints, кроме `POST auth/token/`, требуют авторизации. Без токена — ответ `401 Unauthorized`.

---

## 2. Статусы заказа

| Код | Описание | Когда |
|-----|----------|-------|
| `PENDING` | В ожидании | Заказ создан, свободен для взятия в сборку |
| `ASSEMBLING` | В сборке | Сборщик взял заказ, идёт сканирование |
| `ASSEMBLED` | Собран | Все товары отсканированы и нажата «Завершить сборку» |

---

## 3. Endpoints

### 3.1. Вход (получение токена)

```
POST /api/auth/token/
```

**Request (JSON):**
```json
{
  "username": "picker_login",
  "password": "password123"
}
```

**Response 200:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Ошибки:** `400` — неверные логин/пароль.

---

### 3.2. Список заказов

```
GET /api/picker/orders/
GET /api/picker/orders/?status=PENDING
GET /api/picker/orders/?status=ASSEMBLING
GET /api/picker/orders/?status=ASSEMBLED
```

**Параметр `status` (опционально):** `PENDING`, `ASSEMBLING`, `ASSEMBLED`.

**Логика на backend:** Сборщик видит:
- все заказы со статусом `PENDING`;
- заказы в `ASSEMBLING` и `ASSEMBLED`, если он назначен как `picker`.

**Response 200 (массив заказов):**
```json
[
  {
    "id": 59,
    "status": "PENDING",
    "status_display": "В ожидании",
    "verification_code": null,
    "delivery_comment_picker": "Хрупкое",
    "items": [...],
    "total_items": 3,
    "scanned_items": 0,
    "is_fully_scanned": false,
    "created_at": "2025-02-02T10:00:00Z"
  }
]
```

---

### 3.3. Детали заказа (экран сборки)

```
GET /api/picker/orders/{id}/
```

**Response 200:**
```json
{
  "id": 59,
  "status": "ASSEMBLING",
  "status_display": "В сборке",
  "verification_code": null,
  "delivery_comment_picker": "Хрупкое",
  "items": [
    {
      "id": 101,
      "product": 5,
      "product_name": "Молоко 3.2%",
      "product_image": "http://server/media/products/milk.webp",
      "quantity": 2,
      "expected_barcode": "4601234567890",
      "is_scanned": false
    },
    {
      "id": 102,
      "product": 8,
      "product_name": "Хлеб белый",
      "product_image": "http://server/media/products/bread.webp",
      "quantity": 1,
      "expected_barcode": "4601234567891",
      "is_scanned": true
    }
  ],
  "total_items": 2,
  "scanned_items": 1,
  "is_fully_scanned": false,
  "created_at": "2025-02-02T10:00:00Z"
}
```

**Поле `items`:** список позиций заказа с ожидаемым штрихкодом и статусом `is_scanned`.

---

### 3.4. Начать сборку

```
POST /api/picker/orders/{id}/start_assembly/
```

**Request:** тело пустое `{}` или без тела.

**Логика на backend:**
- Заказ должен быть в статусе `PENDING`;
- Назначает `picker = текущий пользователь` и `status = ASSEMBLING`;
- Если заказ уже принадлежит текущему сборщику — возвращает успех (идемпотентно).

**Response 200:** полный объект заказа (как в GET `/api/picker/orders/{id}/`).

**Ошибки:**
- `400` — `{"error": "Заказ уже собирается или завершен"}` — заказ не `PENDING`;
- `403` — нет доступа;
- `404` — заказ не найден.

---

### 3.5. Верификация штрихкода (сканирование)

```
POST /api/picker/verify-barcode/
```

**Request (JSON):**
```json
{
  "order_id": 59,
  "barcode": "4601234567890"
}
```

**Логика на backend:**
1. Проверяет, что заказ в статусе `PENDING` или `ASSEMBLING`;
2. Проверяет, что штрихкод соответствует товару из этого заказа;
3. Устанавливает `is_scanned = true` для соответствующей позиции;
4. Если заказ был `PENDING` — автоматически переводит в `ASSEMBLING` и назначает `picker`;
5. **Статус `ASSEMBLED` и `verification_code` не меняются** — они задаются только в `finish_assembly`.

**Response 200:**
```json
{
  "success": true,
  "message": "Товар \"Молоко 3.2%\" успешно отсканирован",
  "product_name": "Молоко 3.2%",
  "is_order_complete": false,
  "verification_code": null,
  "scanned_count": 1,
  "total_count": 3
}
```

**Когда `is_order_complete: true`:** все позиции отсканированы. По этому флагу нужно включать кнопку «Завершить сборку».

**Важно:** `verification_code` всегда `null`. Код выдаётся только в `finish_assembly`.

**Ошибки `400`:**
- `{"order_id": "Заказ не найден"}`;
- `{"order_id": "Заказ не может быть собран. Текущий статус: ..."}` — неверный статус;
- `{"barcode": "Штрихкод не соответствует товарам в этом заказе"}`;
- `{"barcode": "Товар '...' уже отсканирован"}`.

---

### 3.6. Завершить сборку

```
POST /api/picker/orders/{id}/finish_assembly/
```

**Request:** тело пустое `{}` или без тела.

**Логика на backend:**
- Заказ должен быть в статусе `ASSEMBLING`;
- Устанавливает `status = ASSEMBLED`;
- Генерирует уникальный `verification_code` (8 символов, для QR);
- Определяет текст `payment_message` по способу оплаты.

**Response 200:**
```json
{
  "status": "ASSEMBLED",
  "verification_code": "A1B2C3D4",
  "payment_message": "ОПЛАЧЕНО",
  "order_id": 59
}
```

**`payment_message`:**
- `"ОПЛАЧЕНО"` — оплата картой онлайн;
- `"ОПЛАТА КУРЬЕРУ (Наличные/Карта)"` — оплата при получении.

**Ошибки:**
- `400` — `{"error": "Заказ еще не в сборке"}` — статус не `ASSEMBLING` (например, ещё не все товары отсканированы или заказ уже собран);
- `403`, `404` — как обычно.

---

### 3.7. Список товаров заказа (альтернативный endpoint)

```
GET /api/picker/order/{order_id}/items/
```

Аналогичен `GET /api/picker/orders/{id}/` — возвращает тот же формат заказа с `items`. Использовать один из этих endpoints.

---

## 4. Типовой сценарий (flow)

### Шаг 1. Вход

```
POST /api/auth/token/
→ сохранить access токен
```

### Шаг 2. Список заказов

```
GET /api/picker/orders/?status=PENDING
GET /api/picker/orders/?status=ASSEMBLING
GET /api/picker/orders/?status=ASSEMBLED
→ объединить результаты, показать в списке
```

### Шаг 3. Открыть заказ

**Если `status == PENDING`:**

```
POST /api/picker/orders/{id}/start_assembly/
→ при успехе — перейти на экран сборки
```

**Если `status == ASSEMBLING` или `status == ASSEMBLED`:**

- Перейти на экран сборки без вызова `start_assembly`.

### Шаг 4. Экран сборки — загрузка данных

```
GET /api/picker/orders/{id}/
→ отобразить items, total_items, scanned_items, is_fully_scanned
```

### Шаг 5. Сканирование штрихкода

```
POST /api/picker/verify-barcode/
Body: { "order_id": 59, "barcode": "4601234567890" }
```

**В ответе:**
- `is_order_complete: true` → включить кнопку «Завершить сборку»;
- `is_order_complete: false` → обновить прогресс (scanned_count / total_count).

### Шаг 6. Завершить сборку

Когда `is_order_complete == true` и пользователь нажал «Завершить сборку»:

```
POST /api/picker/orders/{id}/finish_assembly/
```

**В ответе:**
- `verification_code` → показать QR‑код;
- `payment_message` → отобразить текст.

---

## 5. Сводная таблица

| Действие | Метод | Endpoint | Когда вызывать |
|----------|-------|----------|----------------|
| Вход | POST | `/auth/token/` | Кнопка «Войти» |
| Список заказов | GET | `/picker/orders/?status=` | Загрузка списка |
| Детали заказа | GET | `/picker/orders/{id}/` | Открытие экрана сборки, обновление после скана |
| Начать сборку | POST | `/picker/orders/{id}/start_assembly/` | Только при клике по заказу со статусом PENDING |
| Сканировать штрихкод | POST | `/picker/verify-barcode/` | После каждого успешного скана |
| Завершить сборку | POST | `/picker/orders/{id}/finish_assembly/` | Кнопка «Завершить сборку» (когда все товары отсканированы) |

---

## 6. Важные моменты для Android

1. Кнопку «Завершить сборку» включать по `is_order_complete: true` из ответа `verify-barcode`, а не по `verification_code`.
2. `verification_code` приходит только в ответе на `finish_assembly`.
3. При клике по заказу со статусом `ASSEMBLING` или `ASSEMBLED` не вызывать `start_assembly`.
4. При ошибке `403`/`409` (заказ уже взял другой сборщик) — очистить `active_order_id` и вернуться к списку.

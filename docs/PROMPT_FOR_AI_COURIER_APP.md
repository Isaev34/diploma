# Промпт для создания Android-приложения для курьеров

## Контекст проекта

Ты должен создать **нативное Android-приложение на Kotlin** для курьеров интернет-магазина. Приложение будет работать с Django REST API бэкендом, который использует JWT аутентификацию.

**Бэкенд:**
- Django 4.2 + Django REST Framework
- PostgreSQL база данных
- JWT аутентификация (djangorestframework-simplejwt)
- API находится по адресу: `http://your-server.com/api/`
- JWT эндпоинты: 
  - `POST /api/auth/token/` - получение токена (требует `username` и `password`)
  - `POST /api/auth/token/refresh/` - обновление токена
- Ответ от `/api/auth/token/` содержит: `{"access": "...", "refresh": "..."}`

**Роли в системе:**
- Покупатель (customer)
- Курьер (courier) - новый, будет добавлен на бэкенде
- Менеджер (manager)
- Администратор (admin)

**Модель Order на бэкенде:**
```python
class Order:
    id: int
    user: ForeignKey(User)  # Покупатель
    courier: ForeignKey(User, null=True)  # Назначенный курьер
    status: str  # 'COOKING', 'READY', 'SHIPPING', 'DELIVERED', 'CANCELLED'
    delivery_address: str
    delivery_comment_courier: str  # Комментарий для курьера
    total_amount: Decimal
    created_at: DateTime
    items: List[OrderItem]  # Связанные позиции заказа
```

**OrderItem:**
```python
class OrderItem:
    product_name: str
    quantity: int
    price_at_purchase: Decimal
```

## Технический стек для Android

**Обязательные библиотеки:**
- Kotlin 1.9+
- Android SDK: minSdk 24, targetSdk 34
- **XML разметка** для UI (не Jetpack Compose)
- Retrofit 2.9.0 для сетевых запросов
- OkHttp 4.11.0 + logging interceptor
- Gson для JSON парсинга
- EncryptedSharedPreferences для безопасного хранения JWT токенов
- ViewModel + LiveData для управления состоянием
- Navigation Component для навигации между экранами
- Coroutines для асинхронных операций
- **Glide 4.16.0** для загрузки и отображения изображений
- **Material Components 1.11.0** для готовых UI элементов (MaterialButton, MaterialCardView, TextInputLayout, Chip, Badge и т.д.)
- **Timber 5.0.1** для логирования

## Функциональные требования

### 1. Экран авторизации (Login Screen)
- **Activity**: `LoginActivity` с XML layout `activity_login.xml`
- Использовать Material TextInputLayout для полей ввода:
  - Поле `username` (логин) - TextInputEditText с hint "Логин"
  - Поле `password` (пароль) - TextInputEditText с hint "Пароль", inputType="textPassword"
- Material Button "Войти" (растянутая на всю ширину)
- При успешном входе:
  - Отправить POST запрос на `/api/auth/token/` с `username` и `password`
  - Сохранить `access` и `refresh` токены в EncryptedSharedPreferences
  - Перейти на экран со списком заказов (через Intent или Navigation Component)
- При ошибке показать Material Snackbar с сообщением об ошибке
- Показывать ProgressBar во время запроса (можно в центре экрана или в виде ProgressDialog)

### 2. Экран списка заказов (Orders List Screen)
- **Activity**: `OrdersListActivity` с XML layout `activity_orders_list.xml`
- **Toolbar/AppBar**: заголовок "Мои заказы" с кнопкой меню (профиль/выход)
- **Фильтр по статусу** (использовать Material ChipGroup или HorizontalScrollView с Chips):
  - "Все" - все заказы курьера
  - "Новые" - статус 'READY'
  - "В доставке" - статус 'SHIPPING'
  - "Доставленные" - статус 'DELIVERED'
- **Список заказов** (RecyclerView с MaterialCardView для каждого элемента):
  - Для каждого заказа показать карточку:
    - Номер заказа: "Заказ #123" (заголовок карточки)
    - Адрес доставки (TextView с maxLines="2", ellipsize="end")
    - Сумма: "2 500 ₽" (жирный текст)
    - Статус: Material Badge или Chip с цветом (pending - серый, confirmed - желтый, shipping - синий, delivered - зеленый)
    - Дата создания: "25.12.2024 14:30"
  - При клике на карточку → открыть экран деталей заказа
- **SwipeRefreshLayout** для pull-to-refresh
- Автоматическое обновление каждые 30 секунд (опционально)
- Если заказов нет - показать TextView/ImageView с сообщением "У вас пока нет заказов"
- **FloatingActionButton** (Material) с иконкой обновления (refresh) внизу справа

**API эндпоинт для списка заказов:**
- `GET /api/courier/orders/` - вернет все заказы, назначенные текущему курьеру
- Заголовок: `Authorization: Bearer {access_token}`
- Query параметры: `?status=shipping` (опционально, для фильтрации)
- Ответ: `[{id, user, username, email, status, delivery_address, total_amount, items, created_at, ...}]`

### 3. Экран деталей заказа (Order Detail Screen)
- **Activity**: `OrderDetailActivity` с XML layout `activity_order_detail.xml`
- **ScrollView** или **NestedScrollView** для прокрутки контента
- **Toolbar/AppBar**: заголовок "Заказ #123" с кнопкой назад
- Информация о заказе (в MaterialCardView или LinearLayout):
  - **Статус** (большой Material Chip/Badge сверху с цветом по статусу)
  - **Адрес доставки** (TextView, можно сделать кликабельным для открытия карты/навигации)
  - **Телефон клиента**: Material Button с иконкой телефона (можно кликнуть для звонка через Intent.ACTION_DIAL)
  - **Email клиента**: Material Button с иконкой email (можно кликнуть для открытия почты)
  - **Комментарий для курьера**: если есть, показать в отдельной MaterialCardView с заголовком
  - **Сумма заказа**: "Итого: 2 500 ₽" (большой жирный текст)
  - **Дата создания**: "Создан: 25.12.2024 14:30"
- **RecyclerView** для списка товаров:
  - Заголовок "Состав заказа" (TextView)
  - Для каждого товара показать в MaterialCardView:
    - Название товара (заголовок)
    - Количество: "x3"
    - Цена: "500 ₽"
    - Итого по позиции: "1 500 ₽"
  - В конце показать общую сумму
- **Кнопки действий** (внизу экрана в ConstraintLayout или LinearLayout, зависят от текущего статуса):
  - Если статус 'confirmed' или 'preparing':
    - Material Button "Принять заказ" (primary color, растянутая) → изменить статус на 'shipping'
  - Если статус 'shipping':
    - Material Button "Доставлен" (зеленая, растянутая) → изменить статус на 'delivered'
    - Material Button "Отменить" (красная, опционально) → изменить статус на 'cancelled'
- После изменения статуса показать Material Snackbar с сообщением "Статус обновлен" и обновить данные заказа

**API эндпоинты:**
- `GET /api/courier/orders/{id}/` - получить детали заказа
- `POST /api/courier/orders/{id}/update_status/` - обновить статус
  - Body: `{"status": "shipping"}` или `{"status": "delivered"}`
  - Ответ: обновленный объект Order

### 4. Экран профиля (Profile Screen) - опционально
- **Activity** или **Fragment**: `ProfileActivity` / `ProfileFragment` с XML layout
- Имя пользователя (username) - TextView
- Email - TextView
- Material Button "Выйти" → очистить токены и вернуться на экран логина (через Intent)

**API эндпоинт:**
- `GET /api/users/me/` - получить информацию о текущем пользователе

## Структура проекта

```
app/
├── src/main/java/com/yourapp/courier/
│   ├── data/
│   │   ├── api/
│   │   │   ├── ApiService.kt           # Retrofit интерфейс со всеми эндпоинтами
│   │   │   ├── ApiClient.kt            # Конфигурация Retrofit + Interceptors
│   │   │   └── models/
│   │   │       ├── Order.kt            # data class Order
│   │   │       ├── OrderItem.kt        # data class OrderItem
│   │   │       ├── User.kt             # data class User
│   │   │       ├── LoginRequest.kt     # data class LoginRequest(username, password)
│   │   │       ├── LoginResponse.kt    # data class LoginResponse(access, refresh)
│   │   │       └── UpdateStatusRequest.kt  # data class UpdateStatusRequest(status)
│   │   ├── repository/
│   │   │   ├── AuthRepository.kt       # Логика авторизации
│   │   │   └── OrderRepository.kt      # Логика работы с заказами
│   │   └── local/
│   │       └── TokenManager.kt         # Управление JWT токенами (EncryptedSharedPreferences)
│   ├── ui/
│   │   ├── login/
│   │   │   ├── LoginActivity.kt        # Activity для логина
│   │   │   ├── activity_login.xml      # XML layout для логина
│   │   │   └── LoginViewModel.kt       # ViewModel для логина
│   │   ├── orders/
│   │   │   ├── OrdersListActivity.kt   # Activity для списка заказов
│   │   │   ├── activity_orders_list.xml # XML layout для списка
│   │   │   ├── OrdersListViewModel.kt  # ViewModel для списка
│   │   │   ├── adapter/
│   │   │   │   └── OrdersAdapter.kt    # RecyclerView.Adapter для списка заказов
│   │   │   ├── OrderDetailActivity.kt  # Activity для деталей заказа
│   │   │   ├── activity_order_detail.xml # XML layout для деталей
│   │   │   ├── OrderDetailViewModel.kt # ViewModel для деталей
│   │   │   └── adapter/
│   │   │       └── OrderItemsAdapter.kt # RecyclerView.Adapter для списка товаров
│   │   └── profile/
│   │       ├── ProfileActivity.kt      # Activity для профиля
│   │       ├── activity_profile.xml    # XML layout для профиля
│   │       └── ProfileViewModel.kt     # ViewModel для профиля
│   ├── utils/
│   │   ├── DateFormatter.kt            # Утилиты для форматирования дат
│   │   └── Extensions.kt               # Kotlin extension функции
│   ├── MainActivity.kt                 # Главная Activity (проверяет токен и направляет)
│   └── CouriersApp.kt                  # Application класс (инициализация Timber)
├── src/main/res/
│   ├── layout/                         # XML layout файлы
│   ├── values/
│   │   ├── colors.xml                  # Цвета приложения
│   │   ├── strings.xml                 # Строковые ресурсы
│   │   ├── themes.xml                  # Material Theme
│   │   └── dimens.xml                  # Размеры и отступы
│   └── drawable/                       # Иконки и drawable ресурсы
└── build.gradle.kts                    # Зависимости проекта
```

## Детали реализации

### 1. Настройка Retrofit (ApiClient.kt)

```kotlin
import timber.log.Timber
import okhttp3.logging.HttpLoggingInterceptor

// Добавить Interceptor для автоматического добавления JWT токена в заголовки
class AuthInterceptor(private val tokenManager: TokenManager) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenManager.getAccessToken()
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .addHeader("Content-Type", "application/json")
            .build()
        
        val response = chain.proceed(request)
        
        // Если токен истек (401), попробовать обновить через refresh token
        if (response.code == 401 && token != null) {
            // Реализовать логику обновления токена
        }
        
        return response
    }
}

// Настройка OkHttp с логированием через Timber
val loggingInterceptor = HttpLoggingInterceptor { message ->
    Timber.tag("OkHttp").d(message)
}.apply {
    level = HttpLoggingInterceptor.Level.BODY
}

// База URL: "http://your-server.com/api/"
// Добавить LoggingInterceptor для отладки (используя Timber)
```

### 2. Модели данных (data classes)

Все модели должны быть data class с полями, соответствующими JSON ответу от API.

**Order.kt:**
```kotlin
@Serializable
data class Order(
    val id: Int,
    val user: Int,
    val username: String?,
    val email: String?,
    val status: String,
    val delivery_address: String,
    val delivery_comment_courier: String?,
    val total_amount: String,
    val items: List<OrderItem>,
    @Serializable(with = DateTimeSerializer::class)
    val created_at: String
)
```

### 3. TokenManager

Использовать EncryptedSharedPreferences для безопасного хранения токенов.

### 4. Инициализация Timber

В `CouriersApp.kt` (Application класс):
```kotlin
class CouriersApp : Application() {
    override fun onCreate() {
        super.onCreate()
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        } else {
            Timber.plant(Timber.ReleaseTree()) // Или CrashReportingTree()
        }
    }
}
```

### 5. Использование Glide

Для загрузки изображений (если будут изображения товаров в деталях заказа):
```kotlin
Glide.with(context)
    .load(imageUrl)
    .placeholder(R.drawable.placeholder)
    .error(R.drawable.error_image)
    .into(imageView)
```

### 6. UI/UX требования

- **Material Components**: использовать готовые компоненты из Material Design Library:
  - `com.google.android.material.button.MaterialButton` - кнопки
  - `com.google.android.material.card.MaterialCardView` - карточки
  - `com.google.android.material.textfield.TextInputLayout` и `TextInputEditText` - поля ввода
  - `com.google.android.material.chip.Chip` и `ChipGroup` - чипы для фильтров
  - `com.google.android.material.floatingactionbutton.FloatingActionButton` - FAB
  - `com.google.android.material.snackbar.Snackbar` - уведомления
  - `com.google.android.material.badge.Badge` - бейджи для статусов
- **Цветовая схема**: использовать Material Design 3, настроить в `themes.xml`
- **Темы**: поддержка светлой и темной темы (через AppCompat или Material Components)
- **Анимации**: использовать стандартные Android transitions для Activity переходов
- **Обработка ошибок**: показывать понятные сообщения через Material Snackbar
- **Состояния загрузки**: показывать ProgressBar или ProgressDialog во время запросов
- **Обработка пустых состояний**: если список пуст, показать TextView/ImageView с сообщением
- **RecyclerView**: использовать ViewHolder pattern, оптимизировать через `setHasFixedSize(true)`

### 7. Обработка ошибок

- Ошибки сети → "Нет подключения к интернету"
- 401 Unauthorized → "Сессия истекла, войдите снова" → вернуться на экран логина
- 403 Forbidden → "Нет доступа"
- 404 Not Found → "Заказ не найден"
- Другие ошибки → "Произошла ошибка: {message}"

### 8. Дополнительные функции (опционально, но приветствуется)

- Геолокация: при открытии адреса доставки можно показать на карте
- Push-уведомления: когда новый заказ назначен курьеру
- Статистика: количество доставленных заказов за день/неделю
- История заказов: список всех завершенных заказов

## Тестовые данные

Создать тестового курьера на бэкенде:
- Username: `courier_test`
- Password: `testpass123`
- Роль: курьер (courier)

## Зависимости (build.gradle.kts)

```kotlin
dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    
    // ViewModel & LiveData
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0")
    implementation("androidx.activity:activity-ktx:1.8.2")
    
    // Navigation Component
    implementation("androidx.navigation:navigation-fragment-ktx:2.7.6")
    implementation("androidx.navigation:navigation-ui-ktx:2.7.6")
    
    // Retrofit & Networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // Security (EncryptedSharedPreferences)
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // Glide - загрузка изображений
    implementation("com.github.bumptech.glide:glide:4.16.0")
    kapt("com.github.bumptech.glide:compiler:4.16.0")
    
    // Timber - логирование
    implementation("com.jakewharton.timber:timber:5.0.1")
    
    // RecyclerView (включен в Material Components, но можно явно указать)
    implementation("androidx.recyclerview:recyclerview:1.3.2")
}
```

## Чек-лист реализации

- [ ] Настроен проект Android с Kotlin и XML разметкой
- [ ] Добавлены все необходимые зависимости в build.gradle (включая Material Components, Glide, Timber)
- [ ] Инициализирован Timber в Application классе
- [ ] Создан TokenManager для хранения JWT токенов (EncryptedSharedPreferences)
- [ ] Настроен Retrofit с AuthInterceptor и Timber LoggingInterceptor
- [ ] Созданы все модели данных (Order, OrderItem, LoginRequest, etc.)
- [ ] Реализован XML layout и Activity для экрана логина с авторизацией
- [ ] Реализован XML layout, Activity и RecyclerView.Adapter для экрана списка заказов с фильтрацией
- [ ] Реализован XML layout, Activity и RecyclerView.Adapter для экрана деталей заказа
- [ ] Реализовано изменение статуса заказа через API
- [ ] Добавлена обработка ошибок через Snackbar и состояний загрузки через ProgressBar
- [ ] Реализована навигация между экранами через Intent или Navigation Component
- [ ] Использованы Material Components для всех UI элементов
- [ ] Приложение протестировано на реальном устройстве/эмуляторе

## Важные замечания

1. **Безопасность**: Никогда не логировать JWT токены в production (использовать ReleaseTree для Timber)
2. **Timber**: Использовать Timber вместо Log.d/Log.e везде в коде
3. **Производительность**: Использовать pagination если заказов много (бэкенд поддерживает)
4. **UX**: Все действия пользователя должны иметь визуальную обратную связь
5. **Accessibility**: Добавить contentDescription для всех иконок и ImageView
6. **Lint**: Код должен проходить Android Lint проверки
7. **Material Design**: Следовать Material Design Guidelines, использовать готовые компоненты из библиотеки

## Стиль кода

- Использовать Kotlin Coding Conventions
- Именование: camelCase для переменных и функций, PascalCase для классов
- Комментировать сложную бизнес-логику
- Использовать Sealed Classes для состояний UI (Loading, Success, Error)

---

**ВАЖНО**: При создании приложения убедись, что все API эндпоинты для курьеров уже реализованы на бэкенде. Если нет - сначала нужно добавить их в Django проект.

## Дополнительные инструкции по реализации

### XML Layout рекомендации:

1. **Использовать ConstraintLayout** для сложных макетов (лучшая производительность)
2. **Использовать LinearLayout** для простых вертикальных/горизонтальных списков элементов
3. **Все строки вынести в `strings.xml`** (не хардкодить в XML или коде)
4. **Все цвета вынести в `colors.xml`**
5. **Использовать `tools:` атрибуты** для предпросмотра в Android Studio (например, `tools:text="Тестовый текст"`)

### RecyclerView Adapter паттерн:

```kotlin
class OrdersAdapter(
    private val orders: List<Order>,
    private val onItemClick: (Order) -> Unit
) : RecyclerView.Adapter<OrdersAdapter.ViewHolder>() {
    
    inner class ViewHolder(val binding: ItemOrderBinding) : RecyclerView.ViewHolder(binding.root)
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemOrderBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val order = orders[position]
        // Биндинг данных в ViewHolder
        holder.itemView.setOnClickListener { onItemClick(order) }
    }
    
    override fun getItemCount() = orders.size
}
```

### ViewBinding:

Использовать ViewBinding вместо findViewById для всех XML layouts:
- Включить в `build.gradle`: `buildFeatures { viewBinding = true }`
- Использовать автогенерированные binding классы

Создай полнофункциональное Android-приложение согласно этому техническому заданию. Используй **XML разметку** с **Material Components**, **Glide** для изображений, **Timber** для логирования. Начни с настройки проекта и базовой структуры, затем последовательно реализуй каждый экран (Activity + XML layout + ViewModel).

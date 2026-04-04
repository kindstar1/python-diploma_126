# Дипломный проект: backend сервиса заказов товаров

Backend для автоматизации закупок в розничной сети: REST API на **Django** и **Django REST Framework**, данные в **PostgreSQL** (контейнер **Docker**). Взаимодействие с приложением — через HTTP-запросы (Postman, Insomnia, curl и т.п.).

---

## Содержание

1. [Технологии](#технологии)
2. [Структура репозитория](#структура-репозитория)
3. [Устройство backend](#устройство-backend)
4. [Реализованный функционал](#реализованный-функционал)
5. [База данных в Docker](#база-данных-в-docker)
6. [Переменные окружения](#переменные-окружения)
7. [Запуск проекта](#запуск-проекта)
8. [Логирование](#логирование)
9. [Импорт каталога (YAML)](#импорт-каталога-yaml)
10. [Материалы курса (reference)](#материалы-курса-reference)

---

## Технологии

| Компонент        | Описание                          |
|-----------------|-----------------------------------|
| Python 3.10+    | рекомендуется 3.10–3.13           |
| Django ~5.x     | веб-фреймворк                     |
| DRF ~3.14       | REST API, токен-аутентификация    |
| django-filter   | фильтрация списка товаров         |
| PostgreSQL 14   | СУБД (образ в Docker)             |
| psycopg2-binary | драйвер PostgreSQL                |
| python-dotenv   | загрузка настроек из `.env`       |
| PyYAML          | разбор YAML при импорте каталога  |
| Docker Compose  | запуск PostgreSQL                 |

---

## Структура репозитория

```
DIPLOMA_NETOLOGY/
├── README.md                 # этот файл
├── requirements.txt          # зависимости Python
├── docker-compose.yml        # сервис PostgreSQL
├── .env                      # секреты и настройки
├── data/
│   └── shop1.yaml            # пример файла каталога для импорта
├── orders_backend/           # Django-проект
│   ├── manage.py
│   ├── orders_backend/       # настройки проекта (settings, urls)
│   └── store/                # приложение «магазин»
│       ├── models.py
│       ├── views.py
│       ├── serializers.py
│       ├── urls.py
│       ├── filters.py
│       ├── import_orders.py
│       ├── admin.py
│       └── migrations/
└── reference/                # исходные материалы для предоставления решения
```

Рабочий код диплома — каталог **`orders_backend/`**. Запуск команд (`migrate`, `runserver`) выполняется из **`orders_backend`**.

---

## Устройство backend

### Проект `orders_backend`

- **`orders_backend/settings.py`** — подключение приложений, DRF, БД из переменных окружения, почта, **логирование в консоль** для логгера `store`.
- **`orders_backend/urls.py`** — префикс API `api/v1/`, подключение маршрутов приложения `store`, админка `admin/`.

### Приложение `store`

- **`models.py`** — пользователь (`User`, вход по email), магазины (`Shop`), категории и товары (`Category`, `Product`, `ProductInfo`), параметры (`Parameter`, `ProductParameter`), контакты (`Contact`), корзина (`Cart`, `CartItem`), заказы (`Order`, `OrderItem`), токен подтверждения email (`ConfirmEmailToken`).
- **`views.py`** — классы-представления DRF: регистрация, вход, товары, корзина, контакты, заказы, подтверждение email, смена статуса заказа поставщиком.
- **`serializers.py`** — сериализация сущностей для API.
- **`filters.py`** — фильтры списка товаров (категория, магазин, цена, поиск по названию).
- **`import_orders.py`** — загрузка каталога из YAML в модели (используется из кода/shell при необходимости).

### Аутентификация

После регистрации или входа клиент получает **токен**. Для защищённых эндпоинтов в заголовке передаётся:

```http
Authorization: Token <ключ_токена>
```

Глобально для DRF по умолчанию включена проверка **`IsAuthenticated`**; отдельные эндпоинты (регистрация, вход, список/карточка товара, подтверждение email) открыты через **`AllowAny`**.

---

## Реализованный функционал

Базовый URL API: **`/api/v1/`** (полный путь на локали: `http://127.0.0.1:8000/api/v1/...`).

| Метод и путь | Назначение |
|--------------|------------|
| `POST .../register/` | Регистрация пользователя, письмо с ссылкой подтверждения email |
| `GET .../confirm-email/?token=...` | Подтверждение email |
| `POST .../login/` | Вход, выдача токена |
| `GET .../products/` | Каталог с фильтрами (`category`, `shop`, `price_min`, `price_max`, `search`) |
| `GET .../products/<id>/` | Карточка позиции каталога |
| `GET .../cart/` | Просмотр корзины |
| `POST .../cart/add` | Добавление в корзину (**без** завершающего слэша в пути) |
| `DELETE .../cart/<id>/` | Удаление позиции из корзины |
| `PATCH .../cart/update/<id>/` | Изменение количества |
| `GET/POST .../contacts/` | Список и создание контактов |
| `GET/PATCH/DELETE .../contacts/<id>/` | Один контакт |
| `GET .../orders/` | Список заказов пользователя |
| `POST .../orders/create/` | Оформление заказа из корзины, письмо клиенту |
| `GET .../orders/<id>/` | Детали заказа |
| `PATCH .../orders/<id>/status/` | Смена статуса (для поставщика, по товарам своего магазина) |

---

## База данных в Docker

PostgreSQL поднимается **отдельно** через Docker Compose. В `docker-compose.yml` описан сервис `db` (образ `postgres:14.3`), порт **хоста 5431** проброшен на **5432** внутри контейнера.

Перед запуском Django необходимо убедиться, что контейнер с БД запущен:

```bash
docker compose up -d
```

Остановка:

```bash
docker compose down
```

Переменные `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` для контейнера берутся из **того же файла `.env`**, что и Django (см. ниже), т.к. в `docker-compose.yml` используется подстановка `${POSTGRES_...}`.

---

## Переменные окружения

В корне репозитория создайте файл **`.env`** (не добавляйте его в git). Пример **шаблона** (значения подставьте свои):

```env
# Django
SECRET_KEY=сгенерируйте-длинную-случайную-строку

# PostgreSQL (совпадают с docker-compose)
POSTGRES_DB=имя_базы
POSTGRES_USER=пользователь
POSTGRES_PASSWORD=пароль
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5431

# Почта (для писем при регистрации и создании заказа)
EMAIL_HOST_USER=ваш@ящик
EMAIL_HOST_PASSWORD=пароль_приложения
```

**Важно:** в `settings.py` вызывается `load_dotenv()` **без пути** — ищется файл `.env` в **текущей рабочей директории** процесса.

- Если команды запускаете **из корня репозитория** (`DIPLOMA_NETOLOGY`), держите `.env` **в корне** и вызывайте, например:  
  `python orders_backend/manage.py migrate` — переменные подтянутся из корневого `.env`.
- Если вы **всегда** заходите в `orders_backend` и там запускаете `python manage.py ...`, положите `.env` **внутрь каталога `orders_backend/`** (или скопируйте тот же файл).

Команда **`docker compose`** из корня репозитория подставляет переменные из `.env` рядом с `docker-compose.yml` (обычно тот же корень) — удобно хранить **один** `.env` в корне и запускать Django тоже с корня через `python orders_backend/manage.py`.

---

## Запуск проекта

### 1. Клонирование и виртуальное окружение

```bash
git clone <url-репозитория>
cd DIPLOMA_NETOLOGY
python -m venv venv
```

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 2. Зависимости

```bash
pip install -r requirements.txt
```

При проблемах с доступом к PyPI можно указать зеркало:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. PostgreSQL в Docker

```bash
docker compose up -d
```

### 4. Миграции и (при необходимости) суперпользователь

Из **корня репозитория** (чтобы читался корневой `.env`):

```bash
python orders_backend/manage.py migrate
python orders_backend/manage.py createsuperuser
```

Либо из каталога `orders_backend` (если `.env` лежит там же):

```bash
cd orders_backend
python manage.py migrate
python manage.py createsuperuser
```

### 5. Сервер разработки

```bash
python orders_backend/manage.py runserver
```

или из `orders_backend`: `python manage.py runserver`.

API по умолчанию: **http://127.0.0.1:8000/api/v1/**

---

## Логирование

В `settings.py` настроен вывод в **консоль** для логгера приложения **`store`** (уровень INFO). В `store.views` логируются ключевые события: регистрация, вход, подтверждение email, добавление в корзину, создание заказа, успешная смена статуса заказа поставщиком — без избыточной детализации и без паролей.

---

## Импорт каталога (YAML)

В каталоге **`data/`** лежит пример **`shop1.yaml`**. Импорт в БД реализован в **`orders_backend/store/import_orders.py`** (функция принимает путь к файлу и идентификатор пользователя-владельца магазина). Вызов удобно делать из **`python manage.py shell`** после настройки Django, либо встроить вызов в отдельную management-команду по желанию.

---

## Материалы курса (reference)

В папке **`reference/`** — описание этапов диплома, спецификация экранов, пример эталонного проекта от методистов. Они не являются исполняемым кодом текущей сдачи; основной рабочий проект — **`orders_backend`**.

---


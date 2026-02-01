# Worship Lyrics Bot

Telegram-бот для пошуку текстів пісень: усі пошуки (чат, інлайн, `/id_*`) працюють з локальною базою (SQLite). Дані синхронізуються з Planning Center при старті та за розкладом (03:00, 06:00, 09:00, 12:00).

## Структура проєкту

- **telegram/** — логіка бота (обробники, клавіатури, FSM, форматування, пагінація)
- **storage/** — репозиторій пісень (SQLite)
- **planning_center/** — клієнт Planning Center API (тільки для синхронізації)
- **sync/** — синхронізація з PCO при старті, за розкладом, заглушка webhook
- **lyrics/** — fuzzy-пошук (LanguageTool + fuzzywuzzy), провайдер даних з репозиторію
- **run.py** — точка входу (polling)
- **webhook.py** — фабрика aiohttp-додатку для webhook-режиму та POST /pco-webhook
- **config.py** — конфігурація з змінних середовища

## Вимоги

- Python 3.12 або новіший (рекомендовано 3.12–3.13)
- Змінні середовища: `TELEGRAM_TOKEN`, `PCO_CLIENT_ID`, `PCO_SECRET`; опційно `DATA_PATH` (за замовчуванням `data/songs.db`)

---

## Запуск локально

1. Клонуйте репозиторій та перейдіть у папку проєкту:

   ```bash
   cd worship-lyrics
   ```

2. Створіть віртуальне середовище та встановіть залежності:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # або: .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

   Якщо `pip install` падає на збірці `pydantic-core` (Rust), використовуйте Python 3.12:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Створіть файл `.env` у корені проєкту (або експортуйте змінні в терміналі):

   ```env
   TELEGRAM_TOKEN=ваш_токен_бота
   PCO_CLIENT_ID=ваш_client_id_planning_center
   PCO_SECRET=ваш_secret_planning_center
   DATA_PATH=data/songs.db
   ```

   При першому запуску бот синхронізує пісні з PCO у локальну БД (SQLite). Каталог `data/` створюється автоматично, якщо його немає.

4. Запустіть бота:

   ```bash
   python3 run.py
   ```

---

## Запуск у Docker

1. Створіть файл `.env` у корені проєкту (як у пункті 3 вище).

2. Створіть папку `data` (для збереження SQLite-бази пісень):

   ```bash
   mkdir -p data
   ```

   При старті контейнера бот один раз синхронізує пісні з PCO у `data/songs.db`; далі синхронізація запускається за розкладом (03:00, 06:00, 09:00, 12:00 UTC).

3. Зберіть образ і запустіть контейнер:

   ```bash
   docker compose build
   docker compose up -d
   ```

   Логи: `docker compose logs -f bot`. Зупинка: `docker compose down`.

4. Для webhook-режиму розкоментуйте в `docker-compose.yml` секцію `ports` (8080) та додайте в `.env` змінну `WEBHOOK_URL`. Ендпоінт `POST /pco-webhook` зарезервовано для майбутньої інтеграції з PCO webhooks.

---

## Змінні середовища

| Змінна            | Обовʼязкова | Опис                                                                 |
|-------------------|-------------|----------------------------------------------------------------------|
| `TELEGRAM_TOKEN`  | так         | Токен бота від @BotFather                                            |
| `PCO_CLIENT_ID`   | так         | Client ID застосунку в Planning Center (для синхронізації)           |
| `PCO_SECRET`      | так         | Secret застосунку в Planning Center                                 |
| `DATA_PATH`       | ні          | Шлях до файлу SQLite-бази пісень (за замовч. `data/songs.db`)        |
| `SONGS_DATA_PATH` | ні          | Застаріло; залишено для сумісності (за замовч. `songs_data.json`)    |
| `WEBHOOK_URL`     | ні          | URL для webhook Telegram (якщо використовується webhook)            |
| `PORT`            | ні          | Порт для webhook-сервера (за замовч. 8080)                          |

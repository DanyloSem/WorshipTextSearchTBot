# Worship Lyrics Bot

Telegram-бот для пошуку текстів пісень: пошук через Planning Center API та інлайн-пошук по локальному JSON.

## Структура проєкту

- **telegram/** — логіка бота (обробники, клавіатури, FSM, форматування, пагінація)
- **planning_center/** — клієнт Planning Center API (пошук пісень, отримання текстів)
- **lyrics/** — збереження даних (JSON), fuzzy-пошук для inline, Whoosh-індекс (опційно)
- **run.py** — точка входу (polling)
- **webhook.py** — фабрика aiohttp-додатку для webhook-режиму
- **config.py** — конфігурація з змінних середовища

## Вимоги

- Python 3.12 або новіший (рекомендовано 3.12–3.13)
- Змінні середовища: `TELEGRAM_TOKEN`, `PCO_CLIENT_ID`, `PCO_SECRET`; опційно `SONGS_DATA_PATH` (за замовчуванням `songs_data.json`)

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
   SONGS_DATA_PATH=songs_data.json
   ```

   Файл `songs_data.json` для інлайн-пошуку має лежати у корені проєкту (або вказаний шлях у `SONGS_DATA_PATH`).

4. Запустіть бота:

   ```bash
   python3 run.py
   ```

---

## Запуск у Docker

1. Створіть файл `.env` у корені проєкту (як у пункті 3 вище).

2. Створіть папку `data` і покладіть туди файл `songs_data.json` для інлайн-пошуку:

   ```bash
   mkdir -p data
   cp songs_data.json data/   # якщо файл вже є в проєкті
   ```

3. Зберіть образ і запустіть контейнер:

   ```bash
   docker compose build
   docker compose up -d
   ```

   Логи: `docker compose logs -f bot`. Зупинка: `docker compose down`.

4. (Опційно) Якщо не використовуєте volume для даних — видаліть у `docker-compose.yml` блоки `environment` (SONGS_DATA_PATH) та `volumes`. Тоді буде використовуватися `songs_data.json` з кореня проєкту на момент збірки образу.

5. Для webhook-режиму розкоментуйте в `docker-compose.yml` секцію `ports` (8080) та додайте в `.env` змінну `WEBHOOK_URL`.

---

## Змінні середовища

| Змінна            | Обовʼязкова | Опис                                              |
|-------------------|-------------|---------------------------------------------------|
| `TELEGRAM_TOKEN`  | так         | Токен бота від @BotFather                         |
| `PCO_CLIENT_ID`   | так         | Client ID застосунку в Planning Center            |
| `PCO_SECRET`      | так         | Secret застосунку в Planning Center              |
| `SONGS_DATA_PATH` | ні          | Шлях до JSON з даними для inline (за замовч. `songs_data.json`) |
| `WEBHOOK_URL`     | ні          | URL для webhook (якщо використовується webhook)   |
| `PORT`            | ні          | Порт для webhook-сервера (за замовч. 8080)       |

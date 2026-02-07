# Worship Lyrics Bot

Telegram-бот для пошуку текстів пісень: усі пошуки (чат, інлайн, `/id_*`) працюють з локальною базою (SQLite). Дані синхронізуються з Planning Center при старті та за розкладом (03:00, 06:00, 09:00, 12:00).

## Структура проєкту

- **telegram/** — логіка бота (обробники, клавіатури, FSM, форматування, пагінація)
- **storage/** — репозиторій пісень (SQLite)
- **planning_center/** — клієнт Planning Center API (тільки для синхронізації)
- **sync/** — синхронізація з PCO при старті та за розкладом
- **lyrics/** — fuzzy-пошук (LanguageTool + fuzzywuzzy), провайдер даних з репозиторію
- **run.py** — точка входу (polling)
- **run_webhook.py** — точка входу для webhook-режиму (aiohttp, POST /pco-webhook)
- **webhook/** — фабрика aiohttp-додатку та обробка PCO webhooks (перевірка підпису, парсинг подій)
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

Конфіг `docker-compose.yml` за замовчуванням запускає бота в **webhook-режимі** (порт 8080, `run_webhook.py`).

1. Створіть файл `.env` у корені проєкту. Для webhook-режиму обовʼязково вкажіть `WEBHOOK_URL`:

   ```env
   TELEGRAM_TOKEN=ваш_токен_бота
   PCO_CLIENT_ID=ваш_client_id_planning_center
   PCO_SECRET=ваш_secret_planning_center
   DATA_PATH=data/songs.db

   # Webhook (обовʼязково для режиму з docker compose)
   WEBHOOK_URL=https://ваш-домен.com/webhook
   PORT=8080
   # Опційно — для перевірки підпису PCO на POST /pco-webhook
   # PCO_WEBHOOK_AUTHENTICITY_SECRET=ваш_authenticity_secret
   ```

2. Зберіть образ і запустіть контейнер:

   ```bash
   docker compose build
   docker compose up -d
   ```

   Каталог `data/` для SQLite створюється автоматично. Логи: `docker compose logs -f bot`. Зупинка: `docker compose down`.

   Доступні ендпоінти: `POST /webhook` (Telegram), `POST /pco-webhook` (події PCO song created/updated/destroyed). Перед ботом варто поставити reverse proxy (nginx/Caddy) з HTTPS і проксувати на `http://localhost:8080`.

3. **Polling у Docker**: щоб використовувати polling замість webhook, у `docker-compose.yml` закоментуйте `ports` та замініть `command` на `["python3", "run.py"]`.

---

## Деплой на сервер

Нижче — варіанти запуску бота на VPS/сервері (Linux). Рекомендовано використовувати Docker.

### Вимоги на сервері

- ОС: Linux (Ubuntu 22.04 LTS або аналог)
- Python 3.12+ (якщо без Docker) або Docker і Docker Compose
- Доступ по SSH

### Варіант 1: Деплой через Docker (рекомендовано)

1. Підключіться по SSH та встановіть Docker і Docker Compose (якщо ще не встановлені):

   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install -y docker.io docker-compose-plugin
   sudo usermod -aG docker $USER
   # Вийдіть і зайдіть знову, щоб група docker застосувалась
   ```

2. Клонуйте репозиторій та перейдіть у папку проєкту:

   ```bash
   git clone https://github.com/<ваш-репо>/worship-lyrics.git
   cd worship-lyrics
   ```

3. Створіть файл `.env` на сервері (не комітьте його в git):

   ```bash
   nano .env
   ```

   Додайте змінні (замініть значення на свої). Для webhook-режиму (за замовчуванням у compose) обовʼязково вкажіть `WEBHOOK_URL`:

   ```env
   TELEGRAM_TOKEN=ваш_токен_бота
   PCO_CLIENT_ID=ваш_client_id_planning_center
   PCO_SECRET=ваш_secret_planning_center
   WEBHOOK_URL=https://ваш-домен.com/webhook
   ```

   Опційно: `DATA_PATH` уже задано в `docker-compose.yml` для контейнера; для перевірки PCO webhooks — `PCO_WEBHOOK_AUTHENTICITY_SECRET`.

4. Зберіть образ і запустіть контейнер (каталог `data/` створиться автоматично при старті):

   ```bash
   docker compose build
   docker compose up -d
   ```

5. Перевірте роботу:

   ```bash
   docker compose logs -f bot
   ```

   Зупинка: `docker compose down`. Перезапуск після оновлення коду: `git pull && docker compose build && docker compose up -d`.

### Варіант 2: Деплой без Docker (systemd)

1. На сервері клонуйте репозиторій та налаштуйте середовище:

   ```bash
   git clone https://github.com/<ваш-репо>/worship-lyrics.git
   cd worship-lyrics
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Створіть `.env` у корені проєкту (як у варіанті 1, крок 3).

3. Встановіть Java (потрібно для LanguageTool):

   ```bash
   sudo apt update && sudo apt install -y default-jre-headless
   ```

4. Створіть unit systemd (замініть `semsan` на свого користувача та шлях до проєкту):

   ```bash
   sudo nano /etc/systemd/system/worship-lyrics.service
   ```

   Вміст файлу:

   ```ini
   [Unit]
   Description=Worship Lyrics Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=semsan
   WorkingDirectory=/home/semsan/worship-lyrics
   Environment="PATH=/home/semsan/worship-lyrics/.venv/bin"
   ExecStart=/home/semsan/worship-lyrics/.venv/bin/python run.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

5. Увімкніть та запустіть сервіс:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable worship-lyrics
   sudo systemctl start worship-lyrics
   sudo systemctl status worship-lyrics
   ```

   Логи: `journalctl -u worship-lyrics -f`. Після оновлення коду: `git pull`, потім `sudo systemctl restart worship-lyrics`.

### Після деплою

- **Резервні копії**: періодично бекапте каталог `data/` (файл `songs.db`), якщо не використовуєте лише PCO як джерело правди.
- **Оновлення**: при оновленні залежностей (`requirements.txt`) перезберіть образ Docker або перестворіть venv і перезапустіть systemd-сервіс.
- **Webhook**: у Docker за замовчуванням використовується webhook-режим (порт 8080). Налаштуйте `WEBHOOK_URL` та при потребі — reverse proxy (nginx/Caddy) з HTTPS.

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
| `PCO_WEBHOOK_AUTHENTICITY_SECRET` | ні | Секрет перевірки підпису PCO (для POST /pco-webhook)   |

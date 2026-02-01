# WorshipTextSearchTBot
Telegram bot for searching worship song texts via API.

## Setup

- Python 3.10–3.13. Рекомендовано 3.12 або 3.13 (у проєкті використовується `aiogram>=3.24` з підтримкою 3.13).
- Якщо `pip install -r requirements.txt` падає на збірці `pydantic-core` (Rust/PyO3) — перествори venv на **Python 3.12**:
  ```bash
  rm -rf .venv
  python3.12 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Змінні середовища: `TELEGRAM_TOKEN`, `CLIENT_ID`, `SECRET`; опційно `SONGS_DATA_PATH` (за замовчуванням `songs_data.json`).

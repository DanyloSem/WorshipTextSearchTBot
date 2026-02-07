import logging
import os
from logging.handlers import RotatingFileHandler

# Папка logs має існувати до створення FileHandler (у контейнері може бути відсутня)
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'telegram_bot.log')
os.makedirs(LOG_DIR, exist_ok=True)

# Ротація: max 5 MB на файл, зберігати до 10 архівів (найстаріший видаляється)
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 10

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handlers: list[logging.Handler] = []

try:
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
except OSError:
    pass

# Консоль — завжди, щоб логи були видно в терміналі / docker compose
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
handlers.append(stream_handler)

# Примусово налаштовуємо root logger (basicConfig ігнорується, якщо вже є handlers від aiogram)
root = logging.getLogger()
root.setLevel(logging.DEBUG)
for h in list(root.handlers):
    root.removeHandler(h)
for h in handlers:
    root.addHandler(h)

# httpx та httpcore не засмічують вивід — тільки WARNING і вище
for _logger_name in ('httpx', 'httpcore'):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def apply_log_level(level_name: str) -> None:
    """
    Встановлює рівень логування root logger з рядка (наприклад з Config.log_level).

    Допустимі значення: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    Невалідні значення приводять до INFO.

    Args:
        level_name: Назва рівня (регістр не важливий).
    """
    level = getattr(logging, level_name.upper(), None)
    if level is None:
        level = logging.INFO
    root.setLevel(level)

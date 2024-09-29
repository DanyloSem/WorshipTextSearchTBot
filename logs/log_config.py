import logging

# Створюємо FileHandler з вказаним енкодінгом
file_handler = logging.FileHandler('logs/telegram_bot.log', encoding='utf-8')

# Встановлюємо формат для обробників
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Налаштовуємо логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, logging.StreamHandler()]
)

# Отримуємо логер для httpx і встановлюємо рівень логування на WARNING
httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

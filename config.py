"""Об'єкт конфігурації з валідацією при старті."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """
    Конфігурація бота та зовнішніх сервісів.

    Всі значення читаються з змінних середовища.
    """

    telegram_token: str
    client_id: str
    secret: str
    songs_data_path: str
    data_path: str
    webhook_url: str | None = None
    port: int = 8080
    log_level: str = 'INFO' # DEBUG, INFO, WARNING, ERROR, CRITICAL
    pco_webhook_authenticity_secret: str | None = None

    @classmethod
    def from_env(cls) -> 'Config':
        """
        Створює конфігурацію з змінних середовища.

        Returns:
            Інстанс Config з заповненими полями.

        Raises:
            ValueError: Якщо обов'язкові змінні відсутні.
        """
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        client_id = os.getenv('PCO_CLIENT_ID')
        secret = os.getenv('PCO_SECRET')
        songs_data_path = os.getenv('SONGS_DATA_PATH', 'songs_data.json')
        data_path = os.getenv('DATA_PATH', 'data/songs.db')
        webhook_url = os.getenv('WEBHOOK_URL')
        port_str = os.getenv('PORT', '8080')
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        pco_webhook_authenticity_secret = os.getenv('PCO_WEBHOOK_AUTHENTICITY_SECRET')

        missing = []
        if not telegram_token:
            missing.append('TELEGRAM_TOKEN')
        if not client_id:
            missing.append('PCO_CLIENT_ID')
        if not secret:
            missing.append('PCO_SECRET')
        if missing:
            raise ValueError('Відсутні обов\'язкові змінні середовища: ' + ', '.join(missing))

        try:
            port = int(port_str)
        except ValueError:
            port = 8080

        return cls(
            telegram_token=telegram_token,
            client_id=client_id,
            secret=secret,
            songs_data_path=songs_data_path,
            data_path=data_path,
            webhook_url=webhook_url or None,
            port=port,
            log_level=log_level,
            pco_webhook_authenticity_secret=pco_webhook_authenticity_secret or None,
        )


def load_config() -> Config:
    """
    Завантажує та валідує конфігурацію.

    Returns:
        Валідований інстанс Config.

    Raises:
        ValueError: Якщо валідація не пройдена.
    """
    return Config.from_env()


# Зворотна сумісність для коду, який імпортує змінні напряму (до переходу на DI).
CLIENT_ID = os.getenv('CLIENT_ID')
SECRET = os.getenv('SECRET')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

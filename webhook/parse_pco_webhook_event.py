"""Парсинг події PCO webhook для отримання action та song_id."""

import json
import os
from typing import Any


def get_event_name_from_body(body: bytes) -> str | None:
    """
    Повертає ім'я події з тіла webhook (data[0].attributes.name).

    Args:
        body: Сире тіло POST-запиту (JSON).

    Returns:
        Рядок типу 'services.v2.events.arrangement.updated' або None.
    """
    try:
        root = json.loads(body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    raw_data = root.get('data')
    if isinstance(raw_data, list) and raw_data:
        item = raw_data[0]
    elif isinstance(raw_data, dict):
        item = raw_data
    else:
        return None
    attrs = item.get('attributes') or {}
    name = attrs.get('name')
    return name if name and isinstance(name, str) else None


def event_name_to_env_key(name: str) -> str:
    """
    Перетворює ім'я події на ім'я змінної середовища для секрету.

    Приклад: services.v2.events.arrangement.updated → SERVICES_V2_EVENTS_ARRANGEMENT_UPDATED.
    """
    return name.strip().upper().replace('.', '_')


def get_secret_for_event(event_name: str) -> str | None:
    """
    Повертає секрет для перевірки підпису змінної для даної події з os.environ.

    Args:
        event_name: Ім'я події (наприклад services.v2.events.arrangement.updated).

    Returns:
        Значення змінної (наприклад SERVICES_V2_EVENTS_ARRANGEMENT_UPDATED) або None.
    """
    key = event_name_to_env_key(event_name)
    value = os.getenv(key)
    return value.strip() if value and isinstance(value, str) and value.strip() else None


def parse_pco_webhook_event(body: bytes) -> tuple[str | None, str | None]:
    """
    Визначає action (created/updated/destroyed) та ідентифікатор пісні з тіла події.

    Підтримує формат PCO: data — масив EventDelivery; у кожного attributes.name та
    attributes.payload (рядок JSON або вже об'єкт). Події song.* та arrangement.*.
    Якщо подія не стосується song/arrangement або song_id відсутній, повертає (None, None).

    Args:
        body: Сире тіло POST-запиту (JSON).

    Returns:
        Пара (action, song_id). action — 'created', 'updated' або 'destroyed';
        song_id — ідентифікатор пісні в PCO. Якщо подія не підходить або id немає — (None, None).
    """
    try:
        root = json.loads(body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return (None, None)

    raw_data = root.get('data')
    if isinstance(raw_data, list) and raw_data:
        item = raw_data[0]
    elif isinstance(raw_data, dict):
        item = raw_data
    else:
        return (None, None)

    attrs = item.get('attributes') or {}
    name = attrs.get('name')
    if not name or not isinstance(name, str):
        return (None, None)

    action = _action_from_event_name(name)
    if action is None:
        return (None, None)

    payload_raw = attrs.get('payload')
    if isinstance(payload_raw, dict):
        inner = payload_raw
    elif isinstance(payload_raw, str):
        try:
            inner = json.loads(payload_raw)
        except json.JSONDecodeError:
            return (None, None)
    else:
        return (None, None)

    song_id = _song_id_from_inner_payload(inner)
    if not song_id or not str(song_id).strip():
        return (None, None)

    return (action, str(song_id))


def _action_from_event_name(name: str) -> str | None:
    """
    Повертає 'created'/'updated'/'destroyed' для подій song.* або arrangement.*.
    Arrangement оновлення/видалення трактуємо як оновлення пісні (refetch); лише song.destroyed — видалення.
    """
    name_lower = name.lower()
    if '.song.created' in name_lower or '.arrangement.created' in name_lower:
        return 'created'
    if (
        '.song.updated' in name_lower
        or '.arrangement.updated' in name_lower
        or '.arrangement.destroyed' in name_lower
    ):
        return 'updated'
    if '.song.destroyed' in name_lower:
        return 'destroyed'
    return None


def _song_id_from_inner_payload(inner: Any) -> str | None:
    """
    Витягує song_id з розпарсеного attributes.payload.
    Тип Song: data.id; тип Arrangement: data.relationships.song.data.id.
    """
    def _norm(v: Any) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    data = inner.get('data')
    if not isinstance(data, dict):
        return None
    resource_type = (data.get('type') or '').strip()
    if resource_type == 'Song':
        return _norm(data.get('id'))
    if resource_type == 'Arrangement':
        return _norm(_get_nested(data, 'relationships', 'song', 'data', 'id'))
    return None


def _get_nested(obj: Any, *keys: str) -> Any:
    """Повертає значення по ланцюжку ключів або None."""
    for key in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj

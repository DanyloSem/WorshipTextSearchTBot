"""Парсинг події PCO webhook для отримання action та song_id."""

import json
from typing import Any


def parse_pco_webhook_event(body: bytes) -> tuple[str | None, str | None]:
    """
    Визначає action (created/updated/destroyed) та ідентифікатор пісні з тіла події.

    Підтримує формат PCO: data — масив EventDelivery; у кожного attributes.name та
    attributes.payload (рядок JSON). Події song.* та arrangement.* (для оновлення пісні за arrangement).
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

    payload_str = attrs.get('payload')
    if not isinstance(payload_str, str):
        return (None, None)
    try:
        inner = json.loads(payload_str)
    except json.JSONDecodeError:
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

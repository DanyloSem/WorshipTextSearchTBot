"""Парсинг події PCO webhook для отримання action та song_id."""

import json
from typing import Any


def parse_pco_webhook_event(body: bytes) -> tuple[str | None, str | None]:
    """
    Визначає action (created/updated/destroyed) та ідентифікатор пісні з тіла події.

    Підтримує формат подій Services API (наприклад services.v2.events.song.created).
    Якщо подія не стосується song або id відсутній, повертає (None, None).

    Args:
        body: Сире тіло POST-запиту (JSON).

    Returns:
        Пара (action, song_id). action — 'created', 'updated' або 'destroyed';
        song_id — ідентифікатор пісні в PCO. Якщо подія не для song або id немає — (None, None).
    """
    try:
        payload = json.loads(body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return (None, None)

    action = _extract_action(payload)
    if action is None:
        return (None, None)

    song_id = _extract_song_id(payload)
    if not song_id or not str(song_id).strip():
        return (None, None)

    return (action, str(song_id))


def _extract_action(payload: Any) -> str | None:
    """Повертає 'created', 'updated' або 'destroyed', якщо подія стосується song."""
    name = _get_nested(payload, 'data', 'attributes', 'name')
    if not name or not isinstance(name, str):
        name = _get_nested(payload, 'attributes', 'name')
    if not name or not isinstance(name, str):
        return None
    name_lower = name.lower()
    if not ('.song.created' in name_lower or '.song.updated' in name_lower or '.song.destroyed' in name_lower):
        return None
    if name_lower.endswith('.created'):
        return 'created'
    if name_lower.endswith('.updated'):
        return 'updated'
    if name_lower.endswith('.destroyed'):
        return 'destroyed'
    return None


def _extract_song_id(payload: Any) -> str | None:
    """Витягує ідентифікатор пісні з data.id або з вкладеного payload (string JSON)."""
    def _norm_id(value: Any) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        return s if s else None

    data = payload.get('data')
    if isinstance(data, dict):
        resource_id = data.get('id')
        if _norm_id(resource_id):
            return _norm_id(resource_id)
        inner_payload = data.get('attributes', {}).get('payload') or data.get('payload')
        if isinstance(inner_payload, str):
            try:
                inner = json.loads(inner_payload)
                return _norm_id(_get_nested(inner, 'data', 'id')) or _norm_id(
                    _get_nested(inner, 'data', 'attributes', 'id'),
                )
            except json.JSONDecodeError:
                pass
    inner = _get_nested(payload, 'data', 'attributes', 'payload')
    if isinstance(inner, str):
        try:
            parsed = json.loads(inner)
            return _norm_id(_get_nested(parsed, 'data', 'id')) or _norm_id(
                _get_nested(parsed, 'data', 'attributes', 'id'),
            )
        except json.JSONDecodeError:
            pass
    return None


def _get_nested(obj: Any, *keys: str) -> Any:
    """Повертає значення по ланцюжку ключів або None."""
    for key in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj

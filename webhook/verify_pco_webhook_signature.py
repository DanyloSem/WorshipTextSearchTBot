"""Перевірка підпису X-PCO-Webhooks-Authenticity для запитів від PCO."""

import hmac


def verify_pco_webhook_signature(
    body: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """
    Перевіряє, що заголовок X-PCO-Webhooks-Authenticity відповідає HMAC-SHA256 тіла.

    PCO підписує сире тіло запиту: HMAC-SHA256(authenticity_secret, webhook_body).
    Порівняння виконується constant-time для захисту від timing-атак.

    Args:
        body: Сире тіло POST-запиту (bytes).
        signature_header: Значення заголовка X-PCO-Webhooks-Authenticity.
        secret: Authenticity secret підписки вебхука з PCO.

    Returns:
        True, якщо підпис валідний; False якщо заголовок відсутній або не збігається.
    """
    if not signature_header or not secret:
        return False
    expected = hmac.new(
        secret.encode('utf-8'),
        body,
        digestmod='sha256',
    ).hexdigest()
    return hmac.compare_digest(signature_header, expected)

"""
Rate limiting simples, em memória, por cliente (chave de API).

Aviso honesto: isso funciona para um único processo/instância. Em produção
com múltiplas réplicas, isso precisa virar Redis (INCR + TTL) ou um
gateway de API dedicado (Kong, Apigee, etc.) — deixado como ponto de
extensão explícito, não escondido.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Depends, HTTPException, status

from app.config import get_settings
from app.core.auth import AuthenticatedClient, get_current_client

_WINDOW_SECONDS = 60
_hits: dict[str, deque] = defaultdict(deque)
_lock = Lock()


def _check_and_register(client_id: str, limit_per_minute: int) -> None:
    now = time.monotonic()
    with _lock:
        window = _hits[client_id]
        while window and now - window[0] > _WINDOW_SECONDS:
            window.popleft()
        if len(window) >= limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Limite de {limit_per_minute} requisições por minuto excedido.",
            )
        window.append(now)


async def enforce_rate_limit(
    client: AuthenticatedClient = Depends(get_current_client),
) -> AuthenticatedClient:
    settings = get_settings()
    _check_and_register(client.client_id, settings.rate_limit_per_minute)
    return client

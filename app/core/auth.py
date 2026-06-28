"""
Autenticação por API key.

Em produção, isso seria substituído por OAuth2/mTLS conforme o BSP ou
gateway de API do cliente — API key simples é o suficiente para o MVP
e para demonstrar o ponto de extensão.
"""
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.config import get_settings


@dataclass
class AuthenticatedClient:
    client_id: str
    api_key: str


async def get_current_client(
    x_api_key: str = Header(..., description="Chave de API fornecida ao cliente B2B."),
) -> AuthenticatedClient:
    settings = get_settings()
    client_name = settings.api_keys.get(x_api_key)
    if client_name is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API inválida ou ausente.",
        )
    return AuthenticatedClient(client_id=client_name, api_key=x_api_key)

from src.config.settings import get_setting, Settings

from fastapi import Security, HTTPException, Depends, status
from fastapi.security import APIKeyHeader

from typing import Annotated

API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_apikey(sttg:Annotated[Settings, Depends(get_setting)], x_api_key: str = Security(api_key_header)):
    if x_api_key != sttg.app_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso no autorizado"
        )

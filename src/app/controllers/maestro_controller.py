from src.app.models import maestro_model as mm
from fastapi import APIRouter, Depends, Response, status
from src.config.security import get_apikey
from typing import Annotated

router = APIRouter(
    prefix="/maestro",
    tags=["maestro"],
    dependencies=[Depends(get_apikey)],
    responses={404: {"description":"Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/cargar/manobra")
async def cargar_mano_obra(model: Annotated[dict, Depends(mm.cargar_mano_obra)]):
    return model

@router.post("/cargar/pagos")
async def cargar_mestro_pago(model: Annotated[dict, Depends(mm.cargar_maestro_pagos)]):
    return model

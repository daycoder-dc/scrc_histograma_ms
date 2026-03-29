from fastapi import APIRouter, Depends, Response, status, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config.security import get_apikey
from src.config import database as conn
from src.config import normalize

from typing import Annotated
from loguru import logger
from io import BytesIO

import polars as pl

router = APIRouter(
    prefix="/master",
    tags=["master"],
    dependencies=[Depends(get_apikey)],
    responses={404: {"description":"Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/upload")
async def cargar_mestro_pago(file: Annotated[UploadFile, Form()]):
    content = BytesIO(await file.read())

    pages = [
        {"sheet":"SCR_NORTE-CENTRO", "type": "norte-centro"},
        {"sheet":"SCR_SUR", "type": "sur"}
    ]

    for page in pages:
        logger.info(f"[Maestro - {page.get("sheet")}] archivo leido. ✔️")

        df = pl.read_excel(
            source=content,
            sheet_name=page.get("sheet"),
            engine="calamine",
            read_options={
                "header_row": 0,
                "use_columns": "A:E"
            }
        )

        logger.info(f"[Maestro - {page.get("sheet")}] dataframe cargado. ✔️")

        df.columns = [normalize.text(x) for x in df.columns]

        colums_map = {
            "accion": "accion",
            "estado": "estado",
            "se_paga_si_no": "se_paga",
            "valor_unitario": "valor_unitario",
            "tipo_de_actividad": "tipo_actividad"
        }

        df = df.rename(mapping=colums_map)

        df = df.with_columns(
            pl.col("valor_unitario").cast(pl.Float64, strict=False).fill_null(0),
            pl.lit(page.get("type", pl.String)).alias("zona")
        )

        logger.info(f"[Maestro - {page.get("sheet")}] normalización de columnas. ✔️")

        try:
            logger.info(f"[Maestro - {page.get("seet")}] registrando ⌛")

            df.write_database(
                table_name="maestro_pagos_csr",
                connection=conn.db_uri,
                engine="adbc",
                if_table_exists="append"
            )

            logger.info(f"[Maestro - {page.get("sheet")}] registrado. ✔️")
        except Exception as e:
            logger.error(f"[Maestro - {page.get("sheet")}] error de base de datos. ✖️")
            print(e)

            return JSONResponse(
                content=jsonable_encoder({"status":"error"}),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return JSONResponse(
        content=jsonable_encoder({"status":"registrado"}),
        status_code=status.HTTP_201_CREATED
    )

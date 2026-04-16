from fastapi import APIRouter, Depends, Response, status, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config.security import get_apikey
from src.config import database as conn
from src.config import normalize

from adbc_driver_postgresql import dbapi
from typing import Annotated
from loguru import logger
from io import BytesIO

import polars as pl

router = APIRouter(
    prefix="/v1/map",
    tags=["map"],
    dependencies=[Depends(get_apikey)],
    responses={404: {"description": "Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/upload")
async def upload_file(file:Annotated[UploadFile, Form()]):
    content = BytesIO(await file.read())
    logger.info(f"[Mapa] - archivo leido. ✔️");

    df = pl.read_excel(
        source=content,
        sheet_name="coordenadas atlantico",
        engine="calamine",
        read_options={
            "header_row": 0,
            "use_columns": "A:H"
        }
    )

    logger.info(f"[Dataframe] - cargado ✔️")

    # limpiar nombre de columnas
    df.columns = [normalize.text(c) for c in df.columns]
    logger.info(f"[Dataframe] - columnas normalizadas ✔️")

    # mapa de columnas excel - tabla
    columns_map = {
        "cuenta":"nic",
        "territorial":"zona",
        "eje_x":"longitud",
        "eje_y":"latitud"
    }

    # verifica las columnas existentes en el excel que esten en el map para renombrar
    columns_rename = {k:v for k,v in columns_map.items() if k in df.columns}

    try:
        # renombra las columnas en el dataframe
        df = df.rename(mapping=columns_rename)
        logger.info(f"[Dataframe] columnas renombradas. ✔️")
    except Exception as e:
        logger.error("[Dataframe] - Columnas duplicadas. ✖️")
        logger.error(e)

    # agrega las columnas del mapa que falten en el excel
    for column in set(columns_map.values()):
        if column not in df.columns:
            df = df.with_columns(pl.lit(None, pl.String).alias(column))
            logger.info(f"[Dataframe] - columna ({column}) agregada ✔️")

    # remueve las columnas del excel que no existen en el map
    for column in df.columns:
        if column not in set(columns_map.values()):
            df = df.drop(column)
            logger.info(f"[Dataframe] - columna ({column}) removida. ✔️")

    # normalización de datos
    df = df.with_columns(
        pl.col("nic").cast(pl.String, strict=False),
        pl.col("zona").cast(pl.String, strict=False),
        pl.col("longitud").cast(pl.String, strict=False),
        pl.col("latitud").cast(pl.String, strict=False)
    )

    logger.info(f"[Dataframe] - datos normalizados. ✔️")

    try:
        with dbapi.connect(conn.db_uri) as cnn:
            logger.info(f"[Mapa] - validando datos insertados. ✔️")

            sql = (
                "select * from mapa m "
                "where m.eliminado = false "
                "and m.fecha_registro::date = current_date"
            )

            df_tb = pl.read_database(query=sql, connection=cnn)

            df_mg = df.join(
                df_tb,
                on=["nic", "zona"],
                how="anti"
            )

            logger.info(f"[Mapa] - registrando datos. ⌛")

            df.write_database(
                table_name="mapa",
                connection=cnn,
                engine="adbc",
                if_table_exists="append"
            )

            logger.info(f"[Mapa] - {len(df)} datos registrados. ✔️")

        return JSONResponse(
            content=jsonable_encoder({"status":"registrado"}),
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error(f"[Mapa] - error: {e} ✔️")

    return JSONResponse(
        content=jsonable_encoder({"status": "error"}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

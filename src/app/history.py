from fastapi import APIRouter, Depends, Response, status, UploadFile, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config.security import get_apikey
from adbc_driver_postgresql import dbapi
from src.config import database as conn
from src.config import normalize

from typing import Annotated
from loguru import logger
from io import BytesIO

import polars as pl

router = APIRouter(
    prefix="/v1/history",
    tags=["history"],
    dependencies=[Depends(get_apikey)],
    responses={404: {"description":"Not Found"}}
)

@router.get("/")
async def root():
    return Response(status_code=status.HTTP_200_OK)

@router.post("/upload")
async def upload(file: Annotated[UploadFile, Form()], archivo_id:Annotated[str, Form()]):
    content = BytesIO(await file.read())

    logger.info("[Maestro] archivo leido. ✔️")

    df_mano_obra = pl.read_excel(source=content, read_options={"header_row": 0})

    logger.info("[Maestro] dataframe cargado. ✔️")

    # limpiar nombre de columnas
    df_mano_obra.columns = [normalize.text(c) for c in df_mano_obra.columns]

    # mapa de columnas excel - tabla
    columns_map = {
        "nic": "nic",
        "orden": "orden",
        "contrata": "contrata",
        "territorio": "territorio",
        "zona": "zona",
        "municipio": "municipio",
        "corregimiento": "corregimiento",
        "localidad_barrio": "localidad_barrio",
        "tarifa": "tarifa",
        "tipo_actividad": "tipo_actividad",
        "actividad": "actividad",
        "direccion": "direccion",
        "id_transformador": "id_transformador",
        "id_circuito": "id_circuito",
        "num_medidor": "num_medidor",
        "marca_medidor": "marca_medidor",
        "deuda_act": "deuda_act",
        "deuda_cierre": "deuda_cierre",
        "cant_factura_act": "cant_factura_act",
        "cant_factura_cierre": "cant_factura_cierre",
        "tipo_os": "tipo_os",
        "descripcion_de_tipo_os": "descripcion_tipo_os",
        "tipo_suspension_solicitada": "tipo_suspension_solicitada",
        "tipo_brigada": "tipo_brigada",
        "tipo_operativa": "tipo_brigada",
        "id_tecnico": "id_tecnico",
        "tecnico": "tecnico",
        "av_resultado": "av_resultado",
        "accion": "accion",
        "subaccion_subanomalia": "subaccion_subanomalia",
        "subaccion": "subaccion_subanomalia",
        "estado_osf": "estado_osf",
        "estado_siprem": "estado_siprem",
        "fecha": "fecha",
        "fecha_cierre": "fecha",
        "hora": "hora",
        "hora_fin": "hora"
    }

    # verifica las columnas existente en el archivo excel para renombrar
    columns_rename = {k:v for k,v in columns_map.items() if k in df_mano_obra.columns}

    try:
        # renombrado de columnas
        df_mano_obra = df_mano_obra.rename(mapping=columns_rename)
    except Exception as e:
        logger.error("Columnas duplicada")
        logger.error(e)

    # agrega las columnas del mapa que falten en el excel
    for column in set(columns_map.values()):
        if column not in df_mano_obra.columns:
            df_mano_obra = df_mano_obra.with_columns(
                pl.lit(None, pl.String).alias(column)
            )

    # remueve las columnas del excel que no existen en el map
    for column in df_mano_obra.columns:
        if column not in set(columns_map.values()):
            df_mano_obra = df_mano_obra.drop(column)

    logger.info("[Maestro] columnas renombradas. ✔️")

    df_mano_obra = df_mano_obra.with_columns(
        pl.lit(archivo_id, pl.String).alias("archivo_id"),
        pl.col("nic").cast(pl.String),
        pl.col("orden").cast(pl.String),
        pl.col("id_transformador").cast(pl.String),
        pl.col("id_tecnico").cast(pl.String),
        pl.col("deuda_act").cast(pl.Float64, strict=False),
        pl.col("deuda_cierre").cast(pl.Float64, strict=False),
        pl.col("cant_factura_act").cast(pl.Int32, strict=False),
        pl.col("cant_factura_cierre").cast(pl.Int32, strict=False),
        pl.col("fecha").cast(pl.Date, strict=False)
    )

    # limpieza de datos
    df_mano_obra = df_mano_obra.drop_nulls(subset=["fecha", "tipo_brigada", "tecnico"])
    logger.info("[Maestro] datos limpieados")

    try:
        df_mano_obra = df_mano_obra.with_columns(
            pl.col("hora").str.to_time("%H:%M:%S", strict=False).dt.to_string()
        )
    except Exception as e:
        logger.error("[Maestro] Fallo conversion de hora ❌")

        df_mano_obra = df_mano_obra.with_columns(
            pl.col("hora").cast(pl.Time, strict=False).dt.to_string("%H:%M:%S")
        )

        logger.info("[Maestro] Conversión de hora por cast time ✔️")

    logger.info("[Maestro] casting de columnas. ✔️")

    try:
        with dbapi.connect(conn.db_uri) as cnn:
            logger.info("[Maestro] Validar datos resitrados ⌛")

            sql = (
                "select * from historico h "
                "where h.eliminado = false"
            )

            df_existente = pl.read_database(query=sql, connection=cnn)

            df_insertar = df_mano_obra.join(
                df_existente,
                on=["nic", "orden", "fecha", "hora"],
                how="anti"
            )

            logger.info("[Maestro] datos validados ✔️")
            logger.info("[Maestro] registrando ⌛")

            df_insertar.write_database(
                table_name="historico",
                connection=cnn,
                engine="adbc",
                if_table_exists="append"
            )

            logger.info(f"[Maestro] {len(df_insertar)} datos registrado. ✔️")

        return JSONResponse(
            content=jsonable_encoder({"status":"registrado"}),
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error("[Maestro] error base de datos ✖️")
        print(e)

    return JSONResponse(
        content=jsonable_encoder({"status":"error"}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

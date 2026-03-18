from fastapi import UploadFile, Form, Depends, status
from src.config.database import Session, get_session
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from src.config import database as conn
from typing import Annotated
from loguru import logger
from io import BytesIO

import polars as pl

async def cargar_mano_obra(file: Annotated[UploadFile, Form()], db:Annotated[Session, Depends(get_session)]):
    content = BytesIO(await file.read())

    logger.info("[Maestro] archivo leido. ✔️")

    df_mano_obra = pl.read_excel(
        source=content,
        read_options={
            "header_row": 0,
            "use_columns": "A:AG"
        }
    )

    logger.info("[Maestro] dataframe cargado. ✔️")

    columns = {
        "NIC":"nic",
        "ORDEN":"orden",
        "CONTRATA":"contrata",
        "TERRITORIO":"territorio",
        "ZONA":"zona",
        "MUNICIPIO":"municipio",
        "CORREGIMIENTO":"corregimiento",
        "LOCALIDAD/BARRIO":"localidad_barrio",
        "TARIFA":"tarifa",
        "TIPO ACTIVIDAD":"tipo_actividad",
        "ACTIVIDAD":"actividad",
        "DIRECCION":"direccion",
        "ID_TRANSFORMADOR":"id_transformador",
        "ID_CIRCUITO":"id_circuito",
        "NUM MEDIDOR":"num_medidor",
        "MARCA MEDIDOR":"marca_medidor",
        "DEUDA ACT":"deuda_act",
        "DEUDA CIERRE":"deuda_cierre",
        "CANT FACTURA ACT":"cant_factura_act",
        "CANT FACTURA CIERRE":"cant_factura_cierre",
        "TIPO OS":"tipo_os",
        "DESCRIPCION DE TIPO OS":"descripcion_tipo_os",
        "TIPO SUSPENSION SOLICITADA":"tipo_suspension_solicitada",
        "TIPO BRIGADA":"tipo_brigada",
        "ID TECNICO":"id_tecnico",
        "TECNICO":"tecnico",
        "AV/RESULTADO":"av_resultado",
        "ACCION":"accion",
        "SUBACCION/SUBANOMALIA":"subaccion_subanomalia",
        "ESTADO OSF":"estado_osf",
        "ESTADO SIPREM":"estado_siprem",
        "FECHA":"fecha",
        "HORA":"hora"
    }

    df_mano_obra = df_mano_obra.rename(mapping=columns)

    logger.info("[Maestro] columnas renombradas. ✔️")

    df_mano_obra = df_mano_obra.with_columns(
        pl.col("nic").cast(pl.String),
        pl.col("orden").cast(pl.String),
        pl.col("id_transformador").cast(pl.String),
        pl.col("id_tecnico").cast(pl.String),
        pl.col("deuda_act").cast(pl.Float64, strict=False),
        pl.col("deuda_cierre").cast(pl.Float64, strict=False),
        pl.col("cant_factura_act").cast(pl.Int32, strict=False),
        pl.col("cant_factura_cierre").cast(pl.Int32, strict=False),
        pl.col("hora").cast(pl.Time, strict=False).dt.to_string("%H:%M:%S")
    )

    logger.info("[Maestro] casting de columnas. ✔️")

    logger.info("[Maestro] registrando ⌛")

    try:
        df_mano_obra.write_database(
            table_name="maestro_mano_obra",
            connection=conn.db_uri,
            engine="adbc",
            if_table_exists="append"
        )

        logger.info("[Maestro] datos registrado. ✔️")
    except Exception as e:
        logger.error("[Maestro] error base de datos ✖️")
        print(e)

    return JSONResponse(
        content=jsonable_encoder({"status":"registrado"}),
        status_code=status.HTTP_201_CREATED
    )

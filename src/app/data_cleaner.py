from fastapi import APIRouter, Depends, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.config.security import get_apikey
from adbc_driver_postgresql import dbapi
from src.config import database as conn

import polars as pl

router = APIRouter(
    prefix="/v1/data-cleaner",
    tags=["data-cleaner"],
    dependencies=[Depends(get_apikey)],
    responses={404: {"description":"Not Found"}}
)

@router.get("/")
async def index():
    try:
        with dbapi.connect(conn.db_uri) as cnn:
            columns = ["nic", "orden", "fecha", "hora"]
            print("✅ Consultando historico ⌛")
            sql = "select * from historico h where h.eliminado = false;"
            df = pl.read_database(query=sql, connection=cnn)
            print(f"✅ Total datos: {len(df)}")

            df_unico = df.unique(subset=columns, keep="first")
            print(f"✅ Total limpios: {len(df_unico)}")

            print(f"✅ Eliminando ⌛")
            df_unico.write_database(
                table_name="historico",
                connection=cnn,
                engine="adbc",
                if_table_exists="replace"
            )

            print(f"✅ Tota eliminados: {len(df) - len(df_unico)}")

        return JSONResponse(
            content=jsonable_encoder({"status":"success"}),
            status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        logger.error("[Maestro] error base de datos ✖️")
        print(e)

    return JSONResponse(
        content=jsonable_encoder({"status":"error"}),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

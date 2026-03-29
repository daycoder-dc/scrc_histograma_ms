from src.config.settings import get_setting
from src.app import history
from src.app import master

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import FastAPI, status

import uvicorn

app = FastAPI(
    title = "scrc histograma microservice",
    root_path = "/api/v1"
)

app.add_middleware(
    GZipMiddleware,
    compresslevel=5
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

app.include_router(history.router)
app.include_router(master.router)

@app.get("/")
async def root():
    response = {
        "service": "scrc_histograma_ms",
        "status": "running"
    }

    return JSONResponse(
        content=jsonable_encoder(response),
        status_code=status.HTTP_200_OK
    )

if __name__ == "__main__":
    settings = get_setting()
    uvicorn.run(app, host="0.0.0.0", port=settings.app_port)

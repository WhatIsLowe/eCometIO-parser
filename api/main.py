from fastapi import FastAPI
from db.postgres import AsyncPostgres
from endpoints import router
import logging

from settings import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

logging.basicConfig(level=logging.INFO)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    app.state.db = AsyncPostgres(db_host=POSTGRES_HOST, db_port=POSTGRES_PORT, db_name=POSTGRES_DB,
                                 db_user=POSTGRES_USER, db_pass=POSTGRES_PASSWORD)

    await app.state.db.connect()
    logging.info("Database connected")
    await app.state.db.create_tables()
    logging.info("Tables created or connected")

#
@app.on_event("shutdown")
async def shutdown_event():
    await app.state.db.close()

app.include_router(router, prefix="/api")

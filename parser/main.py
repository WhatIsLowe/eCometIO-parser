import asyncio
import logging

from db.postgres import ParserPostgres
from parser import GithubParser
from settings import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    db = ParserPostgres(db_host=POSTGRES_HOST, db_port=POSTGRES_PORT, db_name=POSTGRES_DB, db_user=POSTGRES_USER,
                        db_pass=POSTGRES_PASSWORD)
    await db.connect()
    logging.info("Connected to DB")
    parser = GithubParser(db)
    await parser.parse_and_save_data()
    logging.info("Data successfully saved to DB")
    await db.close()
    logging.info("DB connection closed")


def handler(event, context):
    # Запуск асинхронной функции main и ожидание ее выполнения
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # Возврат ответа об успешном выполнении
    return {'statusCode': 200, 'body': 'Successfully parsed data'}


if __name__ == "__main__":
    asyncio.run(main())

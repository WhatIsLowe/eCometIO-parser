import logging

import asyncpg

class AsyncPostgres:
    """ Класс для работы с PostgreSQL базой данных. """
    def __init__(self, db_host: str, db_port: int | str, db_name: str, db_user: str, db_pass: str):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.pool = None

    async def connect(self):
        """ Открывает соединение с БД. """
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_pass
            )
            logging.info("Connected to PostgreSQL")
        except asyncpg.PostgresError as e:
            logging.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def execute(self, query: str, *params):
        """ Выполняет SQL запросы. """
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    return await conn.fetch(query, *params)
        except asyncpg.PostgresError as e:
            logging.error(f"Database query failed: {e}")
            raise

    async def create_tables(self):
        """ Создает (если нет) таблицы и триггер функцию. """
        # Запрос для создания таблицы top_repos для хранения данных репозиториев.
        create_top_repos_table = """
            CREATE TABLE IF NOT EXISTS top_repos (
                id SERIAL PRIMARY KEY,
                repo TEXT NOT NULL,
                owner TEXT NOT NULL,
                position_cur INTEGER,
                position_prev INTEGER,
                stars INTEGER NOT NULL,
                watchers INTEGER NOT NULL,
                forks INTEGER NOT NULL,
                open_issues INTEGER NOT NULL,
                language TEXT,
                snapshot_date DATE NOT NULL
            );
        """

        # Запрос для создания таблицы repo_activity для хранения данных активности репозитория.
        create_repo_activity_table = """
            CREATE TABLE IF NOT EXISTS repo_activity (
                id SERIAL PRIMARY KEY,
                repo_id INTEGER REFERENCES top_repos(id) NOT NULL,
                date DATE NOT NULL,
                commits INTEGER NOT NULL,
                authors TEXT[] NOT NULL
            );
        """

        # Запрос для объявления триггер функции, которая присваивает полю position_prev (предыдущая позиция в топе)
        # старое значение position_cur
        create_top_repos_function = """
            CREATE OR REPLACE FUNCTION update_position_prev() RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.position_cur IS DISTINCT FROM OLD.position_cur THEN
                    NEW.position_prev := OLD.position_cur;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """

        # Запрос для создания триггера на основе функции update_position_prev и запускает ее
        # при обновленни значения position_cur (текущей позииции в топе)
        create_top_repos_trigger = """
            CREATE TRIGGER update_position_prev_trigger
            BEFORE UPDATE ON top_repos FOR EACH ROW
            WHEN (OLD.position_cur IS NOT NULL)
            EXECUTE PROCEDURE update_position_prev();
        """

        try:
            # Выполняет объявленные запросы к БД
            await self.execute(create_top_repos_table)
            await self.execute(create_repo_activity_table)
            await self.execute(create_top_repos_function)
            await self.execute(create_top_repos_trigger)
        except asyncpg.PostgresError as e:
            logging.error("Failed to create tables: {e}")
            raise


    async def close(self):
        """ Закрывает соединение с БД. """
        self.pool.close()
        logging.info(f"Closing connection to PostgreSQL database")

    async def get_top_repos(self):
        """ Запрашивает и возвращает топ-100 репозиториев. """
        try:
            result = await self.execute(
                """ 
                    SELECT * FROM top_repos
                    WHERE snapshot_date = CURRENT_DATE - 1
                    ORDER BY position_cur
                """
            )
            if not result:
                return []
            return result
        except asyncpg.PostgresError as e:
            logging.error("Failed to get top_repos: {e}")
            raise

    async def get_repo_activity(self, repo, since_date, until_date):
        """ Запрашивает и возвращает активность репозитория за указанный период.

        :param repo: Полное название репозитория.
        :param since_date: Дата начала периода.
        :param until_date: Дата окончания периода."""

        # Проверяет наличие репозитория в БД. Если нет возвращает None
        try:
            repo_data = await self.execute(
                "SELECT id FROM top_repos WHERE repo = $1", repo
            )

            if not repo_data:
                return None

            repo_id = repo_data[0]["id"]

            # Запрашивает данные активности за указанный период
            result = await self.execute(
                """
                SELECT * FROM repo_activity
                WHERE repo_id = $1 AND date BETWEEN $2 AND $3
                ORDER BY date
                """, repo_id, since_date, until_date
            )

            # if not result:
            #     return []

            return result
        except Exception as e:
            logging.error(f"Failed to get repo_activity from DB: {e}")
            raise
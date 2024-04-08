import asyncpg
import logging


class ParserPostgres:
    def __init__(self, db_host, db_port, db_name, db_user, db_pass):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.pool = None

    async def connect(self):
        """ Подключиться к PostgreSQL базе """

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
            logging.error(f"Error connecting to PostgreSQL: {e}")
            raise

    async def execute(self, query, *params):
        """ Выполнить запрос.

        :param query: SQL запрос.
        :param params: параметры SQL запроса.
        """

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    return await conn.fetch(query, *params)
        except asyncpg.PostgresError as e:
            logging.error(f"Database query error: {e}")
            raise

    async def close(self):
        """ Закрыть соединение с PostgreSQL базой. """

        await self.pool.close()
        logging.info("Closed connection to PostgreSQL")

    async def get_repo_id_by_name_and_owner(self, repo_name):
        """ Получить id репозитория.

            :param repo_name: Полное название репозитория ("{owner}/{repo_name}").
        """
        try:
            return await self.execute(
                "SELECT id FROM top_repos WHERE repo=$1", repo_name
            )
        except asyncpg.PostgresError as e:
            logging.error(f"Error getting repo ID: {e}")
            raise

    async def get_last_activity_date(self, repo_id):
        """ Получить дату последнего действия в репозитории из БД.

            :param repo_id: ID репозитория из БД.
        """
        try:
            result = await self.execute(
                """
                    SELECT MAX(date) AS last_activity_date
                    FROM repo_activity
                    WHERE repo_id=$1
                """, repo_id
            )
            if result and result[0]['last_activity_date']:
                return result[0]['last_activity_date']
            return None
        except asyncpg.PostgresError as e:
            logging.error(f"Error getting repo last activity date: {e}")
            raise

    async def insert_repo(self, repo_data):
        """ Вставить данные репозитория в БД.

            :param repo_data : (models.Repo) Данные репозитория.
        """
        try:
            await self.execute(
                """
                    INSERT INTO top_repos (repo, owner, position_cur, stars, watchers, forks, open_issues, language, snapshot_date)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_DATE - 1)
                """,
                repo_data['repo'],  # 1
                repo_data['owner'],         # 2
                repo_data['position_cur'],  # 3
                repo_data['stars'],         # 4
                repo_data['watchers'],      # 5
                repo_data['forks'],         # 6
                repo_data['open_issues'],   # 7
                repo_data['language']       # 8
            )
            logging.info(f"Inserted repo: {repo_data['repo']}")
        except asyncpg.PostgresError as e:
            logging.error(f"Error inserting repo ({repo_data.model_json()}): {e}")
            raise

    async def update_repo(self, repo_id, repo_data):
        """ Обновить данные репозитория.

            :param repo_id : ID репозитория.
            :param repo_data : (models.Repo) Данные репозитория.
        """
        try:
            await self.execute(
                """
                    UPDATE top_repos
                    SET position_cur = $1,
                        stars = $2,
                        watchers = $3,
                        forks = $4,
                        open_issues = $5,
                        language = $6,
                        snapshot_date = CURRENT_DATE - 1
                    WHERE id = $7
                """,
                repo_data['position_cur'],  # 1
                repo_data['stars'],                 # 2
                repo_data['watchers'],              # 3
                repo_data['forks'],                 # 4
                repo_data['open_issues'],           # 5
                repo_data['language'],              # 6
                repo_id                             # 7
            )
            logging.info(f"Updated repo: {repo_data['repo']}")
        except asyncpg.PostgresError as e:
            logging.error(f"Error updating repo (ID: {repo_id}): {e}")
            raise

    async def insert_repo_activity(self, repo_id, activity_data):
        """ Вставить данные активности репозитория.

            :param repo_id : ID репозитория.
            :param activity_data : (models.Activity) Данные активности репозитория.
        """
        try:
            await self.execute(
                """
                    INSERT INTO repo_activity (repo_id, date, commits, authors)
                    VALUES ($1, $2, $3, $4)
                """,
                repo_id,
                activity_data['date'],
                activity_data['commits'],
                list(activity_data['authors'])
            )

        except asyncpg.PostgresError as e:
            logging.error(f"Error inserting repo activity (ID: {repo_id}): {e}")
            raise
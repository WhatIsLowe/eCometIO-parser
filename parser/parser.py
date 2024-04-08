import asyncio
import logging
from datetime import datetime, timedelta

import aiohttp
from dateutil import parser

from db.postgres import ParserPostgres
from models import Repo, Activity
from settings import GITHUB_TOP_REPOS_ENDPOINT, GITHUB_REPO_ACTIVITY_ENDPOINT, HEADERS

import json


class GithubParser:
    def __init__(self, db: ParserPostgres):
        self.db = db

    async def parse_and_save_data(self):
        """ Точка входа, запуска парсинга """
        async with aiohttp.ClientSession() as session:
            top_repos = await self._get_top_repos(session)
            await self._process_repos(session, top_repos)

    async def _get_top_repos(self, session: aiohttp.ClientSession):
        """ Запрашивает данные топ 100 репозиториев из GitHub """
        async with session.get(GITHUB_TOP_REPOS_ENDPOINT, headers=HEADERS) as response:
            response.raise_for_status()
            data = await response.json()
            return data['items']

    async def _process_repos(self, session: aiohttp.ClientSession, repos):
        """ Обрабатывает данные репозиториев
        :param session: aiohttp.ClientSession
        :param repos: Данные репозиториев"""
        for i, repo_data in enumerate(repos):
            repo = Repo(
                repo=repo_data['full_name'],
                owner=repo_data['owner']['login'],
                position_cur=i+1,
                position_prev=None,
                stars=repo_data['stargazers_count'],
                watchers=repo_data['watchers'],
                forks=repo_data['forks'],
                open_issues=repo_data['open_issues'],
                language=repo_data['language'] or None
            )

            await self._update_or_insert_repo(repo)
            await self._process_repo_activity(session, repo)

    async def _update_or_insert_repo(self, repo: Repo):
        """ Проверяет наличие репозитория в БД и вставляет / обновляет данные

        :param repo: Данные репозитория"""
        existing_repo = await self.db.get_repo_id_by_name_and_owner(repo.repo)
        if existing_repo:
            await self.db.update_repo(existing_repo[0]['id'], repo.dict())
        else:
            await self.db.insert_repo(repo.dict())

    async def _process_repo_activity(self, session: aiohttp.ClientSession, repo: Repo):
        """ Обрабатывает данные активности репозитория

        :param session: aiohttp.ClientSession
        :param repo: данные репозитория """
        # Получает ID репозитория из БД
        repo_data = await self.db.get_repo_id_by_name_and_owner(repo.repo)
        repo_id = repo_data[0]['id']

        # Получает дату последней активности в этом репозитории
        last_activity_date = await self.db.get_last_activity_date(repo_id)
        # Устанавливает значение since (дата последней активности + 1 день) если дата есть, иначе None
        since = last_activity_date + timedelta(days=1) if last_activity_date else None
        # Получает активность репозитория
        activities = await self._get_repo_commits(session, repo, since)
        await self._save_repo_activity(repo_id, activities)

    async def _get_last_activity_date(self, repo_id):
        """ Получает дату последней активности репозитория из БД

        :param repo_id: ID репозитория """
        result = await self.db.get_last_activity_date(repo_id)
        return result

    async def _get_repo_commits(self, session, repo: Repo, since=None):
        # Если since = None - оставляет параметр пустым, иначе - дата (дата последней активности + 1 день)
        params = {'since': since.isoformat()} if since else {}

        # Запрашивает через GitHub API активность репозитория, передавая параметр since (если установлен)
        async with session.get(f"{GITHUB_REPO_ACTIVITY_ENDPOINT}/{repo.repo}/commits", params=params, headers=HEADERS) as response:
            response.raise_for_status()
            commits = await response.json()

            # Словарь для хранения данных о коммитах
            commits_by_date = {}
            # Итерирует по каждому коммиту из полученного ответа
            for commit in commits:
                # Парсит дату коммита и преобразует ее в объект date
                commit_date = parser.parse(commit['commit']['author']['date']).date()
                # Если даты коммита еще нет в словаре - инициализирует запись
                if commit_date not in commits_by_date:
                    commits_by_date[commit_date] = {
                        'date': commit_date,    # Дата коммита
                        'commits': 0,           # Счетчик кол-ва коммитов
                        'authors': set(),       # Множество авторов
                    }
                # Увеличивает счетчик коммитов для каждой даты
                commits_by_date[commit_date]['commits'] += 1
                # Добавляет автора во множество авторов
                commits_by_date[commit_date]['authors'].add(commit["commit"]['author']['name'])

            # Возвращает список значений словаря, содержащий информацию о коммитах по дням
            return list(commits_by_date.values())

    async def _save_repo_activity(self, repo_id, activities):
        """ Сохрвняет активность репозитория в БД.

         :param repo_id: ID репозитория в БД.
         :param activities: models.Activities Данные активности репозитория """
        for activity in activities:
            await self.db.insert_repo_activity(repo_id, activity)
import datetime

from pydantic import BaseModel
from typing import Optional


class Repo(BaseModel):
    """ Модель данных репозитория """
    repo: str
    owner: str
    position_cur: int
    position_prev: Optional[int]
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Optional[str]
#

class Activity(BaseModel):
    """ Модель данных активности """
    date: datetime.date
    commits: int
    authors: list[str]
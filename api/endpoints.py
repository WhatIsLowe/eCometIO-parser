import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from typing import List

from db.postgres import AsyncPostgres
from models import Repo, Activity

router = APIRouter()


def get_db(request: Request):
    return request.app.state.db


@router.get("/repos/top100", response_model=List[Repo])
async def get_top100_repos(db: AsyncPostgres = Depends(get_db)):
    try:
        top_repos_data = await db.get_top_repos()
        top_repos = [Repo(**repo_data) for repo_data in top_repos_data]
        return top_repos
    except Exception as e:
        logging.error(f"Error getting top100: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/{owner}/{repo}/activity", response_model=List[Activity])      # /{owner}/{repo_name}/activity?since={date1}&until={date2}
async def get_repo_activity(owner: str, repo: str, since: str = None, until: str = None, db: AsyncPostgres = Depends(get_db)):
    # Проверяет что параметры since и until не пусты
    if not since or not until:
        raise HTTPException(status_code=400, detail="Invalid parameters. Please provide since and until.")

    # Приводит since и until к объекту date
    try:
        since_date = datetime.strptime(since, "%Y-%m-%d").date()
        until_date = datetime.strptime(until, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    try:
        repo = f"{owner}/{repo}"
        activity_data = await db.get_repo_activity(repo, since_date, until_date)
        if activity_data is None:
            raise HTTPException(status_code=404, detail="Repository does not found.")

        activity = [Activity(**data) for data in activity_data]
        return activity
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error.")

import os

# GITHUB

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

GITHUB_TOP_REPOS_ENDPOINT = "https://api.github.com/search/repositories?q=stars:%3E1&sort=stars&per_page=100"
GITHUB_REPO_ACTIVITY_ENDPOINT = "https://api.github.com/repos"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
}

# POSTGRES
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
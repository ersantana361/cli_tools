import os
import requests
from github import Github

def get_github_instance() -> Github:
    """
    Returns an authenticated Github instance using the GITHUB_TOKEN_WORK environment variable.
    """
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN_WORK")
    if not GITHUB_TOKEN:
        raise Exception("🚫 GITHUB_TOKEN_WORK environment variable not set")
    return Github(GITHUB_TOKEN)

def get_pr_diff(pr_url: str) -> str:
    """
    Fetches the diff (patch) for a pull request from a private repository.
    Expected PR URL format: https://github.com/{owner}/{repo}/pull/{pr_number}
    """
    print("🔍 Fetching PR diff from GitHub...")
    github_instance = get_github_instance()
    parts = pr_url.rstrip("/").split("/")
    if len(parts) < 7:
        raise Exception("🚫 Invalid PR URL format")
    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])
    repository = github_instance.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)

    api_url = pr.url
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN_WORK')}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"🚫 Error fetching diff: {response.status_code} {response.text}")

    print("✅ PR diff fetched successfully!")
    return response.text

def fetch_current_description(pr_url: str) -> str:
    """
    Fetches the current PR description (body) from GitHub.
    """
    github_instance = get_github_instance()
    parts = pr_url.rstrip("/").split("/")
    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])
    repository = github_instance.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    return pr.body if pr.body else "No description provided."

def update_pr_description(pr_url: str, new_body: str):
    """
    Updates the PR description with new content.
    """
    github_instance = get_github_instance()
    parts = pr_url.rstrip("/").split("/")
    owner = parts[3]
    repo = parts[4]
    pr_number = int(parts[6])
    repository = github_instance.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    pr.edit(body=new_body)

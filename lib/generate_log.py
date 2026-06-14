from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import os
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Commit:
    hash: str
    short_hash: str
    author: str
    date: str
    subject: str


def _run_git(args, repo_path):
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout


def get_repository_root(repo_path=None):
    start_path = Path(repo_path or ".").resolve()
    output = _run_git(["rev-parse", "--show-toplevel"], start_path)
    return Path(output.strip())


def get_remote_url(repo_path=None, remote="origin"):
    repo_root = get_repository_root(repo_path)
    return _run_git(["remote", "get-url", remote], repo_root).strip()


def parse_github_remote(remote_url):
    remote_url = remote_url.strip()
    if remote_url.startswith("git@github.com:"):
        repository_path = remote_url.split(":", 1)[1]
    elif remote_url.startswith("https://github.com/"):
        repository_path = remote_url.split("https://github.com/", 1)[1]
    elif remote_url.startswith("http://github.com/"):
        repository_path = remote_url.split("http://github.com/", 1)[1]
    else:
        raise ValueError("Remote URL is not a GitHub repository URL")

    repository_path = repository_path.removesuffix(".git")
    owner, repository = repository_path.split("/", 1)
    return owner, repository


def build_github_commits_url(remote_url, max_count=None):
    owner, repository = parse_github_remote(remote_url)
    url = f"https://api.github.com/repos/{owner}/{repository}/commits"
    if max_count is not None:
        url = f"{url}?per_page={max_count}"
    return url


def get_repository_commits(repo_path=None, max_count=None):
    repo_root = get_repository_root(repo_path)
    args = ["log"]
    if max_count is not None:
        args.extend(["-n", str(max_count)])
    args.append("--pretty=format:%H%x1f%h%x1f%an%x1f%aI%x1f%s")

    output = _run_git(args, repo_root)
    commits = []
    for line in output.splitlines():
        commit_hash, short_hash, author, date, subject = line.split("\x1f")
        commits.append(
            Commit(
                hash=commit_hash,
                short_hash=short_hash,
                author=author,
                date=date,
                subject=subject,
            )
        )
    return commits


def fetch_repository_commits(repo_path=None, max_count=None, github_token=None):
    remote_url = get_remote_url(repo_path)
    api_url = build_github_commits_url(remote_url, max_count)
    token = github_token or os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "course-7-module-6-pip-pypi-scripting-lab",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(api_url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as error:
        raise RuntimeError(f"Could not fetch repository commits: {error}") from error

    commits = []
    for item in payload:
        commit = item["commit"]
        message = commit["message"].splitlines()[0]
        commits.append(
            Commit(
                hash=item["sha"],
                short_hash=item["sha"][:7],
                author=commit["author"]["name"],
                date=commit["author"]["date"],
                subject=message,
            )
        )
    return commits


def format_commits(commits):
    return "\n".join(
        f"{commit.short_hash} {commit.date} {commit.author}: {commit.subject}"
        for commit in commits
    )


def generate_log(data, repo_path=None, include_commits=False, commit_count=None, commit_source="local"):
    if not isinstance(data, list):
        raise ValueError("data must be a list")

    filename = f"log_{datetime.now().strftime('%Y%m%d')}.txt"
    log_lines = [str(entry) for entry in data]

    if include_commits:
        if commit_source == "local":
            commits = get_repository_commits(repo_path, commit_count)
        elif commit_source == "github":
            commits = fetch_repository_commits(repo_path, commit_count)
        else:
            raise ValueError("commit_source must be 'local' or 'github'")
        if commits:
            log_lines.extend(["", "Repository commits:"])
            log_lines.extend(format_commits(commits).splitlines())

    with open(filename, "w") as file:
        for line in log_lines:
            file.write(f"{line}\n")

    print(f"Log written to {filename}")
    return filename


if __name__ == "__main__":
    log_data = ["User logged in", "User updated profile", "Report exported"]
    generate_log(log_data, include_commits=True, commit_source="github")

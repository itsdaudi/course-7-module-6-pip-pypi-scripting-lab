# testing/test_generate_log.py

import os
import pytest
from datetime import datetime
import lib.generate_log as generate_log_module
from lib.generate_log import (
    Commit,
    build_github_commits_url,
    fetch_repository_commits,
    format_commits,
    generate_log,
    get_repository_commits,
    parse_github_remote,
)

@pytest.fixture
def log_data():
    return ["Entry one", "Entry two", "Entry three"]

@pytest.fixture
def generated_file(log_data):
    filename = generate_log(log_data)
    yield filename
    if os.path.exists(filename):
        os.remove(filename)

def test_log_file_created(generated_file):
    """Test that the log file is created with today's date in the filename."""
    assert os.path.exists(generated_file), f"{generated_file} not found."

def test_log_file_name_format(generated_file):
    """Test that the filename follows the expected naming convention."""
    today = datetime.now().strftime("%Y%m%d")
    assert generated_file == f"log_{today}.txt", "Filename does not match expected format."

def test_log_file_content_matches_input(generated_file, log_data):
    """Test that the content written to the log matches the input list."""
    with open(generated_file, "r") as file:
        lines = [line.strip() for line in file.readlines()]
    assert lines == log_data, "Log file contents do not match input data."

def test_generate_log_raises_error_on_invalid_input():
    """Test that the function raises a ValueError when input is not a list."""
    with pytest.raises(ValueError):
        generate_log("This should be a list")

def test_empty_log_list_creates_empty_file():
    """Test that passing an empty list still creates an empty log file."""
    filename = generate_log([])
    with open(filename, "r") as file:
        content = file.read()
    assert content == ""
    os.remove(filename)


def test_generate_log_can_include_repository_commits(generated_file, log_data):
    """Test that the log can include commit history from the repository."""
    commits = get_repository_commits(max_count=2)
    generate_log(log_data, include_commits=True, commit_count=2)

    with open(generated_file, "r") as file:
        content = file.read()

    assert "Repository commits:" in content
    assert format_commits(commits) in content


def test_generate_log_rejects_invalid_input():
    """Test that invalid input raises a clear error."""
    with pytest.raises(ValueError, match="data must be a list"):
        generate_log("This should be a list")


def test_parse_github_remote_https_url():
    """Test parsing a GitHub HTTPS remote URL."""
    assert parse_github_remote("https://github.com/itsdaudi/course-7-module-6-pip-pypi-scripting-lab.git") == (
        "itsdaudi",
        "course-7-module-6-pip-pypi-scripting-lab",
    )


def test_parse_github_remote_ssh_url():
    """Test parsing a GitHub SSH remote URL."""
    assert parse_github_remote("git@github.com:itsdaudi/course-7-module-6-pip-pypi-scripting-lab.git") == (
        "itsdaudi",
        "course-7-module-6-pip-pypi-scripting-lab",
    )


def test_build_github_commits_url():
    """Test building a GitHub commits API URL."""
    url = build_github_commits_url(
        "https://github.com/itsdaudi/course-7-module-6-pip-pypi-scripting-lab.git",
        max_count=2,
    )
    assert url == "https://api.github.com/repos/itsdaudi/course-7-module-6-pip-pypi-scripting-lab/commits?per_page=2"


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'''[
            {
                "sha": "abc123def456",
                "commit": {
                    "author": {
                        "name": "Audi",
                        "date": "2026-06-14T00:00:00Z"
                    },
                    "message": "Initial commit"
                }
            }
        ]'''


def test_fetch_repository_commits(monkeypatch):
    """Test fetching commits from the GitHub API."""
    monkeypatch.setattr(
        generate_log_module,
        "get_remote_url",
        lambda repo_path=None: "https://github.com/itsdaudi/course-7-module-6-pip-pypi-scripting-lab.git",
    )

    def fake_urlopen(request, timeout=30):
        assert request.full_url == "https://api.github.com/repos/itsdaudi/course-7-module-6-pip-pypi-scripting-lab/commits?per_page=1"
        assert request.get_header("User-agent") == "course-7-module-6-pip-pypi-scripting-lab"
        assert request.get_header("Authorization") == "Bearer test-token"
        return FakeResponse()

    monkeypatch.setattr(generate_log_module, "urlopen", fake_urlopen)

    commits = fetch_repository_commits(max_count=1, github_token="test-token")

    assert commits == [
        Commit(
            hash="abc123def456",
            short_hash="abc123d",
            author="Audi",
            date="2026-06-14T00:00:00Z",
            subject="Initial commit",
        )
    ]

import subprocess
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage

from commitpilot import cli, llm


def sh(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """An empty repo as the working directory, isolated from the user's git config."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "repo"
    root.mkdir()
    sh("init", "-q", "-b", "main", cwd=root)
    for k, v in [
        ("user.name", "Test"),
        ("user.email", "t@example.com"),
        ("commit.gpgsign", "false"),
    ]:
        sh("config", k, v, cwd=root)
    monkeypatch.chdir(root)
    return root


def write(root: Path, path: str, text: str) -> None:
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def commit_all(root: Path, message: str = "chore: initial") -> None:
    sh("add", "-A", cwd=root)
    sh("commit", "-q", "-m", message, cwd=root)


def log(root: Path) -> list[str]:
    return sh("log", "--format=%s", cwd=root).splitlines()


class FakeChat:
    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list = []

    def invoke(self, msgs):
        self.calls.append(msgs)
        return AIMessage(self.replies.pop(0))


@pytest.fixture
def model(monkeypatch):
    def install(*replies: str) -> FakeChat:
        fake = FakeChat(list(replies))
        monkeypatch.setattr(llm, "chat_model", lambda: fake)
        return fake

    return install


@pytest.fixture
def keys(monkeypatch):
    """Feed menu choices; also pretend stdin is a terminal."""

    def install(*answers: str) -> list[str]:
        queue = list(answers)
        monkeypatch.setattr(cli, "interactive", lambda: True)
        monkeypatch.setattr(cli, "choose", lambda prompt, k: queue.pop(0))
        return queue

    return install

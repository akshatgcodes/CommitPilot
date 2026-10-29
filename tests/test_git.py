import pytest

from commitpilot import git
from commitpilot.diff import parse
from tests.conftest import commit_all, log, sh, write


def test_split_keeps_partial_staging(repo):
    write(repo, "app.py", "a = 1\nb = 2\n")
    write(repo, "README.md", "# App\n")
    commit_all(repo)
    # Stage one change to app.py, then make another that stays unstaged
    write(repo, "app.py", "a = 10\nb = 2\n")
    sh("add", "app.py", cwd=repo)
    write(repo, "app.py", "a = 10\nb = 20\n")
    write(repo, "README.md", "# App\n\nUsage.\n")
    write(repo, "new.txt", "brand new\n")
    sh("add", "README.md", "new.txt", cwd=repo)

    files = {f.path: f for f in parse(git.staged_patch())}
    done = git.split_commit(
        [
            ("feat: change a", [files["app.py"]]),
            ("docs: add usage", [files["README.md"], files["new.txt"]]),
        ]
    )
    assert len(done) == 2
    assert log(repo)[:2] == ["docs: add usage", "feat: change a"]
    assert sh("show", "HEAD~1:app.py", cwd=repo) == "a = 10\nb = 2\n"  # only the staged part
    assert (repo / "app.py").read_text() == "a = 10\nb = 20\n"  # unstaged edit untouched
    assert sh("diff", "--staged", cwd=repo) == ""
    assert not git.backup_path().exists()


def test_split_works_before_the_first_commit(repo):
    write(repo, "src/a.py", "a = 1\n")
    write(repo, "README.md", "hi\n")
    sh("add", "-A", cwd=repo)
    files = {f.path: f for f in parse(git.staged_patch())}
    git.split_commit(
        [("feat: add a", [files["src/a.py"]]), ("docs: add readme", [files["README.md"]])]
    )
    assert log(repo) == ["docs: add readme", "feat: add a"]


def test_failed_split_restages_the_rest(repo):
    write(repo, "a.py", "a\n")
    write(repo, "b.py", "b\n")
    commit_all(repo)
    write(repo, "a.py", "a2\n")
    write(repo, "b.py", "b2\n")
    sh("add", "-A", cwd=repo)
    # A hook that rejects the second commit
    hook = repo / ".git" / "hooks" / "commit-msg"
    hook.write_text('#!/bin/sh\ngrep -q "^docs" "$1" && exit 1\nexit 0\n')
    hook.chmod(0o755)
    files = {f.path: f for f in parse(git.staged_patch())}
    with pytest.raises(git.GitError, match="Stopped at commit 2 of 2") as e:
        git.split_commit([("feat: a", [files["a.py"]]), ("docs: b", [files["b.py"]])])
    assert "staged again" in str(e.value)
    assert log(repo)[0] == "feat: a"
    assert sh("diff", "--staged", "--name-only", cwd=repo).split() == ["b.py"]
    assert git.backup_path().exists()


def test_not_a_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(git.GitError, match="Not inside a git repository"):
        git.repo_root()

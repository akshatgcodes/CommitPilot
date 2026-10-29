import json

import pytest

from commitpilot import cli, llm
from tests.conftest import commit_all, log, sh, write


@pytest.fixture
def staged(repo):
    write(repo, "api/limit.py", "def limit():\n    return 100\n")
    write(repo, "README.md", "# Service\n")
    commit_all(repo)
    write(
        repo,
        "api/limit.py",
        "def limit(user):\n" + "".join(f"    # rule {i}\n" for i in range(60)) + "    return 100\n",
    )
    write(repo, "tests/test_limit.py", "def test_limit():\n    assert True\n")
    write(repo, "README.md", "# Service\n\n" + "Rate limits apply.\n" * 30)
    sh("add", "-A", cwd=repo)
    return repo


def test_accept(staged, model, keys, capsys):
    fake = model("feat(api): limit requests per user")
    keys("y")
    assert cli.main(["commit"]) == 0
    assert log(staged)[0] == "feat(api): limit requests per user"
    out = capsys.readouterr().out
    assert "3 staged files" in out and "Consider [s] to split" in out
    prompt = fake.calls[0][1].content
    assert (
        "Recent commits in this repo:\n- chore: initial" in prompt and "### api/limit.py" in prompt
    )


def test_bad_format_is_retried(staged, model, keys):
    fake = model("Updated the limiter.", "fix(api): pass the user to the limiter")
    keys("y")
    cli.main(["commit"])
    assert log(staged)[0] == "fix(api): pass the user to the limiter"
    assert "Fix these" in fake.calls[1][1].content


def test_emoji_style_edit_and_regenerate(staged, model, keys, monkeypatch):
    model("feat(api): add limits", "feat(api): limit requests per user")
    keys("r", "e", "y")
    monkeypatch.setattr(cli, "edit", lambda text: text + " (per minute)")
    cli.main(["commit", "--style", "emoji"])
    assert log(staged)[0] == "✨ api: limit requests per user (per minute)"


def test_cancel_and_dry_run_commit_nothing(staged, model, keys):
    model("feat: x", "feat: y")
    keys("n")
    assert cli.main(["commit"]) == 1
    assert cli.main(["commit", "--dry-run"]) == 0
    assert log(staged) == ["chore: initial"]


def test_split_from_menu(staged, model, keys):
    plan = {
        "commits": [
            {
                "files": ["api/limit.py", "tests/test_limit.py"],
                "message": "feat(api): limit requests per user",
            },
            {"files": ["README.md"], "message": "docs: describe rate limits"},
        ]
    }
    fake = model("feat: everything", "Here you go:\n" + json.dumps(plan))
    keys("s", "y")
    assert cli.main(["commit"]) == 0
    assert log(staged)[:2] == ["docs: describe rate limits", "feat(api): limit requests per user"]
    assert "A rough grouping by folder" in fake.calls[1][1].content


def test_invalid_plan_falls_back_to_folders(staged, model, capsys):
    bad = json.dumps({"commits": [{"files": ["api/limit.py"], "message": "feat: a"}]})
    model(bad, bad, "feat(api): limit requests per user", "docs: describe rate limits")
    assert cli.main(["commit", "--split", "--yes"]) == 0
    assert log(staged)[:2] == ["docs: describe rate limits", "feat(api): limit requests per user"]
    assert "grouped by folder instead" in capsys.readouterr().out


def test_message_command_prints_only(staged, model, capsys):
    model("feat(api): limit requests per user")
    assert cli.main(["message"]) == 0
    assert capsys.readouterr().out.strip() == "feat(api): limit requests per user"
    assert log(staged) == ["chore: initial"]


def test_refuses_without_terminal(staged, model, monkeypatch):
    model("feat: x")
    monkeypatch.setattr(cli, "interactive", lambda: False)
    assert cli.main(["commit"]) == 1


def test_nothing_staged(repo, capsys):
    assert cli.main(["commit"]) == 2
    assert "Nothing is staged" in capsys.readouterr().err


def test_missing_key_is_explained(repo, capsys, monkeypatch):
    write(repo, "a.py", "a\n")
    sh("add", "a.py", cwd=repo)
    for var in ("LLM_API_KEY", "GROQ_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    # Don't read the developer's real config file
    monkeypatch.setitem(llm.Settings.model_config, "env_file", None)
    assert cli.main(["message"]) == 2
    assert "No API key" in capsys.readouterr().err

import pytest

from commitpilot import messages


@pytest.mark.parametrize(
    "raw,clean",
    [
        ("feat(api): add rate limits", "feat(api): add rate limits"),
        ("```\nfix: handle empty input\n```", "fix: handle empty input"),
        ('"docs: explain install"', "docs: explain install"),
        ("Commit message:\nchore: tidy", "chore: tidy"),
        ("feat: x\n\nWhy it matters.\n", "feat: x\n\nWhy it matters."),
        ("feat: x\nbody right after", "feat: x\n\nbody right after"),
        (
            "feat(api): add per\u2011IP limits \u2014 \u201cfast\u201d",
            'feat(api): add per-IP limits - "fast"',
        ),
    ],
)
def test_clean(raw, clean):
    assert messages.clean(raw) == clean


@pytest.mark.parametrize(
    "msg,count",
    [
        ("feat(auth): rotate refresh tokens", 0),
        ("feat!: drop python 3.10", 0),
        ("fix(api): handle HTTP 304 responses", 0),
        ("Added a thing", 1),
        ("feature: add x", 1),
        ("feat: Add x.", 2),
        ("feat: " + "x" * 80, 1),
        ("feat: add x\nno blank line", 1),
        ("API: something", 1),
    ],
)
def test_problems(msg, count):
    assert len(messages.problems(msg)) == count, messages.problems(msg)


def test_emoji_style():
    assert messages.to_emoji("feat(api): add rate limits") == "✨ api: add rate limits"
    assert messages.to_emoji("docs: fix typo\n\nbody") == "📝 fix typo\n\nbody"
    assert messages.to_emoji("refactor!: rename config") == "💥 rename config"
    assert messages.to_emoji("not conventional") == "not conventional"

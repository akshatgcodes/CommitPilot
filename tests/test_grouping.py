from commitpilot import grouping
from commitpilot.diff import FileDiff


def f(path: str, changed: int = 10) -> FileDiff:
    return FileDiff(path, None, "modified", False, changed, 0, "")


def labels(paths):
    return {
        k: [x.path for x in v] for k, v in grouping.heuristic_groups([f(p) for p in paths]).items()
    }


def test_areas():
    assert grouping.area("README.md") == "docs"
    assert grouping.area("docs/setup.md") == "docs"
    assert grouping.area("requirements-dev.txt") == "deps"
    assert grouping.area("pyproject.toml") == "deps"
    assert grouping.area(".github/workflows/ci.yml") == "ci"
    assert grouping.area("Makefile") == "root"
    assert grouping.area("backend/app/main.py") == "backend/app"
    assert grouping.area("api/limit.py") == "api"


def test_tests_follow_their_code_and_lockfiles_follow_manifests():
    assert labels(
        [
            "api/limit.py",
            "tests/test_limit.py",
            "README.md",
            "pyproject.toml",
            "uv.lock",
            "web/src/App.tsx",
            "web/src/App.test.tsx",
        ]
    ) == {
        "api": ["api/limit.py", "tests/test_limit.py"],
        "docs": ["README.md"],
        "deps": ["pyproject.toml", "uv.lock"],
        "web": ["web/src/App.tsx", "web/src/App.test.tsx"],
    }


def test_orphan_tests_stay_in_their_folder():
    assert labels(["tests/test_misc.py"]) == {"tests": ["tests/test_misc.py"]}


def test_looks_mixed_needs_size_and_spread():
    assert not grouping.looks_mixed([f("api/a.py", 200)])
    assert not grouping.looks_mixed([f("api/a.py", 5), f("README.md", 5)])
    assert grouping.looks_mixed([f("api/a.py", 60), f("README.md", 30)])


def test_check_plan():
    files = [f("a.py"), f("b.py"), f("c.md")]
    assert grouping.check_plan([{"files": ["a.py", "b.py"]}, {"files": ["c.md"]}], files) == []
    errors = grouping.check_plan([{"files": ["a.py", "a.py", "x.py"]}, {"files": []}], files)
    assert any("not staged: x.py" in e for e in errors)
    assert any("left out: b.py, c.md" in e for e in errors)
    assert any("more than one commit: a.py" in e for e in errors)
    assert any("commit 2 has no files" in e for e in errors)

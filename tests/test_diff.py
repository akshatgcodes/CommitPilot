from commitpilot import git
from commitpilot.diff import condensed, parse
from tests.conftest import commit_all, sh, write


def test_parse_real_diff(repo):
    write(repo, "keep.py", "a = 1\nb = 2\n")
    write(repo, "gone.py", "x = 1\n")
    write(repo, "old name.py", "\n".join(f"line {i}" for i in range(20)) + "\n")
    commit_all(repo)
    write(repo, "keep.py", "a = 1\nb = 3\nc = 4\n")
    (repo / "gone.py").unlink()
    (repo / "src").mkdir()
    sh("mv", "old name.py", "src/new name.py", cwd=repo)
    write(repo, "logo.png", "")
    (repo / "logo.png").write_bytes(b"\x89PNG\x00\x01\x02")
    write(repo, "a b/c.txt", "spaces\n")
    sh("add", "-A", cwd=repo)

    files = {f.path: f for f in parse(git.staged_patch())}
    assert set(files) == {"keep.py", "gone.py", "src/new name.py", "logo.png", "a b/c.txt"}
    assert (files["keep.py"].status, files["keep.py"].added, files["keep.py"].removed) == (
        "modified",
        2,
        1,
    )
    assert files["gone.py"].status == "deleted" and files["gone.py"].removed == 1
    assert (
        files["src/new name.py"].status == "renamed"
        and files["src/new name.py"].old_path == "old name.py"
    )
    assert files["logo.png"].binary and files["logo.png"].status == "added"
    assert files["a b/c.txt"].status == "added"
    assert all(f.patch.startswith("diff --git ") and f.patch.endswith("\n") for f in files.values())


def test_condensed_summarises_lockfiles_binaries_and_big_files(repo):
    write(repo, "uv.lock", "x\n" * 500)
    (repo / "img.bin").write_bytes(bytes(range(256)))
    write(repo, "big.py", "".join(f"value_{i} = {i}\n" for i in range(400)))
    write(repo, "late.py", "late = 1\n")
    sh("add", "-A", cwd=repo)
    text = condensed(parse(git.staged_patch()), budget=3000, per_file=1000)
    assert "### uv.lock (added, +500 -0)\n(lockfile, contents omitted)" in text
    assert "(binary file)" in text
    assert "… (truncated)" in text and "value_399" not in text
    assert "### late.py" in text

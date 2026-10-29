"""Thin wrappers around the git CLI."""

import subprocess
from pathlib import Path

from commitpilot.diff import FileDiff


class GitError(Exception):
    pass


def run(*args: str, input: str | None = None, cwd: str | None = None) -> str:
    try:
        proc = subprocess.run(
            ["git", "-c", "core.quotePath=false", *args],
            input=input,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except FileNotFoundError as e:
        raise GitError("git isn't installed or isn't on PATH") from e
    if proc.returncode != 0:
        raise GitError((proc.stderr or proc.stdout).strip() or f"git {args[0]} failed")
    return proc.stdout


def repo_root() -> Path:
    try:
        return Path(run("rev-parse", "--show-toplevel").strip())
    except GitError as e:
        raise GitError("Not inside a git repository") from e


def staged_patch() -> str:
    # --binary so binary files can be re-applied in split mode; -M to see renames
    return run("diff", "--staged", "--binary", "--no-color", "--no-ext-diff", "-M")


def has_head() -> bool:
    try:
        run("rev-parse", "--verify", "-q", "HEAD")
        return True
    except GitError:
        return False


def recent_subjects(n: int = 10) -> list[str]:
    if not has_head():
        return []
    return [s for s in run("log", f"-n{n}", "--format=%s").splitlines() if s.strip()]


def commit(message: str) -> str:
    """Commit the index with this message (hooks run as usual). Returns git's summary."""
    out = run("commit", "-F", "-", input=message + "\n")
    return out.strip().splitlines()[0] if out.strip() else ""


def backup_path() -> Path:
    return Path(run("rev-parse", "--absolute-git-dir").strip()) / "commitpilot-backup.patch"


def _apply(files: list[FileDiff]) -> None:
    if files:
        run("apply", "--cached", "--whitespace=nowarn", input="".join(f.patch for f in files))


def split_commit(plan: list[tuple[str, list[FileDiff]]]) -> list[str]:
    """Make one commit per (message, files) entry from what's currently staged.

    The staged patch is saved first, the index is reset, then each group's exact patch
    is applied to the index and committed. If anything fails, everything not yet
    committed is put back in the index, and the backup stays on disk.
    """
    backup = backup_path()
    backup.write_text(staged_patch())
    if has_head():
        run("reset", "-q")
    else:
        run("read-tree", "--empty")

    done: list[str] = []
    for i, (message, files) in enumerate(plan):
        applied = False
        try:
            _apply(files)
            applied = True
            done.append(commit(message))
        except GitError as e:
            # If the commit itself failed, this group is already in the index
            rest = [f for _, fs in plan[i + 1 if applied else i :] for f in fs]
            try:
                _apply(rest)
                restored = "The remaining changes are staged again."
            except GitError:
                restored = f"Restore them with: git apply --cached {backup}"
            raise GitError(
                f"Stopped at commit {i + 1} of {len(plan)}: {e}\n"
                f"{len(done)} commit(s) were made. {restored}"
            ) from e
    backup.unlink(missing_ok=True)
    return done

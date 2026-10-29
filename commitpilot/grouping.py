"""Guess which staged files belong together, without a model.

Used to warn that a diff mixes unrelated work, as the hint given to the model when it
plans a split, and as the fallback plan if the model's answer doesn't check out.
"""

import re

from commitpilot.diff import LOCKFILES, FileDiff

MANIFESTS = {
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
}
CONTAINERS = {"src", "app", "lib", "packages", "apps", "backend", "frontend", "services"}
MIXED_MIN_LINES = 80


def _stem(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    name = re.sub(r"^test_|_test(?=\.)|\.(test|spec)(?=\.)", "", name)
    return name.split(".", 1)[0].lower()


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return bool(
        re.search(r"(^|/)(tests?|__tests__|spec)/", path)
        or re.match(r"test_.+\.py$", name)
        or re.search(r"(_test\.(py|go)|\.(test|spec)\.[jt]sx?)$", name)
    )


def area(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    parts = path.split("/")
    if name in MANIFESTS or name.startswith("requirements"):
        return "deps"
    if parts[0] == "docs" or name.endswith((".md", ".rst", ".txt")):
        return "docs"
    if parts[0] == ".github":
        return "ci"
    if len(parts) == 1:
        return "root"
    if parts[0] in CONTAINERS and len(parts) > 2:
        return f"{parts[0]}/{parts[1]}"
    return parts[0]


def heuristic_groups(files: list[FileDiff]) -> dict[str, list[FileDiff]]:
    """area label -> files, in the order areas first appear."""
    groups: dict[str, list[FileDiff]] = {}
    sources = {_stem(f.path): area(f.path) for f in files if not _is_test(f.path)}
    for f in files:
        if f.name in LOCKFILES:
            key = "deps"
        elif _is_test(f.path) and _stem(f.path) in sources:
            key = sources[_stem(f.path)]  # a test travels with the code it tests
        else:
            key = area(f.path)
        groups.setdefault(key, []).append(f)
    return groups


def looks_mixed(files: list[FileDiff]) -> bool:
    """Big enough and spread across separate areas to be worth splitting."""
    return len(heuristic_groups(files)) >= 2 and sum(f.changed for f in files) >= MIXED_MIN_LINES


def check_plan(plan: list[dict], files: list[FileDiff]) -> list[str]:
    """A split plan must use every staged file exactly once and nothing else."""
    staged = [f.path for f in files]
    seen: list[str] = []
    errors = []
    for i, commit in enumerate(plan, 1):
        paths = commit.get("files") or []
        if not paths:
            errors.append(f"commit {i} has no files")
        seen += paths
    unknown = sorted(set(seen) - set(staged))
    missing = sorted(set(staged) - set(seen))
    dupes = sorted({p for p in seen if seen.count(p) > 1})
    if unknown:
        errors.append(f"not staged: {', '.join(unknown)}")
    if missing:
        errors.append(f"left out: {', '.join(missing)}")
    if dupes:
        errors.append(f"in more than one commit: {', '.join(dupes)}")
    return errors

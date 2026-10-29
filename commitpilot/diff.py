"""Split `git diff --staged` output into one record per file.

Each record keeps its exact patch text, which is what split mode re-applies to the
index, so partially staged files are committed exactly as staged.
"""

import re
from dataclasses import dataclass

LOCKFILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
    "composer.lock",
    "Gemfile.lock",
}


@dataclass
class FileDiff:
    path: str
    old_path: str | None
    status: str  # added | deleted | modified | renamed
    binary: bool
    added: int
    removed: int
    patch: str

    @property
    def name(self) -> str:
        return self.path.rsplit("/", 1)[-1]

    @property
    def is_lockfile(self) -> bool:
        return self.name in LOCKFILES

    @property
    def changed(self) -> int:
        return self.added + self.removed


def _header_paths(line: str) -> tuple[str, str]:
    # "diff --git a/P b/Q". When P == Q (the usual case) the split point is exact even
    # if the path contains " b/"; renames are corrected from "rename from/to" lines.
    rest = line[len("diff --git a/") :]
    half = (len(rest) - len(" b/")) // 2
    if rest[half : half + 3] == " b/" and rest[:half] == rest[half + 3 :]:
        return rest[:half], rest[:half]
    a, _, b = rest.partition(" b/")
    return a, b


def parse(patch: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    chunks = re.split(r"(?m)^(?=diff --git )", patch)
    for chunk in chunks:
        if not chunk.startswith("diff --git "):
            continue
        lines = chunk.split("\n")
        old, new = _header_paths(lines[0])
        status, binary, added, removed = "modified", False, 0, 0
        in_hunk = False
        for line in lines[1:]:
            if in_hunk:
                if line.startswith("+"):
                    added += 1
                elif line.startswith("-"):
                    removed += 1
                continue
            if line.startswith("new file mode"):
                status = "added"
            elif line.startswith("deleted file mode"):
                status = "deleted"
            elif line.startswith("rename from "):
                old, status = line[len("rename from ") :], "renamed"
            elif line.startswith("rename to "):
                new = line[len("rename to ") :]
            elif line.startswith("GIT binary patch") or line.startswith("Binary files "):
                binary = True
            elif line.startswith("@@"):
                in_hunk = True
        files.append(
            FileDiff(
                path=new,
                old_path=old if status == "renamed" else None,
                status=status,
                binary=binary,
                added=added,
                removed=removed,
                patch=chunk if chunk.endswith("\n") else chunk + "\n",
            )
        )
    return files


def condensed(files: list[FileDiff], budget: int = 20_000, per_file: int = 2_500) -> str:
    """The diff as the model sees it: lockfiles and binaries summarised, big files cut,
    and once the budget is spent, only stats for the rest."""
    out: list[str] = []
    used = 0
    for f in files:
        head = f"### {f.path} ({f.status}, +{f.added} -{f.removed})"
        if f.old_path:
            head += f" renamed from {f.old_path}"
        if f.binary:
            out.append(f"{head}\n(binary file)")
            continue
        if f.is_lockfile:
            out.append(f"{head}\n(lockfile, contents omitted)")
            continue
        body = f.patch.split("\n@@", 1)
        hunks = "@@" + body[1] if len(body) == 2 else ""
        if used >= budget:
            out.append(f"{head}\n(diff omitted: too large)")
            continue
        if len(hunks) > per_file:
            hunks = hunks[:per_file] + "\n… (truncated)"
        used += len(hunks)
        out.append(f"{head}\n{hunks}")
    return "\n\n".join(out)

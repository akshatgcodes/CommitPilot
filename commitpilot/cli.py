"""`pilot`: commit messages from the staged diff.

pilot commit            suggest a message, then accept / edit / regenerate / split
pilot commit --split    go straight to the split plan
pilot message           just print a suggestion (for scripts and hooks)
"""

import argparse
import os
import shlex
import subprocess
import sys
import tempfile

from commitpilot import git, grouping, llm, messages
from commitpilot.diff import FileDiff, parse

COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if COLOR else text


def bold(t: str) -> str:
    return c(t, "1")


def dim(t: str) -> str:
    return c(t, "2")


def green(t: str) -> str:
    return c(t, "32")


def yellow(t: str) -> str:
    return c(t, "33")


def red(t: str) -> str:
    return c(t, "31")


# --- interaction (tests replace these) ------------------------------------------------


def interactive() -> bool:
    return sys.stdin.isatty()


def choose(prompt: str, keys: str) -> str:
    """Read one of `keys` from stdin; empty input picks the first."""
    while True:
        try:
            answer = input(f"{prompt} > ").strip().lower()
        except EOFError:
            return "n"
        if not answer:
            return keys[0]
        if answer[0] in keys:
            return answer[0]
        print(f"Type one of: {', '.join(keys)}")


def edit(text: str) -> str:
    """Open the user's git editor on `text`; lines starting with # are dropped."""
    editor = git.run("var", "GIT_EDITOR").strip() or os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile("w+", suffix=".COMMIT_EDITMSG", delete=False) as f:
        f.write(text + "\n\n# Edit the message. Lines starting with # are ignored.\n")
        path = f.name
    try:
        subprocess.run([*shlex.split(editor), path], check=True)
        with open(path) as f:
            lines = [line for line in f.read().splitlines() if not line.startswith("#")]
    finally:
        os.unlink(path)
    return "\n".join(lines).strip()


# --- helpers --------------------------------------------------------------------------


def styled(message: str, style: str) -> str:
    return messages.to_emoji(message) if style == "emoji" else message


def summary(files: list[FileDiff]) -> str:
    added = sum(f.added for f in files)
    removed = sum(f.removed for f in files)
    n = len(files)
    return f"{n} staged file{'s' if n != 1 else ''} ({green(f'+{added}')} {red(f'-{removed}')})"


def show_message(message: str) -> None:
    header, _, body = message.partition("\n")
    print(f"{green('✅ Suggested:')} {bold(header)}")
    for line in body.strip("\n").splitlines():
        print(f"   {dim(line)}")


def show_plan(plan: list[tuple[str, list[FileDiff]]]) -> None:
    n = len(plan)
    print(bold(f"✂  Split into {n} commits:" if n > 1 else "✂  One commit:"))
    for i, (message, files) in enumerate(plan, 1):
        print(f" {i}. {bold(message.splitlines()[0])}")
        print(f"    {dim(', '.join(f.path for f in files))}")


# --- commands -------------------------------------------------------------------------


def load() -> tuple[list[FileDiff], list[str]]:
    git.repo_root()
    files = parse(git.staged_patch())
    if not files:
        raise git.GitError("Nothing is staged. Stage changes with `git add` first.")
    return files, git.recent_subjects()


def run_split(files: list[FileDiff], recent: list[str], args) -> int:
    print(dim("🧭 Grouping the changes..."))
    plan, source = llm.plan_split(files, recent)
    plan = [(styled(m, args.style), fs) for m, fs in plan]
    if source == "heuristic":
        print(
            yellow(
                "The model's grouping didn't cover the files cleanly; grouped by folder instead."
            )
        )
    if len(plan) == 1:
        print("These changes belong together, so it's a single commit.")
    show_plan(plan)
    if args.dry_run:
        return 0
    while not args.yes:
        key = choose(
            f"[{bold('y')}] Commit all  [{bold('e')}] Edit messages  [{bold('n')}] Cancel", "yen"
        )
        if key == "n":
            print("Cancelled. Nothing was committed and your staged changes are as they were.")
            return 1
        if key == "y":
            break
        plan = [(edit(m) or m, fs) for m, fs in plan]
        show_plan(plan)
    for line in git.split_commit(plan):
        print(line)
    return 0


def cmd_commit(args) -> int:
    files, recent = load()
    print(f"📋 Analyzing {summary(files)}...")
    if args.split:
        return run_split(files, recent, args)

    message = styled(llm.suggest(files, recent), args.style)
    show_message(message)
    if grouping.looks_mixed(files):
        areas = ", ".join(grouping.heuristic_groups(files))
        print(yellow(f"⚠  This touches separate areas ({areas}). Consider [s] to split it."))
    if args.dry_run:
        return 0
    if args.yes:
        print(git.commit(message))
        return 0
    if not interactive():
        print(red("Not a terminal: pass --yes to commit, or use `pilot message`."))
        return 1

    while True:
        key = choose(
            f"[{bold('y')}] Accept  [{bold('e')}] Edit  [{bold('r')}] Regenerate  "
            f"[{bold('s')}] Split into multiple commits  [{bold('n')}] Cancel",
            "yersn",
        )
        if key == "y":
            print(git.commit(message))
            return 0
        if key == "n":
            print("Cancelled. Nothing was committed.")
            return 1
        if key == "s":
            return run_split(files, recent, args)
        if key == "e":
            edited = edit(message)
            if not edited:
                print("Empty message; keeping the previous one.")
            else:
                message = edited
                issues = messages.problems(message) if args.style != "emoji" else []
                if issues:
                    print(yellow(f"Note: {'; '.join(issues)}"))
        if key == "r":
            hint = "Write a different message from the previous one: " + message.splitlines()[0]
            message = styled(llm.suggest(files, recent, hint=hint), args.style)
        show_message(message)


def cmd_message(args) -> int:
    files, recent = load()
    print(styled(llm.suggest(files, recent), args.style))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pilot",
        description="Commit messages written from your staged diff.",
        epilog=f"API key: LLM_API_KEY (or GROQ_API_KEY) in the environment, {llm.CONFIG_FILE}, "
        "or ./.env. LLM_PROVIDER picks groq (default), openai or ollama.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--style",
            choices=["conventional", "emoji"],
            default=os.environ.get("PILOT_STYLE", "conventional"),
            help="conventional: feat(api): ...  emoji: ✨ api: ...",
        )

    p = sub.add_parser("commit", help="suggest a message and commit")
    common(p)
    p.add_argument(
        "--split", action="store_true", help="plan separate commits for unrelated changes"
    )
    p.add_argument("-y", "--yes", action="store_true", help="commit without asking")
    p.add_argument("--dry-run", action="store_true", help="show the suggestion, don't commit")
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser("message", help="print a suggested message only")
    common(p)
    p.set_defaults(func=cmd_message)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (git.GitError, llm.LLMError) as e:
        print(red(f"✖ {e}"), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130

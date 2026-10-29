"""Ask the model for a message, or for a split plan, and check what comes back."""

import json
import re
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic_settings import BaseSettings, SettingsConfigDict

from commitpilot import grouping, messages
from commitpilot.diff import FileDiff, condensed

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "ollama": ("http://localhost:11434/v1", "llama3.2"),
}
CONFIG_FILE = Path.home() / ".config" / "commitpilot" / "config.env"


class Settings(BaseSettings):
    # The user-wide file first, then a .env in the current directory
    model_config = SettingsConfigDict(env_file=(CONFIG_FILE, ".env"), extra="ignore")

    llm_provider: str = "groq"
    llm_api_key: str = ""
    groq_api_key: str = ""
    llm_model: str = ""
    llm_base_url: str = ""


class LLMError(Exception):
    pass


def chat_model() -> BaseChatModel:
    """Tests replace this with a fake."""
    from langchain_openai import ChatOpenAI

    s = Settings()
    base, model = PROVIDERS.get(s.llm_provider, PROVIDERS["openai"])
    key = s.llm_api_key or s.groq_api_key or ("ollama" if s.llm_provider == "ollama" else "")
    if not key:
        raise LLMError(
            f"No API key. Put LLM_API_KEY=... (or GROQ_API_KEY) in {CONFIG_FILE} "
            "or export it. See `pilot --help`."
        )
    return ChatOpenAI(
        base_url=s.llm_base_url or base,
        model=s.llm_model or model,
        api_key=key,
        temperature=0.2,
        timeout=60,
    )


SYSTEM = """You write git commit messages in the Conventional Commits format.

Format:
type(scope): subject

optional body

Rules:
- type is one of: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- scope is optional: a short lowercase area name (a module, package or folder). Reuse \
scopes seen in the recent commits when they fit.
- subject: imperative mood ("add", not "added"/"adds"), lowercase first letter, no period, \
header at most 72 characters
- Describe what the change does for the project, not which lines changed.
- Add a body only when the reason or impact isn't obvious from the header: at most 3 \
lines, wrapped at 72 columns, saying why rather than restating the diff. Never mention \
file names.
- Reply with the message only. No code fences, no quotes, no explanation.

Examples:
diff: adds refresh-token rotation to auth/tokens.py and a test
feat(auth): rotate refresh tokens on every use

diff: fixes off-by-one in pagination in api/list.py
fix(api): return the last page when total is a multiple of page size

diff: README install section rewritten
docs: explain installing with pipx

diff: bumps fastapi in pyproject.toml and uv.lock
build(deps): bump fastapi to 0.115

diff: renames helper and updates callers, no behaviour change
refactor(utils): rename parse_dt to parse_datetime"""

SPLIT_SYSTEM = (
    SYSTEM.split("\n\nExamples:")[0]
    + """

The staged changes may mix unrelated work. Group the files into separate commits, one \
per logical change. A bug fix, a new feature, a refactor and a docs or CI change are \
separate commits even when they sit in the same folder; the folder grouping below is \
only a starting point. Keep tests with the code they test, and lockfiles with their \
manifest. Docs and dependency changes that describe or support a code change belong \
in that change's commit; give them their own commit only when they're about something \
else. Don't split one change across commits; one commit is fine if it's all one change.

Reply with JSON only, no code fences:
{"commits": [{"files": ["path", ...], "message": "type(scope): subject"}]}
Every staged file must appear in exactly one commit."""
)


def _context(files: list[FileDiff], recent: list[str]) -> str:
    parts = []
    if recent:
        parts.append("Recent commits in this repo:\n" + "\n".join(f"- {s}" for s in recent))
    parts.append("Staged changes:\n\n" + condensed(files))
    return "\n\n".join(parts)


def _ask(system: str, user: str) -> str:
    try:
        reply = chat_model().invoke([SystemMessage(system), HumanMessage(user)])
    except LLMError:
        raise
    except Exception as e:
        raise LLMError(f"The model call failed: {e}") from e
    return reply.content if isinstance(reply.content, str) else str(reply.content)


def suggest(files: list[FileDiff], recent: list[str], hint: str = "") -> str:
    """One commit message, retried once if it breaks the format rules."""
    user = _context(files, recent) + (f"\n\nAlso: {hint}" if hint else "")
    message = messages.clean(_ask(SYSTEM, user))
    issues = messages.problems(message)
    if issues:
        retry = f"{user}\n\nYour last answer was:\n{message}\nFix these: {'; '.join(issues)}"
        message = messages.clean(_ask(SYSTEM, retry))
    return message


def _parse_plan(text: str) -> list[dict]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in the reply")
    data = json.loads(m.group(0))
    commits = data.get("commits")
    if not isinstance(commits, list):
        raise ValueError("'commits' is missing")
    return [
        {"files": list(c.get("files") or []), "message": str(c.get("message", ""))} for c in commits
    ]


def plan_split(
    files: list[FileDiff], recent: list[str]
) -> tuple[list[tuple[str, list[FileDiff]]], str]:
    """Returns ([(message, files)], source) where source is 'model' or 'heuristic'.

    The model's plan is used only if it covers every staged file exactly once; one retry
    with the errors, then fall back to grouping by area and asking for each message.
    """
    by_path = {f.path: f for f in files}
    groups = grouping.heuristic_groups(files)
    hint = "A rough grouping by folder, which you may improve:\n" + "\n".join(
        f"- {label}: {', '.join(f.path for f in fs)}" for label, fs in groups.items()
    )
    user = f"{_context(files, recent)}\n\n{hint}"
    for _ in range(2):
        try:
            plan = _parse_plan(_ask(SPLIT_SYSTEM, user))
            errors = grouping.check_plan(plan, files)
        except (ValueError, json.JSONDecodeError) as e:
            errors = [str(e)]
        if not errors:
            out = []
            for c in plan:
                msg = messages.clean(c["message"])
                group = [by_path[p] for p in c["files"]]
                if messages.problems(msg):
                    msg = suggest(group, recent)
                out.append((msg, group))
            return out, "model"
        user += f"\n\nThat plan was invalid: {'; '.join(errors)}. Try again."
    return [(suggest(fs, recent), fs) for fs in groups.values()], "heuristic"

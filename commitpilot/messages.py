"""Conventional Commits: check a message, tidy up model output, and convert to emoji style."""

import re

TYPES = {
    "feat": "✨",
    "fix": "🐛",
    "docs": "📝",
    "style": "🎨",
    "refactor": "♻️",
    "perf": "⚡",
    "test": "🧪",
    "build": "📦",
    "ci": "👷",
    "chore": "🔧",
    "revert": "⏪",
}
MAX_HEADER = 72

_ASCII = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
)

HEADER = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<bang>!)?: (?P<subject>\S.*)$"
)


def clean(raw: str) -> str:
    """Strip what models wrap around a message: code fences, quotes, a label line."""
    # Models like typographic hyphens and quotes; commit logs are read in terminals
    text = raw.strip().translate(_ASCII)
    text = re.sub(r"^```[a-z]*\n?|\n?```$", "", text).strip()
    text = re.sub(r"^(?:commit message|message|suggested)\s*:\s*\n?", "", text, flags=re.I)
    lines = text.split("\n")
    header = lines[0].strip()
    # Drop quotes only when they wrap the whole header
    if len(header) > 1 and header[0] == header[-1] and header[0] in "`\"'":
        header = header[1:-1].strip()
    body = "\n".join(line.rstrip() for line in lines[1:]).strip()
    return f"{header}\n\n{body}" if body else header


def problems(message: str) -> list[str]:
    header = message.split("\n", 1)[0]
    m = HEADER.match(header)
    if not m:
        return ["header must look like 'type(scope): subject'"]
    out = []
    if m["type"] not in TYPES:
        out.append(f"unknown type '{m['type']}' (use one of {', '.join(TYPES)})")
    if len(header) > MAX_HEADER:
        out.append(f"header is {len(header)} characters (max {MAX_HEADER})")
    if m["subject"].endswith("."):
        out.append("subject ends with a period")
    if m["subject"][0].isupper() and not m["subject"].split()[0].isupper():
        out.append("subject starts with a capital letter")
    lines = message.split("\n")
    if len(lines) > 1 and lines[1].strip():
        out.append("second line must be blank")
    return out


def to_emoji(message: str) -> str:
    """'feat(api): add x' -> '✨ api: add x' (the style these portfolio repos use)."""
    header, _, rest = message.partition("\n")
    m = HEADER.match(header)
    if not m:
        return message
    emoji = "💥" if m["bang"] else TYPES.get(m["type"], "🔧")
    scope = f"{m['scope']}: " if m["scope"] else ""
    return f"{emoji} {scope}{m['subject']}" + (f"\n{rest}" if rest else "")

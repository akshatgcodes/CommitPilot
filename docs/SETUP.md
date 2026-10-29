# Setup

## Requirements

- Python 3.11–3.13 and git
- An API key for an OpenAI-compatible provider. [Groq](https://console.groq.com/keys) is the default and has a free tier.

## Install

With pip, as the original plan describes:

```bash
pip install -r requirements.txt
python /path/to/CommitPilot/pilot.py commit     # run from inside the repo you're committing to
```

With uv, for development:

```bash
uv sync
uv run pilot commit
```

As a command on your PATH (see [DEPLOY.md](DEPLOY.md)):

```bash
uv tool install .      # or: pipx install .
pilot commit
```

## Configuration

Read from the environment first, then `~/.config/commitpilot/config.env`, then `./.env` in the current directory.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | empty | API key for the provider |
| `GROQ_API_KEY` | empty | used if `LLM_API_KEY` is empty |
| `LLM_PROVIDER` | `groq` | `groq`, `openai` or `ollama` (no key needed) |
| `LLM_MODEL` | per provider | groq `openai/gpt-oss-120b` · openai `gpt-4o-mini` · ollama `llama3.2` |
| `LLM_BASE_URL` | per provider | any other OpenAI-compatible endpoint |
| `PILOT_STYLE` | `conventional` | `emoji` for `✨ api: add x` style |

```bash
mkdir -p ~/.config/commitpilot
echo 'GROQ_API_KEY=gsk_...' > ~/.config/commitpilot/config.env
chmod 600 ~/.config/commitpilot/config.env
```

Groq has been tested end to end. The OpenAI and Ollama presets use the same client but haven't been run against those services yet.

## CLI reference

| Command | What it does |
|---|---|
| `pilot commit` | suggest a message, then `y` accept · `e` edit · `r` regenerate · `s` split · `n` cancel |
| `pilot commit --split` | plan separate commits, then `y` commit all · `e` edit messages · `n` cancel |
| `pilot message` | print a suggestion only |

| Flag | Meaning |
|---|---|
| `--style conventional\|emoji` | message style (also `PILOT_STYLE`) |
| `-y`, `--yes` | commit without asking (needed when stdin isn't a terminal) |
| `--dry-run` | show the suggestion or plan, commit nothing |

Exit codes: `0` committed or shown, `1` cancelled, `2` git or model error (nothing staged, not a repo, no key, API failure), `130` Ctrl-C.

The editor is whatever `git var GIT_EDITOR` returns (`GIT_EDITOR`, `core.editor`, `VISUAL`, `EDITOR`, then `vi`).

## If a split stops halfway

A commit can fail mid-split, for example when a `commit-msg` hook rejects it. CommitPilot stops, keeps the commits already made, and stages the remaining changes again. If restaging fails too, it prints the command to restore them from `.git/commitpilot-backup.patch`.

## Checks

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest          # no network or API key needed
```

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>

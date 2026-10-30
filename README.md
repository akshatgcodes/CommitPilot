<p align="center">
  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24"
       fill="none" stroke="#f05033" stroke-width="1.5"
       stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <line x1="3" x2="9" y1="12" y2="12"/>
    <line x1="15" x2="21" y1="12" y2="12"/>
  </svg>
</p>

<h1 align="center">CommitPilot</h1>

<p align="center">
  <strong>Run <code>pilot commit</code> instead of <code>git commit -m</code>. It reads your staged diff, writes a Conventional Commits message, and when the diff mixes unrelated work, offers to split it into separate commits.</strong>
</p>

<p align="center">
  <a href="https://commitpilot.akshatgcodes.in">
    <img src="https://img.shields.io/badge/website-f05033-f05033?style=flat-square" alt="Website">
  </a>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Groq-F55036?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/license-GPL--3.0-f05033?style=flat-square" alt="License">
</p>

---

## What is CommitPilot?

A small AI-powered git CLI. It sends a condensed version of `git diff --staged` and your recent commit subjects to an LLM, checks the reply against the Conventional Commits rules, and lets you accept, edit, regenerate or split before anything is committed.

```
$ pilot commit
📋 Analyzing 5 staged files (+44 -3)...
✅ Suggested: feat(api): add IP-based rate limiting (100 req/min)
   Add a sliding-window limiter (100 req/min per IP) as a FastAPI dependency.
   It caps requests and returns 429 with Retry-After when exceeded.
   Update README, bump FastAPI to 0.115 and add httpx for tests.
[y] Accept  [e] Edit  [r] Regenerate  [s] Split into multiple commits  [n] Cancel >
```

The interesting part is **split mode**. Stage four unrelated changes at once and it plans four commits, then makes them:

```
$ pilot commit --split
📋 Analyzing 5 staged files (+32 -3)...
🧭 Grouping the changes...
✂  Split into 4 commits:
 1. ci: add GitHub Actions workflow for running tests
    .github/workflows/test.yml
 2. docs(readme): clarify rate limit description
    README.md
 3. feat(api): add limit parameter to items endpoint
    api/app.py
 4. feat(export): add CSV export helper
    api/export.py, tests/test_export.py
[y] Commit all  [e] Edit messages  [n] Cancel > y
[main ed135ce] ci: add GitHub Actions workflow for running tests
[main 7fa6207] docs(readme): clarify rate limit description
[main 11b1c03] feat(api): add limit parameter to items endpoint
[main f4908e0] feat(export): add CSV export helper
```

Both are real runs against Groq (`openai/gpt-oss-120b`) on a test repo. Each commit gets exactly the staged patch for its files, so what you staged is what gets committed.

> **Website →** [commitpilot.akshatgcodes.in](https://commitpilot.akshatgcodes.in)
> It's a CLI, so the site is a product page with install steps.

---

## What you get

- **`pilot commit`**: suggest, then `y` accept · `e` edit in your git editor · `r` regenerate · `s` split · `n` cancel
- **`pilot commit --split`**: go straight to the split plan; tests stay with the code they test, lockfiles with their manifest
- **`pilot message`**: print a suggestion only, for scripts and hooks
- **Checked output**: a reply that breaks the format (bad type, header over 72 characters, trailing period, capitalised subject) is sent back once with the problems listed
- **A warning on mixed diffs**: if the changes span separate areas and 80+ lines, `pilot commit` suggests splitting
- **Safe split**: the staged patch is saved under `.git/` first; if a commit fails (a hook, say), the commits not yet made are staged again
- **Emoji style**: `--style emoji` (or `PILOT_STYLE=emoji`) writes `✨ api: add x` instead of `feat(api): add x`
- **Any OpenAI-compatible model**: Groq by default, or OpenAI, or a local Ollama
- **Flags for scripts**: `--yes` commits without asking, `--dry-run` only shows the plan

---

## Stack

| Layer | Tech |
|---|---|
| CLI | argparse, ANSI colours (respects `NO_COLOR` and non-TTY output) |
| Git | the `git` CLI through `subprocess`: `diff --staged --binary -M`, `apply --cached`, `commit -F -` |
| LLM | LangChain (`ChatOpenAI` against any OpenAI-compatible API), few-shot Conventional Commits prompt |
| Config | pydantic-settings: env vars, `~/.config/commitpilot/config.env`, or `./.env` |
| Tooling | uv · pytest (real temp repos, fake chat model) · ruff · GitHub Actions |

---

## Run it

Needs Python 3.11+, git, and an API key ([Groq](https://console.groq.com/keys) has a free tier).

```bash
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...

cd your-repo
git add -A
python /path/to/CommitPilot/pilot.py commit
```

Or install it as a command with `uv tool install .` (or `pipx install .`) and run `pilot commit` in any repo. More in [docs/SETUP.md](docs/SETUP.md).

---

## Engineering Decisions

**Why not trust the model's split plan as-is?**
A plan that drops a file, invents one, or puts a file in two commits would lose or duplicate changes. Every plan is checked so each staged file appears exactly once; a bad plan is sent back once with the errors, and if it's still wrong CommitPilot falls back to grouping by folder.

**Why apply patches instead of `git add`-ing files per commit?**
`git add path` would pick up unstaged edits in the working tree. Applying each file's slice of the staged patch with `git apply --cached` commits exactly what you staged, including renames, deletions and binary files.

**Why send a condensed diff?**
Lockfiles and binaries are summarised in one line, each file is capped at 2,500 characters, and after 20,000 characters only stats are sent. Big diffs stay fast and cheap, and the model sees the code changes rather than `uv.lock`.

**What would you do differently in v2?**
Split by hunk, not just by file, so two unrelated changes in one file can go to different commits. And a `prepare-commit-msg` hook so plain `git commit` gets a suggestion too.

More in [docs/DECISIONS.md](docs/DECISIONS.md).

---

## Docs

| Document | Description |
|---|---|
| [PRD](docs/PRD.md) | Product requirements: goals, user stories, non-goals |
| [Architecture](docs/ARCHITECTURE.md) | Modules, the suggest flow and the split flow |
| [Decisions](docs/DECISIONS.md) | Every major technical decision and why |
| [Setup](docs/SETUP.md) | Install, configuration, CLI reference |
| [Deploy](docs/DEPLOY.md) | Installing it as a command for everyday use |
| [Contributing](CONTRIBUTING.md) | How to propose changes |
| [Changelog](CHANGELOG.md) | What changed in each release |
| [Security](SECURITY.md) | How to report a vulnerability |

---

<div align="center">

<h3>Akshat Gupta</h3>

<a href="https://akshatgcodes.in"><img src="https://img.shields.io/badge/Website-akshatgcodes.in-111111?style=flat-square&logo=googlechrome&logoColor=white" alt="Website"></a>
<a href="https://linkedin.com/in/akshatgcodes"><img src="https://img.shields.io/badge/LinkedIn-akshatgcodes-0A66C2?style=flat-square" alt="LinkedIn"></a>
<a href="https://github.com/akshatgcodes"><img src="https://img.shields.io/badge/GitHub-akshatgcodes-181717?style=flat-square&logo=github&logoColor=white" alt="GitHub"></a>
<a href="mailto:akshatgcodes@gmail.com"><img src="https://img.shields.io/badge/Email-akshatgcodes%40gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>

</div>

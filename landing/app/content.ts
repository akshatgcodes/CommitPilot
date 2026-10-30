import type { Site } from "./types";

export const site: Site = {
  name: "CommitPilot",
  letter: "P",
  title: "CommitPilot — commit messages, and commits split for you",
  description:
    "Run pilot commit instead of git commit -m. It reads your staged diff, writes a Conventional Commits message, and when the diff mixes unrelated work, offers to split it into separate commits.",
  meta: ["CLI", "git + LLM", "GPLv3"],
  headline: ["Four unrelated changes,", "four clean commits."],
  intro:
    "Run `pilot commit` instead of `git commit -m`. It reads your staged diff, writes a Conventional Commits message, and when the diff mixes unrelated work, offers to split it into separate commits.",
  primary: { label: "Install it", href: "#run-it" },
  repo: "https://github.com/akshatgcodes/CommitPilot",
  xfactor: {
    title: "Split mode commits exactly what you staged.",
    intro:
      "Stage everything at once and CommitPilot plans one commit per piece of work, checks the plan, and makes the commits from your staged patch.",
    features: [
      {
        icon: "✂",
        title: "Plans are checked",
        body: "Every staged file must appear in exactly one commit. A bad plan goes back to the model once with the errors; if it's still wrong, files are grouped by folder instead.",
      },
      {
        icon: "⎘",
        title: "Patches, not `git add`",
        body: "Each commit gets its files' slice of the staged patch through `git apply --cached`, so unstaged edits stay out, and renames, deletions and binaries survive.",
      },
      {
        icon: "↺",
        title: "Safe on failure",
        body: "The staged patch is saved under `.git/` first. If a commit fails (a hook, say), the commits not yet made are staged again.",
      },
    ],
  },
  preview: {
    intro: "A real run against Groq (`openai/gpt-oss-120b`) on a test repo with four unrelated changes staged together.",
    terminal: `$ pilot commit --split
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
[main f4908e0] feat(export): add CSV export helper`,
  },
  stack: ["Python 3", "argparse", "git", "subprocess", "LangChain", "Groq", "gpt-oss-120b", "pydantic-settings", "uv", "pytest", "ruff"],
  concepts: [
    { title: "Checked messages", body: "A reply with a bad type, a header over 72 characters, a trailing period or a capitalised subject is sent back once with the problems listed." },
    { title: "Condensed diff", body: "Lockfiles and binaries become one line, each file is capped at 2,500 characters, and past 20,000 only stats are sent." },
    { title: "Accept, edit, regenerate", body: "`y` accepts, `e` opens your git editor, `r` asks again, `s` splits, `n` cancels. Nothing is committed until you say so." },
    { title: "Your repo's style", body: "Recent commit subjects go into the prompt, and `--style emoji` writes `✨ api: add x` instead of `feat(api): add x`." },
    { title: "Script-friendly", body: "`pilot message` only prints a suggestion; `--yes` commits without asking and `--dry-run` only shows the plan." },
    { title: "Tested on real repos", body: "Tests create temporary git repositories and use a fake chat model, so splitting is checked against real `git` behaviour." },
  ],
  run: {
    title: "Install and run",
    intro: "Needs Python 3.11+, git, and an API key. Groq has a free tier; OpenAI or a local Ollama work too.",
    blocks: [
      {
        title: "Install",
        steps: [
          { text: "Clone and install it as a command:", cmd: "git clone https://github.com/akshatgcodes/CommitPilot\ncd CommitPilot && uv tool install ." },
          { text: "Give it a key:", cmd: "export GROQ_API_KEY=gsk_..." },
        ],
      },
      {
        title: "Use",
        steps: [
          { text: "Stage your work and ask for a message:", cmd: "git add -A\npilot commit" },
          { text: "Or go straight to the split plan:", cmd: "pilot commit --split" },
        ],
      },
    ],
  },
  tagline: "AI commit messages and commit splitting for git.",
};
